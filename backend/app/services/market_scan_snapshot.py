"""Manually reviewed sports/TCG offers, separate from complete inventories."""
import gzip
import json
from pathlib import Path

from .new_retailers_snapshot import seed_inventory as import_inventory

ROOT = Path(__file__).resolve().parents[1] / 'snapshots'
REVIEW = json.loads((ROOT / 'market_scan_review_2026_10_07.json').read_text())
INVENTORIES = {
    name: json.loads(gzip.decompress((ROOT / filename).read_bytes()))
    for name, filename in REVIEW['inventories'].items()
}
OFFERS = json.loads((ROOT / 'market_scan_offers_2026_10_07.json').read_text())
PROFILES = json.loads((ROOT / 'market_scan_profiles_2026_10_07.json').read_text())


def seed_inventory(session_factory):
    import_inventory(session_factory, INVENTORIES)
