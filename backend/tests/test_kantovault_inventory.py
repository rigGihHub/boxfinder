from datetime import datetime

from sqlalchemy import func, select

from app import seed
from app.models import CatalogCandidate, Offer, Product, Store
from app.routers import rankings
from app.services.kantovault_snapshot import INVENTORY, OFFERS, PROFILES
from test_real_snapshot import session_factory


def test_complete_catalogue_includes_all_variants_and_is_idempotent(monkeypatch):
    assert INVENTORY['pagination_complete']
    assert INVENTORY['page_counts'] == [250, 207, 0]
    variants = INVENTORY['variants']
    assert len(variants) == len({r['id'] for r in variants}) == 519
    assert len({r['product_id'] for r in variants}) == 457
    assert INVENTORY['product_pages_checked'] == 104
    Session = session_factory()
    monkeypatch.setattr(seed, 'SessionLocal', Session)
    seed.seed_kantovault_inventory()
    seed.seed_kantovault_inventory()
    with Session() as db:
        store = db.scalar(select(Store).where(Store.name == 'Kantovault'))
        candidates = db.scalars(select(CatalogCandidate).where(CatalogCandidate.store_id == store.id)).all()
        assert len(candidates) == 519
        assert {c.external_id for c in candidates} == {r['id'] for r in variants}
        assert any(c.exclusion_reason == 'graded_card' for c in candidates)
        assert any(c.exclusion_reason == 'single_card' for c in candidates)
        assert any(c.exclusion_reason == 'accessory_or_figure' for c in candidates)
        assert (store.adapter_key, store.policy_status) == ('manual', 'review_required')


def test_existing_offer_ids_survive_and_import_matches_snapshot(monkeypatch):
    Session = session_factory()
    monkeypatch.setattr(seed, 'SessionLocal', Session)
    full = seed.REAL_SNAPSHOT
    monkeypatch.setattr(seed, 'REAL_SNAPSHOT', [r for r in full if r['slug'].startswith('kv-one-piece-op10-jp-')])
    seed.seed_verified_snapshot()
    with Session() as db:
        old_ids = dict(db.execute(select(Offer.external_id, Offer.id)).all())
    monkeypatch.setattr(seed, 'REAL_SNAPSHOT', full)
    seed.seed_verified_snapshot()
    seed.seed_verified_snapshot()
    with Session() as db:
        store = db.scalar(select(Store).where(Store.name == 'Kantovault'))
        offers = {o.external_id: o for o in db.scalars(select(Offer).where(Offer.store_id == store.id))}
        assert len(offers) == len(OFFERS) == 240
        assert all(offers[sku].id == ident for sku, ident in old_ids.items())
        for row in OFFERS:
            offer = offers[row['sku']]
            assert (offer.price_sek, offer.stock_status, offer.is_preorder, offer.url) == (
                row['price'], row['stock'], row['preorder'], row['buy_url'])
            assert (offer.variant.format, offer.variant.language) == (row['fmt'], row['language'])


def test_preorders_fixed_items_and_missing_content_do_not_rank(monkeypatch):
    Session = session_factory()
    monkeypatch.setattr(seed, 'SessionLocal', Session)
    seed.seed_verified_snapshot()
    seed.seed_chase_profiles()
    monkeypatch.setattr(rankings, '_resale_cache', dict(until=0, ranked=None, refreshing=False))
    with Session() as db:
        result = rankings.resale_rankings(strategy='value', limit=100, db=db,
            category=None, max_price=None, store_id=None, store_name='Kantovault', cost_basis='item')
        assert result['count'] == len(result['items']) == 84
        expected = {r['slug'] for r in OFFERS if r['stock'] == 'in_stock'
                    and r['slug'] in seed.CHASE_PROFILES}
        assert {r['slug'] for r in result['items']} == expected
        assert all(r['store'] == 'Kantovault' and r['cost_basis'] == 'item' for r in result['items'])
        assert not any('30th-celebration' in r['slug'] or 'stellar-crystal' in r['slug'] for r in result['items'])
        assert not any('premium-card-collection' in r['slug'] or 'starter-set' in r['slug'] for r in result['items'])
        # Same Japanese box has multiple store offers, rather than a duplicate product.
        shared = next(r for r in result['items'] if r['slug'] == 'sp-pokemon-brave-display-jp')
        assert shared['price'] == 1149
        assert db.scalar(select(func.count()).select_from(Product).where(Product.slug == shared['slug'])) == 1


def test_language_specific_configuration_and_scoped_evidence():
    lorcana = [r for r in OFFERS if 'lorcana-rise-of-the-floodborn' in r['slug']]
    assert len(lorcana) == 2
    assert all(r['language'] == 'Japanese' and r['cards'] == 6 for r in lorcana)
    assert next(r for r in lorcana if r['fmt'] == 'booster box')['packs'] == 16
    blister = next(r for r in OFFERS if 'rebel-clash-3-pack-blister' in r['slug'] and 'Rayquaza' in r['name'])
    assert PROFILES[blister['slug']]['key_names'] == ['Rayquaza']
    assert PROFILES[blister['slug']]['format_hits'][0]['family'] == 'Rayquaza promokort'
    china = [r for r in OFFERS if 'gem-pack-vol-6' in r['slug']]
    assert all(r['language'] == 'Chinese' and r['cards'] == 4 for r in china)
    for slug in ['kv-mega-brave-booster-pack-japansk', 'kv-mega-symphonia-booster-pack-japansk']:
        assert PROFILES[slug]['format_hits'] == []
        assert not any('1:' in c['odds'] for c in PROFILES[slug]['headline_chases'])
    for profile in PROFILES.values():
        assert datetime.fromisoformat(profile['verified_at'].replace('Z', '+00:00')).replace(tzinfo=None) <= datetime.utcnow()
    preorders = [r for r in OFFERS if r['preorder']]
    assert len(preorders) == 13 and all(r['stock'] == 'unknown' for r in preorders)
