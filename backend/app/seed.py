import json
from datetime import datetime
from sqlalchemy import select
from .database import SessionLocal
from .models import BoxAnalysis, Offer, PriceHistory, Product, ProductVariant, Store, ProductFact, ChaseCard, VariantChaseCard, ChaseProfile

SEED = [
    ("2025-26 Upper Deck Series 1", "Hockey", "Upper Deck", "2025-26", "Series 1", "Hobby Box", 799, [560,780,86,80,84,48,92,78,82,72,"Medel-hög"]),
    ("Topps Chrome UEFA 2025", "Fotboll", "Topps", "2025", "Chrome UEFA", "Hobby Box", 1499, [850,1280,88,71,90,42,79,84,88,68,"Hög"]),
    ("Pokémon Destined Rivals", "Pokémon", "The Pokémon Company", "2025", "Destined Rivals", "Booster Bundle", 429, [245,410,82,75,86,55,None,90,93,76,"Medel"]),
]

REAL_STORES = [
    dict(name="Terratide", homepage_url="https://terratide.se/", source_url="https://terratide.se/sv-se/samlarkort", collection_method="manual", adapter_key="manual", policy_status="review_required"),
    dict(name="TCG Deals Sverige", homepage_url="https://tcgdeals.se/", source_url="https://tcgdeals.se/", collection_method="manual", adapter_key="manual", policy_status="review_required"),
    dict(name="Coolcard", homepage_url="https://www.coolcard.se/", source_url="https://www.coolcard.se/", collection_method="public_html", adapter_key="public_html_catalog", policy_status="review_required"),
    dict(name="Samlarhobby", homepage_url="https://www.samlarhobby.se/", source_url="https://www.samlarhobby.se/", collection_method="public_html", adapter_key="public_html_catalog", policy_status="review_required"),
    dict(name="Bangerpack", homepage_url="https://bangerpack.se/", source_url="https://bangerpack.se/", collection_method="public_html", adapter_key="public_html_catalog", policy_status="review_required"),
    dict(name="Kortlagret", homepage_url="https://kortlagret.se/", source_url="https://kortlagret.se/", collection_method="public_html", adapter_key="public_html_catalog", policy_status="review_required"),
    dict(name="Pardon My Kicks", homepage_url=None, source_url=None, collection_method="manual", adapter_key="manual", policy_status="review_required"),
    dict(name="MajkiPoké", homepage_url=None, source_url=None, collection_method="manual", adapter_key="manual", policy_status="review_required"),
    dict(name="TCGPoke", homepage_url="https://www.tcgpoke.se/", source_url="https://www.tcgpoke.se/", collection_method="manual", adapter_key="manual", policy_status="review_required"),
    dict(name="Hatstore", homepage_url="https://hatstore.se/", source_url="https://hatstore.se/samlarkort/", collection_method="manual", adapter_key="manual", policy_status="review_required"),
    dict(name="Sunshine", homepage_url="https://sunshine.se/", source_url="https://sunshine.se/", collection_method="manual", adapter_key="manual", policy_status="review_required"),
    dict(name="TCGbutik", homepage_url="https://tcgbutik.se/", source_url="https://tcgbutik.se/", collection_method="manual", adapter_key="manual", policy_status="review_required"),
    dict(name="TCGStore", homepage_url="https://tcgstore.se/", source_url="https://tcgstore.se/", collection_method="manual", adapter_key="manual", policy_status="review_required"),
    dict(name="Hobbykort", homepage_url="https://hobbykort.se/", source_url="https://hobbykort.se/", collection_method="manual", adapter_key="manual", policy_status="review_required"),
    dict(name="Aquitaz", homepage_url="https://aquitaz.se/", source_url="https://aquitaz.se/", collection_method="manual", adapter_key="manual", policy_status="review_required"),
    dict(name="AlphaSpel", homepage_url=None, source_url=None, collection_method="manual", adapter_key="manual", policy_status="review_required"),
    dict(name="Dragons Lair", homepage_url=None, source_url=None, collection_method="manual", adapter_key="manual", policy_status="review_required"),
    dict(name="Röda Goblinen", homepage_url=None, source_url=None, collection_method="manual", adapter_key="manual", policy_status="review_required"),
    dict(name="ManaTorsk", homepage_url=None, source_url=None, collection_method="manual", adapter_key="manual", policy_status="review_required"),
    dict(name="Speltrollet", homepage_url=None, source_url=None, collection_method="manual", adapter_key="manual", policy_status="review_required"),
    dict(name="Webhallen", homepage_url=None, source_url=None, collection_method="manual", adapter_key="manual", policy_status="review_required"),
    dict(name="RA Card", homepage_url=None, source_url=None, collection_method="manual", adapter_key="manual", policy_status="review_required"),
    dict(name="SpelOchSånt", homepage_url=None, source_url=None, collection_method="manual", adapter_key="manual", policy_status="review_required"),
    dict(name="NordicSportsCards", homepage_url=None, source_url=None, collection_method="manual", adapter_key="manual", policy_status="review_required"),
    dict(name="DrakenDavids", homepage_url=None, source_url=None, collection_method="manual", adapter_key="manual", policy_status="review_required"),
    dict(name="Poketalk", homepage_url=None, source_url=None, collection_method="manual", adapter_key="manual", policy_status="review_required"),
    dict(name="Samlartorget", homepage_url=None, source_url=None, collection_method="manual", adapter_key="manual", policy_status="review_required"),
    dict(name="EllieCollectables", homepage_url="https://elliecollectables.se/", source_url="https://elliecollectables.se/", collection_method="manual", adapter_key="manual", policy_status="review_required"),
]



REAL_SNAPSHOT_OBSERVED_AT = datetime(2026, 9, 12, 19, 30, 0)

# Curated, source-verifiable starter snapshot. These are NOT generated scores.
# They exist so a fresh local BoxFinder install has real Swedish sealed-card data to browse
# while live feed integrations are still being onboarded.
REAL_SNAPSHOT = [
    dict(slug="cc-2025-26-opc-retail-blaster", name="2025-26 O-Pee-Chee Hockey Retail Blaster", category="Hockey", manufacturer="Upper Deck", year="2025-26", series="O-Pee-Chee", fmt="blaster", sku="UD59125", price=269, packs=9, cards=8, stock="in_stock"),
    dict(slug="cc-2025-26-extended-retail-blaster", name="2025-26 Upper Deck Extended Series Retail Blaster", category="Hockey", manufacturer="Upper Deck", year="2025-26", series="Extended Series", fmt="blaster", sku="UD09542", price=299, packs=4, cards=12, stock="in_stock"),
    dict(slug="cc-2025-26-opc-platinum-retail-blaster", name="2025-26 Upper Deck O-Pee-Chee Platinum Retail Blaster", category="Hockey", manufacturer="Upper Deck", year="2025-26", series="O-Pee-Chee Platinum", fmt="blaster", sku="UD47423", price=329, packs=6, cards=4, stock="in_stock"),
    dict(slug="cc-2025-26-pwhl-retail-blaster", name="2025-26 Upper Deck PWHL Retail Blaster", category="Hockey", manufacturer="Upper Deck", year="2025-26", series="PWHL", fmt="blaster", sku="UD00390", price=279, packs=5, cards=6, stock="in_stock"),
    dict(slug="cc-2025-26-series2-retail-blaster", name="2025-26 Upper Deck Series 2 Retail Blaster", category="Hockey", manufacturer="Upper Deck", year="2025-26", series="Series 2", fmt="blaster", sku="UD43828", price=379, packs=4, cards=12, stock="in_stock"),
    dict(slug="cc-2025-26-rangers-box-set", name="2025-26 Upper Deck New York Rangers Centennial Box Set", category="Hockey", manufacturer="Upper Deck", year="2025-26", series="Rangers Centennial", fmt="box set", sku="UD05828", price=529, packs=1, cards=105, stock="in_stock"),
    dict(slug="cc-2025-26-opc-hobby", name="2025-26 Upper Deck O-Pee-Chee Hobby", category="Hockey", manufacturer="Upper Deck", year="2025-26", series="O-Pee-Chee", fmt="hobby box", sku="UD59119", price=799, packs=18, cards=10, stock="in_stock",
         facts=["Minst 3 numrerade base/retro-paralleller eller printing plates per box i snitt", "4 O-Pee-Chee Playing Cards per box i snitt", "3 O-Pee-Chee Premier per box i snitt", "Minst 1 rare chase card per box i snitt"]),
    dict(slug="cc-2025-26-pwhl-hobby", name="2025-26 Upper Deck PWHL Hobby", category="Hockey", manufacturer="Upper Deck", year="2025-26", series="PWHL", fmt="hobby box", sku="UD00384", price=1095, packs=12, cards=6, stock="in_stock"),
    dict(slug="cc-2025-26-clear-cut-hobby", name="2025-26 Upper Deck Clear Cut Hobby", category="Hockey", manufacturer="Upper Deck", year="2025-26", series="Clear Cut", fmt="hobby box", sku="UD09547", price=1195, packs=1, cards=1, stock="in_stock",
         facts=["1 hard-signed autograph card per box, eller redemption för autograph card", "Outburst paralleller /25, High Gloss /10 och Gold Outburst 1/1 finns i produkten"]),
    dict(slug="cc-2025-26-mvp-hobby", name="2025-26 Upper Deck MVP Hobby Silver Collection", category="Hockey", manufacturer="Upper Deck", year="2025-26", series="MVP", fmt="hobby box", sku="UD01312", price=1295, packs=20, cards=8, stock="in_stock"),
    dict(slug="cc-2025-26-series1-hobby", name="2025-26 Upper Deck Series 1 Hobby", category="Hockey", manufacturer="Upper Deck", year="2025-26", series="Series 1", fmt="hobby box", sku="UD03670", price=1395, packs=12, cards=12, stock="in_stock",
         facts=["6 Young Guns per box i snitt", "1 Outburst Silver parallel per box i snitt"]),
    dict(slug="cc-2025-26-skybox-metal-hobby", name="2025-26 Upper Deck NHL Skybox Metal Universe Hobby", category="Hockey", manufacturer="Upper Deck", year="2025-26", series="Skybox Metal Universe", fmt="hobby box", sku="UD20019", price=1795, packs=15, cards=6, stock="in_stock"),
    dict(slug="cc-2025-26-extended-hobby", name="2025-26 Upper Deck Extended Series Hobby", category="Hockey", manufacturer="Upper Deck", year="2025-26", series="Extended Series", fmt="hobby box", sku="UD09536", price=1795, packs=12, cards=12, stock="in_stock"),
    dict(slug="cc-2025-26-series2-hobby", name="2025-26 Upper Deck Series 2 Hobby", category="Hockey", manufacturer="Upper Deck", year="2025-26", series="Series 2", fmt="hobby box", sku="UD43816", price=2195, packs=12, cards=12, stock="in_stock",
         facts=["6 Young Guns per box i snitt", "4 UD Canvas/Canvas Young Guns per box i snitt", "1 Outburst Silver parallel per box i snitt", "1 Blue Dazzlers per box i snitt", "1 numbered card, ratio short print eller printing plate per box i snitt"]),
    dict(slug="cc-2025-26-fleer-ultra-pwhl-hobby", name="2025-26 Upper Deck Fleer Ultra PWHL Hobby", category="Hockey", manufacturer="Upper Deck", year="2025-26", series="Fleer Ultra PWHL", fmt="hobby box", sku="UD13305", price=2295, packs=15, cards=8, stock="in_stock"),
    dict(slug="cc-2025-26-sp-authentic-hobby", name="2025-26 Upper Deck SP Authentic Hobby", category="Hockey", manufacturer="Upper Deck", year="2025-26", series="SP Authentic", fmt="hobby box", sku="UD43813", price=2695, packs=10, cards=9, stock="in_stock"),
    dict(slug="cc-2025-26-ultimate-hobby", name="2025-26 Upper Deck Ultimate Hobby", category="Hockey", manufacturer="Upper Deck", year="2025-26", series="Ultimate", fmt="hobby box", sku="UD20012", price=2795, packs=1, cards=4, stock="in_stock"),
    dict(slug="cc-2025-26-premier-hobby", name="2025-26 Upper Deck Premier Hobby", category="Hockey", manufacturer="Upper Deck", year="2025-26", series="Premier", fmt="hobby box", sku="UD20017", price=3995, packs=1, cards=6, stock="in_stock"),
]

REAL_PACK_SNAPSHOT = [
    dict(slug="cc-pack-2025-26-opc-hobby", name="2025-26 Upper Deck O-Pee-Chee Hobby Pack", category="Hockey", manufacturer="Upper Deck", year="2025-26", series="O-Pee-Chee", fmt="single pack", sku="UD59121", price=49, packs=1, cards=10),
    dict(slug="cc-pack-2025-26-mvp-hobby", name="2025-26 Upper Deck MVP Hobby Silver Collection Pack", category="Hockey", manufacturer="Upper Deck", year="2025-26", series="MVP", fmt="single pack", sku="UD01313", price=69, packs=1, cards=8),
    dict(slug="cc-pack-2025-26-pwhl-hobby", name="2025-26 Upper Deck PWHL Hobby Pack", category="Hockey", manufacturer="Upper Deck", year="2025-26", series="PWHL", fmt="single pack", sku="UD00385", price=99, packs=1, cards=6),
    dict(slug="cc-pack-2025-26-parkhurst-hobby", name="2025-26 Upper Deck Parkhurst Hobby Pack", category="Hockey", manufacturer="Upper Deck", year="2025-26", series="Parkhurst", fmt="single pack", sku="UD25692_1", price=119, packs=1, cards=8),
    dict(slug="cc-pack-2025-26-skybox-hobby", name="2025-26 Upper Deck Skybox Metal Universe Hobby Pack", category="Hockey", manufacturer="Upper Deck", year="2025-26", series="Skybox Metal Universe", fmt="single pack", sku="UD20055", price=129, packs=1, cards=6),
    dict(slug="cc-pack-2025-26-series1-hobby", name="2025-26 Upper Deck Series 1 Hobby Pack", category="Hockey", manufacturer="Upper Deck", year="2025-26", series="Series 1", fmt="single pack", sku="UD03671", price=149, packs=1, cards=12),
]


REAL_FOOTBALL_SNAPSHOT = [
    dict(slug="cc-2025-26-pitch-kings-la-liga", name="2025-26 Panini Pitch Kings La Liga International Hobby", category="Fotboll", manufacturer="Panini", year="2025-26", series="Pitch Kings La Liga", fmt="hobby box", sku="25PASPK-INT", price=1595, packs=1, cards=10, stock="in_stock",
         facts=["10 kort per box"]),
    dict(slug="cc-2026-topps-mls-chrome-value", name="2026 Topps Major League Soccer Chrome Value Box", category="Fotboll", manufacturer="Topps", year="2026", series="MLS Chrome", fmt="value box", sku="FGC007106", price=379, packs=7, cards=4, stock="in_stock",
         facts=["7 pack per box", "4 kort per pack"]),
    dict(slug="cc-2025-26-panini-prizm-fifa-choice", name="2025-26 Panini Prizm FIFA Soccer Choice", category="Fotboll", manufacturer="Panini", year="2025-26", series="Prizm FIFA", fmt="choice box", sku="PAN7891", price=2799, packs=1, cards=8, stock="in_stock",
         facts=["8 kort per box", "1 autograf per box i snitt"]),
    dict(slug="cc-2026-futera-world-football-fx3", name="2026 Futera World Football FX Series 3", category="Fotboll", manufacturer="Futera", year="2026", series="World Football FX Series 3", fmt="hobby box", sku="FUT-FXs3-10", price=1499, packs=10, cards=5, stock="in_stock",
         facts=["10 pack per box", "upp till 5 kort per pack"]),
    dict(slug="cc-2026-topps-argentina-team-set", name="2026 Topps Argentina Team Set", category="Fotboll", manufacturer="Topps", year="2026", series="Argentina Team Set", fmt="team set box", sku="FGC007078", price=999, packs=6, cards=5, stock="in_stock",
         facts=["6 pack per box", "5 kort per pack"]),
    dict(slug="cc-2026-topps-chrome-premier-league-hobby", name="2026 Topps Chrome Premier League Soccer Hobby", category="Fotboll", manufacturer="Topps", year="2026", series="Chrome Premier League", fmt="hobby box", sku="FGC007019-20", price=3699, packs=20, cards=4, stock="in_stock",
         facts=["20 pack per box", "4 kort per pack"]),
    dict(slug="cc-2026-topps-finest-premier-league-wave2", name="2026 Topps Finest Premier League Soccer Hobby Wave 2", category="Fotboll", manufacturer="Topps", year="2026", series="Finest Premier League", fmt="hobby box", sku="FS0006415_06", price=5999, packs=6, cards=10, stock="in_stock",
         facts=["6 pack per box", "10 kort per pack"]),
    dict(slug="cc-2025-26-panini-prizm-fifa-retail", name="2025-26 Panini Prizm FIFA Soccer Retail", category="Fotboll", manufacturer="Panini", year="2025-26", series="Prizm FIFA", fmt="retail box", sku="PAN7900-24", price=1299, packs=24, cards=4, stock="in_stock",
         facts=["24 pack per box", "4 kort per pack"]),
    dict(slug="cc-2025-26-topps-chrome-arsenal-hobby", name="2025-26 Topps Chrome Arsenal Soccer Hobby", category="Fotboll", manufacturer="Topps", year="2025-26", series="Chrome Arsenal", fmt="hobby box", sku="FS0006485-16", price=4499, packs=16, cards=4, stock="in_stock",
         facts=["16 pack per box", "4 kort per pack"]),
    dict(slug="cc-2025-26-topps-bayern-lineage", name="2025-26 Topps FC Bayern München Lineage Hobby", category="Fotboll", manufacturer="Topps", year="2025-26", series="FC Bayern Lineage", fmt="hobby box", sku="FS0006413", price=6499, packs=1, cards=7, stock="in_stock",
         facts=["1 pack per box", "7 kort per pack", "3 encased Autograph, Autograph Relics eller Relics per box"]),
    dict(slug="cc-2025-26-topps-real-madrid-team-set", name="2025-26 Topps Real Madrid Team Set", category="Fotboll", manufacturer="Topps", year="2025-26", series="Real Madrid Team Set", fmt="team set box", sku="FS0006419", price=1299, packs=6, cards=5, stock="in_stock",
         facts=["6 pack per box", "5 kort per pack"]),
    dict(slug="cc-2025-26-topps-ucc-flagship-hanger", name="2025-26 Topps UCC Flagship Hanger Box", category="Fotboll", manufacturer="Topps", year="2025-26", series="UCC Flagship", fmt="hanger", sku="FGC007008", price=239, packs=1, cards=35, stock="in_stock",
         facts=["35 kort per box", "2 Diamante Foil parallels per box", "2 insert-kort per box"]),
]

REAL_POKEMON_SNAPSHOT = [
    dict(slug="cc-pokemon-mega-zygarde-premium", name="Pokémon Mega Zygarde ex Premium Collection", category="Pokémon", manufacturer="The Pokémon Company", year="2026", series="Mega Evolution", fmt="collection box", sku="POK10359-101", price=749, packs=8, cards=None, stock="in_stock",
         facts=["8 boosterpaket", "stort promo-kort", "vanligt promo-kort"]),
    dict(slug="cc-pokemon-shrouded-fable-kingambit", name="Pokémon Shrouded Fable Illustration Collection: Kingambit", category="Pokémon", manufacturer="The Pokémon Company", year="2024", series="Shrouded Fable", fmt="collection box", sku="POK85858", price=579, packs=4, cards=None, stock="in_stock",
         facts=["4 boosterpaket", "3 promo-kort"]),
    dict(slug="cc-pokemon-paradox-rift-18", name="Pokémon Paradox Rift Small Booster Box", category="Pokémon", manufacturer="The Pokémon Company", year="2023", series="Paradox Rift", fmt="booster box", sku="POK85399-18", price=1899, packs=18, cards=None, stock="in_stock",
         facts=["18 boosterpaket i förseglad display"]),
    dict(slug="cc-pokemon-temporal-forces-18", name="Pokémon Temporal Forces Small Booster Box", category="Pokémon", manufacturer="The Pokémon Company", year="2024", series="Temporal Forces", fmt="booster box", sku="POK85639-18", price=1899, packs=18, cards=None, stock="in_stock",
         facts=["18 boosterpaket i förseglad display"]),
    dict(slug="cc-pokemon-go-etb", name="Pokémon GO Elite Trainer Box", category="Pokémon", manufacturer="The Pokémon Company", year="2022", series="Pokémon GO", fmt="elite trainer box", sku="POK85050", price=1499, packs=None, cards=None, stock="in_stock",
         facts=["Elite Trainer Box"]),
    dict(slug="cc-pokemon-white-flare-jp-display", name="Pokémon White Flare sv11W Booster Display Japanese", category="Pokémon", manufacturer="The Pokémon Company", year="2025", series="White Flare", fmt="booster box", sku="POKsv11W-30", price=2299, packs=20, cards=7, stock="in_stock",
         facts=["20 pack per box", "7 kort per pack", "japanska kort"]),
]

REAL_SNAPSHOT += REAL_FOOTBALL_SNAPSHOT + REAL_POKEMON_SNAPSHOT

REAL_SNAPSHOT += REAL_PACK_SNAPSHOT

def seed_verified_snapshot():
    db = SessionLocal()
    try:
        coolcard = db.scalar(select(Store).where(Store.name == "Coolcard"))
        if coolcard is None:
            coolcard = Store(
                name="Coolcard", country="SE", active=True,
                homepage_url="https://www.coolcard.se/",
                source_url="https://www.coolcard.se/category/boxar-nhl-2025-26",
                collection_method="manual", adapter_key="manual",
                policy_status="review_required", min_interval_seconds=120,
            )
            db.add(coolcard); db.flush()

        category_url="https://www.coolcard.se/category/boxar-nhl-2025-26"
        pack_url="https://www.coolcard.se/category/paket-nhl-2025-26"
        football_url="https://www.coolcard.se/category/boxar-paket-fotboll-endast-hobby"
        pokemon_url="https://www.coolcard.se/category/pokmon"
        fact_urls={
            "cc-2025-26-series2-hobby":"https://www.coolcard.se/product/hel-box-12-paket-2025-26-upper-deck-series-2-hobby",
            "cc-2025-26-clear-cut-hobby":"https://www.coolcard.se/product/hel-box-2025-26-upper-deck-clear-cut-hobby",
            "cc-2025-26-opc-hobby":"https://www.coolcard.se/en/product/1-pack-2025-26-upper-deck-o-pee-chee-hobby",
            "cc-2025-26-series1-hobby":"https://www.coolcard.se/category/boxar-nhl-2025-26",
        }

        for row in REAL_SNAPSHOT:
            product = db.scalar(select(Product).where(Product.slug == row["slug"]))
            if product is None:
                product = Product(
                    slug=row["slug"], canonical_name=row["name"], category=row["category"],
                    manufacturer=row["manufacturer"], year_season=row["year"], series=row["series"],
                )
                db.add(product); db.flush()

            variant = db.scalar(
                select(ProductVariant).where(
                    ProductVariant.product_id == product.id,
                    ProductVariant.format == row["fmt"],
                )
            )
            if variant is None:
                variant = ProductVariant(
                    product_id=product.id, format=row["fmt"],
                    packs=row["packs"], cards_per_pack=row["cards"],
                )
                db.add(variant); db.flush()
            else:
                variant.packs=row["packs"]; variant.cards_per_pack=row["cards"]

            offer = db.scalar(
                select(Offer).where(
                    Offer.store_id == coolcard.id,
                    Offer.external_id == row["sku"],
                )
            )
            if row["category"]=="Fotboll":
                source_url=football_url
            elif row["category"]=="Pokémon":
                source_url=pokemon_url
            else:
                source_url = pack_url if row["fmt"]=="single pack" else category_url
            if offer is None:
                offer = Offer(
                    store_id=coolcard.id, variant_id=variant.id,
                    external_id=row["sku"], source_title=row["name"],
                    price_sek=row["price"], stock_status=row.get("stock","in_stock"),
                    source_kind="verified_snapshot", source_confidence=100,
                    match_confidence=1.0, match_status="manual_matched",
                    observed_at=REAL_SNAPSHOT_OBSERVED_AT, url=source_url,
                    is_preorder=False,
                )
                db.add(offer); db.flush()
                db.add(PriceHistory(
                    offer_id=offer.id, price_sek=row["price"],
                    stock_status=row.get("stock","in_stock"),
                    observed_at=REAL_SNAPSHOT_OBSERVED_AT,
                ))
            else:
                offer.variant_id=variant.id
                offer.price_sek=row["price"]
                offer.stock_status=row.get("stock","in_stock")
                offer.source_kind="verified_snapshot"
                offer.source_confidence=100
                offer.match_confidence=1.0
                offer.match_status="manual_matched"
                offer.observed_at=REAL_SNAPSHOT_OBSERVED_AT
                offer.url=source_url
                offer.is_preorder=False

            facts=row.get("facts",[])
            if facts:
                pf=db.scalar(select(ProductFact).where(ProductFact.variant_id==variant.id))
                if pf is None:
                    pf=ProductFact(variant_id=variant.id)
                    db.add(pf)
                pf.facts_json=json.dumps(facts,ensure_ascii=False)
                pf.source_name="Coolcard / tillverkarinformation på produktsidan"
                pf.source_url=fact_urls.get(row["slug"],source_url)
                pf.verified_at=REAL_SNAPSHOT_OBSERVED_AT
                pf.confidence=100

        db.commit()
    finally:
        db.close()


CHASE_PROFILES = {
"cc-2025-26-opc-hobby": {
 "source_name":"Coolcard product information / Upper Deck product configuration",
 "source_url":"https://www.coolcard.se/en/product/1-pack-2025-26-upper-deck-o-pee-chee-hobby",
 "key_names":["Marquee Rookies #541-600"],
 "headline_chases":[
   {"card":"Marquee Rookie Retro","tier":"BRA","odds":"High Series 1 per hobby pack; Retro 1:1 hobby packs across base set","why":"Rookie/set-building chase in the 100-card high series."},
   {"card":"Blue Border","tier":"BRA","odds":"1:3 hobby/fat packs","why":"Frequent parallel chase."},
   {"card":"Red Border","tier":"MYCKET BRA","odds":"1:18 hobby/fat packs","why":"Noticeably tougher parallel."},
   {"card":"Retro Black Border /100","tier":"MONSTER","odds":"serial /100","why":"Low-numbered retro parallel."},
   {"card":"Purple Border /49","tier":"MONSTER","odds":"serial /49","why":"Very low-numbered base parallel."},
   {"card":"Red Border Blank Back 1/1","tier":"JACKPOT","odds":"1/1","why":"Unique parallel."},
   {"card":"Printing Plate 1/1","tier":"JACKPOT","odds":"1/1; four plate colours per card","why":"Unique printing-plate chase."}
 ],
 "why_exciting":[
   "Minst tre numrerade base/retro-paralleller eller printing plates per box i snitt ger återkommande serial-number-jakt.",
   "Tre O-Pee-Chee Premier och fyra Playing Cards per box i snitt ger flera separata chase-spår.",
   "Minst ett rare chase card per box i snitt gör att boxen inte enbart lever på en extrem jackpot."
 ],
 "tiers":{
   "everyday":{"label":"Vanligt men intressant","score":76,"items":["3 O-Pee-Chee Premier per box i snitt","4 O-Pee-Chee Playing Cards per box i snitt"]},
   "good":{"label":"Bra träff","score":78,"items":["Numrerad base/retro-parallel","Rare chase card"]},
   "big":{"label":"Riktigt bra","score":82,"items":["Lågt numrerad parallel","Printing plate"]},
   "jackpot":{"label":"Monsterhit","score":74,"items":["Extremt lågnumrerad topp-parallel eller printing plate på rätt spelare"]}
 },
 "caveat":"Styrkan är många parallell- och setbyggarspår snarare än garanterade autografer. Exakta spelarchaser kräver full checklistkartläggning."
},
"cc-pack-2025-26-opc-hobby": {
 "source_name":"Coolcard product information / Upper Deck product configuration",
 "source_url":"https://www.coolcard.se/en/product/1-pack-2025-26-upper-deck-o-pee-chee-hobby",
 "key_names":["Marquee Rookies #541–600"],
 "headline_chases":[
   {"card":"Marquee Rookies #541–600","tier":"BRA","odds":"High Series-rookiepool; exakt spelare och packodds ej verifierade","why":"Det konkreta rookie-spåret i ett löst O-Pee-Chee-paket."},
   {"card":"Blue Border","tier":"BRA","odds":"1:3 hobby/fat packs","why":"Vanligaste dokumenterade parallellspåret."},
   {"card":"Red Border","tier":"MYCKET BRA","odds":"1:18 hobby/fat packs","why":"Tydligt sällsyntare parallell."},
   {"card":"Retro Black Border /100","tier":"MONSTER","odds":"serial /100","why":"Lågnumrerad retroparallel."},
   {"card":"Purple Border /49","tier":"MONSTER","odds":"serial /49","why":"Mycket lågnumrerad parallel."},
   {"card":"Red Border Blank Back 1/1","tier":"JACKPOT","odds":"1/1","why":"Unikt exemplar om rätt kort träffas."}
 ],
 "why_exciting":["Ett löst paket ger en konkret chans på Marquee Rookies och paralleller.","Blue Border är uppgiven till 1:3 och Red Border till 1:18 i hobby/fat packs."],
 "tiers":{"everyday":{"label":"Vanligt men intressant","score":70,"items":["10 kort i paketet"]},"good":{"label":"Bra träff","score":78,"items":["Marquee Rookies #541–600","Blue Border 1:3"]},"big":{"label":"Riktigt bra","score":82,"items":["Red Border 1:18","Retro Black Border /100","Purple Border /49"]},"jackpot":{"label":"Monsterhit","score":72,"items":["Red Border Blank Back 1/1","Printing Plate 1/1"]}},
 "caveat":"Ingen verifierad autografchans är kopplad till just detta lösa paket. Serial- och insertuppgifter är formatets chase-spår; exakta spelarnamn kräver full checklistkoppling."
},
"cc-pack-2025-26-mvp-hobby": {
 "source_name":"Upper Deck 2025-26 MVP Silver Collection checklist",
 "source_url":"https://upperdeck.com/checklist/2025-26-mvp-silver-collection-hockey-checklist/",
 "key_names":["Matthew Schaefer #275","Michael Misa #271","Zeev Buium #273","Danila Yurov #270","Sam Dickinson #267","Sam Rinzel #268"],
 "headline_chases":[
   {"card":"Matthew Schaefer Copper Script Extended Rookie #275","tier":"MYCKET BRA","odds":"Copper Script Extended Rookies 1:10 pack","why":"Namngiven topprookie i den officiella checklistan."},
   {"card":"Michael Misa Copper Script Extended Rookie #271","tier":"MYCKET BRA","odds":"Copper Script Extended Rookies 1:10 pack","why":"En konkret rookie-chase, inte bara ett generiskt rookie-spår."},
   {"card":"Zeev Buium Copper Script Extended Rookie #273","tier":"MYCKET BRA","odds":"Copper Script Extended Rookies 1:10 pack","why":"Officiellt listad Extended Rookie."},
   {"card":"Super Script Black Extended Rookie 1/1","tier":"JACKPOT","odds":"1/1; exakt spelare beror på checklistan","why":"Unik toppparallel på Extended Rookie-korten."}
 ],
 "why_exciting":["Copper Script Extended Rookies ligger på 1:10 paket som kortfamilj.","Schaefer, Misa, Buium, Yurov, Dickinson och Rinzel är namngivna i checklistan."],
 "tiers":{"everyday":{"label":"Vanligt men intressant","score":62,"items":["8 kort i paketet"]},"good":{"label":"Bra träff","score":72,"items":["Copper Script Extended Rookie 1:10"]},"big":{"label":"Riktigt bra","score":58,"items":["Rätt topprookie i rookie-/parallelspåret"]},"jackpot":{"label":"Monsterhit","score":42,"items":["Super Script Black Extended Rookie 1/1"]}},
 "caveat":"Den officiella Silver Collection-checklistan verifierar inget autografspår för produkten. BoxFinder visar därför inte autograf som en möjlig hit."
},
"cc-2025-26-mvp-hobby": {
 "source_name":"Upper Deck 2025-26 MVP Silver Collection checklist",
 "source_url":"https://upperdeck.com/checklist/2025-26-mvp-silver-collection-hockey-checklist/",
 "key_names":["Matthew Schaefer #275","Michael Misa #271","Zeev Buium #273","Danila Yurov #270","Sam Dickinson #267","Sam Rinzel #268"],
 "headline_chases":[
   {"card":"Matthew Schaefer Copper Script Extended Rookie #275","tier":"MYCKET BRA","odds":"Copper Script Extended Rookies 1:10 pack","why":"Namngiven topprookie i officiell checklista."},
   {"card":"Michael Misa Copper Script Extended Rookie #271","tier":"MYCKET BRA","odds":"Copper Script Extended Rookies 1:10 pack","why":"Stark rookie i samma verifierade spår."},
   {"card":"Zeev Buium Copper Script Extended Rookie #273","tier":"MYCKET BRA","odds":"Copper Script Extended Rookies 1:10 pack","why":"Konkret rookie-chase med kortnummer."},
   {"card":"Super Script Black Extended Rookie 1/1","tier":"JACKPOT","odds":"1/1","why":"Produktens tydligaste dokumenterade rookie-jackpot."}
 ],
 "why_exciting":["20 paket ger i teorin omkring två Copper Script Extended Rookies utifrån familjeoddset 1:10.","Sex namngivna rookies visas direkt i stället för en vag rookieetikett."],
 "tiers":{"everyday":{"label":"Vanligt men intressant","score":74,"items":["20 paket","MVP base och Silver Collection-spår"]},"good":{"label":"Bra träff","score":78,"items":["Copper Script Extended Rookie 1:10"]},"big":{"label":"Riktigt bra","score":64,"items":["Schaefer, Misa eller Buium rookieparallel"]},"jackpot":{"label":"Monsterhit","score":48,"items":["Super Script Black Extended Rookie 1/1"]}},
 "caveat":"Checklistan verifierar inget autografspår. Familjeodds är inte samma sak som odds på en viss spelare."
},
"cc-2025-26-pwhl-hobby": {
 "source_name":"Upper Deck 2025-26 UD PWHL checklist",
 "source_url":"https://upperdeck.com/checklist/2025-26-ud-pwhl-checklist/",
 "key_names":["Kristyna Kaltounkova #51","Emma Gentry #52","Rory Guilday #53","Casey O'Brien #57","Kiara Zanon #58","Abby Hustler #59"],
 "headline_chases":[
   {"card":"Casey O'Brien Young Guns #57","tier":"BRA","odds":"Young Guns 1:4 hobby pack; exakt spelare ur 20-kortsgruppen","why":"Namngiven rookie i PWHL Young Guns-checklistan."},
   {"card":"Kristyna Kaltounkova Young Guns #51","tier":"BRA","odds":"Young Guns 1:4 hobby pack","why":"Tydlig rookie-chase med kortnummer."},
   {"card":"UD Canvas Young Guns","tier":"MYCKET BRA","odds":"1:48 hobby pack","why":"Sällsyntare Canvas-version av rookies."},
   {"card":"Young Guns Outburst","tier":"MONSTER","odds":"1:36 hobby pack","why":"Premiumparallel på rookie-spåret."},
   {"card":"Young Guns Deluxe /250, Exclusives /100 eller High Gloss /10","tier":"JACKPOT","odds":"Serienumrerad /250, /100 respektive /10","why":"De lägst numrerade Young Guns-spåren."}
 ],
 "why_exciting":["Young Guns kommer 1:4 hobby pack och boxen innehåller 12 paket.","Checklistan namnger 20 PWHL-rookies och visar formatsspecifika odds."],
 "tiers":{"everyday":{"label":"Vanligt men intressant","score":78,"items":["Young Guns 1:4 hobby pack","UD Canvas 1:16"]},"good":{"label":"Bra träff","score":80,"items":["Kaltounkova, O'Brien eller Zanon Young Guns"]},"big":{"label":"Riktigt bra","score":76,"items":["Canvas Young Guns 1:48","Young Guns Outburst 1:36"]},"jackpot":{"label":"Monsterhit","score":66,"items":["Young Guns High Gloss /10"]}},
 "caveat":"Oddsen gäller kortfamiljen, inte en enskild spelare. Ingen autografchans visas utan verifierat checkliststöd."
},
"cc-pack-2025-26-pwhl-hobby": {
 "source_name":"Upper Deck 2025-26 UD PWHL checklist",
 "source_url":"https://upperdeck.com/checklist/2025-26-ud-pwhl-checklist/",
 "key_names":["Kristyna Kaltounkova #51","Casey O'Brien #57","Kiara Zanon #58","Abby Hustler #59"],
 "headline_chases":[
   {"card":"Young Guns – 20 namngivna PWHL-rookies","tier":"BRA","odds":"1:4 hobby pack","why":"Varje löst paket har ett tydligt, verifierat rookie-spår."},
   {"card":"UD Canvas Young Guns","tier":"MYCKET BRA","odds":"1:48 hobby pack","why":"Sällsynt rookie-Canvas."},
   {"card":"Young Guns Outburst","tier":"MONSTER","odds":"1:36 hobby pack","why":"Premiumparallel som faktiskt finns i hobbyformatet."},
   {"card":"Young Guns High Gloss /10","tier":"JACKPOT","odds":"serial /10","why":"Extremt lågnumrerad rookieparallel."}
 ],
 "why_exciting":["Young Guns 1:4 gör rookiechansen begriplig för ett enskilt paket.","Kaltounkova, O'Brien, Zanon och Hustler är konkreta namn i checklistan."],
 "tiers":{"everyday":{"label":"Vanligt men intressant","score":60,"items":["6 kort"]},"good":{"label":"Bra träff","score":78,"items":["Young Guns 1:4 hobby pack"]},"big":{"label":"Riktigt bra","score":70,"items":["Canvas Young Guns 1:48","Outburst Young Guns 1:36"]},"jackpot":{"label":"Monsterhit","score":60,"items":["Young Guns High Gloss /10"]}},
 "caveat":"Inget autografspår presenteras eftersom det inte är verifierat för detta paket. Spelaroddset är lägre än familjeoddset 1:4."
},
"cc-2025-26-skybox-metal-hobby": {
 "source_name":"Upper Deck 2025-26 Skybox Metal Universe checklist",
 "source_url":"https://upperdeck.com/checklist/2025-2026-skybox-metal-universe-hockey-checklist/",
 "key_names":["Ivan Demidov","Michael Misa","Zeev Buium","Ryan Leonard","Zayne Parekh","Matthew Schaefer"],
 "headline_chases":[
   {"card":"Ivan Demidov Platinum Portraits PP-1","tier":"JACKPOT","odds":"1:1,200 hobby pack","why":"Extremt sällsynt namngiven rookieinsert."},
   {"card":"Ivan Demidov Planet Metal","tier":"MYCKET BRA","odds":"Planet Metal 1:60 hobby pack","why":"Premiuminsert med tydligt familjeodds."},
   {"card":"Rookie Precious Metal Gems Green","tier":"JACKPOT","odds":"serial /10","why":"Ikonisk lågnumrerad PMG-parallel."},
   {"card":"Precious Metal Gems Gold","tier":"JACKPOT","odds":"1/1","why":"Unik PMG-toppträff."}
 ],
 "why_exciting":["Metal Universe har flera namngivna rookieinsertspår med hobbyodds.","PMG Green /10 och Gold 1/1 ger ett verkligt högt tak."],
 "tiers":{"everyday":{"label":"Vanligt men intressant","score":76,"items":["15 paket","flera Metal-insertfamiljer"]},"good":{"label":"Bra träff","score":78,"items":["Rookieinsert på Demidov, Misa, Buium eller Leonard"]},"big":{"label":"Riktigt bra","score":88,"items":["Planet Metal 1:60","sällsynt rookieinsert"]},"jackpot":{"label":"Monsterhit","score":94,"items":["Platinum Portraits 1:1,200","PMG Green /10","PMG Gold 1/1"]}},
 "caveat":"Familjeodds gäller hela insertgruppen. En viss spelare är mer sällsynt än angivet familjeodds."
},
"cc-pack-2025-26-skybox-hobby": {
 "source_name":"Upper Deck 2025-26 Skybox Metal Universe checklist",
 "source_url":"https://upperdeck.com/checklist/2025-2026-skybox-metal-universe-hockey-checklist/",
 "key_names":["Ivan Demidov","Michael Misa","Zeev Buium","Ryan Leonard"],
 "headline_chases":[
   {"card":"Planet Metal rookie","tier":"MYCKET BRA","odds":"1:60 hobby pack","why":"Verifierad sällsynt insertfamilj i löst hobbypaket."},
   {"card":"Ivan Demidov Platinum Portraits PP-1","tier":"JACKPOT","odds":"1:1,200 hobby pack","why":"Namngiven extrem SSP-rookieinsert."},
   {"card":"Precious Metal Gems Green rookie /10","tier":"JACKPOT","odds":"serial /10","why":"Mycket lågnumrerad Metal Universe-chase."}
 ],
 "why_exciting":["Det lösa paketet har verifierade premiuminsertspår.","Ivan Demidov är namngiven på en 1:1,200 hobbyinsert."],
 "tiers":{"everyday":{"label":"Vanligt men intressant","score":58,"items":["6 kort"]},"good":{"label":"Bra träff","score":66,"items":["Rookie eller Metal-insert"]},"big":{"label":"Riktigt bra","score":80,"items":["Planet Metal 1:60"]},"jackpot":{"label":"Monsterhit","score":88,"items":["Platinum Portraits 1:1,200","PMG /10 eller 1/1"]}},
 "caveat":"Inget garanteras i ett löst paket. Familjeodds är inte individuella spelarodds."
},
"cc-2025-26-opc-platinum-retail-blaster": {
 "source_name":"Upper Deck 2025-26 O-Pee-Chee Platinum product and checklist",
 "source_url":"https://upperdeck.com/2025-26-o-pee-chee-platinum/",
 "key_names":["Matthew Schaefer #268","Michael Misa","Ryan Leonard","Beckett Sennecke","Ben Kindel"],
 "headline_chases":[
   {"card":"Matthew Schaefer Neon Yellow Surge Marquee Rookie #268","tier":"BRA","odds":"Neon Yellow Surge Marquee Rookies 1:6 blaster pack","why":"Namngiven topprookie med blasterspecifikt odds."},
   {"card":"Marquee Rookie-paralleller","tier":"MYCKET BRA","odds":"Format varierar; exakt parallel visas bara när retail stöds","why":"Produktens centrala rookie-spår."},
   {"card":"Golden Treasures 1/1","tier":"JACKPOT","odds":"1/1; produktspår, blastertillgänglighet ej separat bekräftad","why":"Produktlinjens högsta parallel, men inte ett påstått blasterodds."}
 ],
 "why_exciting":["Sex pack och ett verifierat blasterodds på Neon Yellow Surge Marquee Rookies.","Schaefer, Misa, Leonard, Sennecke och Kindel är konkreta namn att leta efter."],
 "tiers":{"everyday":{"label":"Vanligt men intressant","score":66,"items":["6 paket","Chrome-liknande paralleller"]},"good":{"label":"Bra träff","score":78,"items":["Neon Yellow Surge Marquee Rookie 1:6"]},"big":{"label":"Riktigt bra","score":68,"items":["Stark rookieparallel"]},"jackpot":{"label":"Monsterhit","score":48,"items":["Extremt lågnumrerad parallel om retailformatet stöder den"]}},
 "caveat":"Produkten har rookieautografer på produktnivå, men BoxFinder påstår inte autografchans eller odds för retailblastern utan formatsspecifikt stöd."
},
"cc-2025-26-extended-hobby": {
 "source_name":"Upper Deck 2025-26 Extended Series product information",
 "source_url":"https://upperdeck.com/2025-26-upper-deck-extended-series/",
 "key_names":["Young Guns #701–750","1st Round Rookies","Debut Game Jersey rookies"],
 "headline_chases":[
   {"card":"Young Guns / 1st Round Rookies","tier":"BRA","odds":"6 per hobbybox i snitt","why":"Boxens återkommande rookieinnehåll."},
   {"card":"Outburst Silver rookieparallel","tier":"MYCKET BRA","odds":"1 per hobbybox i snitt över Outburst-spåret","why":"Verifierad boxträff i premiumparallelspåret."},
   {"card":"Young Guns Deluxe /250","tier":"MYCKET BRA","odds":"serial /250","why":"Numrerad rookieparallel."},
   {"card":"Young Guns Exclusives /100 eller Outburst Red /25","tier":"MONSTER","odds":"serial /100 respektive /25","why":"Mycket lågnumrerade rookieversioner."},
   {"card":"Young Guns High Gloss /10 eller Outburst Gold 1/1","tier":"JACKPOT","odds":"serial /10 respektive 1/1","why":"Rookieparalleller med produktens högsta knapphet."},
   {"card":"Debut Game Jersey Hard-Signed Auto","tier":"JACKPOT","odds":"numrerad till spelarens tröjnummer; ingen boxgaranti","why":"Matchanvänt rookie-material kombinerat med hard-signed autograf."}
 ],
 "why_exciting":["Sex rookie-kort per hobbybox i snitt ger ett tydligt golv för rookieöppningen.","Produkten kombinerar Young Guns-paralleller med ett verifierat rookie jersey/autograf-program."],
 "tiers":{"everyday":{"label":"Vanligt men intressant","score":86,"items":["6 Young Guns/1st Round Rookies per box","4 UD Canvas per box"]},"good":{"label":"Bra träff","score":84,"items":["Stark rookie","Outburst Silver"]},"big":{"label":"Riktigt bra","score":88,"items":["Deluxe /250","Exclusives /100","Outburst Red /25"]},"jackpot":{"label":"Monsterhit","score":92,"items":["High Gloss /10","Outburst Gold 1/1","Debut Game Jersey hard-signed auto"]}},
 "caveat":"Boxsnitt gäller kortfamiljer, inte en viss rookie. Autografen är möjlig enligt produktprogrammet men inte garanterad per box."
},
"cc-2025-26-series2-retail-blaster": {
 "source_name":"Coolcard / Upper Deck Series 2 product information",
 "source_url":"https://www.coolcard.se/category/boxar-nhl-2025-26",
 "key_names":["Matthew Schaefer","Michael Misa","Zeev Buium","Danila Yurov","Easton Cowan","Alexander Nikishin"],
 "why_exciting":[
   "Series 2-rookiepoolen ger tillgång till samma centrala Young Guns-namn som hobbyprodukten till betydligt lägre inköpspris.",
   "Retailformatet är ett billigare sätt att jaga rookies och inserts utan att köpa en hel hobbybox."
 ],
 "tiers":{
   "everyday":{"label":"Vanligt men intressant","score":68,"items":["Series 2 base/inserts","Rookie-jakt över fyra 12-kortspack"]},
   "good":{"label":"Bra träff","score":76,"items":["Young Guns på en av de starka Series 2-rookiesarna"]},
   "big":{"label":"Riktigt bra","score":62,"items":["Sällsynt retail-parallel eller stark rookie-variant"]},
   "jackpot":{"label":"Monsterhit","score":48,"items":["Extremt sällsynt toppträff på checklistans bästa rookie"]}
 },
 "caveat":"Retail har lägre pris men färre pack och ett smalare premiumtak än hobby. BoxFinder påstår inte hobby-exklusiva odds för retail."
},
"cc-2025-26-series1-hobby": {
 "source_name":"Beckett / Upper Deck e-Pack checklist",
 "source_url":"https://www.beckett.com/news/2025-26-upper-deck-series-1-hockey-cards/",
 "key_names":["Ivan Demidov #205","Artyom Levshunov #201","Gabe Perreault #202","Jimmy Snuggerud #207","Noah Ostlund #219","Zayne Parekh #236"],
 "headline_chases":[
   {"card":"Ivan Demidov Young Guns #205","tier":"BRA","odds":"Young Guns 1:2 packs; 50-card YG checklist","why":"En av Series 1:s tydligaste rookie-chaser."},
   {"card":"Artyom Levshunov Young Guns #201","tier":"BRA","odds":"Young Guns 1:2 packs","why":"Topprookie i Series 1 Young Guns-poolen."},
   {"card":"Gabe Perreault Young Guns #202","tier":"BRA","odds":"Young Guns 1:2 packs","why":"Attraktiv rookie i flagship-checklistan."},
   {"card":"Young Guns Outburst Silver","tier":"MYCKET BRA","odds":"1:60 hobby packs","why":"Sällsyntare Young Guns-parallel."},
   {"card":"Young Guns Clear Cut","tier":"MYCKET BRA","odds":"1:144 hobby packs","why":"Hobby-exklusiv transparent rookieparallel."},
   {"card":"Young Guns Deluxe /250","tier":"MYCKET BRA","odds":"serial /250","why":"Numrerad hobby/e-Pack-rookieparallel."},
   {"card":"Young Guns Exclusives /100","tier":"MONSTER","odds":"serial /100","why":"Lågnumrerad flagship-rookie."},
   {"card":"Young Guns Outburst Red /25","tier":"MONSTER","odds":"serial /25","why":"Mycket lågnumrerad Young Guns."},
   {"card":"Young Guns High Gloss /10","tier":"JACKPOT","odds":"serial /10","why":"Bara tio exemplar per Young Guns-kort."},
   {"card":"Young Guns Outburst Gold 1/1","tier":"JACKPOT","odds":"1/1","why":"Unik toppparallel."},
   {"card":"Snow Spray Auto Variation","tier":"JACKPOT","odds":"1:4,000 packs (base variation family)","why":"Extremt sällsynt signerad variation."}
 ],
 "why_exciting":[
   "Sex Young Guns per hobbybox i snitt ger återkommande rookie-jakt, inte bara en jackpotchans.",
   "Ivan Demidov är en av de tydliga rookie-chaserna i Series 1-checklistan.",
   "Young Guns har hobby-exklusiva premiumparalleller som Deluxe /250, Exclusives /100, Outburst Red /25, High Gloss /10 och Outburst Gold 1/1.",
   "Mycket sällsynta variationer och autografer ger ett högt tak ovanpå den vanliga Young Guns-jakten."
 ],
 "tiers":{
   "everyday":{"label":"Vanligt men intressant","score":82,"items":["6 Young Guns per box i snitt","UD Canvas och flera insertfamiljer"]},
   "good":{"label":"Bra träff","score":78,"items":["Stark Young Guns-rookie","Outburst Silver Young Guns 1:60 packs","Clear Cut Young Guns 1:144 hobby packs"]},
   "big":{"label":"Riktigt bra","score":82,"items":["Young Guns Deluxe /250","Young Guns Exclusives /100","Outburst Red /25","High Gloss /10"]},
   "jackpot":{"label":"Monsterhit","score":88,"items":["Young Guns Outburst Gold 1/1","Printing Plate 1/1","Snow Spray Auto Variation 1:4,000 packs"]}
 },
 "caveat":"Series 1 är rookie- och parallelldriven. En normal box garanterar inte autograf eller ett dyrt kort."
},
"cc-2025-26-series2-hobby": {
 "source_name":"Beckett 2025-26 Upper Deck Series 2 checklist",
 "source_url":"https://www.beckett.com/news/2025-26-upper-deck-series-2-hockey-cards/",
 "key_names":["Matthew Schaefer #451","Michael Misa #487","Zeev Buium #486","Danila Yurov #452","Easton Cowan #462","Alexander Nikishin #461"],
 "headline_chases":[
   {"card":"Matthew Schaefer Young Guns #451","tier":"BRA","odds":"Young Guns 1:2 packs; exakt spelare beror på 50-korts YG-checklistan","why":"Flagship-rookie och central Series 2-chase."},
   {"card":"Michael Misa Young Guns #487","tier":"BRA","odds":"Young Guns 1:2 packs","why":"En av de viktigaste rookiesarna i checklistan."},
   {"card":"Zeev Buium Young Guns #486","tier":"BRA","odds":"Young Guns 1:2 packs","why":"Stark rookie i samma 50-korts Young Guns-pool."},
   {"card":"Young Guns Outburst Silver","tier":"MYCKET BRA","odds":"1:60 hobby packs","why":"Betydligt sällsyntare Young Guns-parallel."},
   {"card":"Young Guns Clear Cut","tier":"MYCKET BRA","odds":"1:144 hobby packs","why":"Hobby-exklusiv transparent premiumparallel."},
   {"card":"Young Guns Deluxe /250","tier":"MYCKET BRA","odds":"serial /250","why":"Numrerad hobby/e-Pack-exklusiv rookieparallel."},
   {"card":"Young Guns Exclusives /100","tier":"MONSTER","odds":"serial /100","why":"Lågnumrerad version av rätt rookie."},
   {"card":"Young Guns Outburst Red /25","tier":"MONSTER","odds":"serial /25","why":"Extremt lågnumrerad rookieparallel."},
   {"card":"Young Guns High Gloss /10","tier":"JACKPOT","odds":"serial /10","why":"Bara tio exemplar per spelare."},
   {"card":"Young Guns Outburst Gold 1/1","tier":"JACKPOT","odds":"1/1","why":"Unik toppparallel."},
   {"card":"Matthew Schaefer Celebration Variation","tier":"JACKPOT","odds":"Celebration Variations 1:2,880 hobby/e-Pack packs","why":"Extrem SSP-variation på checklistans stora rookie."},
   {"card":"Matthew Schaefer Program of Excellence Canvas","tier":"MONSTER","odds":"Program of Excellence 1:96 hobby/e-Pack packs","why":"Sällsynt Canvas-spår med Schaefer."}
 ],
 "why_exciting":[
   "Sex Young Guns per hobbybox i snitt ger många chanser på den starka rookiegruppen.",
   "Matthew Schaefer, Michael Misa och Zeev Buium hör till de viktigaste rookie-chaserna.",
   "Hobbyformatet öppnar för numrerade Young Guns-paralleller som /250, /100, /25, /10 och 1/1.",
   "21 inserts och fyra UD Canvas per box i snitt ger betydligt mer action än bara baskort."
 ],
 "tiers":{
   "everyday":{"label":"Vanligt men intressant","score":88,"items":["6 Young Guns per box","21 inserts per box","4 UD Canvas per box"]},
   "good":{"label":"Bra träff","score":86,"items":["Matthew Schaefer Young Guns","Michael Misa Young Guns","Zeev Buium Young Guns","Canvas Young Guns"]},
   "big":{"label":"Riktigt bra","score":91,"items":["Young Guns Deluxe /250","Exclusives /100","Outburst Red /25","High Gloss /10"]},
   "jackpot":{"label":"Monsterhit","score":93,"items":["Young Guns Outburst Gold 1/1","Printing Plate 1/1","Snow Spray Auto 1:4,000 packs","Swagnificent variation 1:1,000 hobby/e-Pack"]}
 },
 "caveat":"Stark chaseprofil betyder inte positivt ekonomiskt EV. De mest extrema träffarna är mycket sällsynta."
},
"cc-2025-26-clear-cut-hobby": {
 "source_name":"Beckett 2025-26 Upper Deck Clear Cut checklist",
 "source_url":"https://www.beckett.com/news/2025-26-upper-deck-clear-cut-hockey-cards/",
 "key_names":["Connor McDavid","Connor Bedard","Alex Ovechkin","Cale Makar","Mario Lemieux","Bobby Orr","Matthew Schaefer","Ivan Demidov","Michael Misa"],
 "headline_chases":[
   {"card":"Base Auto – Connor McDavid","tier":"MONSTER","odds":"base segment odds vary by checklist segment","why":"Hard-signed acetate auto på ett av produktens största namn."},
   {"card":"Base Auto – Connor Bedard","tier":"MONSTER","odds":"base segment","why":"Modern superstjärna i den signerade baschecklistan."},
   {"card":"Base Auto – Alex Ovechkin","tier":"MONSTER","odds":"base segment","why":"Legendariskt toppnamn i base autos."},
   {"card":"Outburst Auto /25","tier":"MONSTER","odds":"serial /25","why":"Lågnumrerad hard-signed parallel."},
   {"card":"High Gloss Auto /10","tier":"JACKPOT","odds":"serial /10","why":"Bara tio exemplar på respektive kort."},
   {"card":"Gold Outburst Auto 1/1","tier":"JACKPOT","odds":"1/1","why":"Produktens unika base-parallel."},
   {"card":"Canvas Signature Gold Ink 1/1","tier":"JACKPOT","odds":"1/1","why":"Unik signerad Canvas-variant."},
   {"card":"Mario Lemieux SPx Starscape Auto","tier":"JACKPOT","odds":"Starscape 1:60 packs; Lemieux SSP inom setet","why":"Ikonisk legend och SSP."},
   {"card":"Bobby Orr SPx Starscape Auto","tier":"JACKPOT","odds":"Starscape 1:60 packs; Orr SSP inom setet","why":"Legendautograf med SSP-status."},
   {"card":"Canvas Rookie Debuts – Schaefer/Demidov/Misa","tier":"MYCKET BRA","odds":"non-auto card + redemption for signed /25 or Gold Ink 1/1","why":"Topprookies med möjlighet till mycket sällsynt signerad redemption."}
 ],
 "why_exciting":[
   "Produkten är extremt hit-koncentrerad: en encased hard-signed autograph eller redemption för signerad version per box.",
   "Checklistan blandar rookies, dagens stjärnor och legendarer.",
   "Outburst /25, High Gloss /10 och Gold Outburst 1/1 ger verklig premium-upside.",
   "Retro- och insertautografer inkluderar flera mycket sällsynta signaturkoncept."
 ],
 "tiers":{
   "everyday":{"label":"Vanligt men intressant","score":94,"items":["1 hard-signed autograph eller autograph redemption per box"]},
   "good":{"label":"Bra träff","score":88,"items":["Rookie autograph","Canvas Signature","Retro Auto","Dazzlers Auto"]},
   "big":{"label":"Riktigt bra","score":94,"items":["Outburst /25","High Gloss /10","Booming Stars Auto /50","Blue parallels /10"]},
   "jackpot":{"label":"Monsterhit","score":97,"items":["Gold Outburst 1/1","Gold Ink 1/1","stora legend-/stjärna-autografer och SSP-designs"]}
 },
 "caveat":"En enda kortplats per box ger extrem varians: hög hit-känsla men mycket beroende av vilket namn och vilken variant du träffar."
},
"cc-2025-26-panini-prizm-fifa-choice": {
 "source_name":"Coolcard verified product snapshot",
 "source_url":"https://www.coolcard.se/category/boxar-paket-fotboll-endast-hobby",
 "key_names":[],
 "why_exciting":[
   "En autograf per box i snitt gör att formatet har en tydlig signerad hit som huvudattraktion.",
   "Bara åtta kort per box gör produkten hit-koncentrerad: få kort, men större fokus på parallels och autograf."
 ],
 "tiers":{
   "everyday":{"label":"Vanligt men intressant","score":62,"items":["8 kort per box"]},
   "good":{"label":"Bra träff","score":86,"items":["1 autograf per box i snitt"]},
   "big":{"label":"Riktigt bra","score":72,"items":["Stark spelare på autograf eller premiumparallel"]},
   "jackpot":{"label":"Monsterhit","score":65,"items":["Toppnamn på mycket sällsynt autograf/parallel"]}
 },
 "caveat":"Full FIFA-checklista och parallelodds är ännu inte kartlagda, därför rankas inte specifika spelare eller påstådda SSP-träffar."
},
"cc-2025-26-topps-bayern-lineage": {
 "source_name":"Coolcard verified product snapshot",
 "source_url":"https://www.coolcard.se/category/boxar-paket-fotboll-endast-hobby",
 "key_names":[],
 "why_exciting":[
   "Tre encased Autograph, Autograph Relics eller Relics per box ger mycket hög hit-koncentration.",
   "Sju kort totalt betyder att en stor del av boxen består av premiumhits snarare än basvolym."
 ],
 "tiers":{
   "everyday":{"label":"Vanligt men intressant","score":88,"items":["7 kort per box","3 encased premiumhits per box"]},
   "good":{"label":"Bra träff","score":92,"items":["Autograph","Autograph Relic","Relic"]},
   "big":{"label":"Riktigt bra","score":82,"items":["Premiumsignatur eller relic på stark Bayern-spelare"]},
   "jackpot":{"label":"Monsterhit","score":72,"items":["Mycket sällsynt toppnamn/premiumvariant"]}
 },
 "caveat":"BoxFinder har verifierat produktkonfigurationen men ännu inte full spelare-, serial- och oddsdata."
},
"cc-pokemon-mega-zygarde-premium": {
 "source_name":"Coolcard verified product snapshot",
 "source_url":"https://www.coolcard.se/category/pokmon",
 "key_names":["Mega Zygarde ex","Mega Starmie ex","Mega Clefable ex","Meowth ex","Yveltal ex","Mega Skarmory ex"],
 "headline_chases":[
   {"card":"Mega Zygarde ex promo (vanligt + stort promo)","tier":"BRA","odds":"2 garanterade promos i Premium Collection","why":"Det säkra innehållet i själva produkten."},
   {"card":"Mega Zygarde ex #120 / Special Illustration Rare","tier":"MYCKET BRA","odds":"Ur Mega Evolution—Perfect Order-boosterpaketen; packodds ej publicerade","why":"Setets centrala Pokémon och en tydlig chase i boosterpaketen."},
   {"card":"Meowth ex #121 / Special Illustration Rare","tier":"MYCKET BRA","odds":"Ur Mega Evolution—Perfect Order-boosterpaketen; packodds ej publicerade","why":"En av de mest eftertraktade Pokémon-träffarna i setets högre rarity-spår."},
   {"card":"Mega Zygarde ex #124 / Mega Hyper Rare","tier":"JACKPOT","odds":"Ur Mega Evolution—Perfect Order-boosterpaketen; packodds ej publicerade","why":"Setets högsta namngivna rarity-spår."},
   {"card":"Mega Starmie ex #118–119 och Mega Clefable ex #119–120","tier":"MYCKET BRA","odds":"Ur Mega Evolution—Perfect Order-boosterpaketen; packodds ej publicerade","why":"Ytterligare konkreta Mega Evolution-chaser i boosterpaketen."}
 ],
 "why_exciting":[
   "Åtta boosterpaket ger åtta separata chanser på setets chase-kort.",
   "Både stort och vanligt promo-kort ger garanterat samlarinnehåll även om boostersen missar."
 ],
 "tiers":{
   "everyday":{"label":"Vanligt men intressant","score":72,"items":["8 boosterpaket","2 typer av promo-kort"]},
   "good":{"label":"Bra träff","score":64,"items":["Stark pull ur något av de åtta boostersen"]},
   "big":{"label":"Riktigt bra","score":58,"items":["Setets premiumillustration/chase-kort"]},
   "jackpot":{"label":"Monsterhit","score":48,"items":["Setets absoluta toppkort ur boosterpaketen"]}
 },
 "caveat":"Produktens två promos är verifierade. Boosterpaketen är Mega Evolution—Perfect Order, men officiella kortspecifika pull rates är inte publicerade i underlaget och visas därför inte som odds."
},
"cc-pokemon-paradox-rift-18": {
 "source_name":"Coolcard verified product snapshot",
 "source_url":"https://www.coolcard.se/category/displayer-booster-boxar",
 "key_names":[],
 "why_exciting":[
   "18 boosterpaket ger många separata chanser att träffa setets illustration- och rarity-chaser.",
   "Förseglad display passar bättre för ren packöppning än collection-produkter där en del av priset ligger i promos/tillbehör."
 ],
 "tiers":{
   "everyday":{"label":"Vanligt men intressant","score":78,"items":["18 boosterpaket"]},
   "good":{"label":"Bra träff","score":70,"items":["Illustration-/rarity-hit ur setet"]},
   "big":{"label":"Riktigt bra","score":64,"items":["Premium chase ur Paradox Rift"]},
   "jackpot":{"label":"Monsterhit","score":55,"items":["Setets mest eftertraktade toppkort"]}
 },
 "caveat":"Full setchecklista, marknadsvärden och verifierade pull rates återstår innan BoxFinder kan namnge och sannolikhetsgradera toppkorten."
}
}


CHASE_CARD_DB = [

    # MVP Silver Collection: exact Extended Rookies and verified family odds.
    dict(slug="cc-2025-26-mvp-hobby", key="hockey:2025-26:mvp-silver:275:matthew-schaefer:copper-script", player="Matthew Schaefer", card="Copper Script Extended Rookie", number="275", rookie=True, tier="MYCKET BRA", odds="Copper Script Extended Rookies 1:10 packs", source="https://upperdeck.com/checklist/2025-26-mvp-silver-collection-hockey-checklist/"),
    dict(slug="cc-pack-2025-26-mvp-hobby", key="hockey:2025-26:mvp-silver:275:matthew-schaefer:copper-script", player="Matthew Schaefer", card="Copper Script Extended Rookie", number="275", rookie=True, tier="MYCKET BRA", odds="Copper Script Extended Rookies 1:10 packs", source="https://upperdeck.com/checklist/2025-26-mvp-silver-collection-hockey-checklist/"),
    dict(slug="cc-2025-26-mvp-hobby", key="hockey:2025-26:mvp-silver:271:michael-misa:copper-script", player="Michael Misa", card="Copper Script Extended Rookie", number="271", rookie=True, tier="MYCKET BRA", odds="Copper Script Extended Rookies 1:10 packs", source="https://upperdeck.com/checklist/2025-26-mvp-silver-collection-hockey-checklist/"),
    dict(slug="cc-pack-2025-26-mvp-hobby", key="hockey:2025-26:mvp-silver:271:michael-misa:copper-script", player="Michael Misa", card="Copper Script Extended Rookie", number="271", rookie=True, tier="MYCKET BRA", odds="Copper Script Extended Rookies 1:10 packs", source="https://upperdeck.com/checklist/2025-26-mvp-silver-collection-hockey-checklist/"),
    dict(slug="cc-2025-26-mvp-hobby", key="hockey:2025-26:mvp-silver:273:zeev-buium:copper-script", player="Zeev Buium", card="Copper Script Extended Rookie", number="273", rookie=True, tier="MYCKET BRA", odds="Copper Script Extended Rookies 1:10 packs", source="https://upperdeck.com/checklist/2025-26-mvp-silver-collection-hockey-checklist/"),
    dict(slug="cc-pack-2025-26-mvp-hobby", key="hockey:2025-26:mvp-silver:273:zeev-buium:copper-script", player="Zeev Buium", card="Copper Script Extended Rookie", number="273", rookie=True, tier="MYCKET BRA", odds="Copper Script Extended Rookies 1:10 packs", source="https://upperdeck.com/checklist/2025-26-mvp-silver-collection-hockey-checklist/"),

    # PWHL exact rookies; links are shared by hobby box and its loose hobby pack.
    dict(slug="cc-2025-26-pwhl-hobby", key="hockey:2025-26:pwhl:51:kristyna-kaltounkova:young-guns", player="Kristyna Kaltounkova", card="Young Guns", number="51", rookie=True, tier="BRA", odds="Young Guns 1:4 hobby packs", source="https://upperdeck.com/checklist/2025-26-ud-pwhl-checklist/"),
    dict(slug="cc-pack-2025-26-pwhl-hobby", key="hockey:2025-26:pwhl:51:kristyna-kaltounkova:young-guns", player="Kristyna Kaltounkova", card="Young Guns", number="51", rookie=True, tier="BRA", odds="Young Guns 1:4 hobby packs", source="https://upperdeck.com/checklist/2025-26-ud-pwhl-checklist/"),
    dict(slug="cc-2025-26-pwhl-hobby", key="hockey:2025-26:pwhl:57:casey-obrien:young-guns", player="Casey O'Brien", card="Young Guns", number="57", rookie=True, tier="BRA", odds="Young Guns 1:4 hobby packs", source="https://upperdeck.com/checklist/2025-26-ud-pwhl-checklist/"),
    dict(slug="cc-pack-2025-26-pwhl-hobby", key="hockey:2025-26:pwhl:57:casey-obrien:young-guns", player="Casey O'Brien", card="Young Guns", number="57", rookie=True, tier="BRA", odds="Young Guns 1:4 hobby packs", source="https://upperdeck.com/checklist/2025-26-ud-pwhl-checklist/"),
    dict(slug="cc-2025-26-pwhl-hobby", key="hockey:2025-26:pwhl:58:kiara-zanon:young-guns", player="Kiara Zanon", card="Young Guns", number="58", rookie=True, tier="BRA", odds="Young Guns 1:4 hobby packs", source="https://upperdeck.com/checklist/2025-26-ud-pwhl-checklist/"),
    dict(slug="cc-pack-2025-26-pwhl-hobby", key="hockey:2025-26:pwhl:58:kiara-zanon:young-guns", player="Kiara Zanon", card="Young Guns", number="58", rookie=True, tier="BRA", odds="Young Guns 1:4 hobby packs", source="https://upperdeck.com/checklist/2025-26-ud-pwhl-checklist/"),

    # Skybox Metal Universe exact high-end rookie inserts.
    dict(slug="cc-2025-26-skybox-metal-hobby", key="hockey:2025-26:skybox:demidov:platinum-portraits-pp1", player="Ivan Demidov", card="Platinum Portraits", number="PP-1", rookie=True, tier="JACKPOT", odds="1:1,200 hobby packs", source="https://upperdeck.com/checklist/2025-2026-skybox-metal-universe-hockey-checklist/"),
    dict(slug="cc-pack-2025-26-skybox-hobby", key="hockey:2025-26:skybox:demidov:platinum-portraits-pp1", player="Ivan Demidov", card="Platinum Portraits", number="PP-1", rookie=True, tier="JACKPOT", odds="1:1,200 hobby packs", source="https://upperdeck.com/checklist/2025-2026-skybox-metal-universe-hockey-checklist/"),
    dict(slug="cc-2025-26-skybox-metal-hobby", key="hockey:2025-26:skybox:buium:planet-metal-26", player="Zeev Buium", card="Planet Metal", number="26 of 40 PM", rookie=True, tier="MYCKET BRA", odds="Planet Metal 1:60 hobby packs", source="https://upperdeck.com/checklist/2025-2026-skybox-metal-universe-hockey-checklist/"),
    dict(slug="cc-pack-2025-26-skybox-hobby", key="hockey:2025-26:skybox:buium:planet-metal-26", player="Zeev Buium", card="Planet Metal", number="26 of 40 PM", rookie=True, tier="MYCKET BRA", odds="Planet Metal 1:60 hobby packs", source="https://upperdeck.com/checklist/2025-2026-skybox-metal-universe-hockey-checklist/"),

    # O-Pee-Chee Platinum retail-specific rookie hit.
    dict(slug="cc-2025-26-opc-platinum-retail-blaster", key="hockey:2025-26:opc-platinum:268:matthew-schaefer:neon-yellow-surge", player="Matthew Schaefer", card="Neon Yellow Surge Marquee Rookie", number="268", rookie=True, tier="BRA", odds="Neon Yellow Surge Marquee Rookies 1:6 blaster packs", source="https://upperdeck.com/checklist/2025-26-o-pee-chee-platinum-hockey-checklist/"),

    # Additional Series 1 exact named rookie/inserts from verified checklist.
    dict(slug="cc-2025-26-series1-hobby", key="hockey:2025-26:ud-s1:demidov:rtd-1", player="Ivan Demidov", card="1994-95 Rookie Die Cuts RTD-1", number="RTD-1", rookie=True, tier="MYCKET BRA", odds="Verified checklist; insert family odds apply", source="https://www.beckett.com/news/2025-26-upper-deck-series-1-hockey-cards/"),
    dict(slug="cc-2025-26-series1-hobby", key="hockey:2025-26:ud-s1:demidov:pc-17", player="Ivan Demidov", card="Population Count 1000 PC-17", number="PC-17", rookie=True, tier="MONSTER", odds="Population Count 1000 family; hobby/e-Pack", source="https://www.beckett.com/news/2025-26-upper-deck-series-1-hockey-cards/"),
    dict(slug="cc-2025-26-series1-hobby", key="hockey:2025-26:ud-s1:demidov:dz-18", player="Ivan Demidov", card="Dazzlers Blue DZ-18", number="DZ-18", rookie=True, tier="BRA", odds="Verified checklist", source="https://www.beckett.com/news/2025-26-upper-deck-series-1-hockey-cards/"),

    # Additional Series 2 exact chase inserts.
    dict(slug="cc-2025-26-series2-hobby", key="hockey:2025-26:ud-s2:schaefer:inc-5", player="Matthew Schaefer", card="Incarnations INC-5", number="INC-5", rookie=True, tier="JACKPOT", odds="1:1,920 hobby/e-Pack packs", source="https://www.beckett.com/news/2025-26-upper-deck-series-2-hockey-cards/"),
    dict(slug="cc-2025-26-series2-hobby", key="hockey:2025-26:ud-s2:misa:inc-2", player="Michael Misa", card="Incarnations INC-2", number="INC-2", rookie=True, tier="JACKPOT", odds="1:1,920 hobby/e-Pack packs", source="https://www.beckett.com/news/2025-26-upper-deck-series-2-hockey-cards/"),
    dict(slug="cc-2025-26-series2-hobby", key="hockey:2025-26:ud-s2:buium:inc-6", player="Zeev Buium", card="Incarnations INC-6", number="INC-6", rookie=True, tier="JACKPOT", odds="1:1,920 hobby/e-Pack packs", source="https://www.beckett.com/news/2025-26-upper-deck-series-2-hockey-cards/"),
    dict(slug="cc-2025-26-series2-hobby", key="hockey:2025-26:ud-s2:schaefer:pc-37", player="Matthew Schaefer", card="Population Count 1000 PC-37", number="PC-37", rookie=True, tier="MONSTER", odds="Hobby/e-Pack exclusive; parallels down to Population Count 1", source="https://www.beckett.com/news/2025-26-upper-deck-series-2-hockey-cards/"),
    dict(slug="cc-2025-26-series2-hobby", key="hockey:2025-26:ud-s2:misa:pc-57", player="Michael Misa", card="Population Count 1000 PC-57", number="PC-57", rookie=True, tier="MONSTER", odds="Hobby/e-Pack exclusive; parallels down to Population Count 1", source="https://www.beckett.com/news/2025-26-upper-deck-series-2-hockey-cards/"),
    dict(slug="cc-2025-26-series2-hobby", key="hockey:2025-26:ud-s2:buium:c-211", player="Zeev Buium", card="UD Canvas Young Guns C-211", number="C-211", rookie=True, tier="MYCKET BRA", odds="Canvas Young Guns 1:24 hobby/e-Pack packs", source="https://www.beckett.com/news/2025-26-upper-deck-series-2-hockey-cards/"),
    dict(slug="cc-2025-26-series2-hobby", key="hockey:2025-26:ud-s2:yurov:c-230", player="Danila Yurov", card="UD Canvas Young Guns C-230", number="C-230", rookie=True, tier="MYCKET BRA", odds="Canvas Young Guns 1:24 hobby/e-Pack packs", source="https://www.beckett.com/news/2025-26-upper-deck-series-2-hockey-cards/"),
    dict(slug="cc-2025-26-series2-hobby", key="hockey:2025-26:ud-s2:schaefer:c-259", player="Matthew Schaefer", card="UD Canvas Program of Excellence C-259", number="C-259", rookie=True, tier="MONSTER", odds="Program of Excellence 1:96 hobby/e-Pack packs", source="https://www.beckett.com/news/2025-26-upper-deck-series-2-hockey-cards/"),
    dict(slug="cc-2025-26-series2-hobby", key="hockey:2025-26:ud-s2:misa:c-267", player="Michael Misa", card="UD Canvas Program of Excellence C-267", number="C-267", rookie=True, tier="MONSTER", odds="Program of Excellence 1:96 hobby/e-Pack packs", source="https://www.beckett.com/news/2025-26-upper-deck-series-2-hockey-cards/"),

    # Series 1 exact rookie cards. Parallel families are represented separately by chase profile.
    dict(slug="cc-2025-26-series1-hobby", key="hockey:2025-26:ud-s1:205:ivan-demidov:young-guns", player="Ivan Demidov", card="Young Guns", number="205", rookie=True, tier="BRA", odds="Young Guns 1:2 packs", source="https://www.beckett.com/news/2025-26-upper-deck-series-1-hockey-cards/"),
    dict(slug="cc-2025-26-series1-hobby", key="hockey:2025-26:ud-s1:201:artyom-levshunov:young-guns", player="Artyom Levshunov", card="Young Guns", number="201", rookie=True, tier="BRA", odds="Young Guns 1:2 packs", source="https://www.beckett.com/news/2025-26-upper-deck-series-1-hockey-cards/"),
    dict(slug="cc-2025-26-series1-hobby", key="hockey:2025-26:ud-s1:202:gabe-perreault:young-guns", player="Gabe Perreault", card="Young Guns", number="202", rookie=True, tier="BRA", odds="Young Guns 1:2 packs", source="https://www.beckett.com/news/2025-26-upper-deck-series-1-hockey-cards/"),
    dict(slug="cc-2025-26-series1-hobby", key="hockey:2025-26:ud-s1:207:jimmy-snuggerud:young-guns", player="Jimmy Snuggerud", card="Young Guns", number="207", rookie=True, tier="BRA", odds="Young Guns 1:2 packs", source="https://www.beckett.com/news/2025-26-upper-deck-series-1-hockey-cards/"),
    dict(slug="cc-2025-26-series1-hobby", key="hockey:2025-26:ud-s1:219:noah-ostlund:young-guns", player="Noah Ostlund", card="Young Guns", number="219", rookie=True, tier="BRA", odds="Young Guns 1:2 packs", source="https://www.beckett.com/news/2025-26-upper-deck-series-1-hockey-cards/"),
    dict(slug="cc-2025-26-series1-hobby", key="hockey:2025-26:ud-s1:236:zayne-parekh:young-guns", player="Zayne Parekh", card="Young Guns", number="236", rookie=True, tier="BRA", odds="Young Guns 1:2 packs", source="https://www.beckett.com/news/2025-26-upper-deck-series-1-hockey-cards/"),

    # Series 2 exact rookies. Same canonical cards can later be linked to retail/blaster variants too.
    dict(slug="cc-2025-26-series2-hobby", key="hockey:2025-26:ud-s2:451:matthew-schaefer:young-guns", player="Matthew Schaefer", card="Young Guns", number="451", rookie=True, tier="BRA", odds="Young Guns 1:2 packs", source="https://www.beckett.com/news/2025-26-upper-deck-series-2-hockey-cards/"),
    dict(slug="cc-2025-26-series2-retail-blaster", key="hockey:2025-26:ud-s2:451:matthew-schaefer:young-guns", player="Matthew Schaefer", card="Young Guns", number="451", rookie=True, tier="BRA", odds="Retail exact odds not asserted", source="https://www.beckett.com/news/2025-26-upper-deck-series-2-hockey-cards/"),
    dict(slug="cc-2025-26-series2-hobby", key="hockey:2025-26:ud-s2:487:michael-misa:young-guns", player="Michael Misa", card="Young Guns", number="487", rookie=True, tier="BRA", odds="Young Guns 1:2 packs", source="https://www.beckett.com/news/2025-26-upper-deck-series-2-hockey-cards/"),
    dict(slug="cc-2025-26-series2-retail-blaster", key="hockey:2025-26:ud-s2:487:michael-misa:young-guns", player="Michael Misa", card="Young Guns", number="487", rookie=True, tier="BRA", odds="Retail exact odds not asserted", source="https://www.beckett.com/news/2025-26-upper-deck-series-2-hockey-cards/"),
    dict(slug="cc-2025-26-series2-hobby", key="hockey:2025-26:ud-s2:486:zeev-buium:young-guns", player="Zeev Buium", card="Young Guns", number="486", rookie=True, tier="BRA", odds="Young Guns 1:2 packs", source="https://www.beckett.com/news/2025-26-upper-deck-series-2-hockey-cards/"),
    dict(slug="cc-2025-26-series2-hobby", key="hockey:2025-26:ud-s2:452:danila-yurov:young-guns", player="Danila Yurov", card="Young Guns", number="452", rookie=True, tier="BRA", odds="Young Guns 1:2 packs", source="https://www.beckett.com/news/2025-26-upper-deck-series-2-hockey-cards/"),
    dict(slug="cc-2025-26-series2-hobby", key="hockey:2025-26:ud-s2:462:easton-cowan:young-guns", player="Easton Cowan", card="Young Guns", number="462", rookie=True, tier="BRA", odds="Young Guns 1:2 packs", source="https://www.beckett.com/news/2025-26-upper-deck-series-2-hockey-cards/"),
    dict(slug="cc-2025-26-series2-hobby", key="hockey:2025-26:ud-s2:461:alexander-nikishin:young-guns", player="Alexander Nikishin", card="Young Guns", number="461", rookie=True, tier="BRA", odds="Young Guns 1:2 packs", source="https://www.beckett.com/news/2025-26-upper-deck-series-2-hockey-cards/"),

    # Clear Cut major named autograph chases.
    dict(slug="cc-2025-26-clear-cut-hobby", key="hockey:2025-26:clear-cut:connor-mcdavid:base-auto", player="Connor McDavid", card="Clear Cut Base Auto", number=None, rookie=False, tier="MONSTER", odds="Checklist segment odds vary", source="https://www.beckett.com/news/2025-26-upper-deck-clear-cut-hockey-cards/"),
    dict(slug="cc-2025-26-clear-cut-hobby", key="hockey:2025-26:clear-cut:connor-bedard:base-auto", player="Connor Bedard", card="Clear Cut Base Auto", number=None, rookie=False, tier="MONSTER", odds="Checklist segment odds vary", source="https://www.beckett.com/news/2025-26-upper-deck-clear-cut-hockey-cards/"),
    dict(slug="cc-2025-26-clear-cut-hobby", key="hockey:2025-26:clear-cut:alex-ovechkin:base-auto", player="Alex Ovechkin", card="Clear Cut Base Auto", number=None, rookie=False, tier="MONSTER", odds="Checklist segment odds vary", source="https://www.beckett.com/news/2025-26-upper-deck-clear-cut-hockey-cards/"),
    dict(slug="cc-2025-26-clear-cut-hobby", key="hockey:2025-26:clear-cut:mario-lemieux:spx-starscape-auto", player="Mario Lemieux", card="SPx Starscape Auto", number=None, rookie=False, tier="JACKPOT", odds="Starscape 1:60 packs; player SSP", source="https://www.beckett.com/news/2025-26-upper-deck-clear-cut-hockey-cards/"),
    dict(slug="cc-2025-26-clear-cut-hobby", key="hockey:2025-26:clear-cut:bobby-orr:spx-starscape-auto", player="Bobby Orr", card="SPx Starscape Auto", number=None, rookie=False, tier="JACKPOT", odds="Starscape 1:60 packs; player SSP", source="https://www.beckett.com/news/2025-26-upper-deck-clear-cut-hockey-cards/"),
]

def seed_chase_card_db():
    db=SessionLocal()
    try:
        for x in CHASE_CARD_DB:
            product=db.scalar(select(Product).where(Product.slug==x["slug"]))
            if not product: continue
            variant=db.scalar(select(ProductVariant).where(ProductVariant.product_id==product.id))
            if not variant: continue
            card=db.scalar(select(ChaseCard).where(ChaseCard.canonical_key==x["key"]))
            if card is None:
                card=ChaseCard(canonical_key=x["key"],player_name=x["player"],card_name=x["card"],
                    card_number=x["number"],category=product.category,rookie=x["rookie"])
                db.add(card); db.flush()
            link=db.scalar(select(VariantChaseCard).where(
                VariantChaseCard.variant_id==variant.id,
                VariantChaseCard.chase_card_id==card.id
            ))
            if link is None:
                db.add(VariantChaseCard(variant_id=variant.id,chase_card_id=card.id,tier=x["tier"],
                    odds_text=x["odds"],source_url=x["source"],confidence=95))
        db.commit()
    finally:
        db.close()

def seed_chase_profiles():
    db=SessionLocal()
    try:
        for slug,data in CHASE_PROFILES.items():
            product=db.scalar(select(Product).where(Product.slug==slug))
            if not product: continue
            variant=db.scalar(select(ProductVariant).where(ProductVariant.product_id==product.id))
            if not variant: continue
            row=db.scalar(select(ChaseProfile).where(ChaseProfile.variant_id==variant.id))
            if row is None:
                row=ChaseProfile(variant_id=variant.id)
                db.add(row)
            row.content_json=json.dumps({k:v for k,v in data.items() if k not in ("source_name","source_url")},ensure_ascii=False)
            row.source_name=data["source_name"]
            row.source_url=data["source_url"]
            row.verified_at=REAL_SNAPSHOT_OBSERVED_AT
            row.confidence=95
        db.commit()
    finally:
        db.close()

def seed_demo_data():
    db = SessionLocal()
    try:
        for info in REAL_STORES:
            if not db.scalar(select(Store.id).where(Store.name == info["name"])):
                db.add(Store(country="SE", active=True, min_interval_seconds=120, **info))
        db.flush()
        demo = db.scalar(select(Store).where(Store.name == "Demo · ej verifierad butik"))
        if not demo:
            demo = Store(name="Demo · ej verifierad butik", country="SE", collection_method="demo", adapter_key="manual", policy_status="manual_allowed", active=True)
            db.add(demo); db.flush()
        # Always ensure the starter/test catalog exists. Earlier versions only seeded
        # it when the entire product table was empty, which meant upgraded local DBs
        # could end up with no usable discovery suggestions at all.
        for idx, row in enumerate(SEED, start=1):
            name, category, manufacturer, year, series, fmt, price, a = row
            slug=f"demo-{idx}"
            p = db.scalar(select(Product).where(Product.slug == slug))
            if p is None:
                p = Product(slug=slug, canonical_name=name, category=category, manufacturer=manufacturer, year_season=year, series=series)
                db.add(p); db.flush()
            v = db.scalar(select(ProductVariant).where(ProductVariant.product_id == p.id, ProductVariant.format == fmt))
            if v is None:
                v = ProductVariant(product_id=p.id, format=fmt, packs=12 if idx==1 else (20 if idx==2 else 6), cards_per_pack=12 if idx==1 else (4 if idx==2 else 10))
                db.add(v); db.flush()
            offer = db.scalar(select(Offer).where(Offer.store_id == demo.id, Offer.external_id == f"demo-{idx}"))
            if offer is None:
                offer = Offer(store_id=demo.id, variant_id=v.id, external_id=f"demo-{idx}", source_title=f"{name} {fmt}", price_sek=price, stock_status="in_stock", source_kind="demo", source_confidence=0, match_confidence=1.0, match_status="demo")
                db.add(offer); db.flush()
                db.add(PriceHistory(offer_id=offer.id, price_sek=price, stock_status="in_stock"))
            if v.analysis is None:
                db.add(BoxAnalysis(variant_id=v.id, ev_low=a[0], ev_high=a[1], checklist_strength=a[2], hit_density=a[3], upside=a[4], floor_score=a[5], rookie_strength=a[6], liquidity=a[7], popularity=a[8], data_quality=a[9], risk=a[10], probability_basis="demo", reasons_json=json.dumps(["Demoanalys – ska ersättas av verifierad checklist-, odds- och marknadsdata."])))
        db.commit()
    finally:
        db.close()
