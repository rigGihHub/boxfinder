from sqlalchemy import select, func

from app import seed
from app.models import CatalogCandidate, Offer, Store
from app.routers import rankings
from app.services.market_scan_snapshot import INVENTORIES, OFFERS, PROFILES, REVIEW
from test_real_snapshot import session_factory


def test_market_scan_preserves_offer_ids_dates_and_candidate_decisions(monkeypatch):
    Session = session_factory()
    monkeypatch.setattr(seed, 'SessionLocal', Session)
    current = seed.REAL_SNAPSHOT
    monkeypatch.setattr(seed, 'REAL_SNAPSHOT', seed.PRE_MARKET_SCAN_SNAPSHOT)
    seed.seed_verified_snapshot()
    with Session() as db:
        previous = {(o.store.name, o.external_id): (o.id, o.observed_at) for o in db.scalars(select(Offer))}
    monkeypatch.setattr(seed, 'REAL_SNAPSHOT', current)
    seed.seed_verified_snapshot()
    seed.seed_market_scan_inventory()
    with Session() as db:
        candidate = db.scalar(select(CatalogCandidate).where(CatalogCandidate.review_status == 'new'))
        candidate.review_status = 'rejected'
        rejected_id = candidate.id
        db.commit()
    seed.seed_verified_snapshot()
    seed.seed_market_scan_inventory()
    with Session() as db:
        actual = {(o.store.name, o.external_id): o for o in db.scalars(select(Offer))}
        assert len(actual) == len(current)
        assert all((actual[k].id, actual[k].observed_at) == v for k, v in previous.items())
        assert db.get(CatalogCandidate, rejected_id).review_status == 'rejected'
        for name, inventory in INVENTORIES.items():
            store = db.scalar(select(Store).where(Store.name == name))
            assert store.policy_status == 'review_required' and store.collection_method == 'manual'
            assert len({r['id'] for r in inventory['variants']}) == inventory['entry_count']
            assert db.scalar(select(func.count()).select_from(CatalogCandidate).where(CatalogCandidate.store_id == store.id)) == inventory['entry_count']
        for row in OFFERS:
            offer = actual[row['store_name'], row['sku']]
            assert (offer.price_sek, offer.stock_status, offer.url, offer.is_preorder) == (row['price'], 'in_stock', row['buy_url'], False)
            assert (offer.variant.product.slug, offer.variant.language, offer.variant.format) == (row['slug'], 'English', row['fmt'])


def test_scan_store_selection_uses_own_offer_before_budget(monkeypatch):
    Session = session_factory()
    monkeypatch.setattr(seed, 'SessionLocal', Session)
    seed.seed_verified_snapshot()
    seed.seed_chase_profiles()
    monkeypatch.setattr(rankings, '_resale_cache', dict(until=0, ranked=None, refreshing=False))
    with Session() as db:
        for name, count in [('Pardon My Kicks', 8), ('RGB KingZ', 4), ('MonMon', 1)]:
            expected = {r['slug']: r for r in OFFERS if r['store_name'] == name}
            result = rankings.resale_rankings(strategy='value', limit=100, offset=0, db=db,
                category=None, max_price=None, store_id=None, store_name=name, cost_basis='total')
            assert result['count'] == count
            assert {i['slug'] for i in result['items']} == expected.keys()
            for item in result['items']:
                assert item['store'] == name and item['cost_basis'] == 'item'
                assert item['price'] == expected[item['slug']]['price']
                assert item['url'] == expected[item['slug']]['buy_url']
            budget = rankings.resale_rankings(strategy='value', limit=100, offset=0, db=db,
                category=None, max_price=150, store_id=None, store_name=name, cost_basis='item')
            assert {i['slug'] for i in budget['items']} == {slug for slug, r in expected.items() if r['price'] <= 150}


def test_inventory_and_content_limits_are_explicit():
    previous = {r['slug'] for r in seed.PRE_MARKET_SCAN_SNAPSHOT}
    assert set(REVIEW['new_product_slugs']) == {r['slug'] for r in OFFERS} - previous
    assert len(REVIEW['new_product_slugs']) == 4
    assert len(OFFERS) == len({(r['store_name'], r['sku']) for r in OFFERS}) == 13
    for name, inventory in INVENTORIES.items():
        if name == 'MonMon':
            assert not inventory['pagination_complete']
            assert inventory['record_scope'] == 'reviewed_product_pages'
        else:
            assert inventory['pagination_complete'] and inventory['page_counts'][-1] == 0
            assert sum(inventory['page_counts']) == inventory['product_count']
    eco = next(r for r in OFFERS if r['slug'].endswith('eco-pack'))
    assert eco['packs'] == 3 and eco['cards'] is None and '25 kort' in eco['facts'][0]
    tins = [r for r in OFFERS if 'mega-tin-' in r['slug']]
    assert len({r['slug'] for r in tins}) == 3
    assert all(r['packs'] == 4 and r['cards'] == 10 for r in tins)
    staged = [r for r in INVENTORIES['RGB KingZ']['variants'] if r.get('product_id') in {'16002314862922', '15665439408458'}]
    assert len(staged) == 2 and all('offer_sku' not in r for r in staged)
    assert any('förhandsbokning' in r['exclusion_reason'] for r in staged)
    assert any('motstridigt' in r['exclusion_reason'] for r in staged)
    assert all(p['format_hits'] == [] and p['confidence'] == 70 for p in PROFILES.values())
    assert all(a['language_evidence'] and a['stock_evidence'] for a in REVIEW['accepted'])
