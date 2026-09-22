from __future__ import annotations
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..models import Offer, PriceSignal, ProductVariant, WatchRule, WatchEvent

TRIGGERS = {"price_below", "back_in_stock", "new_90d_low", "price_drop"}

def _variant_name(db: Session, variant_id: int) -> str:
    v = db.get(ProductVariant, variant_id)
    return f"{v.product.canonical_name} {v.format}" if v else f"Produkt {variant_id}"

def evaluate_signal(db: Session, signal: PriceSignal) -> list[WatchEvent]:
    rules = db.scalars(
        select(WatchRule)
        .where(WatchRule.variant_id == signal.variant_id)
        .where(WatchRule.active.is_(True))
    ).all()
    created: list[WatchEvent] = []
    name = _variant_name(db, signal.variant_id)

    for rule in rules:
        matched = False
        if rule.trigger_type == "back_in_stock":
            matched = signal.signal_type == "back_in_stock"
        elif rule.trigger_type == "new_90d_low":
            matched = signal.signal_type == "new_90d_low"
        elif rule.trigger_type == "price_drop":
            matched = signal.signal_type == "price_drop"
        elif rule.trigger_type == "price_below":
            matched = (
                signal.new_price_sek is not None
                and rule.threshold_sek is not None
                and signal.new_price_sek <= rule.threshold_sek
            )

        if not matched:
            continue

        exists = db.scalar(
            select(WatchEvent.id)
            .where(WatchEvent.watch_rule_id == rule.id)
            .where(WatchEvent.price_signal_id == signal.id)
            .limit(1)
        )
        if exists:
            continue

        if rule.trigger_type == "price_below":
            msg = f"{name} är nu {round(signal.new_price_sek)} kr, under din gräns {round(rule.threshold_sek)} kr."
        elif rule.trigger_type == "back_in_stock":
            msg = f"{name} är åter i lager."
        elif rule.trigger_type == "new_90d_low":
            msg = f"{name} har nått ett nytt 90-dagarslägsta."
        else:
            msg = f"{name} har fått ett nytt prisfall."

        event = WatchEvent(
            watch_rule_id=rule.id,
            variant_id=signal.variant_id,
            price_signal_id=signal.id,
            event_type=rule.trigger_type,
            message=msg,
            price_sek=signal.new_price_sek,
            created_at=signal.observed_at,
        )
        db.add(event)
        rule.last_triggered_at = signal.observed_at
        created.append(event)
    return created

def check_current_price_rule(db: Session, rule: WatchRule) -> WatchEvent | None:
    if not rule.active or rule.trigger_type != "price_below" or rule.threshold_sek is None:
        return None
    offers = db.scalars(
        select(Offer)
        .where(Offer.variant_id == rule.variant_id)
        .where(Offer.stock_status == "in_stock")
        .where(Offer.is_preorder.is_(False))
        .where(Offer.match_status.in_(["auto_matched", "manual_matched"]))
    ).all()
    if not offers:
        return None
    best = min(offers, key=lambda o: o.price_sek)
    if best.price_sek > rule.threshold_sek:
        return None

    # Avoid creating repeated immediate events for the same rule/current price.
    recent = db.scalar(
        select(WatchEvent.id)
        .where(WatchEvent.watch_rule_id == rule.id)
        .where(WatchEvent.event_type == "price_below")
        .where(WatchEvent.price_sek == best.price_sek)
        .limit(1)
    )
    if recent:
        return None

    name = _variant_name(db, rule.variant_id)
    event = WatchEvent(
        watch_rule_id=rule.id,
        variant_id=rule.variant_id,
        event_type="price_below",
        message=f"{name} kostar redan {round(best.price_sek)} kr, under din gräns {round(rule.threshold_sek)} kr.",
        price_sek=best.price_sek,
        created_at=datetime.utcnow(),
    )
    db.add(event)
    rule.last_triggered_at = event.created_at
    return event

def serialize_rules(db: Session) -> list[dict]:
    rules = db.scalars(select(WatchRule).order_by(WatchRule.created_at.desc())).all()
    result=[]
    for r in rules:
        v=db.get(ProductVariant,r.variant_id)
        result.append({
            "id":r.id,
            "variant_id":r.variant_id,
            "product_name":f"{v.product.canonical_name} {v.format}" if v else None,
            "trigger_type":r.trigger_type,
            "threshold_sek":r.threshold_sek,
            "active":r.active,
            "label":r.label,
            "created_at":r.created_at.isoformat(),
            "last_triggered_at":r.last_triggered_at.isoformat() if r.last_triggered_at else None,
        })
    return result

def serialize_events(db: Session, unread_only: bool=False, limit:int=100) -> list[dict]:
    q=select(WatchEvent).order_by(WatchEvent.created_at.desc())
    if unread_only:
        q=q.where(WatchEvent.read_at.is_(None))
    rows=db.scalars(q.limit(limit)).all()
    result=[]
    for e in rows:
        v=db.get(ProductVariant,e.variant_id)
        result.append({
            "id":e.id,
            "watch_rule_id":e.watch_rule_id,
            "variant_id":e.variant_id,
            "product_name":f"{v.product.canonical_name} {v.format}" if v else None,
            "event_type":e.event_type,
            "message":e.message,
            "price_sek":e.price_sek,
            "created_at":e.created_at.isoformat(),
            "read":e.read_at is not None,
        })
    return result
