from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import Offer, Product, ProductFact, ProductVariant, Store
from app.routers.discovery import real_catalog
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


def test_snapshot_includes_cross_category_products(monkeypatch):
    Session=session_factory()
    monkeypatch.setattr(seedmod,"SessionLocal",Session)
    seedmod.seed_verified_snapshot()
    db=Session()
    categories=set(db.scalars(select(Product.category).where(Product.slug.like("cc-%"))).all())
    assert "Hockey" in categories
    assert "Fotboll" in categories
    assert "Pokémon" in categories
    assert "One Piece" in categories
    assert "Marvel" in categories
    assert "Disney" in categories
    db.close()

def test_nonsport_additions_have_direct_store_links_and_pack_formats(monkeypatch):
    Session=session_factory()
    monkeypatch.setattr(seedmod,"SessionLocal",Session)
    seedmod.seed_verified_snapshot()
    db=Session()
    rows=db.execute(select(Product, Offer).join(ProductVariant, ProductVariant.product_id==Product.id).join(Offer, Offer.variant_id==ProductVariant.id).where(Product.slug.in_({
        "cc-pokemon-black-bolt-jp-pack", "cc-one-piece-op15-jp-pack",
        "cc-marvel-2026-chrome-hobby-pack", "cc-lorcana-azurite-pack",
        "cc-mtg-marvel-superheroes-play-display",
    }))).all()
    assert len(rows)==5
    assert all("/product/" in offer.url for _, offer in rows)
    assert any(product.category=="Pokémon" and product.slug.endswith("pack") for product,_ in rows)
    assert any(product.category=="One Piece" and product.slug.endswith("pack") for product,_ in rows)
    japanese=db.scalar(select(ProductVariant).join(Product).where(Product.slug=="cc-pokemon-black-bolt-jp-pack"))
    assert japanese.language=="Japanese"
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

def test_series1_and_opc_have_exact_c