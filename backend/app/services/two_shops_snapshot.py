"""Complete, separately reviewed one-time shop catalogues (facts only).

Full catalogues remain searchable in the review queue. Ranking promotion uses
explicit offer records and a separate content profile; inventory alone never
creates a rankable product or enables scheduled collection.
"""
import gzip
import json
from pathlib import Path

from sqlalchemy import select

from ..models import CatalogCandidate, Store
from .kantovault_snapshot import snapshot_datetime

ROOT = Path(__file__).resolve().parents[1] / 'snapshots'
INVENTORIES = {
    name: json.loads(gzip.decompress((ROOT / f'{name.lower()}_catalog_2026_10_04.json.gz').read_bytes()))
    for name in ('Speltrollet', 'Coolcard')
}
OFFERS = json.loads((ROOT / 'two_shops_offers_2026_10_04.json').read_text())
PROFILES = json.loads((ROOT / 'two_shops_profiles_2026_10_04.json').read_text())


def seed_inventory(session_factory, name):
    inventory = INVENTORIES[name]
    with session_factory() as db:
        store = db.scalar(select(Store).where(Store.name == name))
        if store is None:
            store = Store(name=name, country='SE', active=True,
                          collection_method='manual', adapter_key='manual',
                          policy_status='review_required', min_interval_seconds=120)
            db.add(store)
            db.flush()
        existing = {c.external_id: c for c in db.scalars(
            select(CatalogCandidate).where(CatalogCandidate.store_id == store.id))}
        new_rows = []
        for row in inventory['variants']:
            observed = snapshot_datetime(row['observed_at'])
            candidate = existing.get(row['id'])
            if candidate and candidate.last_seen_at >= observed:
                continue
            values = dict(source_title=row['title'], url=row['url'],
                          price_sek=row['price_sek'], stock_status=row['stock_status'],
                          detected_format=row['format'], category_hint=row['category'],
                          language_hint=row['language'], sealed_candidate=row['randomized_cards'],
                          randomized=row['randomized_cards'], exclusion_reason=row['exclusion_reason'],
                          last_seen_at=observed)
            if candidate:
                for key, value in values.items():
                    setattr(candidate, key, value)
                # Preserve explicit human review decisions when refreshing facts.
                if candidate.review_status not in ('rejected', 'linked') and row.get('offer_sku'):
                    candidate.review_status = 'linked'
            else:
                new_rows.append(dict(store_id=store.id, external_id=row['id'],
                                     first_seen_at=observed,
                                     review_status='linked' if row.get('offer_sku') else 'new', **values))
        if new_rows:
            db.execute(CatalogCandidate.__table__.insert(), new_rows)
        db.commit()
