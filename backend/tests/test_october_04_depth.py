import json
from pathlib import Path

from sqlalchemy import select

from app import seed
from app.models import ChaseProfile, Offer, Product, ProductVariant
from app.routers import rankings
from test_real_snapshot import session_factory


def test_deeper_offers_reuse_exact_variants_and_have_review_evidence(monkeypatch):
    Session = session_factory()
    monkeypatch.setattr(seed, 'SessionLocal', Session)
    seed.seed_verified_snapshot()
    seed.seed_chase_profiles()
    seed.seed_verified_snapshot()
    seed.seed_chase_profiles()
    evidence = json.loads((Path(seed.__file__).parent / 'snapshots/verified_2026_10_04_depth.json').read_text())
    rows = seed.CARDLAND_DEPTH_OFFERS + seed.SPELTROLLET_DEPTH_OFFERS
    assert len(evidence['accepted']) == len(rows) == 35
    with Session() as db:
        for row in rows:
            offers = db.scalars(select(Offer).where(Offer.external_id == row['sku'])).all()
            assert len(offers) == 1
            offer = offers[0]
            assert offer.store.name == row['store_name']
            assert offer.observed_at == seed.OCTOBER_04_DEPTH_VERIFIED_AT
            assert (offer.price_sek, offer.stock_status, offer.is_preorder) == (row['price'], 'in_stock', False)
            variants = db.scalars(select(ProductVariant).join(Product).where(
                Product.slug == row['slug'], ProductVariant.language == row['language'],
                ProductVariant.format == row['fmt'])).all()
            assert len(variants) == 1 and variants[0].id == offer.variant_id
            assert (offer.variant.packs, offer.variant.cards_per_pack) == (row['packs'], row['cards'])
            assert db.scalar(select(ChaseProfile).where(ChaseProfile.variant_id == offer.variant_id))
            assert any(e['url'] == offer.url and e['canonical_slug'] == row['slug'] for e in evidence['accepted'])


def test_new_display_guarantees_scale_contents_without_inventing_named_card_odds(monkeypatch):
    Session = session_factory()
    monkeypatch.setattr(seed, 'SessionLocal', Session)
    seed.seed_verified_snapshot()
    seed.seed_chase_profiles()
    formats = {
        'sp-mtg-bloomburrow-play-display': ('booster box', 36, 14, 'rare/mythic', 36),
        'sp-mtg-spiderman-bundle': ('bundle', 9, 14, 'rare/mythic', 9),
        'sp-mtg-tmnt-collector-display': ('collector booster box', 12, 15, 'Source Material-kort', 12),
    }
    with Session() as db:
        for slug, (fmt, packs, cards, family, count) in formats.items():
            variant = db.scalar(select(ProductVariant).join(Product).where(Product.slug == slug))
            assert (variant.format, variant.packs, variant.cards_per_pack) == (fmt, packs, cards)
            profile = db.scalar(select(ChaseProfile).where(ChaseProfile.variant_id == variant.id))
            assert profile.verified_at == seed.OCTOBER_04_DEPTH_VERIFIED_AT
            data = json.loads(profile.content_json)
            assert data['format_hits'] == [dict(format=fmt, family=family, count=count,
                basis='guaranteed', quality='collectible' if 'collector' in fmt else 'base')]
        collector = seed.CHASE_PROFILES['sp-mtg-tmnt-collector-display']
        assert collector['headline_chases'] == seed.CHASE_PROFILES['dl-mtg-tmnt-collector-pack']['headline_chases']
        assert 'Ingen Eastman-headliner' in collector['caveat']
        assert seed.CHASE_PROFILES['dl-mtg-tmnt-collector-pack']['format_hits'][0]['count'] == 1


def test_deeper_store_coverage_uses_all_offers_even_under_filter_and_page_limit(monkeypatch):
    Session = session_factory()
    monkeypatch.setattr(seed, 'SessionLocal', Session)
    seed.seed_verified_snapshot()
    seed.seed_chase_profiles()
    monkeypatch.setattr(rankings, '_resale_cache', dict(until=0, ranked=None, refreshing=False))
    with Session() as db:
        data = rankings.resale_rankings(strategy='value', category='Magic', max_price=100,
            limit=1, db=db, store_id=None, cost_basis='item')
        stores = {s['name']: s for s in data['available_stores']}
        assert stores['Cardland']['product_count'] == stores['Cardland']['offer_count'] == 27
        assert stores['Speltrollet']['product_count'] == stores['Speltrollet']['offer_count'] == 17
        assert data['catalog_coverage']['current_store_offers'] == sum(s['offer_count'] for s in stores.values())
        assert data['catalog_coverage']['rankable_products'] < data['catalog_coverage']['current_store_offers']
        assert len(data['items']) == 1
