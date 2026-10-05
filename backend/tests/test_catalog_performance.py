from app.routers import products
from app import seed
from test_real_snapshot import session_factory


def test_filtered_catalogue_builds_details_only_for_matching_products(monkeypatch):
    Session = session_factory()
    monkeypatch.setattr(seed, 'SessionLocal', Session)
    seed.seed_verified_snapshot()
    explained = []
    def explain(db, variant):
        explained.append(variant.id)
        return {}
    monkeypatch.setattr(products, 'explain_variant', explain)
    with Session() as db:
        result = products.list_products(category='HOCKEY', max_price=100, db=db)
        assert result
        assert all(p['category'].lower() == 'hockey' and p['price'] <= 100 for p in result)
        assert set(explained) == {p['id'] for p in result}
        assert len(explained) == len(result)


def test_category_filter_preserves_unicode_case_matching(monkeypatch):
    from app.models import Product
    from sqlalchemy import select
    Session = session_factory()
    monkeypatch.setattr(seed, 'SessionLocal', Session)
    seed.seed_verified_snapshot()
    with Session() as db:
        product = db.scalar(select(Product).where(Product.category == 'Hockey'))
        product.category = 'Äventyr'
        db.commit()
        result = products.list_products(category='ÄVENTYR', max_price=None,
                                        db=db, include_details=False)
        assert result
        assert all(p['category'] == 'Äventyr' for p in result)
