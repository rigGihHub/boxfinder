from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload
from ..database import get_db
from ..models import Offer, ProductVariant
from ..services.scoring import calculate_box_value_score
from ..services.deal_scoring import robust_market_reference, deal_confidence, enhanced_deal_score, cross_store_discount, history_low_position, deal_label
from ..services.price_signals import recent_signals, signal_summary

router = APIRouter(prefix="/deals", tags=["deals"])

@router.get("")
def list_deals(days: int = Query(90, ge=7, le=365), min_discount: float = Query(8, ge=0, le=90), db: Session = Depends(get_db)):
    now = datetime.utcnow()
    cutoff = now - timedelta(days=days)
    fresh_cutoff = now - timedelta(days=14)
    q = select(ProductVariant).options(
        joinedload(ProductVariant.product), joinedload(ProductVariant.analysis),
        joinedload(ProductVariant.offers).joinedload(Offer.store),
        joinedload(ProductVariant.offers).joinedload(Offer.history),
    )
    variants = db.execute(q).unique().scalars().all()
    result = []
    for v in variants:
        current = [
            o for o in v.offers
            if o.stock_status == "in_stock"
            and not o.is_preorder
            and o.match_status in {"auto_matched", "manual_matched"}
            and o.source_kind != "demo"
            and (o.observed_at is None or o.observed_at >= fresh_cutoff)
        ]
        if not current:
            continue
        best = min(current, key=lambda o: o.price_sek)
        history = [h.price_sek for o in v.offers for h in o.history if h.observed_at >= cutoff and h.price_sek > 0]
        reference = robust_market_reference(history, [o.price_sek for o in current])
        if reference is None or reference <= 0:
            continue
        discount = (reference - best.price_sek) / reference * 100
        if discount < min_discount:
            continue
        a = v.analysis
        box_score = calculate_box_value_score(
            price=best.price_sek, market_median=reference,
            ev_low=a.ev_low if a else None, ev_high=a.ev_high if a else None,
            checklist_strength=a.checklist_strength if a else None, hit_density=a.hit_density if a else None,
            upside=a.upside if a else None, floor_score=a.floor_score if a else None,
            rookie_strength=a.rookie_strength if a else None, liquidity=a.liquidity if a else None,
            popularity=a.popularity if a else None, data_quality=a.data_quality if a else 0,
        )
        store_count = len({o.store_id for o in current})
        confidence = deal_confidence(
            observations=len(history), store_count=store_count,
            data_quality=a.data_quality if a else 0, discount_pct=discount,
        )
        cross_discount = cross_store_discount(best.price_sek, [o.price_sek for o in current])
        history_position = history_low_position(best.price_sek, history)
        dscore = enhanced_deal_score(
            discount_pct=discount,
            cross_store_pct=cross_discount,
            near_low=history_position["near_90d_low"],
            box_value_score=box_score,
            confidence=confidence,
        )
        label = deal_label(
            discount_pct=discount,
            cross_store_pct=cross_discount,
            near_low=history_position["near_90d_low"],
            confidence=confidence,
        )
        signals = []
        if discount >= 8:
            signals.append(f"{round(discount)} % under robust prisreferens")
        if cross_discount is not None and cross_discount >= 5:
            signals.append(f"{round(cross_discount)} % under övriga butiker")
        if history_position["near_90d_low"]:
            signals.append(f"Nära {days}-dagarslägsta")
        result.append({
            "variant_id": v.id, "name": f"{v.product.canonical_name} {v.format}", "category": v.product.category,
            "price": best.price_sek, "store": best.store.name, "url": best.url,
            "market_reference": round(reference, 2), "discount_pct": round(discount),
            "cross_store_discount_pct": round(cross_discount) if cross_discount is not None else None,
            "history_low": round(history_position["low"], 2) if history_position["low"] is not None else None,
            "history_high": round(history_position["high"], 2) if history_position["high"] is not None else None,
            "history_position_pct": history_position["position_pct"],
            "near_history_low": history_position["near_90d_low"],
            "observations": len(history), "store_count": store_count,
            "box_value_score": box_score, "deal_confidence": confidence, "deal_score": dscore,
            "deal_label": label, "signals": signals,
            "warning": "Granska manuellt" if confidence < 55 or discount > 40 else None,
        })
    return sorted(result, key=lambda x: (x["deal_score"] is not None, x["deal_score"] or -1, x["deal_confidence"]), reverse=True)


@router.get("/signals/recent")
def list_recent_price_signals(days: int = Query(7, ge=1, le=90), limit: int = Query(100, ge=1, le=500), db: Session = Depends(get_db)):
    return recent_signals(db, days=days, limit=limit)


@router.get("/signals/summary")
def price_signal_summary(days: int = Query(7, ge=1, le=90), db: Session = Depends(get_db)):
    return signal_summary(db, days=days)
