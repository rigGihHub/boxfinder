from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Card, CardMarketValue, ProductVariant, Sale
from ..services.ev import update_box_analysis_ev
from ..services.market_values import SUPPORTED_CONDITIONS, rebuild_market_value

router = APIRouter(tags=["market-values"])

class SaleInput(BaseModel):
    card_id: int
    source_name: str
    external_id: str
    source_url: str | None = None
    sold_price: float = Field(gt=0)
    currency: str = "SEK"
    price_sek: float = Field(gt=0)
    condition_bucket: str = "raw"
    grade_company: str | None = None
    grade_value: str | None = None
    sold_at: datetime
    source_confidence: int = Field(default=50, ge=0, le=100)
    verified: bool = False

@router.post("/admin/market/sales")
def add_sale(payload: SaleInput, db: Session = Depends(get_db)):
    card = db.get(Card, payload.card_id)
    if not card: raise HTTPException(404, "Card not found")
    if payload.condition_bucket not in SUPPORTED_CONDITIONS: raise HTTPException(400, "Unsupported condition bucket")
    existing = db.scalar(select(Sale).where(Sale.source_name == payload.source_name, Sale.external_id == payload.external_id))
    if existing: raise HTTPException(409, "Sale already imported")
    sale = Sale(**payload.model_dump())
    db.add(sale); db.flush()
    mv = rebuild_market_value(db, card.id, payload.condition_bucket)
    db.commit(); db.refresh(sale)
    return {"sale_id": sale.id, "market_value_id": mv.id if mv else None, "condition_bucket": payload.condition_bucket}

@router.post("/admin/cards/{card_id}/market-value/rebuild")
def rebuild_card_value(card_id: int, condition_bucket: str = "raw", db: Session = Depends(get_db)):
    if condition_bucket not in SUPPORTED_CONDITIONS: raise HTTPException(400, "Unsupported condition bucket")
    if not db.get(Card, card_id): raise HTTPException(404, "Card not found")
    mv = rebuild_market_value(db, card_id, condition_bucket)
    db.commit()
    if not mv: return {"card_id":card_id,"status":"no_sales"}
    return _serialize_mv(mv)

@router.get("/cards/{card_id}/market-value")
def card_value(card_id: int, condition_bucket: str = "raw", db: Session = Depends(get_db)):
    mv = db.scalar(select(CardMarketValue).where(CardMarketValue.card_id == card_id, CardMarketValue.condition_bucket == condition_bucket))
    if not mv: raise HTTPException(404, "No market value for this card/condition")
    return _serialize_mv(mv)

@router.post("/admin/products/{variant_id}/recalculate-ev")
def recalc_ev(variant_id: int, condition_bucket: str = "raw", db: Session = Depends(get_db)):
    if condition_bucket not in SUPPORTED_CONDITIONS: raise HTTPException(400, "Unsupported condition bucket")
    if not db.get(ProductVariant, variant_id): raise HTTPException(404, "Product variant not found")
    analysis, result = update_box_analysis_ev(db, variant_id, condition_bucket)
    db.commit()
    return {"variant_id":variant_id,"condition_bucket":condition_bucket,"ev_low":result.ev_low,"ev_high":result.ev_high,
            "coverage":{"cards_total":result.cards_total,"with_values":result.cards_with_values,"with_usable_odds":result.cards_with_usable_odds,"in_ev":result.cards_in_ev,
                        "value_pct":result.value_coverage_pct,"odds_pct":result.odds_coverage_pct,"ev_pct":result.ev_coverage_pct},
            "data_quality":result.data_quality,"notes":result.notes}

def _serialize_mv(mv: CardMarketValue):
    return {"card_id":mv.card_id,"condition_bucket":mv.condition_bucket,"latest_price_sek":mv.latest_price_sek,
            "median_7d_sek":mv.median_7d_sek,"median_30d_sek":mv.median_30d_sek,"median_90d_sek":mv.median_90d_sek,
            "low_90d_sek":mv.low_90d_sek,"high_90d_sek":mv.high_90d_sek,"sales_7d":mv.sales_7d,"sales_30d":mv.sales_30d,"sales_90d":mv.sales_90d,
            "data_quality":mv.data_quality,"updated_at":mv.updated_at.isoformat()}
