from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from ..config import settings
from ..database import Base, engine, get_db
from ..models import BoxAnalysis, Offer, Product, ProductVariant, Store
from ..seed import seed_demo_data
from ..services.update_manager import status_payload
router = APIRouter(prefix="/system", tags=["system"])

def _counts(db: Session) -> dict:
    return {
        "products": db.scalar(select(func.count()).select_from(Product)) or 0,
        "variants": db.scalar(select(func.count()).select_from(ProductVariant)) or 0,
        "offers": db.scalar(select(func.count()).select_from(Offer)) or 0,
        "verified_snapshot_offers": db.scalar(
            select(func.count()).select_from(Offer).where(Offer.source_kind == "verified_snapshot")
        ) or 0,
        "analyses": db.scalar(select(func.count()).select_from(BoxAnalysis)) or 0,
        "stores": db.scalar(select(func.count()).select_from(Store)) or 0,
        "starter_products": db.scalar(select(func.count()).select_from(Product).where(Product.slug.in_(["demo-1","demo-2","demo-3"]))) or 0,
    }

@router.get("/diagnostics")
def diagnostics(db: Session = Depends(get_db)):
    counts=_counts(db)
    problems=[]
    if counts["starter_products"]<3: problems.append("starter_catalog_missing")
    if counts["variants"]==0: problems.append("no_product_variants")
    if counts["offers"]==0: problems.append("no_offers")
    return {"status":"ok" if not problems else "needs_repair","backend_version":settings.version,"database":settings.database_url.split(":",1)[0],"counts":counts,"problems":problems,"update_manager":status_payload()}

@router.post("/repair")
def repair(db: Session = Depends(get_db)):
    Base.metadata.create_all(bind=engine)
    seed_demo_data()
    db.expire_all()
    counts=_counts(db)
    return {"status":"repaired","backend_version":settings.version,"counts":counts,"starter_catalog_ready":counts["starter_products"]>=3}
