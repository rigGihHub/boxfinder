from __future__ import annotations
from datetime import datetime, timedelta
from statistics import median
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..models import ProductVariant, ShippingPolicy

TRUSTED_MATCH_STATUSES = {"auto_matched", "manual_matched"}
MAX_OFFER_AGE_DAYS = 14

def shipping_for(policy: ShippingPolicy | None, item_price: float) -> tuple[float | None, str]:
    if policy is None:
        return None, "unknown"
    if policy.verification_status not in {"verified", "manual_verified"}:
        return None, "unverified"
    if policy.free_shipping_threshold_sek is not None and item_price >= policy.free_shipping_threshold_sek:
        return 0.0, "verified"
    if policy.base_shipping_sek is None:
        return None, "unknown"
    return max(0.0, float(policy.base_shipping_sek)), "verified"

def comparison_for_variant(db: Session, variant: ProductVariant, now: datetime | None = None) -> dict:
    now = now or datetime.utcnow()
    cutoff = now - timedelta(days=MAX_OFFER_AGE_DAYS)
    policies = {p.store_id: p for p in db.scalars(select(ShippingPolicy)).all()}
    eligible = []
    for o in variant.offers:
        trusted = o.match_status in TRUSTED_MATCH_STATUSES or o.source_kind == "demo"
        if not trusted or o.is_preorder or o.stock_status != "in_stock":
            continue
        if o.source_kind != "demo" and o.observed_at and o.observed_at < cutoff:
            continue
        shipping, shipping_status = shipping_for(policies.get(o.store_id), o.price_sek)
        total = o.price_sek + shipping if shipping is not None else None
        eligible.append({
            "offer_id": o.id, "store_id": o.store_id, "store": o.store.name,
            "item_price_sek": round(o.price_sek, 2),
            "shipping_sek": round(shipping, 2) if shipping is not None else None,
            "total_price_sek": round(total, 2) if total is not None else None,
            "shipping_status": shipping_status, "stock_status": o.stock_status,
            "url": o.url, "observed_at": o.observed_at.isoformat() if o.observed_at else None,
            "source_kind": o.source_kind, "source_confidence": o.source_confidence,
            "match_status": o.match_status,
        })
    eligible.sort(key=lambda x: (x["total_price_sek"] is None, x["total_price_sek"] if x["total_price_sek"] is not None else x["item_price_sek"], x["item_price_sek"]))
    item_prices = [x["item_price_sek"] for x in eligible]
    totals = [x["total_price_sek"] for x in eligible if x["total_price_sek"] is not None]
    best_item = min(eligible, key=lambda x: x["item_price_sek"]) if eligible else None
    best_total = min([x for x in eligible if x["total_price_sek"] is not None], key=lambda x: x["total_price_sek"], default=None)
    market_median = median(item_prices) if len(item_prices) >= 2 else None
    spread = max(item_prices)-min(item_prices) if len(item_prices) >= 2 else None
    saving = market_median-best_item["item_price_sek"] if best_item and market_median else None
    return {
        "variant_id": variant.id, "offer_count": len(eligible), "store_count": len({x["store_id"] for x in eligible}),
        "best_item_price": best_item, "best_total_price": best_total,
        "market_median_item_price_sek": round(market_median,2) if market_median is not None else None,
        "price_spread_sek": round(spread,2) if spread is not None else None,
        "saving_vs_store_median_sek": round(saving,2) if saving is not None else None,
        "shipping_coverage": {"known":len(totals),"total":len(eligible),"pct":round(len(totals)/len(eligible)*100) if eligible else 0},
        "offers": eligible,
        "note": "Totalpris inkluderar frakt endast när butikens fraktregel är verifierad. Okänd frakt visas inte som 0 kr.",
    }
