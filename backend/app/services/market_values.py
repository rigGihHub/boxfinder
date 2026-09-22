from __future__ import annotations
from datetime import datetime, timedelta
from statistics import median
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..models import CardMarketValue, Sale

SUPPORTED_CONDITIONS = {"raw", "psa_9", "psa_10", "bgs", "cgc"}


def _window_values(sales: list[Sale], now: datetime, days: int) -> list[float]:
    cutoff = now - timedelta(days=days)
    return [s.price_sek for s in sales if s.sold_at >= cutoff and s.price_sek > 0]


def _quality(count_90d: int, verified_count: int, source_count: int, dispersion: float | None) -> int:
    volume = min(55, count_90d * 7)
    verified = min(20, verified_count * 4)
    sources = min(15, source_count * 5)
    stability = 10
    if dispersion is not None:
        stability = max(0, round(10 * (1 - min(dispersion, 1.0))))
    return min(100, volume + verified + sources + stability)


def rebuild_market_value(db: Session, card_id: int, condition_bucket: str = "raw", now: datetime | None = None) -> CardMarketValue | None:
    now = now or datetime.utcnow()
    sales = db.scalars(
        select(Sale).where(Sale.card_id == card_id, Sale.condition_bucket == condition_bucket).order_by(Sale.sold_at.desc())
    ).all()
    if not sales:
        return None
    v7, v30, v90 = (_window_values(sales, now, d) for d in (7, 30, 90))
    relevant = v90 or [s.price_sek for s in sales if s.price_sek > 0]
    med90 = median(v90) if v90 else None
    dispersion = None
    if med90 and len(v90) >= 3:
        dispersion = (max(v90) - min(v90)) / med90
    quality = _quality(
        len(v90),
        sum(1 for s in sales if s.verified and s.sold_at >= now - timedelta(days=90)),
        len({s.source_name for s in sales if s.sold_at >= now - timedelta(days=90)}),
        dispersion,
    )
    mv = db.scalar(select(CardMarketValue).where(CardMarketValue.card_id == card_id, CardMarketValue.condition_bucket == condition_bucket))
    if not mv:
        mv = CardMarketValue(card_id=card_id, condition_bucket=condition_bucket)
        db.add(mv)
    mv.latest_price_sek = sales[0].price_sek
    mv.median_7d_sek = median(v7) if v7 else None
    mv.median_30d_sek = median(v30) if v30 else None
    mv.median_90d_sek = med90
    mv.low_90d_sek = min(v90) if v90 else (min(relevant) if relevant else None)
    mv.high_90d_sek = max(v90) if v90 else (max(relevant) if relevant else None)
    mv.sales_7d, mv.sales_30d, mv.sales_90d = len(v7), len(v30), len(v90)
    mv.data_quality = quality
    mv.updated_at = now
    db.flush()
    return mv


def preferred_value(mv: CardMarketValue) -> float | None:
    return mv.median_30d_sek or mv.median_90d_sek or mv.median_7d_sek or mv.latest_price_sek
