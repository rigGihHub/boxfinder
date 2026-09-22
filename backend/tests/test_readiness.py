from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models import Product, ProductVariant, Store, Offer
from app.services.readiness import ranking_readiness

def test_readiness_is_explainable():
    engine=create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session=sessionmaker(bind=engine)
    db=Session()
    p=Product(slug="x", canonical_name="Test", category="Hockey", manufacturer="Test")
    db.add(p); db.flush()
    v=ProductVariant(product_id=p.id, format="Hobby", language="English", region="Global", packs=12, cards_per_pack=8)
    s=Store(name="Store", country="SE", collection_method="manual", policy_status="approved")
    db.add_all([v,s]); db.flush()
    db.add(Offer(store_id=s.id, variant_id=v.id, external_id="1", source_title="Test Hobby", price_sek=500,
                 stock_status="in_stock", is_preorder=False, source_kind="manual", source_confidence=100,
                 observed_at=datetime.utcnow(), match_confidence=.99, match_status="auto_matched"))
    db.commit(); db.refresh(v)
    result=ranking_readiness(db,v)
    assert result["status"] in {"ready","almost_ready","insufficient"}
    assert 0 <= result["score"] <= 100
    assert result["components"]["fresh_stores"] == 1
    assert "Checklista saknas" in result["blockers"]
