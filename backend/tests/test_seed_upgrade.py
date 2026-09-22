from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
import app.seed as seedmod
from app.database import Base
from app.models import Product, Store

def test_seed_adds_starter_catalog_even_when_product_table_not_empty(monkeypatch):
    engine=create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session=sessionmaker(bind=engine)
    db=Session()
    db.add(Product(slug="existing",canonical_name="Existing",category="Other",manufacturer="Test"))
    db.commit(); db.close()

    monkeypatch.setattr(seedmod,"SessionLocal",Session)
    seedmod.seed_demo_data()

    db=Session()
    slugs=set(db.scalars(select(Product.slug)).all())
    assert {"demo-1","demo-2","demo-3"}.issubset(slugs)
    demo=db.scalar(select(Store).where(Store.name=="Demo · ej verifierad butik"))
    assert demo is not None
    db.close()
