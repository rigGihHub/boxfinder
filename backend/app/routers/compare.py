from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..database import get_db
from .products import list_products
from ..services.comparison import compare_items

router = APIRouter(prefix="/compare", tags=["compare"])

@router.get("")
def compare_products(ids: str = Query(..., description="Comma-separated product variant ids"), db: Session = Depends(get_db)):
    try:
        wanted = [int(x.strip()) for x in ids.split(",") if x.strip()]
    except ValueError:
        raise HTTPException(400, "ids must be comma-separated integers")
    wanted = list(dict.fromkeys(wanted))
    if not 2 <= len(wanted) <= 4:
        raise HTTPException(400, "Choose between 2 and 4 unique products")
    products = [x for x in list_products(db=db) if x["id"] in wanted]
    if len(products) != len(wanted):
        found = {x["id"] for x in products}
        raise HTTPException(404, {"missing_ids": [x for x in wanted if x not in found]})
    ordered = sorted(products, key=lambda x: wanted.index(x["id"]))
    return compare_items(ordered)
