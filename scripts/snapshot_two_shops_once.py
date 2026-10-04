"""Collect complete public catalogues once; preserve evidence for separate review.

No scheduled scraping or automatic promotion. Resume cached observations after
interruptions rather than requesting the same product again.
"""
import json
import os
import ssl
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen, Request
from xml.etree import ElementTree as ET

from bs4 import BeautifulSoup
import httpx

CACHE = Path('/tmp/boxfinder-two-shops')
CACHE.mkdir(exist_ok=True)
CLIENT = httpx.Client(timeout=35, follow_redirects=True, trust_env=False,
                      verify=ssl.create_default_context(),
                      proxy=os.environ.get('HTTPS_PROXY'),
                      limits=httpx.Limits(max_connections=8, max_keepalive_connections=8),
                      headers={'User-Agent': 'BoxFinder/0.59 catalogue import'})


def now():
    return datetime.now(timezone.utc).isoformat()


def fetch(url):
    for attempt in range(3):
        try:
            response = CLIENT.get(url)
            response.raise_for_status()
            return response.content
        except Exception:
            if attempt == 2:
                raise


def collect_speltrollet():
    products, pages = [], []
    for page in range(1, 100):
        path = CACHE / f'sp-page-{page}.json'
        if not path.exists():
            path.write_bytes(fetch(f'https://speltrollet.se/products.json?limit=250&page={page}'))
        rows = json.loads(path.read_text())['products']
        pages.append(len(rows))
        products.extend(rows)
        print('Speltrollet page', page, len(rows), flush=True)
        if not rows:
            break
    else:
        raise RuntimeError('Speltrollet pagination incomplete')
    if len({p['id'] for p in products}) != len(products):
        raise RuntimeError('Duplicate Shopify product across pages')
    result = dict(observed_at=now(), page_counts=pages, pagination_complete=True,
                  source='https://speltrollet.se/products.json?limit=250', products=products)
    (CACHE / 'speltrollet-raw.json').write_text(json.dumps(result, ensure_ascii=False))
    return result


def sitemap_urls(url):
    root = ET.fromstring(fetch(url))
    return [x.text for x in root.iter() if x.tag.endswith('}loc')]


def collect_coolcard_index():
    maps = [u for u in sitemap_urls('https://www.coolcard.se/sitemap.xml')
            if '/sitemap-products-sv-' in u]
    with ThreadPoolExecutor(max_workers=4) as pool:
        pages = list(pool.map(sitemap_urls, maps))
    urls = sorted(set(u for page in pages for u in page))
    result = dict(observed_at=now(), source='https://www.coolcard.se/sitemap.xml',
                  sitemaps=maps, page_counts=[len(p) for p in pages],
                  pagination_complete=True, urls=urls)
    (CACHE / 'coolcard-index.json').write_text(json.dumps(result, ensure_ascii=False, indent=2))
    print('Coolcard index', len(urls), 'products', flush=True)
    return result


def coolcard_product(url):
    path = CACHE / ('cc-' + url.rsplit('/', 1)[-1] + '.json')
    if path.exists():
        return json.loads(path.read_text())
    soup = BeautifulSoup(fetch(url), 'html.parser')
    product, breadcrumbs = None, []
    for node in soup.select('script[type="application/ld+json"]'):
        try:
            data = json.loads(node.get_text())
        except ValueError:
            continue
        for obj in data if isinstance(data, list) else [data]:
            if obj.get('@type') == 'Product':
                product = obj
            elif obj.get('@type') == 'BreadcrumbList':
                breadcrumbs.append([item['name'] for item in obj['itemListElement']])
    if product is None:
        raise ValueError('Missing product schema: ' + url)
    description = soup.select_one('.product-long-description')
    status = soup.select_one('dd.product-stock-status')
    result = dict(url=url, observed_at=now(), schema=product, breadcrumbs=breadcrumbs,
                  description=description.get_text(' ', strip=True) if description else '',
                  stock_text=status.get_text(' ', strip=True) if status else '')
    path.write_text(json.dumps(result, ensure_ascii=False))
    return result


def cached_json(key, url):
    path = CACHE / (key + '.json')
    if not path.exists():
        path.write_bytes(fetch(url))
    return json.loads(path.read_text())


def coolcard_category(node):
    rows, page_counts = [], []
    for page in range(1, 1000):
        data = cached_json(f'cc-list-{node["id"]}-{page}',
            f'https://www.coolcard.se/category/{node["id"]}/get-product-list-tmpl-data?blockId=13&page={page}')
        products = data['productListTmplData']['products']
        rows.extend(products)
        page_counts.append(len(products))
        expected = int(data.get('totalSearchResultsCount', len(rows)))
        if len(rows) >= expected:
            break
        if not products:
            raise RuntimeError(f'Incomplete category {node["id"]}: {len(rows)}/{expected}')
    else:
        raise RuntimeError('Category pagination did not finish')
    return dict(category=node, page_counts=page_counts, expected=expected,
                products=rows, observed_at=now())


def collect_coolcard_catalog():
    soup = BeautifulSoup(fetch('https://www.coolcard.se/'), 'html.parser')
    nodes = {int(a['data-id']): dict(id=int(a['data-id']), name=a.get_text(' ', strip=True),
                                   shopUrl=a['href']) for a in soup.select('a.category-node[href]')}
    roots = list(nodes.values())
    def tree(node):
        return cached_json('cc-tree-' + str(node['id']),
                           f'https://www.coolcard.se/category/{node["id"]}/get-child-tree-tmpl')
    def flatten(items):
        for node in items:
            if node.get('openPage') and node.get('shopUrl'):
                nodes[node['id']] = node
            flatten(node.get('nodes', []))
    with ThreadPoolExecutor(max_workers=8) as pool:
        for result in pool.map(tree, roots):
            flatten(result['nodes'])
    print('Coolcard categories', len(nodes), flush=True)
    products, categories = {}, []
    with ThreadPoolExecutor(max_workers=8) as pool:
        for i, result in enumerate(pool.map(coolcard_category, nodes.values()), 1):
            categories.append({k: result[k] for k in ('category', 'page_counts', 'expected')})
            for row in result['products']:
                row = dict(row, observed_at=result['observed_at'])
                products[row['id']] = row
            if i % 20 == 0:
                print('Coolcard categories read', i, 'unique products', len(products), flush=True)
    index = json.loads((CACHE / 'coolcard-index.json').read_text())
    covered = {'https://www.coolcard.se' + p['url'] for p in products.values()}
    missing = sorted(set(index['urls']) - covered)
    result = dict(observed_at=now(), source=index['source'], pagination_complete=True,
                  categories=categories, products=list(products.values()),
                  sitemap_count=len(index['urls']), missing_sitemap_urls=missing)
    (CACHE / 'coolcard-catalog.json').write_text(json.dumps(result, ensure_ascii=False))
    print('Coolcard complete listings', len(products), 'sitemap gaps', len(missing), flush=True)
    return result


def speltrollet_product(product):
    path = CACHE / f'sp-product-{product["id"]}.json'
    if path.exists():
        return json.loads(path.read_text())
    url = 'https://speltrollet.se/products/' + product['handle']
    soup = BeautifulSoup(fetch(url), 'html.parser')
    for n in soup(['script', 'style', 'header', 'footer', 'nav']):
        n.decompose()
    text = soup.get_text(' ', strip=True)
    # Only product-local content; exclude general shop preorder/returns FAQs.
    result = dict(url=url, observed_at=now(), text=text,
                  preorder=bool(re.search(r'förbeställ|förhandsbok|pre[- ]?order|pre[- ]?sale', text, re.I)))
    path.write_text(json.dumps(result, ensure_ascii=False))
    return result


if __name__ == '__main__':
    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(lambda f: f(), [collect_speltrollet, collect_coolcard_index]))
    catalogue = collect_coolcard_catalog()
    # Items absent from category lists still belong to the full public sitemap.
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(coolcard_product, catalogue['missing_sitemap_urls']))
