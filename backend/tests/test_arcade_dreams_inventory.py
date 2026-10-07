from sqlalchemy import select, func

from app import seed
from app.models import CatalogCandidate, Offer, Store
from app.routers import rankings
from app.services.arcade_dreams_snapshot import INVENTORIES, OFFERS, PROFILES, REVIEW
from app.services.product_format import total_sealed_cards
from test_real_snapshot import session_factory


def test_complete_navigation_inventory_and_strict_review():
    inventory = INVENTORIES['Arcade Dreams']
    assert inventory['pagination_complete']
    assert inventory['record_scope'] == 'all_public_navigation_categories'
    assert len(inventory['categories']) == 19
    assert all(c['pagination_complete'] and c['page_counts'][-1] == 0 for c in inventory['categories'])
    rows = inventory['variants']
    assert len(rows) == len({r['id'] for r in rows}) == 5862
    tcg = [r for r in rows if '25' in r['categories']]
    assert len(tcg) == 434
    assert sum(next(c for c in inventory['categories'] if c['category_id'] == '25')['page_counts']) == 434
    assert len(OFFERS) == len({r['sku'] for r in OFFERS}) == 48
    assert sum(r['stock'] == 'in_stock' for r in OFFERS) == 47
    assert set(REVIEW['new_product_slugs']) == {r['slug'] for r in OFFERS} - {r['slug'] for r in seed.PRE_ARCADE_CATALOG_SNAPSHOT}
    assert len(REVIEW['new_product_slugs']) == 12
    assert set(PROFILES).isdisjoint(seed.PRE_ARCADE_CATALOG_PROFILES)
    assert all(p['confidence'] in {70, 90} and not p['format_hits'] for p in PROFILES.values())
    assert all(a['language_evidence'] and a['stock_evidence'] and a['content_source'] for a in REVIEW['accepted'])
    assert all('offer_sku' not in r for r in rows if r['preorder'] or not r['randomized_cards'])
    staged = {r['id']: r for r in rows if r['id'] in {s['id'] for s in REVIEW['staged']}}
    assert len(staged) == 23 and all(r['exclusion_reason'] and 'offer_sku' not in r for r in staged.values())
    assert 'Spark of Rebellion' in staged['37245']['exclusion_reason']
    china = [r for r in OFFERS if r['language'] == 'Chinese']
    assert len(china) == 2 and all('CSV9.5C' in r['name'] for r in china)
    assert next(r for r in china if r['fmt'] == 'booster box')['packs'] is None
    assert next(r for r in OFFERS if r['slug'] == 'ad-mtg-tmnt-pizza-bundle')['cards'] is None
    assert next(r for r in OFFERS if r['slug'] == 'ad-mtg-marvel-superheroes-draft-night-en')['cards'] is None


def test_migration_preserves_ids_other_observation_dates_and_review_decisions(monkeypatch):
    Session = session_factory()
    monkeypatch.setattr(seed, 'SessionLocal', Session)
    current = seed.REAL_SNAPSHOT
    monkeypatch.setattr(seed, 'REAL_SNAPSHOT', seed.PRE_ARCADE_CATALOG_SNAPSHOT)
    seed.seed_verified_snapshot()
    with Session() as db:
        previous = {(o.store.name, o.external_id): (o.id, o.observed_at) for o in db.scalars(select(Offer))}
        assert sum(k[0] == 'Arcade Dreams' for k in previous) == 4
    monkeypatch.setattr(seed, 'REAL_SNAPSHOT', current)
    seed.seed_verified_snapshot()
    seed.seed_arcade_dreams_inventory()
    with Session() as db:
        store = db.scalar(select(Store).where(Store.name == 'Arcade Dreams'))
        c = db.scalar(select(CatalogCandidate).where(CatalogCandidate.store_id == store.id, CatalogCandidate.review_status == 'new'))
        c.review_status = 'rejected'
        cid = c.id
        db.commit()
    seed.seed_verified_snapshot()
    seed.seed_arcade_dreams_inventory()
    with Session() as db:
        actual = {(o.store.name, o.external_id): o for o in db.scalars(select(Offer))}
        assert len(actual) == len(current)
        assert all(actual[k].id == v[0] for k, v in previous.items())
        assert all(actual[k].observed_at == v[1] for k, v in previous.items() if k[0] != 'Arcade Dreams')
        assert db.get(CatalogCandidate, cid).review_status == 'rejected'
        store = db.scalar(select(Store).where(Store.name == 'Arcade Dreams'))
        assert store.collection_method == 'manual' and store.policy_status == 'review_required'
        assert db.scalar(select(func.count()).select_from(CatalogCandidate).where(CatalogCandidate.store_id == store.id)) == 5862
        for r in OFFERS:
            o = actual['Arcade Dreams', r['sku']]
            assert (o.price_sek, o.stock_status, o.url, o.variant.language, o.variant.format) == (r['price'], r['stock'], r['buy_url'], r['language'], r['fmt'])
        pizza = actual['Arcade Dreams', 'AD-35750']
        assert pizza.stock_status == 'out_of_stock' and total_sealed_cards(pizza.variant) == 141
        assert actual['Arcade Dreams', '37250'].price_sek == 1149


def test_arcade_rankings_use_own_price_url_and_budget(monkeypatch):
    Session = session_factory()
    monkeypatch.setattr(seed, 'SessionLocal', Session)
    seed.seed_verified_snapshot()
    seed.seed_chase_profiles()
    monkeypatch.setattr(rankings, '_resale_cache', dict(until=0, ranked=None, refreshing=False))
    expected = {r['slug']: r for r in OFFERS if r['stock'] == 'in_stock'}
    with Session() as db:
        result = rankings.resale_rankings(strategy='value', limit=100, offset=0, db=db,
            category=None, max_price=None, store_id=None, store_name='Arcade Dreams', cost_basis='total')
        assert result['count'] == 47
        assert {i['slug'] for i in result['items']} == expected.keys()
        for item in result['items']:
            assert item['store'] == 'Arcade Dreams' and item['cost_basis'] == 'item'
            assert item['price'] == expected[item['slug']]['price']
            assert item['url'] == expected[item['slug']]['buy_url']
        budget = rankings.resale_rankings(strategy='value', limit=100, offset=0, db=db,
            category=None, max_price=100, store_id=None, store_name='Arcade Dreams', cost_basis='item')
        assert {i['slug'] for i in budget['items']} == {slug for slug, r in expected.items() if r['price'] <= 100}
        assert all('pizza-bundle' not in i['slug'] for i in result['items'])
