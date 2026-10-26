from datetime import datetime, timedelta, timezone

from app.models import Offer, Product, ProductVariant, Store
from app.routers.discovery import real_catalog
from test_real_snapshot import session_factory


def add_offer(db, store, number, *, age=0, price=100, stock="in_stock", preorder=False):
    product = Product(slug=f"browse-{number}", canonical_name=f"Chrome Hockey {number}",
                      category="Hockey", manufacturer="Example")
    variant = ProductVariant(product=product, format="hobby box")
    db.add(variant)
    db.flush()
    db.add(Offer(variant_id=variant.id, store_id=store.id, external_id=str(number),
                 source_title=product.canonical_name, source_kind="verified_snapshot",
                 match_status="manual_matched", stock_status=stock, is_preorder=preorder,
                 price_sek=price, url=f"https://example.test/products/{number}",
                 observed_at=datetime.now(timezone.utc)-timedelta(days=age)))


def catalog(db, **kwargs):
    return real_catalog(budget=None, limit=60, db=db, **kwargs)


def test_pages_cover_whole_store_without_duplicates_and_keep_filters():
    with session_factory()() as db:
        selected = Store(name="Selected")
        other = Store(name="Other")
        db.add_all([selected, other])
        db.flush()
        for number in range(65):
            add_offer(db, selected, number, price=1200)
        add_offer(db, other, 100)
        db.commit()
        first = catalog(db, store_name=" selected ", q="chrome hockey")
        second = catalog(db, store_name="Selected", q="CHROME hockey", offset=60)
        assert first["count"] == second["count"] == 65
        assert first["has_more"] and not second["has_more"]
        ids = [p["id"] for page in (first, second) for p in page["products"]]
        assert len(ids) == len(set(ids)) == 65
        assert all(p["store"] == "Selected" and p["price"] == 1200
                   for page in (first, second) for p in page["products"])
        assert catalog(db, store_name="Selected", offset=120)["products"] == []
        assert catalog(db, q="absent")["count"] == 0


def test_expired_summary_is_filtered_and_never_promotes_old_stock():
    with session_factory()() as db:
        selected, other = Store(name="Selected"), Store(name="Other")
        db.add_all([selected, other])
        db.flush()
        add_offer(db, selected, 1, age=16)
        add_offer(db, selected, 2, age=16, stock="out_of_stock")
        add_offer(db, selected, 3, age=16, preorder=True)
        add_offer(db, selected, 4, age=-1)
        add_offer(db, other, 5, age=16)
        db.commit()
        result = catalog(db, store_name="Selected", q="Chrome")
        assert result["products"] == [] and result["expired_count"] == 1
        assert result["latest_observed_at"] is not None
        assert catalog(db, store_name="Selected", q="absent")["expired_count"] == 0
        assert catalog(db, store_name="Selected", category="Basket")["expired_count"] == 0
        assert real_catalog(budget=50, limit=60, db=db)["expired_count"] == 0


def test_fresh_alternative_prevents_expired_product_count():
    with session_factory()() as db:
        selected = Store(name="Selected")
        db.add(selected)
        db.flush()
        add_offer(db, selected, 1, age=16, price=10)
        db.flush()
        old = db.query(Offer).one()
        db.add(Offer(variant_id=old.variant_id, store_id=selected.id, external_id="fresh",
                     source_title="New price", source_kind="verified_snapshot",
                     match_status="manual_matched", stock_status="in_stock", is_preorder=False,
                     price_sek=200, url="https://example.test/products/fresh",
                     observed_at=datetime.now(timezone.utc)))
        db.commit()
        result = catalog(db)
        assert result["count"] == 1 and result["expired_count"] == 0
        assert result["products"][0]["price"] == 200


def test_catalog_http_query_validation_and_response():
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool
    from app.database import Base, get_db
    from app.routers.discovery import router

    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    with Session() as db:
        store = Store(name="Selected")
        db.add(store)
        db.flush()
        add_offer(db, store, 1, price=1200)
        db.commit()

    def database():
        with Session() as db:
            yield db

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_db] = database
    with TestClient(app) as client:
        response = client.get("/discovery/real-catalog", params={"store_name": "Selected", "q": "Chrome", "limit": 1})
        assert response.status_code == 200
        assert response.json()["products"][0]["price"] == 1200
        assert client.get("/discovery/real-catalog?offset=-1").status_code == 422
        assert client.get("/discovery/real-catalog", params={"q": "a"*161}).status_code == 422
