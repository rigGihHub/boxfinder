"""Fetch public Shopify catalogues once for separate identity/content review.

Usage: python scripts/snapshot_new_retailers_once.py /tmp/retailer-evidence
The raw output is evidence, never permission to promote or schedule collection.
"""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen

SHOPS = {
    'Hobbybutiken': 'https://hobbybutiken.com',
    'TheMinifigVault': 'https://theminifigvault.com',
    'The Sealed Poke Vault': 'https://www.tspvault.se',
}


def collect(name, base):
    products, page_counts = [], []
    for page in range(1, 100):
        with urlopen(f'{base}/products.json?limit=250&page={page}', timeout=40) as response:
            rows = json.load(response)['products']
        products.extend(rows)
        page_counts.append(len(rows))
        if not rows:
            break
    else:
        raise RuntimeError(f'Incomplete pagination for {name}')
    if len({p['id'] for p in products}) != len(products):
        raise RuntimeError(f'Duplicate products across pages for {name}')
    return dict(store_name=name, base_url=base,
                observed_at=datetime.now(timezone.utc).isoformat(),
                page_counts=page_counts, pagination_complete=True, products=products)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    for name, base in SHOPS.items():
        result = collect(name, base)
        filename = name.lower().replace(' ', '_') + '.json'
        (args.output / filename).write_text(json.dumps(result, ensure_ascii=False))
        print(name, len(result['products']), 'products', flush=True)
