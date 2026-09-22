from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models import Product, ProductVariant, Offer, Store, BoxAnalysis
from app.routers.system import diagnostics

def session():
    engine=create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()

def test_diagnostics_detects_missing_starter_catalog():
    db=session(); result=diagnostics(db); assert result["status"]=="needs_repair"; assert "starter_catalog_missing" in result["problems"]

def test_diagnostics_accepts_complete_starter_catalog():
    db=session(); store=Store(name="Demo",country="SE",collection_method="demo",policy_status="manual_allowed"); db.add(store); db.flush()
    for i in range(1,4):
        product=Product(slug=f"demo-{i}",canonical_name=f"Demo {i}",category="Test",manufacturer="Test"); db.add(product); db.flush(); variant=ProductVariant(product_id=product.id,format="hobby box"); db.add(variant); db.flush(); db.add(Offer(store_id=store.id,variant_id=variant.id,external_id=f"d{i}",source_title=f"Demo {i}",price_sek=100+i,stock_status="in_stock",source_kind="demo",match_status="demo")); db.add(BoxAnalysis(variant_id=variant.id,data_quality=50))
    db.commit(); result=diagnostics(db); assert result["counts"]["starter_products"]==3; assert "starter_catalog_missing" not in result["problems"]
