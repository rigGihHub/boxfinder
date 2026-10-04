from sqlalchemy import select, func

from app import seed
from app.models import CatalogCandidate, Offer, Product, Store
from app.routers import rankings
from app.routers.admin import catalog_candidates
from app.services.two_shops_snapshot import INVENTORIES, OFFERS, PROFILES
from test_real_snapshot import session_factory


def test_complete_catalogues_are_idempotent_and_keep_review_decisions(monkeypatch):
    Session = session_factory()
    monkeypatch.setattr(seed, 'SessionLocal', Session)
    seed.seed_verified_snapshot()
    seed.seed_speltrollet_inventory()
    seed.seed_coolcard_inventory()
    with Session() as db:
        rejected = db.scalar(select(CatalogCandidate).where(CatalogCandidate.review_status == 'new'))
        rejected.review_status = 'rejected'
        rejected_id = rejected.id
        db.commit()
    seed.seed_speltrollet_inventory()
    seed.seed_coolcard_inventory()
    with Session() as db:
        assert db.get(CatalogCandidate, rejected_id).review_status == 'rejected'
        for name, expected in [('Speltrollet', (4389, 4985)), ('Coolcard', (24604, 24604))]:
            inventory = INVENTORIES[name]
            assert inventory['pagination_complete']
            assert (inventory['product_count'], inventory['entry_count']) == expected
            assert inventory['record_scope'] == ('variant' if name == 'Speltrollet' else 'product')
            store = db.scalar(select(Store).where(Store.name == name))
            assert db.scalar(select(func.count()).select_from(CatalogCandidate).where(CatalogCandidate.store_id == store.id)) == expected[1]
            assert store.policy_status == 'review_required'
            first = catalog_candidates(sealed_only=False, limit=20, store_name=name, offset=0, db=db)
            second = catalog_candidates(sealed_only=False, limit=20, store_name=name, offset=20, db=db)
            assert len(first) == len(second) == 20
            assert {r['id'] for r in first}.isdisjoint(r['id'] for r in second)
            assert all(r['store_name'] == name for r in first + second)


def test_refresh_preserves_offer_ids_and_language_format_identity(monkeypatch):
    Session = session_factory()
    monkeypatch.setattr(seed, 'SessionLocal', Session)
    full = seed.REAL_SNAPSHOT
    monkeypatch.setattr(seed, 'REAL_SNAPSHOT', seed.PRE_TWO_SHOPS_SNAPSHOT)
    seed.seed_verified_snapshot()
    with Session() as db:
        original = {(o.store.name, o.external_id): o.id for o in db.scalars(select(Offer))}
        product_ids = dict(db.execute(select(Product.slug, Product.id)).all())
    monkeypatch.setattr(seed, 'REAL_SNAPSHOT', full)
    seed.seed_verified_snapshot()
    seed.seed_chase_profiles()
    seed.seed_verified_snapshot()
    with Session() as db:
        actual = {(o.store.name, o.external_id): o for o in db.scalars(select(Offer))}
        assert len(actual) == len(full)
        assert all(actual[key].id == ident for key, ident in original.items())
        assert all(db.scalar(select(Product.id).where(Product.slug == slug)) == ident for slug, ident in product_ids.items())
        for row in OFFERS:
            offer = actual[row['store_name'], row['sku']]
            assert (offer.price_sek, offer.stock_status, offer.is_preorder, offer.url) == (row['price'], row['stock'], row['preorder'], row['buy_url'])
            assert (offer.variant.format, offer.variant.language) == (row['fmt'], row['language'])
        # ETB code cards/dividers must not be matched to the sealed ETB.
        assert not any(o.stock_status == 'in_stock' and o.variant.product.slug == 'cc-pokemon-go-etb' and o.price_sek < 100 for o in actual.values())


def test_all_store_rankings_are_pageable_and_exclude_preorders(monkeypatch):
    Session = session_factory()
    monkeypatch.setattr(seed, 'SessionLocal', Session)
    seed.seed_verified_snapshot()
    seed.seed_chase_profiles()
    monkeypatch.setattr(rankings, '_resale_cache', dict(until=0, ranked=None, refreshing=False))
    with Session() as db:
        for name in INVENTORIES:
            pages = []
            for offset in range(0, 1000, 100):
                result = rankings.resale_rankings(strategy='value', limit=100, offset=offset,
                    db=db, category=None, max_price=None, store_id=None, store_name=name, cost_basis='total')
                pages.extend(result['items'])
                if len(pages) >= result['count']:
                    break
            assert len(pages) == len({r['id'] for r in pages}) == result['count']
            assert result['count'] > 100
            assert all(r['store'] == name and r['cost_basis'] == 'item' for r in pages)
            eligible = {r['slug'] for r in OFFERS if r['store_name'] == name and r['stock'] == 'in_stock' and not r['preorder'] and r['slug'] in seed.CHASE_PROFILES}
            assert {r['slug'] for r in pages} == eligible


def test_retailer_family_profiles_do_not_invent_guarantees_or_odds():
    assert len(PROFILES) > 400
    for profile in PROFILES.values():
        assert profile['confidence'] == 70
        assert profile['evidence_scope'] == 'retailer_product_families'
        assert profile['format_hits'] == []
        assert profile['source_url'].startswith(('https://www.coolcard.se/product/', 'https://speltrollet.se/products/'))
        assert all('odds och garanti saknas' in chase['odds'] for chase in profile['headline_chases'])
