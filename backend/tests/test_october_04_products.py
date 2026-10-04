import json
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import func, select

from app import seed
from app.models import ChaseProfile, Offer, Product, ProductVariant
from app.routers import rankings
from test_real_snapshot import session_factory


def test_forty_new_variants_migrate_existing_catalog_and_all_rank(monkeypatch):
    Session = session_factory()
    monkeypatch.setattr(seed, 'SessionLocal', Session)
    expansion = seed.OCTOBER_04_NEW_PRODUCTS
    full_snapshot = seed.REAL_SNAPSHOT
    baseline = [r for r in full_snapshot if r['slug'] not in seed.OCTOBER_04_PRODUCTS_PROFILE_SLUGS]
    assert len(expansion) == len({r['slug'] for r in expansion}) == 40
    old_identities = {(r['category'], r['series'], r['fmt'], r.get('language', 'English')) for r in baseline}
    assert not any((r['category'], r['series'], r['fmt'], r['language']) in old_identities for r in expansion)
    assert seed.OCTOBER_04_PRODUCTS_VERIFIED_AT <= datetime.now(timezone.utc).replace(tzinfo=None)

    monkeypatch.setattr(seed, 'REAL_SNAPSHOT', baseline)
    seed.seed_verified_snapshot()
    seed.seed_chase_profiles()
    with Session() as db:
        original_ids = dict(db.execute(select(Product.slug, Product.id)).all())
    monkeypatch.setattr(seed, 'REAL_SNAPSHOT', full_snapshot)
    seed.seed_verified_snapshot()
    seed.seed_chase_profiles()
    seed.seed_verified_snapshot()
    seed.seed_chase_profiles()

    evidence = json.loads((Path(seed.__file__).parent / 'snapshots/verified_2026_10_04_products.json').read_text())
    assert {r['canonical_slug'] for r in evidence['accepted']} == seed.OCTOBER_04_PRODUCTS_PROFILE_SLUGS
    with Session() as db:
        assert db.scalar(select(func.count()).select_from(Offer)) == len(full_snapshot)
        assert all(db.scalar(select(Product.id).where(Product.slug == slug)) == ident for slug, ident in original_ids.items())
        for r in expansion:
            offers = db.scalars(select(Offer).where(Offer.external_id == r['sku'])).all()
            assert len(offers) == 1
            offer = offers[0]
            assert (offer.url, offer.price_sek, offer.stock_status, offer.is_preorder) == (r['buy_url'], r['price'], 'in_stock', False)
            assert (offer.variant.format, offer.variant.language, offer.variant.packs, offer.variant.cards_per_pack) == (r['fmt'], r['language'], r['packs'], r['cards'])
            profile = db.scalar(select(ChaseProfile).where(ChaseProfile.variant_id == offer.variant_id))
            assert profile and profile.verified_at == seed.OCTOBER_04_PRODUCTS_VERIFIED_AT
            assert profile.source_url.startswith('https://')

        monkeypatch.setattr(rankings, '_resale_cache', dict(until=0, ranked=None, refreshing=False))
        data = rankings.resale_rankings(strategy='value', limit=200, db=db,
            category=None, max_price=None, store_id=None, cost_basis='item')
        assert data['catalog_coverage'] == dict(rankable_products=137, current_store_offers=182, stores=21)
        assert seed.OCTOBER_04_PRODUCTS_PROFILE_SLUGS <= {item['slug'] for item in data['items']}


def test_language_and_format_exclusive_chases_are_not_promoted():
    profiles = seed.CHASE_PROFILES
    # Store pack descriptions sometimes duplicate box text. Only the sealed
    # Aetherdrift display includes the two first-place foil bonus cards.
    for suffix in ['pack', 'bundle']:
        p = profiles['sp-mtg-aetherdrift-' + suffix]
        assert not any('Box Topper' in hit['family'] for hit in p['format_hits'])
        assert all('serialized' not in chase['card'].lower() for chase in p['headline_chases'])
    display = profiles['sp-mtg-aetherdrift-display']
    assert next(h for h in display['format_hits'] if 'Box Topper' in h['family'])['count'] == 2
    for suffix, count in [('pack', 1), ('bundle', 9), ('display', 30)]:
        p = profiles['sp-mtg-strx-' + suffix]
        assert next(h for h in p['format_hits'] if h['family'] == 'Mystical Archive-kort')['count'] == count
        assert not any('Japanese' in c['card'] or 'silver scroll' in c['card'] for c in p['headline_chases'])
    hobbit = profiles['sp-mtg-hobbit-bundle']
    assert not any('Mox Amber' in c['card'] or 'Smaug' in c['card'] for c in hobbit['headline_chases'])
    for key in ['sp-pokemon-brave-display-jp', 'sp-pokemon-symphonia-display-jp']:
        assert profiles[key]['format_hits'] == []  # No inferred Japanese box hits.
    assert 'Mega Lucario ex' in profiles['sp-pokemon-brave-display-jp']['key_names']
    assert 'Mega Gardevoir ex' not in profiles['sp-pokemon-brave-display-jp']['key_names']
    assert 'Mega Gardevoir ex' in profiles['sp-pokemon-symphonia-display-jp']['key_names']
    assert 'Mega Meloetta ex' not in profiles['sp-pokemon-symphonia-display-jp']['key_names']
    assert profiles['sp-mtg-spiderman-collector-display']['format_hits'][0]['count'] == 60
    assert profiles['sp-mtg-spiderman-prerelease']['format_hits'][0]['count'] == 6
    assert profiles['sp-yugioh-rc5-display']['format_hits'][0]['count'] == 24
