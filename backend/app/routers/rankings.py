from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from .products import list_products
from ..services.rankings import rank_items

router = APIRouter(prefix="/rankings", tags=["rankings"])
ALLOWED_MODES = {"value", "upside", "rookies", "hit_density", "balanced"}


def _items(db: Session, category: str | None, max_price: float | None):
    return list_products(category=category, max_price=max_price, db=db)


@router.get("")
def rankings(
    mode: str = Query("value"), category: str | None = None,
    max_price: float | None = Query(None, ge=0), limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    mode = mode.lower().strip()
    if mode not in ALLOWED_MODES:
        return {"error": "unknown_ranking_mode", "allowed_modes": sorted(ALLOWED_MODES)}
    items = _items(db, category, max_price)
    ranked = rank_items(items, mode)[:limit]
    return {"mode": mode, "category": category, "max_price": max_price, "count": len(ranked), "items": ranked}


@router.get("/overview")
def ranking_overview(db: Session = Depends(get_db)):
    items = _items(db, None, None)
    return {
        "value": rank_items(items, "value")[:10],
        "upside": rank_items(items, "upside")[:10],
        "balanced": rank_items(items, "balanced")[:10],
        "rookies": rank_items(items, "rookies")[:10],
        "hit_density": rank_items(items, "hit_density")[:10],
        "under_500": rank_items([x for x in items if x.get("price", 10**12) <= 500], "value")[:10],
        "under_1000": rank_items([x for x in items if x.get("price", 10**12) <= 1000], "value")[:10],
        "categories": {
            category: rank_items([x for x in items if x.get("category", "").lower() == category.lower()], "value")[:10]
            for category in sorted({x.get("category") for x in items if x.get("category")})
        },
    }
