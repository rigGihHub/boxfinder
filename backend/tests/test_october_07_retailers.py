from sqlalchemy import select, func

from app import seed
from app.models import CatalogCandidate, Offer, Store
from app.routers import rankings
from app.services.new_retailers_snapshot import INVENTORIES, OFFERS, PROFILES, REVIEW
from test_real_snapshot import session_factory


def test_reviewed_inventory_import_preserves_existing_ids_and_decisions(monkeypatch):
    Session = session_factory()
    monkeypatch.setattr(seed, 'SessionLocal', Session)
    current = seed.REAL_SNAPSHOT
    monkeypatch.setattr(seed, 'REAL_SNAPSHOT', seed.PRE_NEW_RETAILERS_SNAPSHOT)
    seed.seed_verified_snapshot()
    with Session() as db:
        previous = {(o.store.name, o.external_id): (o.id, o.observed_at) for o in db.scalars(select(Offer))}
    monkeypatch.setattr(seed, 'REAL_SNAPSHOT', current)
    seed.seed_verified_snapshot()
    seed.seed_new_retailers_inventory()
    with Session() as db:
        candidate = db.scalar(select(CatalogCandidate).where(CatalogCandidate.review_status == 'new'))
        candidate.review_status = 'rejected'
        rejected_id = candidate.id
        db.commit()
    seed.seed_verified_snapshot()
    seed.seed_new_retailers_inventory()
    with Session() as db:
        actual = {(o.store.name, o.external_id): o for o in db.scalars(select(Offer))}
        assert len(actual) == len(current)
        assert all((actual[key].id, actual[key].observed_at) == value for key, value in previous.items())
        assert db.get(CatalogCandidate, rejected_id).review_status == 'rejected'
        for name, inventory in INVENTORIES.items():
            store = db.scalar(select(Store).where(Store.name == name))
            assert store.policy_status == 'review_required'
            assert store.collection_method == 'manual'
            assert inventory['pagination_complete'] and inventory['page_counts'][-1] == 0
            assert sum(inventory['page_counts']) == inventory['product_count']
            assert len({r['id'] for r in inventory['variants']}) == inventory['entry_count']
            assert db.scalar(select(func.count()).select_from(CatalogCandidate).where(CatalogCandidate.store_id == store.id)) == inventory['entry_count']
        for row in OFFERS:
            offer = actual[row['store_name'], row['sku']]
            assert (offer.price_sek, offer.stock_status, offer.url, offer.is_preorder) == (row['price'], 'in_stock', row['buy_url'], False)
            assert (offer.variant.product.slug, offer.variant.language, offer.variant.format) == (row['slug'], row['language'], row['fmt'])


def test_new_store_rankings_use_own_prices_and_budget(monkeypatch):
    Session = session_factory()
    monkeypatch.setattr(seed, 'SessionLocal', Session)
    seed.seed_verified_snapshot()
    seed.seed_chase_profiles()
    monkeypatch.setattr(rankings, '_resale_cache', dict(until=0, ranked=None, refreshing=False))
    with Session() as db:
        for name, count in [('Hobbybutiken', 2), ('TheMinifigVault', 16), ('The Sealed Poke Vault', 4)]:
            result = rankings.resale_rankings(strategy='value', limit=100, offset=0,
                db=db, category=None, max_price=None, store_id=None, store_name=name, cost_basis='total')
            expected = {r['slug']: r for r in OFFERS if r['store_name'] == name}
            assert result['count'] == count
            assert {item['slug'] for item in result['items']} == expected.keys()
            for item in result['items']:
                assert item['store'] == name and item['cost_basis'] == 'item'
                assert item['price'] == expected[item['slug']]['price']
                assert item['url'] == expected[item['slug']]['buy_url']
            budget = rankings.resale_rankings(strategy='value', limit=100, offset=0,
                db=db, category=None, max_price=150, store_id=None, store_name=name, cost_basis='item')
            assert {item['slug'] for item in budget['items']} == {slug for slug, row in expected.items() if row['price'] <= 150}


def test_evidence_separates_language_formats_and_unknown_facts():
    old = {r['slug'] for r in seed.PRE_NEW_RETAILERS_SNAPSHOT}
    assert set(REVIEW['new_product_slugs']) == {r['slug'] for r in OFFERS} - old
    assert len(REVIEW['new_product_slugs']) == 10
    assert len(OFFERS) == len({(r['store_name'], r['sku']) for r in OFFERS}) == 22
    assert all(r['observed_at'].startswith('2026-10-07') for r in OFFERS)
    # English anniversary products do not share Japanese/Chinese pack identities.
    anniversary = [r for r in OFFERS if '30th-celebration-en-' in r['slug']]
    assert len(anniversary) == 4 and all(r['language'] == 'English' for r in anniversary)
    assert all(r['cards'] is None for r in anniversary)
    assert {r['fmt'] for r in anniversary} == {'single pack', 'elite trainer box', 'blister', 'collection box'}
    assert not any(r['store_name'] == 'Swepoke' for r in OFFERS)
    assert any(row['store_name'] == 'Swepoke' for row in REVIEW['discovered_only'])
    for profile in PROFILES.values():
        assert profile['format_hits'] == []
        assert profile['verified_at'].startswith('2026-10-07')
        assert all('odds' in chase for chase in profile['headline_chases'])
    # Misleading retailer text mixes unrelated sets; it remains in the review queue.
    vault = INVENTORIES['The Sealed Poke Vault']['variants']
    growlithe = next(r for r in vault if 'Growlithe' in r['title'])
    assert 'offer_sku' not in growlithe
    # A Chinese product profile cannot inherit an unrelated One Piece name.
    chinese = PROFILES['kv-pokemon-chasing-glory-together-slim-booster-box-kinesisk']
    assert 'Brook' not in str(chinese)
