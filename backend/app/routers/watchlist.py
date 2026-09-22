from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import ProductVariant, WatchRule, WatchEvent, ScopeWatchRule
from ..services.watch_engine import TRIGGERS, check_current_price_rule, serialize_rules, serialize_events
from ..services.scope_watch import ALLOWED_TRIGGERS, serialize_scope_rules, serialize_scope_events

router = APIRouter(prefix="/watchlist", tags=["watchlist"])

class WatchRulePayload(BaseModel):
    variant_id: int
    trigger_type: str
    threshold_sek: float | None = None
    label: str | None = None


class ScopeWatchPayload(BaseModel):
    category: str | None = None
    format: str | None = None
    manufacturer: str | None = None
    max_price_sek: float | None = None
    trigger_type: str = "matching_offer"
    label: str | None = None

@router.get("/scope-rules")
def list_scope_rules(db: Session = Depends(get_db)):
    return serialize_scope_rules(db)

@router.post("/scope-rules")
def create_scope_rule(payload: ScopeWatchPayload, db: Session = Depends(get_db)):
    if payload.trigger_type not in ALLOWED_TRIGGERS:
        raise HTTPException(400, f"Unknown trigger_type. Allowed: {sorted(ALLOWED_TRIGGERS)}")
    if not any([payload.category, payload.format, payload.manufacturer, payload.max_price_sek]):
        raise HTTPException(400, "At least one scope filter is required")
    if payload.max_price_sek is not None and payload.max_price_sek <= 0:
        raise HTTPException(400, "max_price_sek must be > 0")
    rule=ScopeWatchRule(
        category=payload.category.strip() if payload.category else None,
        format=payload.format.strip() if payload.format else None,
        manufacturer=payload.manufacturer.strip() if payload.manufacturer else None,
        max_price_sek=payload.max_price_sek,
        trigger_type=payload.trigger_type,
        label=payload.label,
        active=True,
    )
    db.add(rule)
    db.commit()
    return {"id":rule.id,"active":rule.active}

@router.patch("/scope-rules/{rule_id}/toggle")
def toggle_scope_rule(rule_id: int, db: Session = Depends(get_db)):
    rule=db.get(ScopeWatchRule,rule_id)
    if not rule:
        raise HTTPException(404,"Scope watch rule not found")
    rule.active=not rule.active
    db.commit()
    return {"id":rule.id,"active":rule.active}

@router.get("/scope-events")
def list_scope_events(limit: int = 100, db: Session = Depends(get_db)):
    return serialize_scope_events(db, limit=min(max(limit,1),500))

@router.get("/rules")
def list_rules(db: Session = Depends(get_db)):
    return serialize_rules(db)

@router.post("/rules")
def create_rule(payload: WatchRulePayload, db: Session = Depends(get_db)):
    if payload.trigger_type not in TRIGGERS:
        raise HTTPException(400, f"Unknown trigger_type. Allowed: {sorted(TRIGGERS)}")
    if db.get(ProductVariant, payload.variant_id) is None:
        raise HTTPException(404, "Product variant not found")
    if payload.trigger_type == "price_below":
        if payload.threshold_sek is None or payload.threshold_sek <= 0:
            raise HTTPException(400, "price_below requires threshold_sek > 0")
    else:
        payload.threshold_sek = None

    rule = WatchRule(
        variant_id=payload.variant_id,
        trigger_type=payload.trigger_type,
        threshold_sek=payload.threshold_sek,
        label=payload.label,
        active=True,
    )
    db.add(rule)
    db.flush()
    immediate = check_current_price_rule(db, rule)
    db.commit()
    return {
        "rule_id": rule.id,
        "active": rule.active,
        "triggered_immediately": immediate is not None,
        "event_id": immediate.id if immediate else None,
    }

@router.patch("/rules/{rule_id}/toggle")
def toggle_rule(rule_id: int, db: Session = Depends(get_db)):
    rule = db.get(WatchRule, rule_id)
    if not rule:
        raise HTTPException(404, "Watch rule not found")
    rule.active = not rule.active
    db.commit()
    return {"id": rule.id, "active": rule.active}

@router.delete("/rules/{rule_id}")
def delete_rule(rule_id: int, db: Session = Depends(get_db)):
    rule = db.get(WatchRule, rule_id)
    if not rule:
        raise HTTPException(404, "Watch rule not found")
    # Keep historical events for auditability; deactivate instead of hard-delete.
    rule.active = False
    db.commit()
    return {"id": rule.id, "active": False, "archived": True}

@router.get("/events")
def list_events(unread_only: bool = False, limit: int = 100, db: Session = Depends(get_db)):
    return serialize_events(db, unread_only=unread_only, limit=min(max(limit, 1), 500))

@router.post("/events/{event_id}/read")
def mark_read(event_id: int, db: Session = Depends(get_db)):
    event = db.get(WatchEvent, event_id)
    if not event:
        raise HTTPException(404, "Watch event not found")
    if event.read_at is None:
        event.read_at = datetime.utcnow()
        db.commit()
    return {"id": event.id, "read": True}
