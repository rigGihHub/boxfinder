"""Manually verified standard shipping within Sweden. Dates never advance on boot."""
from datetime import datetime
from sqlalchemy import select
from ..database import SessionLocal
from ..models import ShippingPolicy, Store

CHECKED_AT = datetime(2026, 10, 3, 21, 14)
# AlphaSpel's terms explicitly state 59 SEK for DHL parcel-point delivery.
# Their current page footer states free shipping within Sweden from 1,000 SEK.
SHIPPING_SNAPSHOT = [dict(store="AlphaSpel", base=59, free_from=1000,
                         source="https://alphaspel.se/kopvillkor/")]


def seed_shipping_policies():
    with SessionLocal() as db:
        for row in SHIPPING_SNAPSHOT:
            store = db.scalar(select(Store).where(Store.name == row["store"]))
            if store is None:
                continue
            policy = db.scalar(select(ShippingPolicy).where(ShippingPolicy.store_id == store.id))
            if policy is not None and policy.updated_at >= CHECKED_AT:
                continue
            if policy is None:
                policy = ShippingPolicy(store_id=store.id)
                db.add(policy)
            policy.base_shipping_sek = row["base"]
            policy.free_shipping_threshold_sek = row["free_from"]
            policy.source_url = row["source"]
            policy.verification_status = "manual_verified"
            policy.confidence = 100
            policy.updated_at = CHECKED_AT
        db.commit()
