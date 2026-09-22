from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models import Offer, Product, ProductVariant, ShippingPolicy, Store
from app.services.price_compare import comparison_for_variant, shipping_for

def make_db():
    engine=create_engine("sqlite:///:memory:"); Base.metadata.create_all(engine); return sessionmaker(bind=engine)()

def test_unknown_shipping_is_not_zero():
    amount,status=shipping_for(None,899)
    assert amount is None and status=="unknown"

def test_free_shipping_threshold():
    p=ShippingPolicy(store_id=1,base_shipping_sek=59,free_shipping_threshold_sek=1000,verification_status="verified",confidence=90)
    assert shipping_for(p,1100)[0]==0
    assert shipping_for(p,900)[0]==59

def test_compare_same_variant_across_stores():
    db=make_db()
    try:
        product=Product(slug="x",canonical_name="2025-26 Upper Deck Series 1",category="Hockey",manufacturer="Upper Deck",year_season="2025-26")
        variant=ProductVariant(product=product,format="hobby box",language="English",region="Global")
        a=Store(name="A",country="SE",collection_method="manual",policy_status="manual_allowed")
        b=Store(name="B",country="SE",collection_method="manual",policy_status="manual_allowed")
        db.add_all([product,variant,a,b]); db.flush()
        db.add_all([
            Offer(store_id=a.id,variant_id=variant.id,external_id="a1",source_title="UD S1 Hobby",price_sek=899,stock_status="in_stock",source_kind="manual_csv",match_status="auto_matched",observed_at=datetime.utcnow()),
            Offer(store_id=b.id,variant_id=variant.id,external_id="b1",source_title="UD S1 Hobby",price_sek=949,stock_status="in_stock",source_kind="manual_csv",match_status="manual_matched",observed_at=datetime.utcnow()),
            ShippingPolicy(store_id=a.id,base_shipping_sek=59,verification_status="verified",confidence=90),
            ShippingPolicy(store_id=b.id,base_shipping_sek=0,verification_status="verified",confidence=90),
        ]); db.commit(); db.refresh(variant)
        out=comparison_for_variant(db,variant)
        assert out["store_count"]==2
        assert out["best_item_price"]["store"]=="A"
        assert out["best_total_price"]["store"]=="B"
        assert out["price_spread_sek"]==50
    finally: db.close()

def test_stale_real_offer_is_excluded():
    db=make_db()
    try:
        product=Product(slug="y",canonical_name="Test Product",category="Hockey",manufacturer="Test")
        variant=ProductVariant(product=product,format="hobby box",language="English",region="Global")
        store=Store(name="Stale",country="SE",collection_method="manual",policy_status="manual_allowed")
        db.add_all([product,variant,store]); db.flush()
        db.add(Offer(store_id=store.id,variant_id=variant.id,external_id="s1",source_title="Test Product Hobby Box",price_sek=500,stock_status="in_stock",source_kind="manual_csv",match_status="auto_matched",observed_at=datetime.utcnow()-timedelta(days=30)))
        db.commit(); db.refresh(variant)
        assert comparison_for_variant(db,variant)["offer_count"]==0
    finally: db.close()
