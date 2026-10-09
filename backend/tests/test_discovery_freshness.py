from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import Offer
from app.routers.discovery import real_catalog
from app.services.offer_freshness import MAX_OFFER_AGE_DAYS


def test_discovery_excludes_expired_store_offers_and_restores_fresh_ones():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    with Session() as db:
        from app.models import Product, ProductVariant, Store

        store = Store(name="Example Store", homepage_url="https://example.test")
        product = Product(slug="freshness-example", canonical_name="Freshness Example", category="Hockey", manufacturer="Example")
        variant = ProductVariant(product=product, format="hobby box")
        db.add_all([store, variant])
        db.flush()
        offer = Offer(
            variant_id=variant.id, store_id=store.id, external_id="freshness-example",
            source_title="Freshness Example", source_kind="verified_snapshot",
            match_status="manual_matched", stock_status="in_stock", is_preorder=False,
            price_sek=100, url="https://example.test/product/freshness-example",
            observed_at=datetime.now(timezone.utc) - timedelta(days=MAX_OFFER_AGE_DAYS + 1),
        )
        db.add(offer)
        db.commit()

        assert real_catalog(budget=None, limit=60, db=db)["products"] == []
        offer.observed_at = datetime.now(timezone.utc).replace(tzinfo=None)
        db.add(Offer(
            variant_id=variant.id, store_id=store.id, external_id="expired-cheap",
            source_title="Old cheap listing", source_kind="verified_snapshot",
            match_status="manual_matched", stock_status="in_stock", is_preorder=False,
            price_sek=10, url="https://example.test/product/expired-cheap",
            observed_at=datetime.now(timezone.utc) - timedelta(days=MAX_OFFER_AGE_DAYS + 1),
        ))
        db.commit()
        products = real_catalog(budget=None, limit=60, db=db)["products"]
        assert len(products) == 1
        assert products[0]["price"] == 100
        assert products[0]["explanation"]["deal"]["status"] == "not_verified"
