from sqlalchemy import create_engine, select, func, event
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import ChaseProfile, Offer, Product, ProductFact, ProductVariant, Store
from app.routers.discovery import real_catalog
from app.routers.products import list_products
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
    assert len({product.slug for product,_ in rows})==5
    assert all("/product/" in offer.url or "/products/" in offer.url for _, offer in rows)
    assert any(product.category=="Pokémon" and product.slug.endswith("pack") for product,_ in rows)
    assert any(product.category=="One Piece" and product.slug.endswith("pack") for product,_ in rows)
    japanese=db.scalar(select(ProductVariant).join(Product).where(Product.slug=="cc-pokemon-black-bolt-jp-pack"))
    assert japanese.language=="Japanese"
    db.close()

def test_new_pokemon_and_one_piece_products_have_named_checklists(monkeypatch):
    Session=session_factory()
    monkeypatch.setattr(seedmod,"SessionLocal",Session)
    seedmod.seed_verified_snapshot()
    seedmod.seed_chase_profiles()
    db=Session()
    slugs={
        "cc-pokemon-ninja-spinner-m4-display", "cc-pokemon-ninja-spinner-m4-pack",
        "cc-pokemon-storm-emeralda-m6-display", "cc-pokemon-storm-emeralda-m6-pack",
        "cc-one-piece-op14-jp-display", "cc-one-piece-op14-jp-pack",
        "cc-one-piece-op16-jp-display", "cc-one-piece-op16-jp-pack",
    }
    products={p.slug:p for p in db.scalars(select(Product).where(Product.slug.in_(slugs))).all()}
    assert set(products)==slugs
    assert all(seedmod.CHASE_PROFILES[slug]["headline_chases"] for slug in slugs)
    offers=db.scalars(select(Offer).join(ProductVariant).join(Product).where(Product.slug.in_(slugs))).all()
    # Storm Emeralda and Ninja Spinner each have a second verified MaxGaming
    # offer in addition to their original Coolcard offer.
    assert len(offers)==10
    assert all(offer.url.startswith("https://") and offer.url.count("/") >= 4 for offer in offers)
    assert all("Japanese" in products[slug].canonical_name or products[slug].category=="One Piece" for slug in slugs)
    statements=[]
    bind=db.get_bind()
    def count_query(*args): statements.append(args[2])
    event.listen(bind,"before_cursor_execute",count_query)
    catalog=real_catalog(category="Pokémon",budget=None,format=None,limit=100,db=db)
    event.remove(bind,"before_cursor_execute",count_query)
    assert any(x["slug"]=="cc-pokemon-ninja-spinner-m4-pack" and x["chase_coverage"]["status"]=="card_level" for x in catalog["products"])
    assert len(statements)<=5, f"real catalog should batch facts and chase profiles, got {len(statements)} SQL statements"
    db.close()

def test_ranking_product_list_uses_one_bulk_chase_profile_query(monkeypatch):
    Session=session_factory()
    monkeypatch.setattr(seedmod,"SessionLocal",Session)
    seedmod.seed_verified_snapshot()
    seedmod.seed_chase_profiles()
    db=Session()
    statements=[]
    bind=db.get_bind()
    def count_query(*args): statements.append(args[2])
    event.listen(bind,"before_cursor_execute",count_query)
    items=list_products(max_price=None,db=db,include_details=False)
    event.remove(bind,"before_cursor_execute",count_query)
    assert items
    assert any(x["chase_profile"] and x["chase_ladder"] for x in items)
    assert len(statements)<=2, f"ranking list should load products and profiles in bulk, got {len(statements)} SQL statements"
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

def test_latest_box_and_pack_expansion_has_direct_links_and_profiles(monkeypatch):
    Session=session_factory()
    monkeypatch.setattr(seedmod,"SessionLocal",Session)
    seedmod.seed_verified_snapshot()
    db=Session()
    slugs={
        "cc-2026-topps-universe-wwe-value",
        "cc-2026-topps-universe-wwe-hobby",
        "cc-2026-topps-baseball-series2-value",
        "cc-2026-topps-chrome-ufc-value",
        "cc-2026-topps-stadium-club-ufc-pack",
        "cc-2026-topps-stadium-club-ufc-hobby",
        "cc-2025-26-spx-hobby-pack",
        "cc-2025-26-spx-hobby",
        "cc-2025-topps-disney-wonder-pack",
        "cc-2025-topps-chrome-deadpool-hobby",
    }
    rows=db.execute(
        select(Product, Offer)
        .join(ProductVariant, ProductVariant.product_id==Product.id)
        .join(Offer, Offer.variant_id==ProductVariant.id)
        .where(Product.slug.in_(slugs))
    ).all()
    assert {product.slug for product,_ in rows}==slugs
    assert all("/product/" in offer.url or "/products/" in offer.url for _,offer in rows)
    assert all(slug in seedmod.CHASE_PROFILES for slug in slugs)
    assert all(seedmod.CHASE_PROFILES[slug]["key_names"] for slug in slugs)
    assert all(seedmod.CHASE_PROFILES[slug]["headline_chases"] for slug in slugs)
    db.close()

def test_research_expansion_covers_thin_categories_with_exact_links(monkeypatch):
    Session=session_factory()
    monkeypatch.setattr(seedmod,"SessionLocal",Session)
    seedmod.seed_verified_snapshot()
    db=Session()
    slugs={x["slug"] for x in seedmod.REAL_RESEARCH_EXPANSION}
    rows=db.execute(
        select(Product, ProductVariant, Offer)
        .join(ProductVariant, ProductVariant.product_id==Product.id)
        .join(Offer, Offer.variant_id==ProductVariant.id)
        .where(Product.slug.in_(slugs))
    ).all()
    assert {product.slug for product,_,_ in rows}==slugs
    assert {product.category for product,_,_ in rows} >= {"Basket","NFL","Yu-Gi-Oh","Racing"}
    assert all("/product/" in offer.url for _,_,offer in rows)
    assert all(offer.stock_status=="in_stock" and not offer.is_preorder for _,_,offer in rows)
    assert all(slug in seedmod.CHASE_PROFILES for slug in slugs)
    assert all(seedmod.CHASE_PROFILES[slug]["headline_chases"] for slug in slugs)
    db.close()

def test_research_expansion_preserves_verified_format_counts():
    by_slug={x["slug"]:x for x in seedmod.REAL_RESEARCH_EXPANSION}
    assert (by_slug["cc-2025-26-topps-nba-hoops-value"]["packs"],by_slug["cc-2025-26-topps-nba-hoops-value"]["cards"])==(7,8)
    assert (by_slug["cc-2025-26-topps-nba-hoops-hanger"]["packs"],by_slug["cc-2025-26-topps-nba-hoops-hanger"]["cards"])==(1,25)
    assert (by_slug["cc-2026-topps-flagship-nfl-hobby"]["packs"],by_slug["cc-2026-topps-flagship-nfl-hobby"]["cards"])==(20,12)
    assert (by_slug["cc-2026-topps-flagship-nfl-mega"]["packs"],by_slug["cc-2026-topps-flagship-nfl-mega"]["cards"])==(12,15)
    assert (by_slug["cc-2026-topps-flagship-nfl-fat-pack"]["packs"],by_slug["cc-2026-topps-flagship-nfl-fat-pack"]["cards"])==(1,36)

def test_loose_pack_profiles_are_not_shared_display_profiles():
    pairs=(
        ("cc-star-wars-unlimited-shadows-pack","cc-star-wars-unlimited-shadows-display"),
        ("cc-star-wars-unlimited-twilight-pack","cc-star-wars-unlimited-twilight-display"),
        ("cc-pokemon-ninja-spinner-m4-pack","cc-pokemon-ninja-spinner-m4-display"),
        ("cc-pokemon-storm-emeralda-m6-pack","cc-pokemon-storm-emeralda-m6-display"),
        ("cc-one-piece-op14-jp-pack","cc-one-piece-op14-jp-display"),
        ("cc-one-piece-op16-jp-pack","cc-one-piece-op16-jp-display"),
        ("cc-2026-topps-baseball-series2-pack","cc-2026-topps-baseball-series2-hobby"),
        ("dl-mtg-marvel-superheroes-play-pack","cc-mtg-marvel-superheroes-play-display"),
        ("dl-mtg-spiderman-play-pack","dl-mtg-spiderman-play-display"),
    )
    for pack_slug,box_slug in pairs:
        pack=seedmod.CHASE_PROFILES[pack_slug]
        box=seedmod.CHASE_PROFILES[box_slug]
        assert pack is not box
        assert "löst" in pack["caveat"].lower()
        assert pack["tiers"]["everyday"]["score"] < box["tiers"]["everyday"]["score"]

def test_dragons_lair_magic_expansion_has_live_format_safe_offers(monkeypatch):
    Session=session_factory()
    monkeypatch.setattr(seedmod,"SessionLocal",Session)
    seedmod.seed_verified_snapshot()
    db=Session()
    new_slugs={
        "dl-mtg-marvel-superheroes-play-pack",
        "dl-mtg-marvel-superheroes-bundle",
        "dl-mtg-spiderman-play-pack",
        "dl-mtg-spiderman-play-display",
    }
    rows=db.execute(
        select(Product, ProductVariant, Offer, Store)
        .join(ProductVariant, ProductVariant.product_id==Product.id)
        .join(Offer, Offer.variant_id==ProductVariant.id)
        .join(Store, Store.id==Offer.store_id)
        .where(Product.slug.in_(new_slugs))
    ).all()
    assert {product.slug for product,_,_,_ in rows}==new_slugs
    assert all(store.name=="Dragons Lair" for _,_,_,store in rows)
    assert all("dragonslair.se/en/products/" in offer.url for _,_,offer,_ in rows)
    assert all(offer.stock_status=="in_stock" and not offer.is_preorder for _,_,offer,_ in rows)
    assert {(variant.packs,variant.cards_per_pack) for _,variant,_,_ in rows} >= {(1,14),(9,14),(30,14)}

    display=db.scalar(select(Product).where(Product.slug=="cc-mtg-marvel-superheroes-play-display"))
    display_offers=db.scalars(
        select(Offer).join(ProductVariant).where(ProductVariant.product_id==display.id)
    ).all()
    assert len(display_offers)==2
    assert {offer.price_sek for offer in display_offers}=={1899,2099}
    db.close()

def test_magic_play_booster_profiles_exclude_collector_only_headliners():
    slugs={
        "cc-mtg-marvel-superheroes-play-display",
        "dl-mtg-marvel-superheroes-play-pack",
        "dl-mtg-marvel-superheroes-bundle",
        "dl-mtg-spiderman-play-pack",
        "dl-mtg-spiderman-play-display",
    }
    for slug in slugs:
        profile=seedmod.CHASE_PROFILES[slug]
        headlines=" ".join(item["card"] for item in profile["headline_chases"]).lower()
        assert "cosmic foil" not in headlines
        assert "classic comic" not in headlines
        assert "gauntlet" not in headlines
        assert profile["headline_chases"]
        assert "collector booster" in profile["caveat"].lower()

def test_store_expansion_chase_profiles_use_current_verification_time(monkeypatch):
    Session=session_factory()
    monkeypatch.setattr(seedmod,"SessionLocal",Session)
    seedmod.seed_verified_snapshot()
    seedmod.seed_chase_profiles()
    db=Session()
    slugs={x["slug"] for x in seedmod.REAL_STORE_EXPANSION}
    rows=db.execute(
        select(Product.slug, ChaseProfile.verified_at)
        .join(ProductVariant, ProductVariant.product_id==Product.id)
        .join(ChaseProfile, ChaseProfile.variant_id==ProductVariant.id)
        .where(Product.slug.in_(slugs))
    ).all()
    assert {slug for slug,_ in rows}==slugs
    assert all(verified_at==seedmod.REAL_STORE_EXPANSION_OBSERVED_AT for _,verified_at in rows)
    db.close()

def test_additional_store_expansion_uses_exact_in_stock_article_links(monkeypatch):
    Session=session_factory()
    monkeypatch.setattr(seedmod,"SessionLocal",Session)
    seedmod.seed_verified_snapshot()
    seedmod.seed_chase_profiles()
    db=Session()
    slugs={x["slug"] for x in seedmod.ADDITIONAL_STORE_EXPANSION}
    rows=db.execute(
        select(Product, ProductVariant, Offer, Store)
        .join(ProductVariant, ProductVariant.product_id==Product.id)
        .join(Offer, Offer.variant_id==ProductVariant.id)
        .join(Store, Store.id==Offer.store_id)
        .where(Product.slug.in_(slugs))
    ).all()
    assert {product.slug for product,_,_,_ in rows}==slugs
    assert {store.name for _,_,_,store in rows}=={"MaxGaming","Arcade Dreams","TCGStore","SpelOchSånt","Coolcard"}
    assert all(offer.stock_status=="in_stock" and not offer.is_preorder for _,_,offer,_ in rows)
    assert all("/" in offer.url.removeprefix("https://").split("/",1)[-1] for _,_,offer,_ in rows)
    assert all(slug in seedmod.CHASE_PROFILES for slug in slugs)
    profile_dates=db.scalars(
        select(ChaseProfile.verified_at).join(ProductVariant).join(Product).where(Product.slug.in_(slugs))
    ).all()
    assert profile_dates and all(value==seedmod.ADDITIONAL_STORE_OBSERVED_AT for value in profile_dates)

    storm=db.scalar(select(Product).where(Product.slug=="cc-pokemon-storm-emeralda-m6-display"))
    storm_offers=db.execute(
        select(Offer,Store).join(Store,Store.id==Offer.store_id).join(ProductVariant).where(ProductVariant.product_id==storm.id)
    ).all()
    assert {store.name for _,store in storm_offers}=={"Coolcard","MaxGaming"}
    assert {offer.price_sek for offer,_ in storm_offers}=={1499,1549}
    db.close()

def test_new_loose_pokemon_packs_do_not_claim_published_odds():
    for slug in {"tcgs-pokemon-destined-rivals-pack","sos-pokemon-journey-together-pack"}:
        profile=seedmod.CHASE_PROFILES[slug]
        assert "löst" in profile["caveat"].lower()
        assert "kortspecifika packodds" in profile["caveat"].lower()
        assert all("garanterat" not in item["odds"].lower() for item in profile["headline_chases"])

def test_one_piece_market_scan_uses_exact_in_stock_article_links(monkeypatch):
    Session=session_factory()
    monkeypatch.setattr(seedmod,"SessionLocal",Session)
    seedmod.seed_verified_snapshot()
    seedmod.seed_chase_profiles()
    db=Session()
    slugs={x["slug"] for x in seedmod.ONE_PIECE_MARKET_EXPANSION}
    rows=db.execute(
        select(Product, ProductVariant, Offer, Store)
        .join(ProductVariant, ProductVariant.product_id==Product.id)
        .join(Offer, Offer.variant_id==ProductVariant.id)
        .join(Store, Store.id==Offer.store_id)
        .where(Product.slug.in_(slugs))
    ).all()
    assert len(slugs)==7
    assert len(rows)==10
    assert {store.name for _,_,_,store in rows}=={
        "Kantovault","AlphaSpel","Aquitaz","Bangerpack","Kortlagret"
    }
    assert all(offer.stock_status=="in_stock" and not offer.is_preorder for _,_,offer,_ in rows)
    assert all(offer.url.startswith("https://") and offer.url.count("/")>=4 for _,_,offer,_ in rows)
    assert all(slug in seedmod.CHASE_PROFILES for slug in slugs)
    profile_dates=db.scalars(
        select(ChaseProfile.verified_at).join(ProductVariant).join(Product).where(Product.slug.in_(slugs))
    ).all()
    assert profile_dates and all(value==seedmod.ONE_PIECE_MARKET_OBSERVED_AT for value in profile_dates)

    op14=[(offer,store) for product,_,offer,store in rows if product.slug=="as-one-piece-op14-en-pack"]
    assert {offer.price_sek for offer,_ in op14}=={79,89,99}
    assert min(op14,key=lambda row: row[0].price_sek)[1].name=="AlphaSpel"
    op17=[(offer,store) for product,_,offer,store in rows if product.slug=="kl-one-piece-op17-en-pack"]
    assert {offer.price_sek for offer,_ in op17}=={189,199}
    assert min(op17,key=lambda row: row[0].price_sek)[1].name=="Kortlagret"
    db.close()

def test_one_piece_market_profiles_keep_pack_and_display_claims_separate():
    pack_slugs={
        "kv-one-piece-op10-jp-pack",
        "as-one-piece-op14-en-pack",
        "aq-one-piece-op15-eb04-en-pack",
        "kl-one-piece-eb03-en-pack",
        "kl-one-piece-op17-en-pack",
    }
    for slug in pack_slugs:
        caveat=seedmod.CHASE_PROFILES[slug]["caveat"].lower()
        assert "löst" in caveat
        assert ("inte" in caveat or "ingen" in caveat) and "garanter" in caveat
    display=seedmod.CHASE_PROFILES["bp-one-piece-op17-en-display"]
    assert "4 299 kr" in display["caveat"]
    assert "inte beskrivas som verifierad ekonomisk avkastning" in display["caveat"]

def test_cardsurfer_expansion_adds_two_products_and_three_alternate_offers(monkeypatch):
    Session=session_factory()
    monkeypatch.setattr(seedmod,"SessionLocal",Session)
    seedmod.seed_verified_snapshot()
    seedmod.seed_chase_profiles()
    db=Session()
    rows=db.execute(
        select(Product, ProductVariant, Offer, Store)
        .join(ProductVariant, ProductVariant.product_id==Product.id)
        .join(Offer, Offer.variant_id==ProductVariant.id)
        .join(Store, Store.id==Offer.store_id)
        .where(Store.name=="CardSurfer")
    ).all()
    assert len(rows)==5
    assert {product.slug for product,_,_,_ in rows}=={
        "cs-2025-26-panini-prizm-basketball-blaster",
        "cs-2025-26-topps-chrome-uwcl-hobby",
        "cc-2026-topps-universe-wwe-value",
        "cc-2025-26-opc-hobby",
        "cc-2025-26-pwhl-hobby",
    }
    assert all("cardsurferbreak.com/products/" in offer.url for _,_,offer,_ in rows)
    assert all(offer.stock_status=="in_stock" and not offer.is_preorder for _,_,offer,_ in rows)
    assert all(offer.observed_at==seedmod.RETAILER_EXPANSION_OBSERVED_AT for _,_,offer,_ in rows)
    prizm=next(variant for product,variant,_,_ in rows if product.slug=="cs-2025-26-panini-prizm-basketball-blaster")
    uwcl=next(variant for product,variant,_,_ in rows if product.slug=="cs-2025-26-topps-chrome-uwcl-hobby")
    assert (prizm.packs,prizm.cards_per_pack)==(6,5)
    assert (uwcl.packs,uwcl.cards_per_pack)==(20,4)
    assert seedmod.CHASE_PROFILES["cs-2025-26-panini-prizm-basketball-blaster"]["headline_chases"]
    assert seedmod.CHASE_PROFILES["cs-2025-26-topps-chrome-uwcl-hobby"]["headline_chases"]
    db.close()

def test_cardsurfer_profiles_preserve_retail_and_family_odds_distinctions():
    prizm=seedmod.CHASE_PROFILES["cs-2025-26-panini-prizm-basketball-blaster"]
    uwcl=seedmod.CHASE_PROFILES["cs-2025-26-topps-chrome-uwcl-hobby"]
    assert "hobbyboxens garantier gäller inte" in prizm["caveat"].lower()
    assert "inte cooper flagg" in prizm["caveat"].lower()
    assert "2 autografer" in uwcl["tiers"]["everyday"]["items"]
    assert "inte en särskild spelare" in uwcl["caveat"].lower()
    assert any("1:650,160" in item["odds"] for item in uwcl["headline_chases"])

def test_retail_and_loose_pack_profiles_do_not_claim_hobby_box_guarantees():
    retail_slugs={
        "cc-2026-topps-universe-wwe-value",
        "cc-2026-topps-baseball-series2-value",
        "cc-2026-topps-chrome-ufc-value",
    }
    for slug in retail_slugs:
        caveat=seedmod.CHASE_PROFILES[slug]["caveat"].lower()
        assert "inte" in caveat and ("garanti" in caveat or "garanter" in caveat)
    for slug in ("cc-2026-topps-stadium-club-ufc-pack","cc-2025-26-spx-hobby-pack","cc-2025-topps-disney-wonder-pack"):
        assert "löst pack" in seedmod.CHASE_PROFILES[slug]["caveat"].lower()

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
    assert "Matthew Schaefer #275" in mvp["key_names"]
    assert any("1:10" in x["odds"] for x in mvp["headline_chases"])
    assert not any("Autograf" in x["card"] for x in mvp["headline_chases"])
    assert "Mega Zygarde ex" in pokemon["key_names"]
    assert any("#124" in x["card"] for x in pokemon["headline_chases"])

def test_researched_hockey_products_have_named_chases_and_odds():
    slugs=(
        "cc-2025-26-mvp-hobby",
        "cc-2025-26-pwhl-hobby",
        "cc-pack-2025-26-pwhl-hobby",
        "cc-2025-26-skybox-metal-hobby",
        "cc-pack-2025-26-skybox-hobby",
        "cc-2025-26-opc-platinum-retail-blaster",
        "cc-2025-26-extended-hobby",
        "cc-pack-2025-26-parkhurst-hobby",
        "cc-2025-26-pwhl-retail-blaster",
        "cc-2025-26-fleer-ultra-pwhl-hobby",
        "cc-2025-26-sp-authentic-hobby",
        "cc-2025-26-ultimate-hobby",
        "cc-2025-26-premier-hobby",
        "cc-2025-26-rangers-box-set",
    )
    for slug in slugs:
        profile=seedmod.CHASE_PROFILES[slug]
        assert profile["key_names"]
        assert profile["headline_chases"]
        assert all(x.get("card") and x.get("odds") for x in profile["headline_chases"])

def test_new_checklist_profiles_distinguish_family_odds_from_player_odds():
    parkhurst=seedmod.CHASE_PROFILES["cc-pack-2025-26-parkhurst-hobby"]
    spa=seedmod.CHASE_PROFILES["cc-2025-26-sp-authentic-hobby"]
    rangers=seedmod.CHASE_PROFILES["cc-2025-26-rangers-box-set"]
    assert "Matthew Schaefer #211" in parkhurst["key_names"]
    assert any("1:40" in x["odds"] and "Autograph" in x["card"] for x in parkhurst["headline_chases"])
    assert "2 autografer per box i snitt" in spa["tiers"]["everyday"]["items"]
    assert any("1:10 boxar" in x["odds"] for x in rangers["headline_chases"])
    assert "inte för en särskild spelare" in rangers["caveat"]

def test_new_products_have_searchable_named_cards():
    expected={
        "cc-pack-2025-26-parkhurst-hobby":"Ivan Demidov",
        "cc-2025-26-pwhl-retail-blaster":"Casey O'Brien",
        "cc-2025-26-fleer-ultra-pwhl-hobby":"Natalie Spooner",
        "cc-2025-26-sp-authentic-hobby":"Matthew Schaefer",
        "cc-2025-26-ultimate-hobby":"Michael Misa",
        "cc-2025-26-premier-hobby":"Ivan Demidov",
        "cc-2025-26-rangers-box-set":"Henrik Lundqvist",
    }
    for slug,player in expected.items():
        assert any(x["slug"]==slug and x["player"]==player for x in seedmod.CHASE_CARD_DB)

def test_researched_football_products_have_named_chases_and_sources():
    slugs=(
        "cc-2025-26-pitch-kings-la-liga",
        "cc-2025-26-panini-prizm-fifa-choice",
        "cc-2025-26-panini-prizm-fifa-retail",
        "cc-2026-futera-world-football-fx3",
        "cc-2025-26-topps-bayern-lineage",
        "cc-2026-topps-mls-chrome-value",
        "cc-2026-topps-chrome-premier-league-hobby",
        "cc-2026-topps-finest-premier-league-wave2",
        "cc-2025-26-topps-chrome-arsenal-hobby",
        "cc-2026-topps-argentina-team-set",
        "cc-2025-26-topps-real-madrid-team-set",
        "cc-2025-26-topps-ucc-flagship-hanger",
    )
    for slug in slugs:
        profile=seedmod.CHASE_PROFILES[slug]
        assert profile["key_names"]
        assert len(profile["headline_chases"]) >= 5
        assert profile["source_url"].startswith("https://")
        assert all(x.get("card") and x.get("tier") and x.get("odds") for x in profile["headline_chases"])

def test_football_retail_profiles_only_assert_retail_specific_odds():
    mls=seedmod.CHASE_PROFILES["cc-2026-topps-mls-chrome-value"]
    ucc=seedmod.CHASE_PROFILES["cc-2025-26-topps-ucc-flagship-hanger"]
    prizm=seedmod.CHASE_PROFILES["cc-2025-26-panini-prizm-fifa-retail"]
    assert any("1:342 value-pack" in x["odds"] for x in mls["headline_chases"])
    assert any("1:112 hanger-pack" in x["odds"] for x in ucc["headline_chases"])
    assert any("1 Red Pulsar Autograph per 2 retailboxar" in x["odds"] for x in prizm["headline_chases"])
    assert "Hobbyexklusiva" in mls["caveat"]
    assert "35-korts hanger-pack" in ucc["caveat"]
    assert "Choice- och hobbyexklusiva" in prizm["caveat"]


def test_ucc_hanger_uses_exact_product_buy_url():
    product = next(
        row for row in seedmod.REAL_SNAPSHOT
        if row["slug"] == "cc-2025-26-topps-ucc-flagship-hanger"
    )
    assert product["store_name"] == "Cardland"
    assert product["price"] == 178
    assert product["buy_url"] == "https://www.cardland.se/fotboll/2025-26-topps-ucc-flagship-hanger-box"


def test_every_available_snapshot_product_resolves_to_an_article_url():
    from app.services.purchase_links import is_direct_purchase_url

    legacy_urls = {
        "cc-one-piece-op13-jp-display": "https://www.coolcard.se/en/product/one-piece-card-game-booster-display-24-boosters-carrying-on-his-will-op-13-japanese",
        "cc-pokemon-mega-zygarde-premium": "https://www.coolcard.se/en/product/pokemon-mega-zygarde-ex-premium-collection-2",
        "cc-pokemon-shrouded-fable-kingambit": "https://www.coolcard.se/product/pokemon-sv6-5-shrouded-fable-kingambit-illustration-collection",
        "cc-pokemon-go-etb": "https://www.coolcard.se/en/product/pokemon-pokemon-go-elite-trainer-box-2",
        "cc-pokemon-paradox-rift-18": "https://www.coolcard.se/en/product/pokmon-sv4-paradox-rift-small-booster-box-contains-18-boosters",
    }
    for product in seedmod.REAL_SNAPSHOT:
        if product["slug"] in seedmod.UNAVAILABLE_PURCHASE_SLUGS:
            continue
        url = (
            product.get("buy_url")
            or seedmod.DIRECT_BUY_URLS.get(product["slug"])
            or legacy_urls.get(product["slug"])
        )
        assert is_direct_purchase_url(url), product["slug"]

def test_football_search_cards_include_rookies_and_star_autographs():
    expected={
        "cc-2025-26-pitch-kings-la-liga":("Karl Etta Eyong",True),
        "cc-2025-26-panini-prizm-fifa-choice":("Lionel Messi",False),
        "cc-2025-26-panini-prizm-fifa-retail":("Rio Ngumoha",True),
        "cc-2026-futera-world-football-fx3":("Lionel Messi / Cristiano Ronaldo",False),
        "cc-2025-26-topps-bayern-lineage":("Lennart Karl",True),
        "cc-2026-topps-chrome-premier-league-hobby":("Max Dowman",True),
        "cc-2026-topps-finest-premier-league-wave2":("Estêvão Willian",True),
        "cc-2025-26-topps-chrome-arsenal-hobby":("Bukayo Saka",False),
        "cc-2026-topps-argentina-team-set":("Lionel Messi",False),
        "cc-2025-26-topps-real-madrid-team-set":("Franco Mastantuono",True),
        "cc-2025-26-topps-ucc-flagship-hanger":("Rio Ngumoha",True),
    }
    for slug,(player,rookie) in expected.items():
        assert any(x["slug"]==slug and x["player"]==player and x["rookie"] is rookie for x in seedmod.CHASE_CARD_DB)

def test_prizm_choice_and_retail_keep_format_specific_guarantees_separate():
    choice=seedmod.CHASE_PROFILES["cc-2025-26-panini-prizm-fifa-choice"]
    retail=seedmod.CHASE_PROFILES["cc-2025-26-panini-prizm-fifa-retail"]
    assert "1 autograf per box" in choice["tiers"]["everyday"]["items"]
    assert "3 numrerade Choice Prizms" in choice["tiers"]["everyday"]["items"]
    assert not any("Choice" in item for item in retail["tiers"]["everyday"]["items"])
    assert any("Red Pulsar Autograph 1:2 boxar" in item for item in retail["tiers"]["big"]["items"])

def test_futera_and_bayern_do_not_turn_checklist_presence_into_fake_odds():
    futera=seedmod.CHASE_PROFILES["cc-2026-futera-world-football-fx3"]
    bayern=seedmod.CHASE_PROFILES["cc-2025-26-topps-bayern-lineage"]
    assert "autograf är alltså inte garanterad" in futera["caveat"]
    assert any(x["card"].startswith("Yamal OFOA01") and x["odds"]=="1/1" for x in futera["headline_chases"])
    assert "En relic kan vara en av de tre träffarna" in bayern["caveat"]
    assert any("Lennart Karl" in x["card"] for x in bayern["headline_chases"])

def test_pokemon_one_piece_marvel_and_disney_have_named_chases():
    expected={
        "cc-pokemon-paradox-rift-18":"Roaring Moon ex #251",
        "cc-pokemon-temporal-forces-18":"Raging Bolt ex #208",
        "cc-pokemon-shrouded-fable-kingambit":"Cassiopeia #94",
        "cc-pokemon-go-etb":"Mewtwo VSTAR #86",
        "cc-pokemon-white-flare-jp-display":"Reshiram ex #174",
        "cc-one-piece-op13-jp-display":"Gol.D.Roger OP09-118",
        "cc-2025-topps-marvel-studios-chrome-hobby":"Hugh Jackman Wolverine Autograph",
        "cc-2026-topps-disney-chrome-value":"Miley Cyrus Hannah Montana Autograph",
    }
    for slug,name in expected.items():
        profile=seedmod.CHASE_PROFILES[slug]
        assert name in profile["key_names"]
        assert len(profile["headline_chases"]) >= 5

def test_unpublished_odds_do_not_raise_evidence_grade():
    from app.services.chase_content import has_actionable_odds
    pokemon=seedmod.CHASE_PROFILES["cc-pokemon-paradox-rift-18"]
    one_piece=seedmod.CHASE_PROFILES["cc-one-piece-op13-jp-display"]
    marvel=seedmod.CHASE_PROFILES["cc-2025-topps-marvel-studios-chrome-hobby"]
    disney=seedmod.CHASE_PROFILES["cc-2026-topps-disney-chrome-value"]
    assert has_actionable_odds(pokemon) is False
    assert has_actionable_odds(one_piece) is False
    assert has_actionable_odds(marvel) is True
    assert has_actionable_odds(disney) is True

def test_facsimile_signatures_are_never_described_as_authentic():
    disney=seedmod.CHASE_PROFILES["cc-2026-topps-disney-chrome-value"]
    facsimiles=[x for x in disney["headline_chases"] if "Facsimile" in x["card"]]
    assert facsimiles
    assert all("tryckta" in x["why"] or "tryckt" in x["why"] for x in facsimiles)
    assert "inte förväxlas med Authentic Autographs" in disney["caveat"]

def test_new_entertainment_cards_are_searchable():
    expected={
        "cc-one-piece-op13-jp-display":"Gol.D.Roger",
        "cc-2025-topps-marvel-studios-chrome-hobby":"Hugh Jackman / Ryan Reynolds",
        "cc-2026-topps-disney-chrome-value":"Miley Cyrus",
        "cc-pokemon-white-flare-jp-display":"Reshiram ex",
    }
    for slug,player in expected.items():
        assert any(x["slug"]==slug and x["player"]==player for x in seedmod.CHASE_CARD_DB)

def test_real_catalog_can_filter_to_loose_packs(monkeypatch):
    Session=session_factory()
    monkeypatch.setattr(seedmod,"SessionLocal",Session)
    seedmod.seed_verified_snapshot()
    seedmod.seed_chase_profiles()
    db=Session()
    result=real_catalog(category="Hockey",budget=250,format="single pack",limit=60,db=db)
    assert result["products"]
    assert all(x["format"]=="single pack" for x in result["products"])
    assert all(x["price"]<=250 for x in result["products"])
    db.close()

def test_cross_category_expansion_has_direct_buy_links_and_rankable_chases():
    rows = {row["slug"]: row for row in seedmod.REAL_CROSS_CATEGORY_EXPANSION}
    assert {"Basket", "Baseboll", "NFL", "WWE", "UFC", "Golf", "Racing", "Star Wars"}.issubset(
        {row["category"] for row in rows.values()}
    )
    assert all(row["buy_url"].startswith("https://www.coolcard.se/") for row in rows.values())
    for slug in (
        "cc-2025-26-topps-chrome-update-basketball-pack",
        "cc-2025-26-topps-nba-hoops-hobby-pack",
        "cc-2026-topps-baseball-series2-pack",
        "cc-2026-topps-baseball-series2-hobby",
        "cc-2026-topps-chrome-baseball-value",
        "cc-2026-topps-flagship-nfl-pack",
        "cc-2026-topps-universe-wwe-pack",
        "cc-2026-fleer-ultra-golf-pack",
        "cc-star-wars-unlimited-shadows-pack",
        "cc-star-wars-unlimited-shadows-display",
        "cc-star-wars-unlimited-twilight-pack",
        "cc-star-wars-unlimited-twilight-display",
    ):
        profile = seedmod.CHASE_PROFILES[slug]
        assert profile["key_names"]
        assert profile["headline_chases"]
        assert profile["source_url"].startswith("https://")
