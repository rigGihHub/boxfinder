import json

from sqlalchemy import select

from app import seed
from app.models import ChaseProfile, Offer, Product, ProductVariant, Store
from app.routers import rankings
from app.services.chase_content import format_hits
from test_real_snapshot import session_factory


def seeded_db(monkeypatch):
    Session = session_factory()
    monkeypatch.setattr(seed, "SessionLocal", Session)
    seed.seed_verified_snapshot()
    seed.seed_chase_profiles()
    monkeypatch.setattr(rankings, "_resale_cache", dict(until=0, ranked=None, refreshing=False))
    return Session()


def test_competing_stores_share_variant_and_filter_selects_actual_offer(monkeypatch):
    with seeded_db(monkeypatch) as db:
        catalog = rankings.resale_rankings(strategy="value", category="Magic", max_price=None, limit=100, db=db, store_id=None)
        box = next(x for x in catalog["items"] if x["slug"] == "hk-mtg-tmnt-play-display")
        assert box["price"] == 1695 and box["store"] == "Hobbykort"
        assert {x["store"] for x in box["store_offers"]} == {"Hobbykort", "Mox Games", "Speltrollet"}
        mox = db.scalar(select(Store).where(Store.name == "Mox Games"))
        result = rankings.resale_rankings(strategy="value", category="Magic", max_price=2000, limit=100, db=db, store_id=mox.id)
        assert len(result["items"]) == 1
        assert result["items"][0]["id"] == box["id"]
        assert result["items"][0]["price"] == 1995
        assert result["items"][0]["url"].startswith("https://moxgames.se/")
        assert rankings._resale_items(db, "value", "Magic", 1800, mox.id) == []
        assert {"Mox Games", "Alara Games"} <= {x["name"] for x in catalog["available_stores"]}


def test_new_loose_packs_fit_low_budget_and_keep_own_store_prices(monkeypatch):
    with seeded_db(monkeypatch) as db:
        result = rankings.resale_rankings(strategy="value", category="Tennis", max_price=150, limit=100, db=db, store_id=None)
        pack = next(x for x in result["items"] if x["slug"] == "cc-2026-topps-chrome-tennis-pack")
        assert (pack["price"], pack["packs"], pack["cards_per_pack"]) == (149, 1, 8)
        assert not pack["format_hits"]
        alara = db.scalar(select(Store).where(Store.name == "Alara Games"))
        packs = rankings._resale_items(db, "value", "Magic", 100, alara.id)
        assert len(packs) == 3 and all(x["price"] == 85 for x in packs)
        assert all(x["url"].startswith("https://www.alaragames.se/products/") for x in packs)


def test_play_chases_exclude_collector_only_treatments_and_pack_counts_are_exact():
    for slug, fmt, count in [("dl-mtg-tmnt-play-pack", "single pack", 1), ("hk-mtg-tmnt-play-display", "booster box", 30)]:
        profile = seed.CHASE_PROFILES[slug]
        chases = json.dumps(profile["headline_chases"], ensure_ascii=False).lower()
        assert "eastman" not in chases and "fracture foil" not in chases
        assert "1:28" in chases and "kortspecifikt odds saknas" in chases
        assert format_hits(profile, fmt)[0]["count"] == count
        assert format_hits(profile, "hobby box") == []
    collector = seed.CHASE_PROFILES["dl-mtg-tmnt-collector-pack"]
    assert any("Eastman" in x["card"] for x in collector["headline_chases"])
    assert "inte handskriven autograf" in collector["caveat"]
    assert format_hits(collector, "single pack")[0]["count"] == 1
    pack = seed.CHASE_PROFILES["cc-2026-topps-chrome-tennis-pack"]
    assert format_hits(pack, "single pack") == []
    assert "Ingen autografgaranti" in pack["tiers"]["everyday"]["items"]
    assert format_hits(seed.CHASE_PROFILES["cs-2026-topps-chrome-tennis-hobby"], "hobby box")[0]["count"] == 2


def test_restart_keeps_original_verification_times_and_does_not_duplicate_offers(monkeypatch):
    with seeded_db(monkeypatch) as db:
        before = len(db.scalars(select(Offer)).all())
        seed.seed_verified_snapshot()
        seed.seed_chase_profiles()
        db.expire_all()
        assert len(db.scalars(select(Offer)).all()) == before
        for slug in seed.OCTOBER_03_NEW_PROFILE_SLUGS:
            product = db.scalar(select(Product).where(Product.slug == slug))
            variant = db.scalar(select(ProductVariant).where(ProductVariant.product_id == product.id))
            assert db.scalar(select(ChaseProfile).where(ChaseProfile.variant_id == variant.id)).verified_at == seed.OCTOBER_03_OBSERVED_AT
            original_ids = {(row['store_name'], row['sku']) for row in seed.OCTOBER_03_EXPANSION if row['slug'] == slug}
            original_offers = [x for x in variant.offers if (x.store.name, x.external_id) in original_ids]
            assert len(original_offers) == len(original_ids)
            assert all(x.observed_at == seed.OCTOBER_03_OBSERVED_AT for x in original_offers)
        urls = {x.url for x in db.scalars(select(Offer))}
        assert "https://nordicsportscards.se/products/2026-topps-chrome-tennis-hobby-box" not in urls
        assert "https://tcgstore.se/products/magic-the-gathering-teenage-mutant-ninja-turtles-play-booster-box" not in urls
