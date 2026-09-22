from dataclasses import asdict
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload
from ..database import get_db
from ..models import ProductVariant, Offer
from .products import serialize_variant
from ..services.budget_optimizer import optimize_budget

router = APIRouter(prefix='/budget', tags=['budget'])

@router.get('/recommendations')
def budget_recommendations(
    budget: float = Query(..., gt=0, le=100000),
    goal: str = Query('balanced', pattern='^(balanced|value|chase|fun)$'),
    limit: int = Query(5, ge=1, le=10),
    db: Session = Depends(get_db),
):
    q = select(ProductVariant).options(
        joinedload(ProductVariant.product),
        joinedload(ProductVariant.offers).joinedload(Offer.store),
        joinedload(ProductVariant.analysis),
    )
    variants = db.execute(q).unique().scalars().all()
    products = [serialize_variant(v) for v in variants]
    products = [p for p in products if p]
    recs = optimize_budget(products, budget, goal, limit)
    return {
        'budget': budget,
        'goal': goal,
        'disclaimer': 'Statistisk jämförelse av samlarvärde och öppningsprofil, inte en prognos om vinst.',
        'recommendations': [asdict(r) for r in recs],
    }
