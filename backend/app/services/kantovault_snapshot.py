"""Reviewed one-time Kantovault inventory; never enables scheduled collection."""
import json
from datetime import datetime
from pathlib import Path

from sqlalchemy import select

from ..models import CatalogCandidate, Store

SNAPSHOT_DIR = Path(__file__).resolve().parents[1] / "snapshots"
INVENTORY = json.loads((SNAPSHOT_DIR / "kantovault_2026_10_04.json").read_text())
OFFERS = json.loads((SNAPSHOT_DIR / "kantovault_offers_2026_10_04.json").read_text())
PROFILES = json.loads((SNAPSHOT_DIR / "kantovault_profiles_2026_10_04.json").read_text())


def snapshot_datetime(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)


def seed_inventory(session_factory):
    with session_factory() as db:
        store = db.scalar(select(Store).where(Store.name == "Kantovault"))
        if store is None:
            store = Store(name="Kantovault", country="SE", active=True,
                          collection_method="manual", adapter_key="manual",
                          policy_status="review_required", min_interval_seconds=120)
            db.add(store)
            db.flush()
        store.homepage_url = "https://kantovault.se/"
        store.source_url = "https://kantovault.se/collections/all"
        existing = {c.external_id: c for c in db.scalars(
            select(CatalogCandidate).where(CatalogCandidate.store_id == store.id))}
        for row in INVENTORY["variants"]:
            observed_at = snapshot_datetime(row["observed_at"])
            candidate = existing.get(row["id"])
            if candidate and candidate.last_seen_at >= observed_at:
                continue
            if candidate is None:
                candidate = CatalogCandidate(store_id=store.id, external_id=row["id"],
                                             first_seen_at=observed_at)
                db.add(candidate)
            candidate.source_title = row["title"]
            candidate.url = row["url"]
            candidate.price_sek = row["price_sek"]
            candidate.stock_status = row["stock_status"]
            candidate.detected_format = row["format"]
            candidate.category_hint = row["category"]
            candidate.language_hint = row["language"]
            candidate.sealed_candidate = row["randomized_cards"]
            candidate.randomized = row["randomized_cards"]
            candidate.exclusion_reason = row["exclusion_reason"]
            candidate.review_status = "linked" if row.get("offer_sku") else "new"
            candidate.last_seen_at = observed_at
        db.commit()
