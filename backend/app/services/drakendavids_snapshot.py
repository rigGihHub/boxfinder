"""Complete one-time public Shopify inventory; unreviewed content is never scored."""
import gzip
import json
import re
from pathlib import Path
from urllib.parse import urlsplit

from bs4 import BeautifulSoup

from .new_retailers_snapshot import seed_inventory as import_inventory
from .kantovault_snapshot import snapshot_datetime

ROOT = Path(__file__).resolve().parents[1] / 'snapshots'
RAW = json.loads(gzip.decompress((ROOT / 'drakendavids_catalog_2026_10_15.json.gz').read_bytes()))


def classify(product):
    title = product['title'].lower()
    text = ' '.join([title, product.get('product_type', ''), *product.get('tags', [])]).lower()
    body = BeautifulSoup(product.get('body_html') or '', 'html.parser').get_text(' ', strip=True)
    reason = None
    if re.search(r'boxbreak|break\s*#|personal break', title):
        reason = 'Breakplats, inte en förseglad produkt som skickas hem'
    elif re.search(r'funko|minix|pussel|sleeve|toploader|ultra pro|magnetic|card holder|cardholder|stativ|pärm|förvaring|presentkort|frakt|gradering|sticker|album|card bag|team bag|cardpreserver|one touch', text):
        reason = 'Tillbehör, tjänst, klistermärken eller annan samlarvara'
    elif re.search(r'\s/\d|\bauto\b|memorabilia|psa\s*\d|\[rc\]| - inserts|box insert', title):
        reason = 'Singelkort eller vald insert, inte förseglad slumpmässig kortprodukt'
    formats = [
        (r'bundle|\b\d+st hobby box', 'bundle'),
        (r'\b1st.*(?:paket|pack)|fat pack|value pack|booster.paket|\b1st paket', 'single pack'),
        (r'blaster', 'blaster'), (r'mega box', 'mega box'),
        (r'value box', 'value box'), (r'jumbo', 'jumbo box'),
        (r'tin', 'tin'), (r'display|booster box|hel box', 'booster box'),
        (r'hobby|h2 box|tmall|choice box|breakaway', 'hobby box'),
        (r'team set|fan set|curated set|collector.*set', 'team set'),
        (r'eco pack|multipack|booster|\bpaket\b', 'single pack'),
        (r'\bbox\b|hobbybox', 'box'),
    ]
    fmt = next((fmt for pattern, fmt in formats if re.search(pattern, title)), None)
    if reason is None and fmt is None:
        reason = 'Förpackning och slumpmässigt kortinnehåll behöver granskas'
    if reason is None and fmt == 'team set' and not re.search(r'parallell|autogra|random|slump|chans', body, re.I):
        reason = 'Setets slumpmässiga innehåll behöver granskas'
    categories = [
        ('Star Wars', r'star wars'), ('Marvel', r'marvel'),
        ('Lorcana', r'lorcana'), ('Disney', r'disney'), ('Hockey', r'nhl|hockey|\bshl\b'),
        ('Basket', r'basket|\bnba\b'), ('Baseboll', r'baseball|baseboll'),
        ('NFL', r'\bnfl\b|amerikansk fotboll'), ('F1', r'formula 1|formel 1|\bf1\b'),
        ('Golf', r'golf'), ('UFC', r'ufc'), ('WWE', r'wwe|wrestling'),
        ('Fotboll', r'soccer|fifa|uefa|\bucc\b|\buwcl\b|premier league|bundesliga|serie a|la liga|fotboll|team set|fan set|collector tin|world cup|world football|\befl\b|copa america|match attax|adrenalyn|\beuro\b|\bmls\b|barcelona|arsenal|chelsea|liverpool|manchester|dortmund|real madrid|newcastle|tottenham|argentina|germany|topps (?:deco|inception|merlin|stadium|knockout)'),
    ]
    category = next((name for name, pattern in categories if re.search(pattern, text)), 'Övrigt')
    language = ('Japanese' if re.search(r'japansk|japanese', text + ' ' + body.lower()) else
                'English' if re.search(r'engelska|english', body, re.I) else
                'Swedish' if re.search(r'svenska kort|nordic edition|nordic', text) else 'Unknown')
    preorder = bool(re.search(r'förbok|förhandsbok|pre.?order|pre.?sale', title))
    # Only local sales notices count; a historic release date in marketing copy does not.
    preorder = preorder or bool(re.search(r'(?:detta är en|detta är en produkt för|available for)\s+(?:förbokning|förhandsbokning|pre.?order)', body, re.I))
    return fmt or 'unknown', category, language, preorder, reason, body


def build_catalog(raw, previous_offers):
    previous = {urlsplit(r.get('buy_url', '')).path.split('/products/')[-1]: r
                for r in previous_offers if r.get('store_name') == 'DrakenDavids'}
    variants, offers = [], []
    for product in raw['products']:
        fmt, category, language, preorder, reason, body = classify(product)
        old = previous.get(product['handle'])
        for variant in product['variants']:
            variant_id = str(variant['id'])
            title = product['title']
            if variant['title'] != 'Default Title':
                title += ' – ' + variant['title']
            url = f"{raw['base_url']}/products/{product['handle']}?variant={variant_id}"
            price = float(variant['price'])
            stock = 'in_stock' if variant['available'] else 'out_of_stock'
            row = dict(id=variant_id, product_id=str(product['id']), title=title, url=url,
                       price_sek=price, stock_status=stock, format=fmt, category=category,
                       language=language, preorder=preorder, randomized_cards=reason is None,
                       exclusion_reason=reason, observed_at=raw['observed_at'])
            variants.append(row)
            if reason is not None or price <= 0:
                continue
            # Keep existing product, offer and chase-profile identities for exact URL matches.
            offer = dict(old) if old and len(product['variants']) == 1 else {}
            offer.update(slug=offer.get('slug', f"dd-{product['handle']}-{variant_id}"),
                         sku=offer.get('sku', f'DD-SHOPIFY-{variant_id}'), name=title,
                         store_name='DrakenDavids', price=price, stock=stock, preorder=preorder,
                         observed_at=snapshot_datetime(raw['observed_at']), buy_url=url,
                         category=offer.get('category', category), fmt=offer.get('fmt', fmt),
                         language=offer.get('language', language), packs=offer.get('packs'),
                         cards=offer.get('cards'), manufacturer=offer.get('manufacturer', product.get('vendor') or 'Unknown'),
                         year=offer.get('year', ''), series=offer.get('series', product['title']),
                         facts=offer.get('facts', []))
            offers.append(offer)
            row['offer_sku'] = offer['sku']
    return {**{k: v for k, v in raw.items() if k != 'products'}, 'variants': variants}, offers


def seed_inventory(session_factory, inventory):
    import_inventory(session_factory, {'DrakenDavids': inventory})
