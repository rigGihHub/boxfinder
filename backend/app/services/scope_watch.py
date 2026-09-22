from __future__ import annotations
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..models import PriceSignal, ProductVariant, ScopeWatchRule, ScopeWatchEvent

ALLOWED_TRIGGERS={"matching_offer","price_drop","new_90d_low","back_in_stock"}

def _matches(rule: ScopeWatchRule, variant: ProductVariant, signal: PriceSignal) -> bool:
    p=variant.product
    if rule.category and p.category.lower()!=rule.category.lower():
        return False
    if rule.format and variant.format.lower()!=rule.format.lower():
        return False
    if rule.manufacturer and p.manufacturer.lower()!=rule.manufacturer.lower():
        return False
    if rule.max_price_sek is not None:
        if signal.new_price_sek is None or signal.new_price_sek>rule.max_price_sek:
            return False
    if rule.trigger_type!="matching_offer" and signal.signal_type!=rule.trigger_type:
        return False
    return True

def evaluate_scope_signal(db: Session, signal: PriceSignal) -> list[ScopeWatchEvent]:
    variant=db.get(ProductVariant, signal.variant_id)
    if variant is None:
        return []
    rules=db.scalars(select(ScopeWatchRule).where(ScopeWatchRule.active.is_(True))).all()
    created=[]
    for rule in rules:
        if not _matches(rule,variant,signal):
            continue
        exists=db.scalar(
            select(ScopeWatchEvent.id)
            .where(ScopeWatchEvent.scope_watch_rule_id==rule.id)
            .where(ScopeWatchEvent.price_signal_id==signal.id)
            .limit(1)
        )
        if exists:
            continue
        name=f"{variant.product.canonical_name} {variant.format}"
        parts=[]
        if rule.category: parts.append(rule.category)
        if rule.format: parts.append(rule.format)
        if rule.max_price_sek is not None: parts.append(f"under {round(rule.max_price_sek)} kr")
        scope=", ".join(parts) if parts else "din breda bevakning"
        msg=f"{name} matchar {scope}"
        if signal.new_price_sek is not None:
            msg+=f" och kostar {round(signal.new_price_sek)} kr"
        msg+="."
        event=ScopeWatchEvent(
            scope_watch_rule_id=rule.id,
            variant_id=signal.variant_id,
            price_signal_id=signal.id,
            message=msg,
            price_sek=signal.new_price_sek,
            created_at=signal.observed_at,
        )
        db.add(event)
        rule.last_triggered_at=signal.observed_at
        created.append(event)
    return created

def serialize_scope_rules(db: Session) -> list[dict]:
    rows=db.scalars(select(ScopeWatchRule).order_by(ScopeWatchRule.created_at.desc())).all()
    return [{
        "id":r.id,"category":r.category,"format":r.format,"manufacturer":r.manufacturer,
        "max_price_sek":r.max_price_sek,"trigger_type":r.trigger_type,"active":r.active,
        "label":r.label,"created_at":r.created_at.isoformat(),
        "last_triggered_at":r.last_triggered_at.isoformat() if r.last_triggered_at else None,
    } for r in rows]

def serialize_scope_events(db: Session, limit:int=100) -> list[dict]:
    rows=db.scalars(select(ScopeWatchEvent).order_by(ScopeWatchEvent.created_at.desc()).limit(limit)).all()
    result=[]
    for e in rows:
        v=db.get(ProductVariant,e.variant_id)
        result.append({
            "id":e.id,"scope_watch_rule_id":e.scope_watch_rule_id,"variant_id":e.variant_id,
            "product_name":f"{v.product.canonical_name} {v.format}" if v else None,
            "message":e.message,"price_sek":e.price_sek,"created_at":e.created_at.isoformat(),
            "read":e.read_at is not None,
        })
    return result
