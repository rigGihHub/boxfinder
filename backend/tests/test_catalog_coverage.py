from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import Store, Product, ProductVariant, Offer
from app.services.catalog_coverage import coverage_report

def session():
    engine=create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()

def test_fresh_trusted_offer_counts_as_live_coverage():
    db=session()
    now=datetime.utcnow()
    store=Store(name="Coolcard",country="SE",collection_method="manual",policy_status="manual_allowed",
                last_success_at=now)
    product=Product(slug="x",canonical_name="Test Hockey Box",category="Hockey",manufacturer="Test")
    db.add_all([store,product]); db.flush()
    variant=ProductVariant(product_id=product.id,format="hobby box",language="English")
    db.add(variant); db.flush()
    db.add(Offer(store_id=store.id,variant_id=variant.id,external_id="1",source_title="Test",
                 price_sek=500,stock_status="in_stock",is_preorder=False,source_kind="manual",
                 match_status="auto_matched",observed_at=now))
    db.flush()
    report=coverage_report(db,now=now)
    assert report["summary"]["fresh_in_stock_offers"]==1
    coolcard=next(x for x in report["stores"] if x["name"]=="Coolcard")
    assert coolcard["fresh_in_stock_offers"]==1
    hockey=next(x for x in report["categories"] if x["category"]=="Hockey")
    assert hockey["active_source_count"]==1

def test_stale_offer_is_not_fresh():
    db=session()
    now=datetime.utcnow()
    store=Store(name="Coolcard",country="SE",collection_method="manual",policy_status="manual_allowed",
                last_success_at=now-timedelta(days=20))
    product=Product(slug="x",canonical_name="Old Box",category="Hockey",manufacturer="Test")
    db.add_all([store,product]); db.flush()
    variant=ProductVariant(product_id=product.id,format="hobby box",language="English")
    db.add(variant); db.flush()
    db.add(Offer(store_id=store.id,variant_id=variant.id,external_id="1",source_title="Old",
                 price_sek=500,stock_status="in_stock",is_preorder=False,source_kind="manual",
                 match_status="auto_matched",observed_at=now-timedelta(days=30)))
    db.flush()
    report=coverage_report(db,now=now)
    coolcard=next(x for x in report["stores"] if x["name"]=="Coolcard")
    assert coolcard["fresh_in_stock_offers"]==0
    assert coolcard["stale_trusted_offers"]==1
    assert "inga färska lagerförda erbjudanden" in coolcard["blockers"]

def test_unapproved_store_surfaces_policy_action():
    db=session()
    store=Store(name="Terratide",country="SE",collection_method="public_html_catalog",
                policy_status="review_required")
    db.add(store); db.flush()
    report=coverage_report(db,now=datetime.utcnow())
    action=next(x for x in report["next_actions"] if x["store"]=="Terratide")
    assert action["action"].startswith("Granska policy")
