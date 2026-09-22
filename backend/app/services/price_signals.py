from __future__ import annotations
import json
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..models import Offer, PriceHistory, PriceSignal, ProductVariant, Store

SIGNAL_LABELS = {
    "price_drop": "Prisfall",
    "new_30d_low": "Nytt 30-dagarslägsta",
    "new_90d_low": "Nytt 90-dagarslägsta",
    "back_in_stock": "Åter i lager",
    "new_store": "Ny butik för boxen",
}

def detect_offer_signals(db: Session, offer: Offer, *, previous_price: float | None,
                         previous_stock: str | None, now: datetime | None = None) -> list[PriceSignal]:
    now = now or datetime.utcnow()
    signals: list[PriceSignal] = []
    price = offer.price_sek

    def add(kind: str, **evidence):
        pct = None
        if previous_price and price and previous_price > 0:
            pct = (price - previous_price) / previous_price * 100
        signal = PriceSignal(
            offer_id=offer.id, variant_id=offer.variant_id, store_id=offer.store_id,
            signal_type=kind, old_price_sek=previous_price, new_price_sek=price,
            change_pct=round(pct, 1) if pct is not None else None,
            previous_stock_status=previous_stock, current_stock_status=offer.stock_status,
            evidence=json.dumps(evidence, ensure_ascii=False),
            observed_at=now,
        )
        db.add(signal); signals.append(signal)

    if previous_price and price < previous_price * .98:
        add("price_drop", threshold=">2%")

    if previous_stock and previous_stock != "in_stock" and offer.stock_status == "in_stock":
        add("back_in_stock")

    # Compare only with observations strictly before this ingestion moment.
    if price and price > 0:
        for days, kind in [(30, "new_30d_low"), (90, "new_90d_low")]:
            cutoff = now - timedelta(days=days)
            previous = db.scalars(
                select(PriceHistory.price_sek)
                .join(Offer, PriceHistory.offer_id == Offer.id)
                .where(Offer.variant_id == offer.variant_id)
                .where(PriceHistory.observed_at >= cutoff)
                .where(PriceHistory.observed_at < now)
                .where(PriceHistory.price_sek > 0)
            ).all()
            if previous and price < min(previous):
                add(kind, previous_low=min(previous), window_days=days)

    # First trusted offer from this store for this variant.
    if offer.variant_id:
        others = db.scalar(
            select(Offer.id)
            .where(Offer.variant_id == offer.variant_id)
            .where(Offer.store_id == offer.store_id)
            .where(Offer.id != offer.id)
            .limit(1)
        )
        if others is None:
            # Only meaningful when at least one other store already covers the variant.
            other_store = db.scalar(
                select(Offer.id)
                .where(Offer.variant_id == offer.variant_id)
                .where(Offer.store_id != offer.store_id)
                .limit(1)
            )
            if other_store is not None:
                add("new_store")

    return signals

def recent_signals(db: Session, days: int = 7, limit: int = 100, variant_id: int | None = None) -> list[dict]:
    cutoff = datetime.utcnow() - timedelta(days=days)
    q = (
        select(PriceSignal)
        .where(PriceSignal.observed_at >= cutoff)
        .order_by(PriceSignal.observed_at.desc())
    )
    if variant_id is not None:
        q = q.where(PriceSignal.variant_id == variant_id)
    rows = db.scalars(q.limit(limit)).all()

    variant_ids = {s.variant_id for s in rows}
    store_ids = {s.store_id for s in rows}
    variants = {
        v.id: v for v in db.scalars(select(ProductVariant).where(ProductVariant.id.in_(variant_ids))).all()
    } if variant_ids else {}
    stores = {
        s.id: s for s in db.scalars(select(Store).where(Store.id.in_(store_ids))).all()
    } if store_ids else {}

    result = []
    for s in rows:
        v = variants.get(s.variant_id)
        store = stores.get(s.store_id)
        product_name = None
        category = None
        if v is not None:
            product_name = f"{v.product.canonical_name} {v.format}"
            category = v.product.category
        result.append({
            "id": s.id,
            "variant_id": s.variant_id,
            "store_id": s.store_id,
            "store_name": store.name if store else None,
            "product_name": product_name,
            "category": category,
            "signal_type": s.signal_type,
            "label": SIGNAL_LABELS.get(s.signal_type, s.signal_type),
            "old_price_sek": s.old_price_sek,
            "new_price_sek": s.new_price_sek,
            "change_pct": s.change_pct,
            "previous_stock_status": s.previous_stock_status,
            "current_stock_status": s.current_stock_status,
            "observed_at": s.observed_at.isoformat(),
            "evidence": json.loads(s.evidence) if s.evidence else {},
        })
    return result

def signal_summary(db: Session, days: int = 7) -> dict:
    rows = recent_signals(db, days=days, limit=1000)
    counts = {key: 0 for key in SIGNAL_LABELS}
    for row in rows:
        counts[row["signal_type"]] = counts.get(row["signal_type"], 0) + 1

    biggest_drop = None
    drops = [r for r in rows if r["signal_type"] == "price_drop" and r["change_pct"] is not None]
    if drops:
        biggest_drop = min(drops, key=lambda r: r["change_pct"])

    newest_lows = [
        r for r in rows if r["signal_type"] in {"new_30d_low", "new_90d_low"}
    ][:10]

    return {
        "days": days,
        "total_signals": len(rows),
        "price_drops": counts.get("price_drop", 0),
        "new_30d_lows": counts.get("new_30d_low", 0),
        "new_90d_lows": counts.get("new_90d_low", 0),
        "back_in_stock": counts.get("back_in_stock", 0),
        "new_stores": counts.get("new_store", 0),
        "biggest_drop": biggest_drop,
        "newest_lows": newest_lows,
    }
