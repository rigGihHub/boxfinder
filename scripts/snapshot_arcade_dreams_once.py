"""One-time public Arcade Dreams navigation catalogue collection.

Usage: python scripts/snapshot_arcade_dreams_once.py OUTPUT_DIRECTORY
Uses the same guest sort preference and public products_load request as the
storefront. No account, purchase action, automatic matching or schedule.
Requires beautifulsoup4. Individual offers need separate article-page review.
"""
import argparse
import json,time
from pathlib import Path
from datetime import datetime,timezone
from urllib.request import build_opener,HTTPCookieProcessor,Request
from urllib.parse import urlencode,urljoin
from http.cookiejar import CookieJar
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('output',type=Path)
args=parser.parse_args()
ROOT=args.output
ROOT.mkdir(parents=True,exist_ok=True)
BASE='https://arcadedreams.se'
def req(op,url,data=None):
 for attempt in range(3):
  try:
   with op.open(Request(url,data=urlencode(data).encode()if data else None,headers={'Content-Type':'application/x-www-form-urlencoded'}if data else {}),timeout=25)as r:return r.read()
  except Exception:
   if attempt==2:raise
   time.sleep(1+attempt)
# Public visitor preference picks the UI's A-Z sort for stable pagination.
op=build_opener(HTTPCookieProcessor(CookieJar()));req(op,BASE+'/shop/tcg');print('sort',req(op,BASE+'/action',dict(sbmt='cat_sort',opt='a-z'))[:100],flush=True)
main=BeautifulSoup(req(op,BASE+'/shop/tcg'),'html.parser');routes=sorted({a['href'].rstrip('/')for a in main.select('nav a[href]')if a['href'].startswith('/shop/')and a['href']not in ['/shop/varukorg']});routes.sort(key=lambda r: r!='/shop/tcg');print('routes',routes,flush=True)
def parse_items(html):
 s=BeautifulSoup(html,'html.parser');rows=[]
 for a in s.select('a.item[data-id]'):
  title=a.select_one('.title').get_text(' ',strip=True);stock=int(a.get('data-stock','0'));pre=a.get('data-pre-book')=='1';d=a.select_one('.descr');img=a.select_one('.img')
  rows.append(dict(id=a['data-id'],title=title,url=urljoin(BASE,a['href']),price_sek=float(a['data-price']),stock_quantity=stock,stock_status='preorder'if pre else 'in_stock'if stock>0 else 'out_of_stock',preorder=pre,categories=[x for x in a.get('data-categories','').split(',')if x],description_hint=d.get_text(' ',strip=True)if d else '',image_url=urljoin(BASE,img.get('data-src',''))if img else None))
 return rows
# Each worker has an independent visitor cookie, sorted through the same public UI operation.
def collect(route):
 local=build_opener(HTTPCookieProcessor(CookieJar()));req(local,BASE+route);req(local,BASE+'/action',dict(sbmt='cat_sort',opt='a-z'))
 b=req(local,BASE+route);s=BeautifulSoup(b,'html.parser');c=s.select_one('#category');im=s.select_one('#items_main')
 if not c or not im:return dict(route=route,error='No category listing')
 batch=int(im['data-batch']);rows=[];counts=[]
 for page in range(100):
  params=dict(sbmt='products_load',shop_url=c['data-shop-url'],cat_id=c['data-id'],subcat_id='',sort=im['data-sort'],batch=batch,loaded=page*batch,in_stock=0,prod_name='',price_range_min=0,price_range_max=0)
  b=req(local,BASE+'/action',params);result=json.loads(b);items=parse_items(result.get('items') or '');counts.append(len(items));rows+=items
  if not items:
   assert result.get('items_tot',0)==0 and not result.get('items'),result
   break
 else:raise ValueError('Incomplete pagination '+route)
 assert len({r['id']for r in rows})==len(rows),'Duplicate page entries '+route
 data=dict(route=route,category_id=c['data-id'],title=c.select_one('h1').get_text(' ',strip=True),source=BASE+route,sort=im['data-sort'],batch=batch,page_counts=counts,pagination_complete=True,observed_at=datetime.now(timezone.utc).isoformat(),products=rows)
 (ROOT/('category-'+c['data-id']+'.json')).write_text(json.dumps(data,ensure_ascii=False));print(route,len(rows),'pages',counts,flush=True);return data
with ThreadPoolExecutor(max_workers=4)as pool:results=list(pool.map(collect,routes))
assert not any(r.get('error')for r in results),results
products={}
for result in results:
 for row in result['products']:
  if row['id']not in products:products[row['id']]=dict(row,observed_at=result['observed_at'],listing_routes=[])
  products[row['id']]['listing_routes'].append(result['route'])
cat=dict(store_name='Arcade Dreams',source=BASE,observed_at=datetime.now(timezone.utc).isoformat(),record_scope='all_public_navigation_categories',pagination_complete=True,categories=[{k:v for k,v in r.items()if k!='products'}for r in results],product_count=len(products),products=list(products.values()))
(ROOT/'catalog.json').write_text(json.dumps(cat,ensure_ascii=False));print('TOTAL',len(products),'TCG',sum('25'in p['categories']for p in products.values()),flush=True)
