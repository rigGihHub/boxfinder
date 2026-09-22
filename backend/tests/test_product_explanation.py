from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models import Store, Product, ProductVariant, Offer, ProductFact
from app.services.product_explanation import explain_variant
import json

def session():
    e=create_engine("sqlite:///:memory:")
    Base.metadata.create_all(e)
    return sessionmaker(bind=e)()

def setup(db, price=799):
    s=Store(name="S",country="SE",collection_method="manual",policy_status="manual_allowed")
    p=Product(slug="x",canonical_name="Test Hobby",category="Hockey",manufacturer="Upper Deck")
    db.add_all([s,p]);db.flush()
    v=ProductVariant(product_id=p.id,format="hobby box",packs=12,cards_per_pack=12)
    db.add(v);db.flush()
    db.add(Offer(store_id=s.id,variant_id=v.id,external_id="1",source_title="Test",price_sek=price,
                 stock_status="in_stock",match_status="manual_matched",source_kind="verified_snapshot"))
    db.add(ProductFact(variant_id=v.id,facts_json=json.dumps(["6 Young Guns per box i snitt","1 Outburst Silver parallel"]),
                       source_name="source",source_url="https://example.test",verified_at=__import__("datetime").datetime.utcnow(),confidence=100))
    db.commit()
    return v

def test_single_store_never_claims_verified_deal():
    db=session();v=setup(db)
    x=explain_variant(db,v)
    assert x["deal"]["status"]=="not_verified"
    assert "två" in x["deal"]["reason"].lower()

def test_young_guns_creates_rookie_reason():
    db=session();v=setup(db)
    x=explain_variant(db,v)
    assert any("rookie" in r.lower() for r in x["why_good"])
