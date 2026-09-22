from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import delete, select
from sqlalchemy.orm import Session, joinedload
from ..database import get_db
from ..models import Card, Checklist, Odds, ProductVariant
from ..services.checklists import ALLOWED_BASIS, classify_outcome, odds_to_box_probability, parse_checklist_csv

router = APIRouter(tags=["checklists"])

class ChecklistImport(BaseModel):
    variant_id: int
    source_name: str
    source_url: str | None = None
    source_type: str = "official"
    verification_status: str = "review_required"
    confidence: int = Field(ge=0, le=100)
    csv_text: str

class OddsInput(BaseModel):
    card_id: int | None = None
    category_key: str
    basis: str = "unknown"
    source_name: str | None = None
    source_url: str | None = None
    confidence: int = Field(ge=0, le=100)
    one_in_packs: float | None = Field(None, gt=0)
    hits_per_box: float | None = Field(None, ge=0)
    notes: str | None = None

@router.post("/admin/checklists/import-csv")
def import_csv(payload: ChecklistImport, db: Session = Depends(get_db)):
    variant = db.get(ProductVariant, payload.variant_id)
    if not variant: raise HTTPException(404, "Product variant not found")
    parsed = parse_checklist_csv(payload.csv_text)
    if not parsed: raise HTTPException(400, "No checklist rows could be parsed")
    existing = db.scalar(select(Checklist).where(Checklist.variant_id == variant.id))
    if existing:
        db.execute(delete(Odds).where(Odds.card_id.in_(select(Card.id).where(Card.checklist_id == existing.id))))
        db.execute(delete(Card).where(Card.checklist_id == existing.id))
        cl = existing
        cl.source_name, cl.source_url, cl.source_type = payload.source_name, payload.source_url, payload.source_type
        cl.verification_status, cl.confidence = payload.verification_status, payload.confidence
    else:
        cl = Checklist(variant_id=variant.id, source_name=payload.source_name, source_url=payload.source_url, source_type=payload.source_type, verification_status=payload.verification_status, confidence=payload.confidence)
        db.add(cl); db.flush()
    for x in parsed:
        db.add(Card(checklist_id=cl.id, source_confidence=payload.confidence, **x.__dict__))
    db.commit()
    return {"checklist_id": cl.id, "rows": len(parsed), "verification_status": cl.verification_status, "confidence": cl.confidence}

@router.post("/admin/products/{variant_id}/odds")
def add_odds(variant_id: int, payload: OddsInput, db: Session = Depends(get_db)):
    v = db.get(ProductVariant, variant_id)
    if not v: raise HTTPException(404, "Product variant not found")
    if payload.basis not in ALLOWED_BASIS: raise HTTPException(400, "Invalid probability basis")
    if payload.card_id:
        c = db.get(Card, payload.card_id)
        if not c or c.checklist.variant_id != variant_id: raise HTTPException(400, "Card does not belong to this variant")
    prob = odds_to_box_probability(packs_per_box=v.packs, one_in_packs=payload.one_in_packs, hits_per_box=payload.hits_per_box)
    o = Odds(variant_id=variant_id, probability_per_box=prob, **payload.model_dump())
    db.add(o); db.commit(); db.refresh(o)
    return {"id":o.id,"basis":o.basis,"confidence":o.confidence,"probability_per_box":o.probability_per_box}

@router.get("/products/{variant_id}/what-can-i-get")
def what_can_i_get(variant_id: int, db: Session = Depends(get_db)):
    q = select(ProductVariant).where(ProductVariant.id == variant_id).options(
        joinedload(ProductVariant.product),
    )
    v = db.execute(q).unique().scalar_one_or_none()
    if not v: raise HTTPException(404, "Product variant not found")
    cl = db.scalar(select(Checklist).where(Checklist.variant_id == variant_id))
    if not cl:
        return {"variant_id":variant_id,"status":"missing_checklist","message":"Ingen verifierad checklista är importerad ännu."}
    cards = db.scalars(select(Card).where(Card.checklist_id == cl.id)).all()
    odds = db.scalars(select(Odds).where(Odds.variant_id == variant_id)).all()
    odds_by_card = {}
    for o in odds:
        if o.card_id: odds_by_card.setdefault(o.card_id, []).append(o)
    groups = {"common":[],"good_hit":[],"big_hit":[],"jackpot":[]}
    for c in cards:
        entry = {"card_id":c.id,"card_number":c.card_number,"subject":c.subject,"subset":c.subset,"parallel":c.parallel,"numbered_to":c.serial_numbered_to,"rookie":c.is_rookie,"autograph":c.is_autograph,"memorabilia":c.is_memorabilia}
        co = odds_by_card.get(c.id, [])
        if co:
            best = max(co, key=lambda x:x.confidence)
            entry["probability"] = best.probability_per_box
            entry["probability_basis"] = best.basis
            entry["odds_confidence"] = best.confidence
        else:
            entry["probability"] = None; entry["probability_basis"] = "unknown"; entry["odds_confidence"] = 0
        groups[classify_outcome(c)].append(entry)
    return {
        "variant_id":variant_id,"product":f"{v.product.canonical_name} {v.format}",
        "checklist":{"source":cl.source_name,"source_url":cl.source_url,"type":cl.source_type,"verification_status":cl.verification_status,"confidence":cl.confidence,"card_count":len(cards)},
        "important_note":"Okända odds visas som okända. BoxFinder fyller inte i saknade sannolikheter med AI.",
        "common":groups["common"][:50],"good_hit":groups["good_hit"][:50],"big_hit":groups["big_hit"][:50],"jackpot":groups["jackpot"][:50],
    }
