"""Fetch all public DrakenDavids product pages once; stop at an empty page.

Usage: python scripts/snapshot_drakendavids_once.py /tmp/drakendavids.json.gz
Review the new snapshot before replacing the bundled catalogue.
"""
import argparse
import gzip
import json
from pathlib import Path
from snapshot_new_retailers_once import collect

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    result = collect('DrakenDavids', 'https://www.drakendavids.se')
    variants = [str(v['id']) for p in result['products'] for v in p['variants']]
    if len(variants) != len(set(variants)):
        raise RuntimeError('Duplicate variant IDs; catalogue not saved')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(gzip.compress(json.dumps(result, ensure_ascii=False).encode(), mtime=0))
    print(len(result['products']), 'products,', len(variants), 'variants, pages', result['page_counts'])
