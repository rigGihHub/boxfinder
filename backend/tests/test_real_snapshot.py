from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import Offer, Product, ProductFact, Store
import app.seed as seedmod

def session_factory():
    engine=create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)

def test_verified_snapshot_seeds_real_swedish_products(monkeypatch):
    Session=session_factory()
    monkeypatch.setattr(seedmod,"SessionLocal",Session)
    seedmod.seed_verified_snapshot()
    db=Session()
    offers=db.scalars(select(Offer).where(Offer.source_kind=="verified_snapshot")).all()
    assert len(offers) >= 20
    assert all(o.match_status=="manual_matched" for o in offers)
    assert all(o.source_confidence==100 for o in offers)
    coolcard=db.scalar(select(Store).where(Store.name=="Coolcard"))
    assert coolcard is not None
    db.close()

def test_verified_snapshot_is_idempotent(monkeypatch):
    Session=session_factory()
    monkeypatch.setattr(seedmod,"SessionLocal",Session)
    seedmod.seed_verified_snapshot()
    seedmod.seed_verified_snapshot()
    db=Session()
    count=db.scalar(select(func.count()).select_from(Offer).where(Offer.source_kind=="verified_snapshot"))
    assert count == len(seedmod.REAL_SNAPSHOT)
    db.close()

def test_verified_product_facts_exist_for_supported_products(monkeypatch):
    Session=session_factory()
    monkeypatch.setattr(seedmod,"SessionLocal",Session)
    seedmod.seed_verified_snapshot()
    db=Session()
    facts=db.scalars(select(ProductFact)).all()
    assert len(facts) >= 4
    assert all(f.confidence==100 for f in facts)
    db.close()


def test_snapshot_includes_football_and_pokemon(monkeypatch):
    Session=session_factory()
    monkeypatch.setattr(seedmod,"SessionLocal",Session)
    seedmod.seed_verified_snapshot()
    db=Session()
    categories=set(db.scalars(select(Product.category).where(Product.slug.like("cc-%"))).all())
    assert "Hockey" in categories
    assert "Fotboll" in categories
    assert "Pokémon" in categories
    db.close()

def test_all_chase_profiles_point_to_seeded_products(monkeypatch):
    Session=session_factory()
    monkeypatch.setattr(seedmod,"SessionLocal",Session)
    seedmod.seed_verified_snapshot()
    db=Session()
    slugs={x for x in seedmod.CHASE_PROFILES.keys()}
    found=set(db.scalars(select(Product.slug).where(Product.slug.in_(slugs))).all())
    assert found==slugs
    db.close()

def test_series2_and_clearcut_have_card_level_chases():
    for slug in ("cc-2025-26-series2-hobby","cc-2025-26-clear-cut-hobby"):
        profile=seedmod.CHASE_PROFILES[slug]
        assert len(profile.get("headline_chases",[])) >= 8
        assert all(x.get("card") and x.get("tier") and x.get("odds") for x in profile["headline_chases"])

def test_series1_and_opc_have_exact_chase_ladders():
    for slug in ("cc-2025-26-series1-hobby","cc-2025-26-opc-hobby"):
        profile=seedmod.CHASE_PROFILES[slug]
        assert len(profile.get("headline_chases",[])) >= 7
        assert all(x.get("card") and x.get("tier") and x.get("odds") for x in profile["headline_chases"])

def test_loose_packs_and_pokemon_expose_named_content_without_fake_odds():
    opc = seedmod.CHASE_PROFILES["cc-pack-2025-26-opc-hobby"]
    mvp = seedmod.CHASE_PROFILES["cc-pack-2025-26-mvp-hobby"]
    pokemon = seedmod.CHASE_PROFILES["cc-pokemon-mega-zygarde-premium"]
    assert any("Marquee Rookies" in x["card"] for x in opc["headline_chases"])
    assert any("Autograf" in x["card"] and "Ingen verifierad" in x["odds"] for x in mvp["headline_chases"])
    assert "Mega Zygarde ex" in pokemon["key_names"]
    assert any("#124" in x["card"] for x in pokemon["headline_chases"])
