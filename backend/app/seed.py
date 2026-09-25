import copy
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
    dict(name="Cardland", homepage_url="https://www.cardland.se/", source_url="https://www.cardland.se/", collection_method="manual", adapter_key="manual", policy_status="review_required"),
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
    dict(name="DrakenDavids", homepage_url="https://www.drakendavids.se/", source_url="https://www.drakendavids.se/collections/alla-samlarkort-tillbehor", collection_method="manual", adapter_key="manual", policy_status="review_required"),
    dict(name="CardSurfer", homepage_url="https://cardsurferbreak.com/", source_url="https://cardsurferbreak.com/", collection_method="manual", adapter_key="manual", policy_status="review_required"),
    dict(name="Poketalk", homepage_url=None, source_url=None, collection_method="manual", adapter_key="manual", policy_status="review_required"),
    dict(name="Samlartorget", homepage_url=None, source_url=None, collection_method="manual", adapter_key="manual", policy_status="review_required"),
    dict(name="EllieCollectables", homepage_url="https://elliecollectables.se/", source_url="https://elliecollectables.se/", collection_method="manual", adapter_key="manual", policy_status="review_required"),
    dict(name="MaxGaming", homepage_url="https://www.maxgaming.se/", source_url="https://www.maxgaming.se/sv/hem-fritid/samlarkortsspel", collection_method="manual", adapter_key="manual", policy_status="review_required"),
    dict(name="Arcade Dreams", homepage_url="https://arcadedreams.se/", source_url="https://arcadedreams.se/shop/tcg", collection_method="manual", adapter_key="manual", policy_status="review_required"),
    dict(name="Spelexperten", homepage_url="https://www.spelexperten.com/", source_url="https://www.spelexperten.com/sallskapsspel/pokemon/", collection_method="manual", adapter_key="manual", policy_status="review_required"),
    dict(name="Mana Land", homepage_url="https://manaland.se/", source_url="https://manaland.se/", collection_method="manual", adapter_key="manual", policy_status="review_required"),
    dict(name="Playoteket", homepage_url="https://playoteket.com/", source_url="https://playoteket.com/80-pokemon", collection_method="manual", adapter_key="manual", policy_status="review_required"),
    dict(name="Amazon.se", homepage_url="https://www.amazon.se/", source_url="https://www.amazon.se/", collection_method="manual", adapter_key="manual", policy_status="review_required"),
    dict(name="Kantovault", homepage_url="https://kantovault.se/", source_url="https://kantovault.se/collections/japanska-one-piece-booster-pack", collection_method="manual", adapter_key="manual", policy_status="review_required"),
]



REAL_SNAPSHOT_OBSERVED_AT = datetime(2026, 9, 12, 19, 30, 0)
REAL_EXPANSION_OBSERVED_AT = datetime(2026, 9, 24, 12, 0, 0)

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
         facts=["10 kort per box", "1 autograf per box i snitt", "2 base-paralleller per box i snitt", "3 Rookies I-IV per box i snitt"]),
    dict(slug="cc-2026-topps-mls-chrome-value", name="2026 Topps Major League Soccer Chrome Value Box", category="Fotboll", manufacturer="Topps", year="2026", series="MLS Chrome", fmt="value box", sku="FGC007106", price=379, packs=7, cards=4, stock="in_stock",
         facts=["7 pack per box", "4 kort per pack"]),
    dict(slug="cc-2025-26-panini-prizm-fifa-choice", name="2025-26 Panini Prizm FIFA Soccer Choice", category="Fotboll", manufacturer="Panini", year="2025-26", series="Prizm FIFA", fmt="choice box", sku="PAN7891", price=2799, packs=1, cards=8, stock="in_stock",
         facts=["8 kort per box", "1 autograf per box i snitt", "3 numrerade Choice Prizms per box i snitt", "3 ytterligare Choice Prizms per box i snitt"]),
    dict(slug="cc-2026-futera-world-football-fx3", name="2026 Futera World Football FX Series 3", category="Fotboll", manufacturer="Futera", year="2026", series="World Football FX Series 3", fmt="hobby box", sku="FUT-FXs3-10", price=1499, packs=10, cards=5, stock="in_stock",
         facts=["10 pack per box", "upp till 5 kort per pack", "2 numrerade paralleller per box i snitt", "1 autograf, memorabilia eller numrerat rare insert per box i snitt"]),
    dict(slug="cc-2026-topps-argentina-team-set", name="2026 Topps Argentina Team Set", category="Fotboll", manufacturer="Topps", year="2026", series="Argentina Team Set", fmt="team set box", sku="FGC007078", price=999, packs=6, cards=5, stock="in_stock",
         facts=["6 pack per box", "5 kort per pack"]),
    dict(slug="cc-2026-topps-chrome-premier-league-hobby", name="2026 Topps Chrome Premier League Soccer Hobby", category="Fotboll", manufacturer="Topps", year="2026", series="Chrome Premier League", fmt="hobby box", sku="FGC007019-20", price=3699, packs=20, cards=4, stock="in_stock",
         facts=["20 pack per box", "4 kort per pack"]),
    dict(slug="cc-2026-topps-finest-premier-league-wave2", name="2026 Topps Finest Premier League Soccer Hobby Wave 2", category="Fotboll", manufacturer="Topps", year="2026", series="Finest Premier League", fmt="hobby box", sku="FS0006415_06", price=5999, packs=6, cards=10, stock="in_stock",
         facts=["6 pack per box", "10 kort per pack"]),
    dict(slug="cc-2025-26-panini-prizm-fifa-retail", name="2025-26 Panini Prizm FIFA Soccer Retail", category="Fotboll", manufacturer="Panini", year="2025-26", series="Prizm FIFA", fmt="retail box", sku="PAN7900-24", price=1299, packs=24, cards=4, stock="in_stock",
         facts=["24 pack per box", "4 kort per pack", "1 numrerad Pulsar per box i snitt", "Red Pulsar Autograph i varannan box i snitt"]),
    dict(slug="cc-2025-26-topps-chrome-arsenal-hobby", name="2025-26 Topps Chrome Arsenal Soccer Hobby", category="Fotboll", manufacturer="Topps", year="2025-26", series="Chrome Arsenal", fmt="hobby box", sku="FS0006485-16", price=4499, packs=16, cards=4, stock="in_stock",
         facts=["16 pack per box", "4 kort per pack"]),
    dict(slug="cc-2025-26-topps-bayern-lineage", name="2025-26 Topps FC Bayern München Lineage Hobby", category="Fotboll", manufacturer="Topps", year="2025-26", series="FC Bayern Lineage", fmt="hobby box", sku="FS0006413", price=6499, packs=1, cards=7, stock="in_stock",
         facts=["1 pack per box", "7 kort per pack", "3 encased Autograph, Autograph Relics eller Relics per box"]),
    dict(slug="cc-2025-26-topps-real-madrid-team-set", name="2025-26 Topps Real Madrid Team Set", category="Fotboll", manufacturer="Topps", year="2025-26", series="Real Madrid Team Set", fmt="team set box", sku="FS0006419", price=1299, packs=6, cards=5, stock="in_stock",
         facts=["6 pack per box", "5 kort per pack"]),
    dict(slug="cc-2025-26-topps-ucc-flagship-hanger", name="2025-26 Topps UCC Flagship Hanger Box", category="Fotboll", manufacturer="Topps", year="2025-26", series="UCC Flagship", fmt="hanger", sku="52022", price=178, packs=1, cards=35, stock="in_stock", store_name="Cardland", buy_url="https://www.cardland.se/fotboll/2025-26-topps-ucc-flagship-hanger-box", observed_at=REAL_EXPANSION_OBSERVED_AT,
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

REAL_ENTERTAINMENT_SNAPSHOT = [
    dict(slug="cc-one-piece-op13-jp-display", name="One Piece Carrying on His Will OP-13 Japanese Booster Display", category="One Piece", manufacturer="Bandai", year="2025", series="Carrying on His Will OP-13", fmt="booster box", sku="OPCG-OP-13-24-JPN", price=2299, packs=24, cards=6, stock="in_stock",
         facts=["24 japanska boosterpaket", "6 kort per pack", "WANTED Edition med Gol.D.Roger, Luffy, Ace och Sabo finns i setet", "officiella packodds är inte publicerade"]),
    dict(slug="cc-2025-topps-marvel-studios-chrome-hobby", name="2025 Topps Marvel Studios Chrome Hobby", category="Marvel", manufacturer="Topps", year="2025", series="Marvel Studios Chrome", fmt="hobby box", sku="FGC006444_10", price=3499, packs=10, cards=8, stock="in_stock",
         facts=["10 hobby-pack", "8 kort per pack", "Single Autographs 1:25 hobby-pack", "Standard Sketch Card Silver Foil 1:143 hobby-pack"]),
    dict(slug="cc-2026-topps-disney-chrome-value", name="2026 Topps Chrome Disney Value Box", category="Disney", manufacturer="Topps", year="2026", series="Chrome Disney", fmt="value box", sku="FGC006789", price=599, packs=8, cards=4, stock="in_stock",
         facts=["8 value-pack", "4 kort per pack", "2 exklusiva Raywave-paralleller per box", "Authentic Autographs 1:2 261 value-pack"]),
]

# Current sealed products and loose packs found on Coolcard's product pages.
# Prices and stock are snapshots; links go straight to the individual listing.
REAL_NONSPORT_EXPANSION = [
    dict(slug="cc-pokemon-black-bolt-jp-display", name="Pokémon Black Bolt sv11B Booster Box Japanese", category="Pokémon", manufacturer="Pokémon Company Japan", year="2025", series="Black Bolt sv11B", fmt="booster box", sku="POKsv11B-30", price=2299, packs=20, cards=7, stock="in_stock", language="Japanese", facts=["20 japanska boosterpaket", "7 kort per paket", "Black Bolt-set; enskilda pull odds publiceras inte av Pokémon"], buy_url="https://www.coolcard.se/en/product/pokmon-black-bolt-sv11b-booster-box-30-paket-japanese"),
    dict(slug="cc-pokemon-black-bolt-jp-pack", name="Pokémon Black Bolt sv11B Booster Pack Japanese", category="Pokémon", manufacturer="Pokémon Company Japan", year="2025", series="Black Bolt sv11B", fmt="single pack", sku="POKsv11B-1", price=129, packs=1, cards=7, stock="in_stock", language="Japanese", facts=["7 japanska kort per paket", "Black Bolt-set; enskilda pull odds publiceras inte av Pokémon"], buy_url="https://www.coolcard.se/en/product/pokmon-black-bolt-sv11b-booster-pack-5-cards-japanese"),
    dict(slug="cc-pokemon-nihil-zero-jp-display", name="Pokémon Mega Nihil Zero M3 Booster Display Japanese", category="Pokémon", manufacturer="Pokémon Company Japan", year="2026", series="Mega Nihil Zero M3", fmt="booster box", sku="POKM3-30", price=999, packs=30, cards=5, stock="in_stock", language="Japanese", facts=["30 japanska boosterpaket", "5 kort per paket", "Exakta kortodds är inte publicerade"], buy_url="https://www.coolcard.se/en/product/pokmon-mega-nihil-zero-m3-booster-display-30-packs-japanese"),
    dict(slug="cc-pokemon-nihil-zero-jp-pack", name="Pokémon Mega Nihil Zero M3 Booster Pack Japanese", category="Pokémon", manufacturer="Pokémon Company Japan", year="2026", series="Mega Nihil Zero M3", fmt="single pack", sku="POKM3-01", price=39, packs=1, cards=5, stock="in_stock", language="Japanese", facts=["5 japanska kort per paket", "Exakta kortodds är inte publicerade"], buy_url="https://www.coolcard.se/en/product/pokmon-mega-nihil-zero-m3-booster-5-card-japanese"),
    dict(slug="cc-one-piece-op15-jp-pack", name="One Piece Adventure on KAMI's Island OP-15 Booster Japanese", category="One Piece", manufacturer="Bandai", year="2026", series="Adventure on KAMI's Island OP-15", fmt="single pack", sku="OPCG-OP-15-01-JPN", price=59, packs=1, cards=6, stock="in_stock", language="Japanese", facts=["6 japanska kort per paket", "Setets toppspår omfattar Secret Rare Luffy och Enel samt Enel Super Alternate Art", "Individuella pack odds saknas"], buy_url="https://www.coolcard.se/en/product/one-piece-card-game-booster-6-cards-adventure-on-kamis-island-op-15-japanese"),
    dict(slug="cc-one-piece-op15-jp-display", name="One Piece Adventure on KAMI's Island OP-15 Booster Display Japanese", category="One Piece", manufacturer="Bandai", year="2026", series="Adventure on KAMI's Island OP-15", fmt="booster box", sku="OPCG-OP-15-24-JPN", price=1199, packs=24, cards=6, stock="in_stock", language="Japanese", buy_url="https://www.coolcard.se/en/product/one-piece-card-game-booster-display-24-boosters-adventure-on-kamis-island-op-15-japanese"),
    dict(slug="cc-one-piece-eb04-jp-pack", name="One Piece Egghead Crisis EB-04 Booster Japanese", category="One Piece", manufacturer="Bandai", year="2026", series="Egghead Crisis EB-04", fmt="single pack", sku="OPCG-EB-04-01-JPN", price=69, packs=1, cards=6, stock="in_stock", language="Japanese", facts=["6 japanska kort per paket", "Egghead Crisis-set; officiella kortspecifika pack odds saknas"], buy_url="https://www.coolcard.se/en/product/one-piece-card-game-booster-6-cards-egghead-crisis-eb-04-japanese"),
    dict(slug="cc-one-piece-eb04-jp-display", name="One Piece Egghead Crisis EB-04 Booster Display Japanese", category="One Piece", manufacturer="Bandai", year="2026", series="Egghead Crisis EB-04", fmt="booster box", sku="OPCG-EB-04-24-JPN", price=1399, packs=24, cards=6, stock="in_stock", language="Japanese", facts=["24 japanska boosterpaket", "6 kort per paket", "Officiella kortspecifika pack odds saknas"], buy_url="https://www.coolcard.se/en/product/one-piece-card-game-booster-display-24-boosters-egghead-crisis-eb-04-japanese"),
    dict(slug="cc-marvel-2026-chrome-hobby-pack", name="2026 Topps Marvel Comics Chrome Hobby Pack", category="Marvel", manufacturer="Topps", year="2026", series="Marvel Comics Chrome", fmt="single pack", sku="FGC006774-01", price=479, packs=1, cards=6, stock="in_stock", facts=["6 kort per hobby-paket", "Checklistan omfattar numrerade paralleller, case-hit inserts, skisser, autografer och reliker", "Individuella pack odds anges inte på butikssidan"], buy_url="https://www.coolcard.se/product/1st-paket-2026-topps-marvel-comics-hobby"),
    dict(slug="cc-marvel-2025-deadpool-value", name="2025 Topps Chrome Marvel Deadpool Value Box", category="Marvel", manufacturer="Topps", year="2025", series="Marvel Deadpool Chrome", fmt="value box", sku="FGC006436", price=479, packs=7, cards=4, stock="in_stock", facts=["7 paket, 4 kort per paket", "Produktbeskrivningen nämner autografer, skisser och case hits", "Exakta odds för value-formatet saknas"], buy_url="https://www.coolcard.se/en/product/sealed-value-box-2025-topps-chrome-marvel-deadpool"),
    dict(slug="cc-marvel-2026-mint-hobby", name="2026 Topps Marvel MINT Hobby Box", category="Marvel", manufacturer="Topps", year="2026", series="Marvel MINT", fmt="hobby box", sku="FGC007425", price=6299, packs=1, cards=10, stock="in_stock", facts=["1 paket med 10 kort och 1 encased card per box", "Marvel premiumformat; specifika kortodds saknas"], buy_url="https://www.coolcard.se/en/product/sealed-box-2026-topps-marvel-mint-hobby"),
    dict(slug="cc-lorcana-archazias-display", name="Disney Lorcana Archazia's Island Booster Display", category="Disney", manufacturer="Ravensburger", year="2026", series="Archazia's Island", fmt="booster box", sku="Lorcana-Set7-Display", price=1449, packs=24, cards=12, stock="in_stock", facts=["24 paket per display, 12 kort per paket", "2 Rare/Super Rare/Legendary och 1 foil av valfri rarity per paket", "Lorcana anger inga garanterade pull rates per display"], buy_url="https://www.coolcard.se/en/product/lorcana-archazias-island-display-24-boosters-2"),
    dict(slug="cc-lorcana-archazias-trove", name="Disney Lorcana Archazia's Island Illumineer's Trove", category="Disney", manufacturer="Ravensburger", year="2026", series="Archazia's Island", fmt="collection box", sku="Lorcana-Set7-Trove", price=699, packs=8, cards=12, stock="in_stock", facts=["8 boosterpaket plus förvaringslåda och tillbehör", "Enskilda Disney-karaktärer/kort är inte garanterade"], buy_url="https://www.coolcard.se/en/product/lorcana-archazias-island-illumineers-trove-2"),
    dict(slug="cc-lorcana-azurite-pack", name="Disney Lorcana Azurite Sea Booster Pack", category="Disney", manufacturer="Ravensburger", year="2024", series="Azurite Sea", fmt="single pack", sku="Lorcana-Set6-Booster", price=79, packs=1, cards=12, stock="in_stock", facts=["12 kort: 6 common, 3 uncommon, 2 rare eller högre och 1 foil med slumpad rarity"], buy_url="https://www.coolcard.se/en/product/lorcana-azurite-sea-booster-4"),
    dict(slug="cc-mtg-marvel-superheroes-play-display", name="Magic Marvel Super Heroes Play Booster Display", category="Magic", manufacturer="Wizards of the Coast", year="2026", series="Marvel Super Heroes", fmt="booster box", sku="MAGD5356-30", price=1899, packs=30, cards=14, stock="in_stock", facts=["30 Play Boosters, 14 kort per paket", "Marvel crossover-set; exakta chase-korts odds inte publicerade på butikssidan"], buy_url="https://www.coolcard.se/en/product/magic-the-gatheringmarvel-super-heroes-play-booster-display-2"),
    dict(slug="cc-mtg-marvel-superheroes-jumpstart-display", name="Magic Marvel Super Heroes Jumpstart Booster Display", category="Magic", manufacturer="Wizards of the Coast", year="2026", series="Marvel Super Heroes Jumpstart", fmt="booster box", sku="MAGD5363-24", price=1499, packs=24, cards=20, stock="in_stock", facts=["24 Jumpstart Boosters, 20 kort per paket", "Kortpaketen kombineras för spel; individuella chase odds inte publicerade"], buy_url="https://www.coolcard.se/en/product/magic-the-gatheringmarvel-super-heroes-jumpstart-booster-display-2"),
    dict(slug="cc-pokemon-ninja-spinner-m4-display", name="Pokémon Mega: Ninja Spinner M4 Booster Display Japanese", category="Pokémon", manufacturer="Pokémon Company Japan", year="2026", series="Ninja Spinner M4", fmt="booster box", sku="POKM4-30", price=1299, packs=30, cards=5, stock="in_stock", language="Japanese", facts=["30 japanska boosterpaket, 5 kort per paket", "Checklistan innehåller Mega Greninja ex MUR #120/083 och flera SAR/AR", "Officiella kortspecifika packodds publiceras inte"], buy_url="https://www.coolcard.se/product/pokmon-mega-ninja-spinner-m4-booster-display-30-paket-japansk"),
    dict(slug="cc-pokemon-ninja-spinner-m4-pack", name="Pokémon Mega: Ninja Spinner M4 Booster Pack Japanese", category="Pokémon", manufacturer="Pokémon Company Japan", year="2026", series="Ninja Spinner M4", fmt="single pack", sku="POKM4-01", price=49, packs=1, cards=5, stock="in_stock", language="Japanese", facts=["5 japanska kort per paket", "Mega Greninja ex MUR finns i setets checklist", "En enstaka pack har inga publicerade kortspecifika odds"], buy_url="https://www.coolcard.se/en/product/pokmon-mega-ninja-spinner-m4-booster-5-kort-japanese"),
    dict(slug="cc-pokemon-storm-emeralda-m6-display", name="Pokémon Mega: Storm Emeralda M6 Booster Display Japanese", category="Pokémon", manufacturer="Pokémon Company Japan", year="2026", series="Storm Emeralda M6", fmt="booster box", sku="POKM6-30", price=1499, packs=30, cards=5, stock="in_stock", language="Japanese", facts=["30 japanska boosterpaket, 5 kort per paket", "Checklistan innehåller Mega Rayquaza ex MUR #113/076 och flera SAR/AR", "Officiella kortspecifika packodds publiceras inte"], buy_url="https://www.coolcard.se/product/pokmon-mega-storm-emeralda-m6-booster-display-30-paket-japansk"),
    dict(slug="cc-pokemon-storm-emeralda-m6-pack", name="Pokémon Mega: Storm Emeralda M6 Booster Pack Japanese", category="Pokémon", manufacturer="Pokémon Company Japan", year="2026", series="Storm Emeralda M6", fmt="single pack", sku="POKM6-01", price=79, packs=1, cards=5, stock="in_stock", language="Japanese", facts=["5 japanska kort per paket", "Mega Rayquaza ex MUR finns i setets checklist", "En enstaka pack har inga publicerade kortspecifika odds"], buy_url="https://www.coolcard.se/en/product/pokmon-mega-storm-emeralda-m6-booster-5-cards-japanese"),
    dict(slug="cc-one-piece-op14-jp-pack", name="One Piece The Azure Sea's Seven OP-14 Booster Pack Japanese", category="One Piece", manufacturer="Bandai", year="2026", series="The Azure Sea's Seven OP-14", fmt="single pack", sku="OPCG-OP-14-01-JPN", price=79, packs=1, cards=6, stock="in_stock", language="Japanese", facts=["6 japanska kort per paket", "Officiell kortlista innehåller bland annat Boa Hancock OP14-112 och flera SP-varianter", "Bandai publicerar inte kortspecifika packodds"], buy_url="https://www.coolcard.se/product/one-piece-card-game-booster-6-kort-the-azure-seas-seven-op-14-japansk"),
    dict(slug="cc-one-piece-op14-jp-display", name="One Piece The Azure Sea's Seven OP-14 Booster Display Japanese", category="One Piece", manufacturer="Bandai", year="2026", series="The Azure Sea's Seven OP-14", fmt="booster box", sku="OPCG-OP-14-24-JPN", price=1699, packs=24, cards=6, stock="in_stock", language="Japanese", facts=["24 japanska boosterpaket, 6 kort per paket", "Officiell kortlista innehåller bland annat Boa Hancock OP14-112 och flera SP-varianter", "Bandai publicerar inte kortspecifika packodds"], buy_url="https://www.coolcard.se/en/product/one-piece-card-game-booster-display-24-boosters-the-azure-seas-seven-op-14-japanese"),
    dict(slug="cc-one-piece-op16-jp-pack", name="One Piece The Time of Battle OP-16 Booster Pack Japanese", category="One Piece", manufacturer="Bandai", year="2026", series="The Time of Battle OP-16", fmt="single pack", sku="OPCG-OP-16-01-JPN", price=79, packs=1, cards=6, stock="in_stock", language="Japanese", facts=["6 japanska kort per paket", "Marineford/Paramount War-tema; setet innehåller Ace, Luffy, Buggy, Sengoku, Yamato och Teach", "Bandai publicerar inte kortspecifika packodds"], buy_url="https://www.coolcard.se/product/one-piece-card-game-booster-6-kort-the-time-of-battle-op-16-japansk"),
    dict(slug="cc-one-piece-op16-jp-display", name="One Piece The Time of Battle OP-16 Booster Display Japanese", category="One Piece", manufacturer="Bandai", year="2026", series="The Time of Battle OP-16", fmt="booster box", sku="OPCG-OP-16-24-JPN", price=1599, packs=24, cards=6, stock="in_stock", language="Japanese", facts=["24 japanska boosterpaket, 6 kort per paket", "Marineford/Paramount War-tema med sex officiellt namngivna leaders", "Bandai publicerar inte kortspecifika packodds"], buy_url="https://www.coolcard.se/en/product/one-piece-card-game-booster-display-24-boosters-the-time-of-battle-op-16-japanese"),
]

# Cross-category expansion verified against individual Coolcard listings on 2026-09-24.
# A product may be searchable without being rankable until its chase profile is verified.
REAL_CROSS_CATEGORY_EXPANSION = [
    dict(slug="cc-2025-26-topps-chrome-update-basketball-pack", name="2025-26 Topps Chrome Update Series Basketball NBA Hobby Pack", category="Basket", manufacturer="Topps", year="2025-26", series="Chrome Update Basketball", fmt="single pack", sku="FGC006720-01", price=599, packs=1, cards=4, stock="in_stock", facts=["4 kort per hobby-pack", "Rookie Debut Patch Autographs 1/1 kan dras", "Rookies inkluderar Cooper Flagg, Kon Knueppel och Dylan Harper", "Exakt packodds för ett visst kort är inte publicerat"], buy_url="https://www.coolcard.se/en/product/1st-paket-2025-26-topps-chrome-updates-update-series-basketball-nba-hobby-2"),
    dict(slug="cc-2025-26-topps-nba-hoops-hobby-pack", name="2025-26 Topps NBA Hoops Basketball Hobby Pack", category="Basket", manufacturer="Topps", year="2025-26", series="NBA Hoops", fmt="single pack", sku="FGC006698-01", price=229, packs=1, cards=8, stock="in_stock", facts=["8 kort per hobby-pack", "Hobbyboxen innehåller 1 autograf; ett löst pack garanterar inte autograf", "Case hits omfattar Oasis, Joy, Checkmate och Hoopnotic"], buy_url="https://www.coolcard.se/en/product/1-pack-2025-26-topps-nba-hoops-basketball-hobby"),
    dict(slug="cc-2026-topps-baseball-series2-pack", name="2026 Topps Baseball MLB Series 2 Hobby Pack", category="Baseboll", manufacturer="Topps", year="2026", series="Topps Baseball Series 2", fmt="single pack", sku="FGC006599-01", price=99, packs=1, cards=12, stock="in_stock", facts=["12 kort per hobby-pack", "350-kortsbas med rookies, stjärnor och Future Stars", "Autografer, reliker, Heavy Lumber och Home Field finns i produkten", "Löst pack saknar garanterad hit"], buy_url="https://www.coolcard.se/en/product/1-pack-2026-topps-baseball-series-2-hobby-12-cards"),
    dict(slug="cc-2026-topps-baseball-series2-hobby", name="2026 Topps Baseball MLB Series 2 Hobby Box", category="Baseboll", manufacturer="Topps", year="2026", series="Topps Baseball Series 2", fmt="hobby box", sku="FGC006599-20", price=1699, packs=20, cards=12, stock="in_stock", facts=["20 hobby-pack, 12 kort per pack", "1 autograf eller relic per box", "1 promo-pack per box", "350-kortsbas med rookies, stjärnor och Future Stars"], buy_url="https://www.coolcard.se/product/hel-box-2026-topps-baseball-series-2-hobby-20-paket"),
    dict(slug="cc-2026-topps-chrome-baseball-value", name="2026 Topps Chrome Baseball MLB Value Box", category="Baseboll", manufacturer="Topps", year="2026", series="Topps Chrome Baseball", fmt="value box", sku="PKG017717", price=449, packs=7, cards=4, stock="in_stock", facts=["7 pack, 4 kort per pack", "Retail Rookie Autographs och numrerade Raywave-paralleller finns", "Case hits omfattar Ultraviolet, Helix och Static Noise", "Ingen autograf är garanterad"], buy_url="https://www.coolcard.se/product/hel-value-box-2026-topps-chrome-mlb-7-paket"),
    dict(slug="cc-2026-topps-flagship-nfl-pack", name="2026 Topps Flagship NFL Football Hobby Pack", category="NFL", manufacturer="Topps", year="2026", series="Topps Flagship Football", fmt="single pack", sku="FGC006854-01", price=119, packs=1, cards=12, stock="in_stock", facts=["12 kort per hobby-pack", "Rookies inkluderar Fernando Mendoza, Jeremiyah Love och Carnell Tate", "Autografer, relics, SSP och numrerade paralleller finns", "Löst pack saknar garanterad hit"], buy_url="https://www.coolcard.se/en/product/1-pack-2026-topps-flagship-nfl-football-hobby"),
    dict(slug="cc-2025-panini-score-a-treat-nfl", name="2025 Panini Score Football NFL Score-A-Treat Bundle", category="NFL", manufacturer="Panini", year="2025", series="Score-A-Treat", fmt="bundle", sku="PAN-score-a-treat-40", price=299, packs=40, cards=3, stock="in_stock", facts=["40 småpaket, 3 kort per pack", "120 kort totalt", "Halloweenformat med låg styckkostnad", "Premiumautograf eller memorabilia är inte verifierad som boxgaranti"], buy_url="https://www.coolcard.se/product/hel-bundle-2025-panini-score-football-score-a-treat-40-paket"),
    dict(slug="cc-2026-topps-universe-wwe-pack", name="2026 Topps Universe WWE Wrestling Hobby Pack", category="WWE", manufacturer="Topps", year="2026", series="Topps Universe WWE", fmt="single pack", sku="FGC007161-01", price=229, packs=1, cards=12, stock="in_stock", facts=["12 kort per hobby-pack", "Hobbyboxen innehåller 2 autografer och 1 relic; löst pack garanterar ingen hit", "Numrerade paralleller, short prints, autograph relics och matchanvänt material finns"], buy_url="https://www.coolcard.se/en/product/1-pack-2026-topps-universe-wwe-wrestling-hobby-12-cards"),
    dict(slug="cc-2026-topps-chrome-ufc-pack", name="2026 Topps Chrome UFC Fighting Hobby Pack", category="UFC", manufacturer="Topps", year="2026", series="Topps Chrome UFC", fmt="single pack", sku="FGC007129-01", price=229, packs=1, cards=8, stock="in_stock", facts=["8 kort: 6 base, minst 1 onumrerad parallel och 1 insert", "Hobbyboxen innehåller 2 autografer och 4 numrerade paralleller", "Case-hit-spår inkluderar Kings & Queens, Immortal Force och Radiating Rookies"], buy_url="https://www.coolcard.se/en/product/1-pack-2026-topps-chrome-ufc-hobby"),
    dict(slug="cc-2026-fleer-ultra-golf-pack", name="2026 Upper Deck Fleer Ultra Golf Hobby Pack", category="Golf", manufacturer="Upper Deck", year="2026", series="Fleer Ultra Golf", fmt="single pack", sku="UD00110", price=129, packs=1, cards=8, stock="in_stock", facts=["8 kort per hobby-pack", "Rookieautograf 1:60 pack och veteranautograf 1:150 pack", "Hole in One och Thunderclap 1:188 pack", "Medallions 1:4 pack"], buy_url="https://www.coolcard.se/en/product/1-pack-2026-upper-deck-fleer-ultra-golf-hobby"),
    dict(slug="cc-2026-wrc-retail-pack", name="2026 FIA World Rally Championship Retail Pack", category="Racing", manufacturer="Topps", year="2026", series="FIA WRC", fmt="single pack", sku="FWR-P03816-01", price=39, packs=1, cards=6, stock="in_stock", facts=["6 kort per retail-pack", "Låg ingångskostnad", "Kortspecifik checklist- och oddsprofil återstår att verifiera"], buy_url="https://www.coolcard.se/en/product/1-pack-2026-fia-world-rally-championships-wrc-retail"),
    dict(slug="cc-star-wars-unlimited-shadows-pack", name="Star Wars Unlimited Shadows of the Galaxy Booster Pack", category="Star Wars", manufacturer="Fantasy Flight Games", year="2024", series="Shadows of the Galaxy", fmt="single pack", sku="SWU105813-1", price=69, packs=1, cards=16, stock="in_stock", facts=["16 kort: 9 common, 3 uncommon, 1 rare/legendary, 1 leader, 1 base/token och 1 foil", "Showcase-ledare och hyperspace/foil-varianter är chase-spår", "Ett visst kort eller Showcase är inte garanterat"], buy_url="https://www.coolcard.se/product/star-wars-unlimited-shadows-of-the-galaxy-booster"),
    dict(slug="cc-star-wars-unlimited-shadows-display", name="Star Wars Unlimited Shadows of the Galaxy Booster Display", category="Star Wars", manufacturer="Fantasy Flight Games", year="2024", series="Shadows of the Galaxy", fmt="booster box", sku="SWU105813-24", price=1099, packs=24, cards=16, stock="in_stock", facts=["24 boosterpaket, 16 kort per pack", "Varje pack har rare/legendary-plats och foil-plats", "Showcase-ledare är extremt sällsynta och inte garanterade"], buy_url="https://www.coolcard.se/product/star-wars-unlimited-shadows-of-the-galaxy-booster-display"),
    dict(slug="cc-star-wars-unlimited-twilight-pack", name="Star Wars Unlimited Twilight of the Republic Booster Pack", category="Star Wars", manufacturer="Fantasy Flight Games", year="2024", series="Twilight of the Republic", fmt="single pack", sku="FSWH0301-1", price=69, packs=1, cards=16, stock="in_stock", facts=["16 kort: 9 common, 3 uncommon, 1 rare/legendary, 1 leader, 1 base/token och 1 foil", "Set med över 250 kort och Clone Wars-tema", "Showcase och parallelvariant är inte garanterad"], buy_url="https://www.coolcard.se/product/star-wars-unlimited-twilight-of-the-republic-booster"),
    dict(slug="cc-star-wars-unlimited-twilight-display", name="Star Wars Unlimited Twilight of the Republic Booster Display", category="Star Wars", manufacturer="Fantasy Flight Games", year="2024", series="Twilight of the Republic", fmt="booster box", sku="FSWH0301-24", price=1199, packs=24, cards=16, stock="in_stock", facts=["24 boosterpaket, 16 kort per pack", "Över 250 kort med Clone Wars-karaktärer", "Varje pack har rare/legendary-plats och foil-plats"], buy_url="https://www.coolcard.se/product/star-wars-unlimited-twilight-of-the-republic-booster-display"),
    dict(slug="cc-2026-topps-universe-wwe-value", name="2026 Topps Universe WWE Wrestling Value Box", category="WWE", manufacturer="Topps", year="2026", series="Topps Universe WWE", fmt="value box", sku="FGC007165", price=329, packs=6, cards=6, stock="in_stock", facts=["6 value-pack, 6 kort per pack", "Autografer, relics, numrerade paralleller och short prints kan dras", "Ingen autograf eller relic är garanterad i value-formatet"], buy_url="https://www.coolcard.se/product/hel-value-box-2026-topps-universe-wwe-wrestling-6-paket"),
    dict(slug="cc-2026-topps-universe-wwe-hobby", name="2026 Topps Universe WWE Wrestling Hobby Box", category="WWE", manufacturer="Topps", year="2026", series="Topps Universe WWE", fmt="hobby box", sku="FGC007161-10", price=1899, packs=10, cards=12, stock="in_stock", facts=["10 hobby-pack, 12 kort per pack", "2 autografer och 1 relic per box", "Numrerade paralleller, autograph relics och short prints finns"], buy_url="https://www.coolcard.se/product/hel-box-2026-topps-universe-wwe-wrestling-hobby-10-paket"),
    dict(slug="cc-2026-topps-baseball-series2-value", name="2026 Topps Baseball MLB Series 2 Value Box", category="Baseboll", manufacturer="Topps", year="2026", series="Topps Baseball Series 2", fmt="value box", sku="FGC006608", price=329, packs=6, cards=12, stock="in_stock", facts=["6 value-pack, 12 kort per pack", "Varje pack har 11 base och 1 Stars of MLB/Titans-insert", "Holiday-varianter är value-exklusiva", "Autografer och relics kan dras men är inte garanterade"], buy_url="https://www.coolcard.se/product/hel-value-box-2026-topps-baseball-series-2-6-paket"),
    dict(slug="cc-2026-topps-chrome-ufc-value", name="2026 Topps Chrome UFC Fighting Value Box", category="UFC", manufacturer="Topps", year="2026", series="Topps Chrome UFC", fmt="value box", sku="FGC007136", price=349, packs=6, cards=4, stock="in_stock", facts=["6 value-pack, 4 kort per pack", "2 Base Refractors och 3 UFC Glove Refractors per box", "Autografer och case hits finns men är inte garanterade"], buy_url="https://www.coolcard.se/en/product/sealed-value-box-2026-topps-chrome-ufc"),
    dict(slug="cc-2026-topps-stadium-club-ufc-pack", name="2026 Topps Stadium Club UFC Fighting Hobby Pack", category="UFC", manufacturer="Topps", year="2026", series="Topps Stadium Club UFC", fmt="single pack", sku="FGC007305_01", price=99, packs=1, cards=8, stock="in_stock", facts=["8 kort per hobby-pack", "Hobbyboxen har 2 autografer i snitt; ett löst pack har ingen garanti", "Fight Motion Autos, Dual Autos, Beam Team och Triumvirates finns"], buy_url="https://www.coolcard.se/product/1st-paket-2026-topps-stadium-club-ufc-fighting-hobby"),
    dict(slug="cc-2026-topps-stadium-club-ufc-hobby", name="2026 Topps Stadium Club UFC Fighting Hobby Box", category="UFC", manufacturer="Topps", year="2026", series="Topps Stadium Club UFC", fmt="hobby box", sku="FGC007305_16", price=1399, packs=16, cards=8, stock="in_stock", facts=["16 hobby-pack, 8 kort per pack", "2 autografer per box i snitt", "On-card autos, Gold Minted Chrome, Members Only, Beam Team och Triumvirates finns"], buy_url="https://www.coolcard.se/product/hel-box-2025-26-topps-stadium-club-ufc-fighting-hobby"),
    dict(slug="cc-2025-26-spx-hobby-pack", name="2025-26 Upper Deck SPx Hockey Hobby Pack", category="Hockey", manufacturer="Upper Deck", year="2025-26", series="SPx", fmt="single pack", sku="UD18576", price=199, packs=1, cards=3, stock="in_stock", facts=["3 kort per hobby-pack", "Rookie SuperScripts ligger 1:120 hobby-pack över checklistan", "Rookie Holograms ligger 1:86 hobby-pack", "Ett löst pack har ingen boxgaranti"], buy_url="https://www.coolcard.se/en/product/1-pack-2025-26-upper-deck-spx-hobby"),
    dict(slug="cc-2025-26-spx-hobby", name="2025-26 Upper Deck SPx Hockey Hobby Box", category="Hockey", manufacturer="Upper Deck", year="2025-26", series="SPx", fmt="hobby box", sku="UD18575", price=1395, packs=8, cards=3, stock="in_stock", facts=["8 hobby-pack, 3 kort per pack", "4 base rookies, 3 Silver och 1 Gold parallel per box i snitt", "Rookie Holograms faller cirka 2 per case", "Autografer och 1/1-paralleller finns men är inte boxgaranterade"], buy_url="https://www.coolcard.se/product/hel-box-2025-26-upper-deck-spx-hobby-8-paket"),
    dict(slug="cc-2025-topps-disney-wonder-pack", name="2025 Topps Disney Wonder Hobby Pack", category="Disney", manufacturer="Topps", year="2025", series="Disney Wonder", fmt="single pack", sku="FGC006414-01", price=99, packs=1, cards=6, stock="in_stock", facts=["6 kort per hobby-pack", "Tier 2-kort 1 per pack", "Enchanted Autographs, Princess Sketch Cards och 1/1 PrincessFractors finns", "Ett löst pack garanterar ingen autograf eller sketch"], buy_url="https://www.coolcard.se/product/topps-disney-wonder-hobby-paket-6-kort"),
    dict(slug="cc-2025-topps-chrome-deadpool-hobby", name="2025 Topps Chrome Marvel Deadpool Hobby Box", category="Marvel", manufacturer="Topps", year="2025", series="Marvel Deadpool Chrome", fmt="hobby box", sku="FGC006433-10", price=3699, packs=10, cards=8, stock="in_stock", facts=["10 hobby-pack, 8 kort per pack", "Ryan Reynolds- och Hugh Jackman-autografer finns", "Sketch cards, case hits och SuperFractors 1/1 finns", "Autograf eller sketch är inte uttryckligen boxgaranterad"], buy_url="https://www.coolcard.se/product/hel-box-2025-topps-chrome-marvel-deadpool-hobby"),
]

# Manually verified against the exact Coolcard article pages on 2026-09-24.
# Format facts below are deliberately product-specific; hobby guarantees must
# never leak into retail boxes or loose packs from the same set.
REAL_RESEARCH_OBSERVED_AT = datetime(2026, 9, 24, 20, 51, 0)
REAL_RESEARCH_EXPANSION = [
    dict(slug="cc-2025-26-topps-nba-hoops-value", name="2025-26 Topps NBA Hoops Basketball Value Box", category="Basket", manufacturer="Topps", year="2025-26", series="NBA Hoops", fmt="value box", sku="FGC006700", price=429, packs=7, cards=8, stock="in_stock", observed_at=REAL_RESEARCH_OBSERVED_AT, facts=["7 retail-pack, 8 kort per pack", "Green Hoops-paralleller är exklusiva för Value Box", "Retail-autografer och Block by Block/Boom Shaka Laka case hits kan dras", "Ingen autograf eller case hit är garanterad"], buy_url="https://www.coolcard.se/product/hel-value-box-2025-26-topps-nba-hoops-basketball"),
    dict(slug="cc-2025-26-topps-nba-hoops-hanger", name="2025-26 Topps NBA Hoops Basketball Hanger Box", category="Basket", manufacturer="Topps", year="2025-26", series="NBA Hoops", fmt="hanger", sku="FGC006694", price=329, packs=1, cards=25, stock="in_stock", observed_at=REAL_RESEARCH_OBSERVED_AT, facts=["1 retail-pack med 25 kort", "Orange Hoops-paralleller är exklusiva för Hanger Box", "Retail-autografer och Block by Block/Boom Shaka Laka case hits kan dras", "Ingen autograf eller case hit är garanterad"], buy_url="https://www.coolcard.se/product/hel-hanger-box-2025-26-topps-nba-hoops-basketball-25-kort"),
    dict(slug="cc-2026-topps-flagship-nfl-hobby", name="2026 Topps Flagship NFL Football Hobby Box", category="NFL", manufacturer="Topps", year="2026", series="Topps Flagship Football", fmt="hobby box", sku="FGC006854-20", price=2199, packs=20, cards=12, stock="in_stock", observed_at=REAL_RESEARCH_OBSERVED_AT, facts=["20 hobby-pack, 12 kort per pack", "Aqua Rainbow och numrerade paralleller, autografer, relics och SSP finns", "1957 Rookie Variations, All Kings och Golden Mirror Image Variations finns", "Butikssidan anger ingen garanterad autograf eller relic per box"], buy_url="https://www.coolcard.se/product/hel-box-2026-topps-flagship-nfl-football-hobby"),
    dict(slug="cc-2026-topps-flagship-nfl-mega", name="2026 Topps Flagship NFL Football Mega Box", category="NFL", manufacturer="Topps", year="2026", series="Topps Flagship Football", fmt="mega box", sku="FGC006856", price=699, packs=12, cards=15, stock="in_stock", observed_at=REAL_RESEARCH_OBSERVED_AT, facts=["12 retail-pack, 15 kort per pack", "Aqua Holo, numrerade och 1991 Topps Football Crackle-paralleller finns", "Retailformatet ger 180 kort men butikssidan lovar ingen autograf eller relic", "Hobbyformatets innehåll får inte användas som Mega Box-garanti"], buy_url="https://www.coolcard.se/product/hel-mega-box-2026-topps-flagship-nfl-football"),
    dict(slug="cc-2026-topps-flagship-nfl-fat-pack", name="2026 Topps Flagship NFL Football Fat Pack", category="NFL", manufacturer="Topps", year="2026", series="Topps Flagship Football", fmt="single pack", sku="FGC006850", price=99, packs=1, cards=36, stock="in_stock", observed_at=REAL_RESEARCH_OBSERVED_AT, facts=["36 kort per retail-pack", "Aqua Holo, numrerade paralleller, retail-exklusiva inserts och Team Color Border finns", "Ingen autograf, relic eller SSP är garanterad", "Löst retail-pack ska inte ärva hobbyboxens konfiguration"], buy_url="https://www.coolcard.se/product/1st-fat-pack-2026-topps-flagship-nfl-football"),
    dict(slug="cc-yugioh-phantom-revenge-display", name="Yu-Gi-Oh! Phantom Revenge Booster Display", category="Yu-Gi-Oh", manufacturer="Konami", year="2025", series="Phantom Revenge", fmt="booster box", sku="YGO-PRV-EN-24", price=779, packs=24, cards=7, stock="in_stock", observed_at=REAL_RESEARCH_OBSERVED_AT, facts=["24 engelska boosterpaket, 7 kort per pack", "60-kortsset med 10 Ultra Rare, 10 Super Rare och 40 Rare", "15 kort finns som Collector's Rare och 10 som Starlight Rare", "Konami publicerar rarity-listan men inga kortspecifika packodds"], buy_url="https://www.coolcard.se/product/yu-gi-oh-phantom-revenge-booster-display"),
    dict(slug="cc-2023-panini-chronicles-racing-hobby", name="2023 Panini Chronicles NASCAR Racing Hobby Box", category="Racing", manufacturer="Panini", year="2023", series="Chronicles NASCAR", fmt="hobby box", sku="23-Chr-Rac-H", price=1695, packs=6, cards=8, stock="in_stock", observed_at=REAL_RESEARCH_OBSERVED_AT, facts=["6 hobby-pack, 8 kort per pack", "3 autografer och 1 memorabilia per box i snitt", "2 Immaculate-kort per box", "Checklistan omfattar bland annat Jimmie Johnson, Dale Earnhardt Jr., Jeff Gordon, Chase Elliott och Kyle Busch"], buy_url="https://www.coolcard.se/product/hel-box-2023-panini-chronicles-racing-hobby-nascar"),
]

# Verified against exact Dragon's Lair article pages on 2026-09-25.  The
# repeated Marvel Super Heroes display slug intentionally adds a second store
# offer to the existing product/variant instead of creating a duplicate item.
REAL_STORE_EXPANSION_OBSERVED_AT = datetime(2026, 9, 25, 4, 55, 0)
REAL_STORE_EXPANSION = [
    dict(slug="cc-mtg-marvel-superheroes-play-display", name="Magic Marvel Super Heroes Play Booster Display", category="Magic", manufacturer="Wizards of the Coast", year="2026", series="Marvel Super Heroes", fmt="booster box", sku="165211", price=2099, packs=30, cards=14, stock="in_stock", store_name="Dragons Lair", observed_at=REAL_STORE_EXPANSION_OBSERVED_AT, facts=["30 engelska Play Boosters, 14 kort per paket", "Varje paket innehåller 1–4 rare/mythic och 1 traditional foil", "En non-foil Source Material-träff förekommer i 1 av 24 Play Boosters", "Collector Booster-exklusiva Cosmic Foil-, Gauntlet- och Classic Comic-kort kan inte dras"], buy_url="https://dragonslair.se/en/products/magic-the-gathering-marvel-super-heroes-play-booster-display-30-magic-the-gathering"),
    dict(slug="dl-mtg-marvel-superheroes-play-pack", name="Magic Marvel Super Heroes Play Booster", category="Magic", manufacturer="Wizards of the Coast", year="2026", series="Marvel Super Heroes", fmt="single pack", sku="165210", price=79, packs=1, cards=14, stock="in_stock", store_name="Dragons Lair", observed_at=REAL_STORE_EXPANSION_OBSERVED_AT, facts=["1 engelskt Play Booster med 14 kort", "1–4 rare/mythic och 1 traditional foil per paket", "Source Material-familjen förekommer i 1 av 24 Play Boosters", "Collector Booster-exklusiva toppbehandlingar ingår inte"], buy_url="https://dragonslair.se/en/products/magic-the-gathering-marvel-super-heroes-play-booster-magic-the-gathering"),
    dict(slug="dl-mtg-marvel-superheroes-bundle", name="Magic Marvel Super Heroes Bundle", category="Magic", manufacturer="Wizards of the Coast", year="2026", series="Marvel Super Heroes", fmt="bundle", sku="165215", price=829, packs=9, cards=14, stock="in_stock", store_name="Dragons Lair", observed_at=REAL_STORE_EXPANSION_OBSERVED_AT, facts=["9 engelska Play Boosters med 14 kort vardera", "Traditional foil The Scarlet Witch promo ingår", "30 basic lands, varav 15 foil och 10 full-art city chaos", "Cosmic Foil Mind Stone finns endast i Collector Boosters och är inte möjlig här"], buy_url="https://dragonslair.se/en/products/magic-the-gathering-marvel-super-heroes-bundle-magic-the-gathering"),
    dict(slug="dl-mtg-spiderman-play-pack", name="Magic Marvel's Spider-Man Play Booster", category="Magic", manufacturer="Wizards of the Coast", year="2025", series="Marvel's Spider-Man", fmt="single pack", sku="157246", price=59, packs=1, cards=14, stock="in_stock", store_name="Dragons Lair", observed_at=REAL_STORE_EXPANSION_OBSERVED_AT, facts=["1 engelskt Play Booster med 14 kort", "Minst 1 rare/mythic och 1 traditional foil per paket", "En non-foil Source Material-träff förekommer i 1 av 24 Play Boosters", "Cosmic Foil Soul Stone och Classic Comic-kort finns endast i Collector Boosters"], buy_url="https://dragonslair.se/en/products/marvels-spider-man-play-booster-magic-the-gathering"),
    dict(slug="dl-mtg-spiderman-play-display", name="Magic Marvel's Spider-Man Play Booster Display", category="Magic", manufacturer="Wizards of the Coast", year="2025", series="Marvel's Spider-Man", fmt="booster box", sku="157245", price=1469, packs=30, cards=14, stock="in_stock", store_name="Dragons Lair", observed_at=REAL_STORE_EXPANSION_OBSERVED_AT, facts=["30 engelska Play Boosters, 14 kort per paket", "Minst 1 rare/mythic och 1 traditional foil per paket", "Source Material-familjen förekommer i 1 av 24 Play Boosters", "Play Booster-formatet innehåller inte Collector Booster-exklusiva Cosmic Foil-, Gauntlet- eller Classic Comic-kort"], buy_url="https://dragonslair.se/en/products/marvels-spider-man-play-booster-display-magic-the-gathering"),
]

# CardSurfer products verified against exact Shopify article pages on
# 2026-09-25. Repeated slugs intentionally create alternate store offers for
# an existing format. NordicBreaks personals were unavailable and DrakenDavids
# candidates were either sold out or preorders, so neither supplies an offer in
# this snapshot.
RETAILER_EXPANSION_OBSERVED_AT = datetime(2026, 9, 25, 5, 35, 0)
RETAILER_EXPANSION = [
    dict(slug="cs-2025-26-panini-prizm-basketball-blaster", name="2025-26 Panini Prizm Basketball Blaster Box", category="Basket", manufacturer="Panini", year="2025-26", series="Prizm Basketball", fmt="blaster", sku="CS-PRIZM-NBA-2526-BLASTER", price=499, packs=6, cards=5, stock="in_stock", store_name="CardSurfer", observed_at=RETAILER_EXPANSION_OBSERVED_AT, facts=["6 retail-pack, 5 kort per pack", "3 Blaster-exklusiva Purple Wave Prizms per box i snitt", "Uptown och Black Color Blast är retail-exklusiva SSP-spår", "Autografer kan dras men är inte garanterade"], buy_url="https://cardsurferbreak.com/products/2025-26-panini-prizm-basketball-blaster-box"),
    dict(slug="cs-2025-26-topps-chrome-uwcl-hobby", name="2025-26 Topps Chrome UEFA Women's Champions League Hobby Box", category="Fotboll", manufacturer="Topps", year="2025-26", series="Chrome UWCL", fmt="hobby box", sku="TOPPS-UWCL-2526-HBY", price=1590, packs=20, cards=4, stock="in_stock", store_name="CardSurfer", observed_at=RETAILER_EXPANSION_OBSERVED_AT, facts=["20 hobby-pack, 4 kort per pack", "2 autografer per hobbybox", "Refractor 1:3 hobby-pack och Pulsar Refractor 1:6 hobby-pack", "Dual-, triple- och autograph-relic-kort finns enligt officiell checklista"], buy_url="https://cardsurferbreak.com/products/2025-26-topps-chrome-uefa-womens-champions-league-hobby-box"),
    dict(slug="cc-2026-topps-universe-wwe-value", name="2026 Topps Universe WWE Wrestling Value Box", category="WWE", manufacturer="Topps", year="2026", series="Topps Universe WWE", fmt="value box", sku="TOPPS-WWE-UNI-2026-VALUE", price=399, packs=6, cards=6, stock="in_stock", store_name="CardSurfer", observed_at=RETAILER_EXPANSION_OBSERVED_AT, facts=["6 value-pack, 6 kort per pack", "Galaxy-paralleller är exklusiva för Value Box", "Autografer, relics och numrerade paralleller kan dras", "Ingen autograf eller relic är garanterad i value-formatet"], buy_url="https://cardsurferbreak.com/products/2026-topps-universe-wwe-value-box"),
    dict(slug="cc-2025-26-opc-hobby", name="2025-26 Upper Deck O-Pee-Chee Hobby", category="Hockey", manufacturer="Upper Deck", year="2025-26", series="O-Pee-Chee", fmt="hobby box", sku="2526-UD-OPC-HOBBY", price=899, packs=18, cards=10, stock="in_stock", store_name="CardSurfer", observed_at=RETAILER_EXPANSION_OBSERVED_AT, facts=["18 hobby-pack, 10 kort per pack", "1 Red Border och 6 Blue Border-paralleller per box i snitt", "Minst 3 numrerade paralleller eller Printing Plates per box i snitt", "4 hobby-exklusiva O-Pee-Chee Playing Cards per box i snitt"], buy_url="https://cardsurferbreak.com/products/2025-26-o-pee-chee-hockey-hobby-box"),
    dict(slug="cc-2025-26-pwhl-hobby", name="2025-26 Upper Deck PWHL Hobby", category="Hockey", manufacturer="Upper Deck", year="2025-26", series="PWHL", fmt="hobby box", sku="CS-2526-UD-PWHL-HOBBY", price=1095, packs=12, cards=6, stock="in_stock", store_name="CardSurfer", observed_at=RETAILER_EXPANSION_OBSERVED_AT, facts=["12 hobby-pack, 6 kort per pack", "Young Guns, UD Canvas, Dazzlers och Outburst-paralleller finns", "Namngivna Young Guns-odds gäller hobbyformatet", "Ingen viss spelare är garanterad"], buy_url="https://cardsurferbreak.com/products/2025-26-upper-deck-pwhl-hockey-hobby-box"),
]

# Additional Swedish retailer checks performed against exact article pages on
# 2026-09-25. Repeated slugs are deliberate alternate offers for an already
# researched format. Stores without a stable, shippable in-stock article stay
# in the source map but do not receive catalog offers.
ADDITIONAL_STORE_OBSERVED_AT = datetime(2026, 9, 25, 16, 36, 0)
ADDITIONAL_STORE_EXPANSION = [
    dict(slug="cc-pokemon-storm-emeralda-m6-display", name="Pokémon Mega: Storm Emeralda M6 Booster Display Japanese", category="Pokémon", manufacturer="Pokémon Company Japan", year="2026", series="Storm Emeralda M6", fmt="booster box", sku="40625", price=1549, packs=30, cards=5, stock="in_stock", language="Japanese", store_name="MaxGaming", observed_at=ADDITIONAL_STORE_OBSERVED_AT, facts=["30 japanska boosterpaket, 5 kort per paket", "Checklistan innehåller Mega Rayquaza ex MUR #113/076 och flera SAR/AR", "Officiella kortspecifika packodds publiceras inte"], buy_url="https://www.maxgaming.se/sv/pokemon/pokemon-storm-emeralda-booster-box-japanese"),
    dict(slug="cc-pokemon-ninja-spinner-m4-display", name="Pokémon Mega: Ninja Spinner M4 Booster Display Japanese", category="Pokémon", manufacturer="Pokémon Company Japan", year="2026", series="Ninja Spinner M4", fmt="booster box", sku="MAX-NINJA-SPINNER-M4", price=1090, packs=30, cards=5, stock="in_stock", language="Japanese", store_name="MaxGaming", observed_at=ADDITIONAL_STORE_OBSERVED_AT, facts=["30 japanska boosterpaket, 5 kort per paket", "Checklistan innehåller Mega Greninja ex MUR #120/083 och flera SAR/AR", "Officiella kortspecifika packodds publiceras inte"], buy_url="https://www.maxgaming.se/sv/pokemon/pokemon-ninja-spinner-booster-box-japansk"),
    dict(slug="ad-pokemon-abyss-eye-m5-display", name="Pokémon Mega: Abyss Eye M5 Booster Box Japanese", category="Pokémon", manufacturer="Pokémon Company Japan", year="2026", series="Abyss Eye M5", fmt="booster box", sku="37250", price=1199, packs=30, cards=5, stock="in_stock", language="Japanese", store_name="Arcade Dreams", observed_at=ADDITIONAL_STORE_OBSERVED_AT, facts=["30 japanska boosterpaket, 5 kort per paket", "Officiella setpresentationen namnger Mega Darkrai ex, Mega Zeraora ex och Mega Chandelure ex", "Mega Chandelure ex och Muku visas officiellt som SAR", "Pokémon publicerar inga kortspecifika packodds"], buy_url="https://arcadedreams.se/shop/tcg/pokemon-abyss-eye-booster-box-jp-m5"),
    dict(slug="tcgs-pokemon-destined-rivals-pack", name="Pokémon Scarlet & Violet: Destined Rivals Booster Pack", category="Pokémon", manufacturer="The Pokémon Company", year="2025", series="Destined Rivals", fmt="single pack", sku="TCGS-SV10-PACK", price=159, packs=1, cards=10, stock="in_stock", store_name="TCGStore", observed_at=ADDITIONAL_STORE_OBSERVED_AT, facts=["1 engelskt boosterpaket med 10 kort och 1 Basic Energy", "Officiella galleriet namnger Team Rocket's Mewtwo ex, Cynthia's Garchomp ex, Ethan's Ho-Oh ex och Team Rocket's Crobat ex", "Officiella kortspecifika packodds publiceras inte"], buy_url="https://tcgstore.se/products/pokemon-scarlet-violet-10-destined-rivals-booster-pack"),
    dict(slug="sos-pokemon-journey-together-pack", name="Pokémon Scarlet & Violet: Journey Together Booster Pack", category="Pokémon", manufacturer="The Pokémon Company", year="2025", series="Journey Together", fmt="single pack", sku="56046", price=99, packs=1, cards=10, stock="in_stock", store_name="SpelOchSånt", observed_at=ADDITIONAL_STORE_OBSERVED_AT, facts=["1 engelskt boosterpaket med 10 kort och 1 Basic Energy", "N's Zoroark ex, Lillie's Clefairy ex, Iono's Bellibolt ex och Hop's Zacian ex är officiellt namngivna", "Över 30 Pokémon- och Trainer-kort med specialillustrationer finns i setet", "Officiella kortspecifika packodds publiceras inte"], buy_url="https://www.spelochsant.se/produkt/pokemonkort/losaboosters/pokemontcgscarletvioletjourneytogetherboosterpackmax6perhushall"),
]

# One Piece market scan: exact, shippable article pages checked 2026-09-25.
# Repeated slugs are verified competing offers for the same language/format.
ONE_PIECE_MARKET_OBSERVED_AT = datetime(2026, 9, 25, 17, 18, 0)
ONE_PIECE_MARKET_EXPANSION = [
    dict(slug="kv-one-piece-op10-jp-pack", name="One Piece Royal Blood OP-10 Booster Pack Japanese", category="One Piece", manufacturer="Bandai", year="2025", series="Royal Blood OP-10", fmt="single pack", sku="KV-OP10-JP-PACK", price=35, packs=1, cards=6, stock="in_stock", language="Japanese", store_name="Kantovault", observed_at=ONE_PIECE_MARKET_OBSERVED_AT, facts=["1 japanskt boosterpaket med 6 kort", "Officiella setet innehåller 2 Secret Rares, 6 Special Cards och 1 Treasure Rare", "Bandai publicerar inte kortspecifika packodds"], buy_url="https://kantovault.se/products/one-piece-op-10-royal-blood-booster-pack-japansk"),
    dict(slug="kv-one-piece-op10-jp-box", name="One Piece Royal Blood OP-10 Booster Box Japanese", category="One Piece", manufacturer="Bandai", year="2025", series="Royal Blood OP-10", fmt="booster box", sku="KV-OP10-JP-BOX", price=999, packs=24, cards=6, stock="in_stock", language="Japanese", store_name="Kantovault", observed_at=ONE_PIECE_MARKET_OBSERVED_AT, facts=["24 japanska boosterpaket med 6 kort per paket", "Royal Blood har Punk Hazard-, Supernovas-, Dressrosa- och Donquixote-spår", "Ingen viss rarity eller karaktär är garanterad"], buy_url="https://kantovault.se/products/one-piece-op-10-royal-blood-booster-box-japansk"),
    dict(slug="as-one-piece-op14-en-pack", name="One Piece The Azure Sea's Seven OP-14 Booster Pack English", category="One Piece", manufacturer="Bandai", year="2026", series="The Azure Sea's Seven OP-14", fmt="single pack", sku="BAN-2821706-OP14-B", price=79, packs=1, cards=12, stock="in_stock", language="English", store_name="AlphaSpel", observed_at=ONE_PIECE_MARKET_OBSERVED_AT, facts=["1 engelskt boosterpaket med 12 kort", "Setet har 2 Secret Rares, 6 Special Cards, 2 anniversary-specialkort och 1 Treasure Rare", "Bandai publicerar inte kortspecifika packodds"], buy_url="https://main.alphaspel.se/4544-star-wars-unlimited-ccg/346520-one-piece-card-game-op14-the-azure-seas-seven-booster-pack"),
    dict(slug="as-one-piece-op14-en-pack", name="One Piece The Azure Sea's Seven OP-14 Booster Pack English", category="One Piece", manufacturer="Bandai", year="2026", series="The Azure Sea's Seven OP-14", fmt="single pack", sku="AQ-OP14-EN-PACK", price=89, packs=1, cards=12, stock="in_stock", language="English", store_name="Aquitaz", observed_at=ONE_PIECE_MARKET_OBSERVED_AT, facts=["1 engelskt boosterpaket med 12 kort", "Namngivna huvudspår omfattar Trafalgar Law, Dracule Mihawk, Boa Hancock och Buggy", "Ingen träff är garanterad i ett löst paket"], buy_url="https://aquitaz.se/en/products/one-piece-op-14-the-azure-seas-seven-booster-pack-12-kort-eng"),
    dict(slug="as-one-piece-op14-en-pack", name="One Piece The Azure Sea's Seven OP-14 Booster Pack English", category="One Piece", manufacturer="Bandai", year="2026", series="The Azure Sea's Seven OP-14", fmt="single pack", sku="BP-OP14-EN-PACK", price=99, packs=1, cards=12, stock="in_stock", language="English", store_name="Bangerpack", observed_at=ONE_PIECE_MARKET_OBSERVED_AT, facts=["1 engelskt boosterpaket med 12 kort", "Mihawk och Crocodile är Secret Rares; Mihawk har ett Super Alternate Art-spår", "Bandai publicerar inte kortspecifika packodds"], buy_url="https://bangerpack.se/tcg-samlarkort/one-piece/one-piece-op-14-the-azure-seas-seven-booster"),
    dict(slug="aq-one-piece-op15-eb04-en-pack", name="One Piece Adventure on KAMI's Island OP15-EB04 Booster Pack English", category="One Piece", manufacturer="Bandai", year="2026", series="Adventure on KAMI's Island OP15-EB04", fmt="single pack", sku="AQ-OP15-EB04-EN-PACK", price=99, packs=1, cards=12, stock="in_stock", language="English", store_name="Aquitaz", observed_at=ONE_PIECE_MARKET_OBSERVED_AT, facts=["1 engelskt boosterpaket med 12 kort", "Bandai namnger Secret Rare Monkey.D.Luffy och Enel samt Enel Super Alternate Art", "Bandai publicerar inte kortspecifika packodds"], buy_url="https://aquitaz.se/en/products/one-piece-op-15-eb-04-adventure-on-kamis-island-booster-pack-12-kort-eng"),
    dict(slug="kl-one-piece-eb03-en-pack", name="One Piece Heroines Edition EB-03 Booster Pack English", category="One Piece", manufacturer="Bandai", year="2026", series="Heroines Edition EB-03", fmt="single pack", sku="KL-EB03-EN-PACK", price=199, packs=1, cards=12, stock="in_stock", language="English", store_name="Kortlagret", observed_at=ONE_PIECE_MARKET_OBSERVED_AT, facts=["1 engelskt boosterpaket med 12 kort", "Nefeltari Vivi debuterar som Leader och setet innehåller 9 SP-kort", "Fyra DON!!-motiv finns även som alternate art"], buy_url="https://kortlagret.se/produkter/eb03-heroines-edition-booster-pack"),
    dict(slug="kl-one-piece-op17-en-pack", name="One Piece The World's Strongest Warriors OP-17 Booster Pack English", category="One Piece", manufacturer="Bandai", year="2026", series="The World's Strongest Warriors OP-17", fmt="single pack", sku="KL-OP17-EN-PACK", price=189, packs=1, cards=12, stock="in_stock", language="English", store_name="Kortlagret", observed_at=ONE_PIECE_MARKET_OBSERVED_AT, facts=["1 engelskt boosterpaket med 12 kort", "OP17 har Super Leader Alt-Art Monkey.D.Luffy, Rocks.D.Xebec och Four Emperors-specialspår", "Ingen specifik rarity är garanterad"], buy_url="https://kortlagret.se/produkter/op17-the-worlds-strongest-warriors-booster-pack"),
    dict(slug="kl-one-piece-op17-en-pack", name="One Piece The World's Strongest Warriors OP-17 Booster Pack English", category="One Piece", manufacturer="Bandai", year="2026", series="The World's Strongest Warriors OP-17", fmt="single pack", sku="BP-OP17-EN-PACK", price=199, packs=1, cards=12, stock="in_stock", language="English", store_name="Bangerpack", observed_at=ONE_PIECE_MARKET_OBSERVED_AT, facts=["1 engelskt boosterpaket med 12 kort", "Bandais fjärde jubileumsset med alternativa illustrationer och specialkort", "Bandai publicerar inte kortspecifika packodds"], buy_url="https://bangerpack.se/tcg-samlarkort/one-piece/one-piece-card-game-booster-pack-the-worlds-strongest-warriors-op-17"),
    dict(slug="bp-one-piece-op17-en-display", name="One Piece The World's Strongest Warriors OP-17 Booster Display English", category="One Piece", manufacturer="Bandai", year="2026", series="The World's Strongest Warriors OP-17", fmt="booster box", sku="BP-OP17-EN-DISPLAY", price=4299, packs=24, cards=12, stock="in_stock", language="English", store_name="Bangerpack", observed_at=ONE_PIECE_MARKET_OBSERVED_AT, facts=["24 engelska boosterpaket med 12 kort per paket", "Setet innehåller Super Leader Alt-Art, Secret Rares, Treasure Rare och flera specialkort", "Det höga svenska marknadspriset ska vägas mot 24 öppningsförsök; boxen saknar kortspecifik garanti"], buy_url="https://bangerpack.se/tcg-samlarkort/one-piece/booster-box-display-op-17"),
]

# Thin-category market scan verified against exact Swedish article pages on
# 2026-09-25. Duplicate slugs are intentional backup/price-comparison offers
# for an already modelled product; format-specific products keep separate slugs.
TCG_MARKET_OBSERVED_AT = datetime(2026, 9, 25, 19, 4, 0)
TCG_MARKET_EXPANSION = [
    dict(slug="as-yugioh-phantom-revenge-pack", name="Yu-Gi-Oh! Phantom Revenge Booster Pack", category="Yu-Gi-Oh", manufacturer="Konami", year="2025", series="Phantom Revenge", fmt="single pack", sku="YGO834-6-p", price=59, packs=1, cards=7, stock="in_stock", language="English", store_name="AlphaSpel", observed_at=TCG_MARKET_OBSERVED_AT, facts=["1 engelskt boosterpaket med 7 kort", "1 foil och 6 Rare per paket", "15 kort finns som Collector's Rare och 10 som Starlight Rare", "Ingen Collector's Rare eller Starlight Rare är garanterad"], buy_url="https://alphaspel.se/1763-yu-gi-oh/340639-yu-gi-oh-tcg-phantom-revenge-booster-pack"),
    dict(slug="cc-yugioh-phantom-revenge-display", name="Yu-Gi-Oh! Phantom Revenge Booster Display", category="Yu-Gi-Oh", manufacturer="Konami", year="2025", series="Phantom Revenge", fmt="booster box", sku="YGO834-6", price=949, packs=24, cards=7, stock="in_stock", language="English", store_name="AlphaSpel", observed_at=TCG_MARKET_OBSERVED_AT, facts=["24 engelska boosterpaket med 7 kort per paket", "1 foil och 6 Rare per paket", "Backup-erbjudande; ingen hög rarity är garanterad per display"], buy_url="https://alphaspel.se/1763-yu-gi-oh/306138-yu-gi-oh-tcg-phantom-revenge-booster-display-24"),
    dict(slug="as-yugioh-maze-muertos-pack", name="Yu-Gi-Oh! Maze of Muertos Booster Pack", category="Yu-Gi-Oh", manufacturer="Konami", year="2026", series="Maze of Muertos", fmt="single pack", sku="YGO409-6-b", price=49, packs=1, cards=7, stock="in_stock", language="English", store_name="AlphaSpel", observed_at=TCG_MARKET_OBSERVED_AT, facts=["1 engelskt boosterpaket med 7 kort", "1 foil och 6 Rare per paket", "Starlight-, Collector's-, Secret-, Ultra- och Super Rare finns i checklistan", "Ingen viss rarity eller namngiven träff är garanterad"], buy_url="https://www.alphaspel.se/1763-yu-gi-oh/345247-yu-gi-oh-tcg-maze-of-muertos-booster-pack"),
    dict(slug="as-yugioh-maze-muertos-display", name="Yu-Gi-Oh! Maze of Muertos Booster Display", category="Yu-Gi-Oh", manufacturer="Konami", year="2026", series="Maze of Muertos", fmt="booster box", sku="YGO409-6", price=949, packs=24, cards=7, stock="in_stock", language="English", store_name="AlphaSpel", observed_at=TCG_MARKET_OBSERVED_AT, facts=["24 engelska boosterpaket med 7 kort per paket", "Varje paket innehåller 1 foil och 6 Rare", "Konami publicerar checklistans rarities men ingen displaygaranti för Starlight eller Collector's Rare"], buy_url="https://www.alphaspel.se/1763-yu-gi-oh/337424-yu-gi-oh-tcg-maze-of-muertos-booster-display-24"),
    dict(slug="as-yugioh-blazing-dominion-pack", name="Yu-Gi-Oh! Blazing Dominion Booster Pack", category="Yu-Gi-Oh", manufacturer="Konami", year="2026", series="Blazing Dominion", fmt="single pack", sku="YGO934-3-b", price=49, packs=1, cards=None, stock="in_stock", language="English", store_name="AlphaSpel", observed_at=TCG_MARKET_OBSERVED_AT, facts=["1 engelskt boosterpaket; butikssidan anger inte antal kort", "101-kortschecklista med 10 Secret, 14 Ultra, 26 Super och 50 Common", "25 kort finns som Starlight Rare", "Starlight Rare beskriver kortversionen, inte dragchansen"], buy_url="https://www.main.alphaspel.se/1763-yu-gi-oh/342862-yu-gi-oh-tcg-blazing-dominion-booster-pack"),
    dict(slug="cc-lorcana-azurite-pack", name="Disney Lorcana Azurite Sea Booster Pack", category="Disney", manufacturer="Ravensburger", year="2024", series="Azurite Sea", fmt="single pack", sku="DL-AZURITE-SEA-PACK", price=70, packs=1, cards=12, stock="in_stock", language="English", store_name="Dragons Lair", observed_at=TCG_MARKET_OBSERVED_AT, facts=["1 engelskt boosterpaket med 12 slumpade kort", "Alternativt butikserbjudande till samma verifierade produkt", "Ravensburger publicerar inte kortspecifika packodds"], buy_url="https://dragonslair.se/products/disney-lorcana-tcg-azurite-sea-booster-pack-disney-lorcana"),
    dict(slug="dl-lorcana-azurite-display", name="Disney Lorcana Azurite Sea Booster Display", category="Disney", manufacturer="Ravensburger", year="2024", series="Azurite Sea", fmt="booster box", sku="DL-AZURITE-SEA-DISPLAY", price=1549, packs=24, cards=12, stock="in_stock", language="English", store_name="Dragons Lair", observed_at=TCG_MARKET_OBSERVED_AT, facts=["24 engelska boosterpaket med 12 slumpade kort per paket", "Checklistan har 204 baskort och 18 Enchanted-kort", "Ingen Enchanted eller annan specifik rarity är garanterad per display"], buy_url="https://dragonslair.se/products/disney-lorcana-tcg-azurite-sea-booster-pack-display-24-boosters-disney-lorcana"),
]

REAL_SNAPSHOT += REAL_FOOTBALL_SNAPSHOT + REAL_POKEMON_SNAPSHOT + REAL_ENTERTAINMENT_SNAPSHOT

REAL_SNAPSHOT += REAL_PACK_SNAPSHOT
REAL_SNAPSHOT += REAL_NONSPORT_EXPANSION
REAL_SNAPSHOT += REAL_CROSS_CATEGORY_EXPANSION
REAL_SNAPSHOT += REAL_RESEARCH_EXPANSION
REAL_SNAPSHOT += REAL_STORE_EXPANSION
REAL_SNAPSHOT += RETAILER_EXPANSION
REAL_SNAPSHOT += ADDITIONAL_STORE_EXPANSION
REAL_SNAPSHOT += ONE_PIECE_MARKET_EXPANSION
REAL_SNAPSHOT += TCG_MARKET_EXPANSION

DIRECT_BUY_URLS = {
    "cc-2025-26-opc-retail-blaster": "https://www.coolcard.se/product/hel-blaster-box-2025-26-o-pee-chee-hockey-retail-9-paket",
    "cc-2025-26-extended-retail-blaster": "https://www.coolcard.se/product/hel-blaster-box-2025-26-upper-deck-extended-series-retail-4-paket",
    "cc-2025-26-opc-platinum-retail-blaster": "https://www.coolcard.se/product/hel-blaster-box-2025-26-upper-deck-o-pee-chee-platinum-retail",
    "cc-2025-26-pwhl-retail-blaster": "https://www.coolcard.se/product/hel-blaster-box-2025-26-upper-deck-pwhl-professional-womens-hockey-league-retail-5-packs",
    "cc-2025-26-series2-retail-blaster": "https://www.coolcard.se/product/hel-blaster-box-2025-26-upper-deck-series-2-retail-4-paket",
    "cc-2025-26-rangers-box-set": "https://www.coolcard.se/product/hel-box-2025-26-upper-deck-new-york-rangers-centennial-box-set",
    "cc-2025-26-opc-hobby": "https://www.coolcard.se/product/hel-box-2025-26-upper-deck-o-pee-chee-hobby-18-packs",
    "cc-2025-26-pwhl-hobby": "https://www.coolcard.se/product/hel-box-2025-26-upper-deck-pwhl-professional-womens-hockey-league-hobby",
    "cc-2025-26-mvp-hobby": "https://www.coolcard.se/product/hel-box-2025-26-upper-deck-mvp-hobby-silver-collection-cdd-20-paket",
    "cc-2025-26-series1-hobby": "https://www.coolcard.se/product/hel-box-12-paket-2025-26-upper-deck-series-1-hobby",
    "cc-2025-26-skybox-metal-hobby": "https://www.coolcard.se/product/hel-box-15-paket-2025-26-upper-deck-nhl-skybox-metal-universe-hobby-20018",
    "cc-2025-26-extended-hobby": "https://www.coolcard.se/product/hel-box-12-paket-2025-26-upper-deck-extended-series-hobby",
    "cc-2025-26-series2-hobby": "https://www.coolcard.se/product/hel-box-12-paket-2025-26-upper-deck-series-2-hobby",
    "cc-2025-26-fleer-ultra-pwhl-hobby": "https://www.coolcard.se/product/hel-box-2025-2026-fleer-ultra-pwhl-hobby",
    "cc-2025-26-sp-authentic-hobby": "https://www.coolcard.se/product/hel-box-2025-26-upper-deck-sp-authentic-hobby",
    "cc-2025-26-ultimate-hobby": "https://www.coolcard.se/product/hel-box-2025-26-upper-deck-ultimate-hobby",
    "cc-pack-2025-26-opc-hobby": "https://www.coolcard.se/product/1st-paket-2025-26-upper-deck-o-pee-chee-hobby",
    "cc-pack-2025-26-mvp-hobby": "https://www.coolcard.se/product/1st-paket-2025-26-upper-deck-mvp-hobby-silver-collection-cdd-8-cards",
    "cc-pack-2025-26-pwhl-hobby": "https://www.coolcard.se/product/1st-paket-2025-26-upper-deck-pwhl-professional-womens-hockey-league-hobby",
    "cc-pack-2025-26-parkhurst-hobby": "https://www.coolcard.se/product/1st-paket-2025-26-upper-deck-parkhurst-hobby",
    "cc-pack-2025-26-skybox-hobby": "https://www.coolcard.se/product/1st-paket-2025-26-upper-deck-nhl-skybox-metal-universe-hobby",
    "cc-pack-2025-26-series1-hobby": "https://www.coolcard.se/product/1st-paket-2025-26-upper-deck-series-1-hobby",
    "cc-2025-26-pitch-kings-la-liga": "https://www.coolcard.se/product/hel-box-2025-26-panini-pitch-kings-la-liga-international-hobby",
    "cc-2026-topps-mls-chrome-value": "https://www.coolcard.se/product/hel-value-box-2026-topps-major-league-soccer-chrome-soccer-mls",
    "cc-2025-26-panini-prizm-fifa-choice": "https://www.coolcard.se/product/hel-box-2025-26-panini-prizm-fifa-soccer-choice-8-cards-per-box",
    "cc-2026-topps-chrome-premier-league-hobby": "https://www.coolcard.se/product/hel-box-2026-topps-chrome-premier-league-soccer-trading-cards-hobby-20-paket",
    "cc-2026-topps-finest-premier-league-wave2": "https://www.coolcard.se/product/hel-box-2026-topps-finest-premier-league-soccer-hobby",
    "cc-2025-26-panini-prizm-fifa-retail": "https://www.coolcard.se/product/hel-box-2025-26-panini-prizm-fifa-soccer-retail-24-packs",
    "cc-2025-26-topps-chrome-arsenal-hobby": "https://www.coolcard.se/product/hel-box-2025-26-topps-chrome-arsenal-soccer-hobby",
    "cc-2025-26-topps-bayern-lineage": "https://www.coolcard.se/product/hel-box-2025-26-topps-fc-bayern-munchen-lineage-hobby",
    "cc-pokemon-white-flare-jp-display": "https://www.coolcard.se/product/pokmon-white-flare-sv11w-booster-display-30-paket-japansk",
    "cc-pokemon-temporal-forces-18": "https://www.coolcard.se/product/pokmon-sv5-temporal-forces-liten-booster-box-innehaller-18-boosters",
}

UNAVAILABLE_PURCHASE_SLUGS = {
    "cc-2025-26-clear-cut-hobby",
    "cc-2025-26-premier-hobby",
    "cc-2026-futera-world-football-fx3",
    "cc-2026-topps-argentina-team-set",
    "cc-2025-26-topps-real-madrid-team-set",
    "cc-2025-topps-marvel-studios-chrome-hobby",
    "cc-2026-topps-disney-chrome-value",
    "cc-marvel-2025-deadpool-value",
}

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
        one_piece_url="https://www.coolcard.se/category/one-piece-japanska-kort"
        marvel_url="https://www.coolcard.se/category/dc-seriefigurer"
        disney_url="https://www.coolcard.se/en/product/sealed-value-box-2026-topps-disney-chrome-8-packs"
        fact_urls={
            "cc-2025-26-series2-hobby":"https://www.coolcard.se/product/hel-box-12-paket-2025-26-upper-deck-series-2-hobby",
            "cc-2025-26-clear-cut-hobby":"https://www.coolcard.se/product/hel-box-2025-26-upper-deck-clear-cut-hobby",
            "cc-2025-26-opc-hobby":"https://www.coolcard.se/en/product/1-pack-2025-26-upper-deck-o-pee-chee-hobby",
            "cc-2025-26-series1-hobby":"https://www.coolcard.se/category/boxar-nhl-2025-26",
            "cc-one-piece-op13-jp-display":"https://en.onepiece-cardgame.com/products/boosters/op13/",
            "cc-2025-topps-marvel-studios-chrome-hobby":"https://www.topps.com/pages/topps-marvel-studios-chrome",
            "cc-2026-topps-disney-chrome-value":"https://www.topps.com/products/2026-topps-chrome%C2%AE-disney-value-box",
        }
        buy_urls={
            "cc-one-piece-op13-jp-display":"https://www.coolcard.se/en/product/one-piece-card-game-booster-display-24-boosters-carrying-on-his-will-op-13-japanese",
            "cc-2026-topps-disney-chrome-value":"https://www.coolcard.se/en/product/sealed-value-box-2026-topps-disney-chrome-8-packs",
            "cc-pokemon-mega-zygarde-premium":"https://www.coolcard.se/en/product/pokemon-mega-zygarde-ex-premium-collection-2",
            "cc-pokemon-shrouded-fable-kingambit":"https://www.coolcard.se/product/pokemon-sv6-5-shrouded-fable-kingambit-illustration-collection",
            "cc-pokemon-go-etb":"https://www.coolcard.se/en/product/pokemon-pokemon-go-elite-trainer-box-2",
            "cc-pokemon-paradox-rift-18":"https://www.coolcard.se/en/product/pokmon-sv4-paradox-rift-small-booster-box-contains-18-boosters",
            "cc-pokemon-black-bolt-jp-display":"https://www.coolcard.se/en/product/pokmon-black-bolt-sv11b-booster-box-30-paket-japanese",
            "cc-pokemon-black-bolt-jp-pack":"https://www.coolcard.se/en/product/pokmon-black-bolt-sv11b-booster-pack-5-cards-japanese",
            "cc-pokemon-nihil-zero-jp-display":"https://www.coolcard.se/en/product/pokmon-mega-nihil-zero-m3-booster-display-30-packs-japanese",
            "cc-pokemon-nihil-zero-jp-pack":"https://www.coolcard.se/en/product/pokmon-mega-nihil-zero-m3-booster-5-card-japanese",
        }

        for row in REAL_SNAPSHOT:
            row_store = coolcard
            if row.get("store_name") and row["store_name"] != coolcard.name:
                row_store = db.scalar(select(Store).where(Store.name == row["store_name"]))
                if row_store is None:
                    store_info = next(x for x in REAL_STORES if x["name"] == row["store_name"])
                    row_store = Store(
                        country="SE", active=True, min_interval_seconds=120, **store_info
                    )
                    db.add(row_store); db.flush()
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
                    ProductVariant.language == row.get("language", "English"),
                    ProductVariant.region == row.get("region", "Global"),
                )
            )
            if variant is None:
                variant = ProductVariant(
                    product_id=product.id, format=row["fmt"],
                    packs=row["packs"], cards_per_pack=row["cards"],
                    language=row.get("language", "English"), region=row.get("region", "Global"),
                )
                db.add(variant); db.flush()
            else:
                variant.packs=row["packs"]; variant.cards_per_pack=row["cards"]
                variant.language=row.get("language", "English"); variant.region=row.get("region", "Global")

            offer = db.scalar(
                select(Offer).where(
                    Offer.store_id == row_store.id,
                    Offer.external_id == row["sku"],
                )
            )
            if row["category"]=="Fotboll":
                source_url=football_url
            elif row["category"]=="Pokémon":
                source_url=pokemon_url
            elif row["category"]=="One Piece":
                source_url=one_piece_url
            elif row["category"]=="Marvel":
                source_url=marvel_url
            elif row["category"]=="Disney":
                source_url=disney_url
            else:
                source_url = pack_url if row["fmt"]=="single pack" else category_url
            source_url = row.get("buy_url") or DIRECT_BUY_URLS.get(row["slug"]) or buy_urls.get(row["slug"]) or source_url
            stock_status = "out_of_stock" if row["slug"] in UNAVAILABLE_PURCHASE_SLUGS else row.get("stock", "in_stock")
            is_expansion = row in REAL_NONSPORT_EXPANSION or row in REAL_CROSS_CATEGORY_EXPANSION or row in REAL_RESEARCH_EXPANSION or row in REAL_STORE_EXPANSION or row in RETAILER_EXPANSION
            observed_at = row.get("observed_at", REAL_EXPANSION_OBSERVED_AT if is_expansion else REAL_SNAPSHOT_OBSERVED_AT)
            if offer is None:
                offer = Offer(
                    store_id=row_store.id, variant_id=variant.id,
                    external_id=row["sku"], source_title=row["name"],
                    price_sek=row["price"], stock_status=stock_status,
                    source_kind="verified_snapshot", source_confidence=100,
                    match_confidence=1.0, match_status="manual_matched",
                    observed_at=observed_at, url=source_url,
                    is_preorder=False,
                )
                db.add(offer); db.flush()
                db.add(PriceHistory(
                    offer_id=offer.id, price_sek=row["price"],
                    stock_status=stock_status,
                    observed_at=observed_at,
                ))
            else:
                offer.variant_id=variant.id
                offer.price_sek=row["price"]
                offer.stock_status=stock_status
                offer.source_kind="verified_snapshot"
                offer.source_confidence=100
                offer.match_confidence=1.0
                offer.match_status="manual_matched"
                offer.observed_at=observed_at
                offer.url=source_url
                offer.is_preorder=False

            facts=row.get("facts",[])
            if facts:
                pf=db.scalar(select(ProductFact).where(ProductFact.variant_id==variant.id))
                if pf is None:
                    pf=ProductFact(variant_id=variant.id)
                    db.add(pf)
                pf.facts_json=json.dumps(facts,ensure_ascii=False)
                pf.source_name=f"{row_store.name} / tillverkarinformation på produktsidan"
                pf.source_url=fact_urls.get(row["slug"],source_url)
                pf.verified_at=observed_at
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
"cc-pack-2025-26-parkhurst-hobby": {
 "source_name":"Upper Deck 2025-26 Parkhurst checklist and product information",
 "source_url":"https://upperdeck.com/checklist/2025-26-parkhurst-checklist/",
 "key_names":["Matthew Schaefer #211","Michael Misa #222","Ryan Leonard #225","Gabe Perreault #232","Ivan Demidov #236","Zayne Parekh #246"],
 "headline_chases":[
   {"card":"Ivan Demidov Base Rookie #236","tier":"BRA","odds":"Base rookies 1 per hobby pack i snitt; exakt spelare ur rookiegruppen","why":"Namngiven topprookie i den officiella checklistan."},
   {"card":"Matthew Schaefer Base Rookie #211","tier":"BRA","odds":"Base rookies 1 per hobby pack i snitt","why":"Konkret rookie med kortnummer."},
   {"card":"Prominent Prospects","tier":"MYCKET BRA","odds":"1:8 hobby packs","why":"Verifierat prospect-insertspår."},
   {"card":"Parkhurst Penworks Rookie Autograph","tier":"MONSTER","odds":"Penworks Rookie-familjen 1:40 hobby packs","why":"Möjlig rookieautograf i ett löst paket."},
   {"card":"Est. 1951 Rookie Autograph","tier":"MONSTER","odds":"Est. 1951 Rookie Auto-familjen 1:40 hobby packs","why":"Ytterligare verifierat autografspår."},
   {"card":"Ivan Demidov Rookie Auto Patch /25","tier":"JACKPOT","odds":"serial /25; inga individuella packodds publicerade","why":"Lågnumrerad rookieauto med memorabilia."},
   {"card":"Base Rookie Gold Spectrum 1/1","tier":"JACKPOT","odds":"1/1","why":"Unik rookieparallel."}
 ],
 "why_exciting":["En rookie per hobby-pack i snitt ger ett tydligt innehållsgolv.","Penworks Rookie Auto och Est. 1951 Rookie Auto ligger båda på 1:40 hobby-pack som kortfamiljer."],
 "tiers":{"everyday":{"label":"Vanligt men intressant","score":78,"items":["1 rookie per hobby-pack i snitt"]},"good":{"label":"Bra träff","score":80,"items":["Demidov, Schaefer, Misa eller Leonard rookie","Prominent Prospects 1:8"]},"big":{"label":"Riktigt bra","score":84,"items":["Penworks Rookie Auto 1:40","Est. 1951 Rookie Auto 1:40"]},"jackpot":{"label":"Monsterhit","score":79,"items":["Rookie Auto Patch /25 eller /49","Gold Spectrum 1/1"]}},
 "caveat":"1:40 gäller hela respektive autografserie, inte en viss spelare. Ett löst paket garanterar varken autograf eller en specifik rookie."
},
"cc-2025-26-pwhl-retail-blaster": {
 "source_name":"Upper Deck 2025-26 UD PWHL checklist",
 "source_url":"https://upperdeck.com/checklist/2025-26-ud-pwhl-checklist/",
 "key_names":["Kristyna Kaltounkova #51","Emma Gentry #52","Rory Guilday #53","Casey O'Brien #57","Kiara Zanon #58","Abby Hustler #59"],
 "headline_chases":[
   {"card":"Casey O'Brien Young Guns #57","tier":"BRA","odds":"Young Guns 1:3 blaster packs; exakt spelare ur 20-kortsgruppen","why":"Namngiven rookie i checklistan."},
   {"card":"Kristyna Kaltounkova Young Guns #51","tier":"BRA","odds":"Young Guns 1:3 blaster packs","why":"Konkret rookie med retailformatets odds."},
   {"card":"Young Guns Outburst","tier":"MONSTER","odds":"1:60 blaster packs","why":"Premiumparallel i retailformatet."},
   {"card":"UD Canvas Young Guns","tier":"MYCKET BRA","odds":"1:48 blaster packs","why":"Sällsyntare rookie-Canvas."}
 ],
 "why_exciting":["Young Guns kommer 1:3 blaster-pack som kortfamilj.","Kaltounkova, O'Brien, Zanon och Hustler är namngivna rookies i den officiella checklistan."],
 "tiers":{"everyday":{"label":"Vanligt men intressant","score":70,"items":["Young Guns 1:3 blaster-pack"]},"good":{"label":"Bra träff","score":79,"items":["Namngiven Young Guns-rookie"]},"big":{"label":"Riktigt bra","score":73,"items":["Canvas Young Guns 1:48"]},"jackpot":{"label":"Monsterhit","score":64,"items":["Young Guns Outburst 1:60"]}},
 "caveat":"Familjeoddset 1:3 är inte oddset för en särskild spelare. Ingen autograf visas eftersom checklistunderlaget inte verifierar ett autografspår för blastern."
},
"cc-2025-26-fleer-ultra-pwhl-hobby": {
 "source_name":"Upper Deck 2025-26 Fleer Ultra PWHL checklist",
 "source_url":"https://upperdeck.com/checklist/2025-26-fleer-ultra-pwhl-checklist/",
 "key_names":["Casey O'Brien","Kristyna Kaltounkova","Emma Gentry","Rory Guilday","Nicole Gosling","Natalie Spooner","Alex Carpenter"],
 "headline_chases":[
   {"card":"Casey O'Brien Rising Stars","tier":"BRA","odds":"Rising Stars-paralleller serial /199, /99, /49, /35, /15 och 1/1","why":"Namngiven rookie/prospect med full numreringsstege."},
   {"card":"Fresh Ink Autograph – Natalie Spooner","tier":"MYCKET BRA","odds":"Fresh Ink 1:150 hobby/e-Pack; Spooner är SP inom serien","why":"Namngiven signerad stjärnträff."},
   {"card":"Fresh Ink Autograph – Alex Carpenter","tier":"MYCKET BRA","odds":"Fresh Ink 1:150 hobby/e-Pack; Carpenter är SP inom serien","why":"Signerad toppspelare med SP-status."},
   {"card":"Casey O'Brien Rising Stars Green /15","tier":"MONSTER","odds":"serial /15","why":"Mycket lågnumrerad rookie/prospect-parallel."},
   {"card":"Casey O'Brien Rising Stars Black 1/1","tier":"JACKPOT","odds":"1/1","why":"Unikt exemplar."}
 ],
 "why_exciting":["Fresh Ink ger ett verifierat autografspår på 1:150 hobby-pack som kortfamilj.","Rising Stars har namngivna PWHL-talanger och paralleller ned till 1/1."],
 "tiers":{"everyday":{"label":"Vanligt men intressant","score":74,"items":["Fleer Ultra rookie- och insertspår"]},"good":{"label":"Bra träff","score":80,"items":["Rising Stars på O'Brien eller annan topprookie"]},"big":{"label":"Riktigt bra","score":84,"items":["Fresh Ink 1:150","Rising Stars /35 eller lägre"]},"jackpot":{"label":"Monsterhit","score":78,"items":["Rising Stars Black 1/1"]}},
 "caveat":"Fresh Ink 1:150 gäller hela serien och inte Natalie Spooner eller Alex Carpenter individuellt. SP-status anger relativ knapphet men inget exakt spelarodds."
},
"cc-2025-26-sp-authentic-hobby": {
 "source_name":"Upper Deck 2025-26 SP Authentic product and checklist",
 "source_url":"https://upperdeck.com/checklist/2025-26-sp-authentic-checklist/",
 "key_names":["Ivan Demidov #149","Ryan Leonard #133","Matthew Schaefer #168","Michael Misa #169","Gabe Perreault"],
 "headline_chases":[
   {"card":"Ivan Demidov Future Watch Autograph #149 /999","tier":"MYCKET BRA","odds":"Minst 1 Future Watch Autograph per box i snitt; exakt spelare ur checklistan","why":"Produktens klassiska signerade rookie-kort."},
   {"card":"Matthew Schaefer Future Watch Autograph #168 /999","tier":"MYCKET BRA","odds":"Minst 1 Future Watch Autograph per box i snitt","why":"Namngiven topprookie med kortnummer."},
   {"card":"Future Watch Auto Patch /100","tier":"MONSTER","odds":"serial /100; ingen separat boxgaranti","why":"Signerad rookie med memorabilia."},
   {"card":"Matthew Schaefer Sign of the Times Rookies Black /25","tier":"MONSTER","odds":"serial /25","why":"Lågnumrerad namngiven rookieautograf."},
   {"card":"Matthew Schaefer eller Michael Misa Future Watch Auto Patch Black 1/1","tier":"JACKPOT","odds":"1/1","why":"Unik toppversion av premium-rookieautografen."}
 ],
 "why_exciting":["Minst en Future Watch Autograph och ytterligare en autograf per box i snitt.","Demidov, Schaefer, Misa och Leonard finns i de centrala signerade rookiespåren."],
 "tiers":{"everyday":{"label":"Vanligt men intressant","score":91,"items":["2 autografer per box i snitt","10 Limited Red per box i snitt"]},"good":{"label":"Bra träff","score":92,"items":["Future Watch Autograph /999"]},"big":{"label":"Riktigt bra","score":95,"items":["Future Watch Auto Patch /100","Sign of the Times Rookie /25"]},"jackpot":{"label":"Monsterhit","score":97,"items":["Future Watch Auto Patch Black 1/1"]}},
 "caveat":"Boxsnitten gäller autografkategorierna, inte ett visst namn. Två autografer i snitt är inte samma sak som två topprookie-autografer."
},
"cc-2025-26-ultimate-hobby": {
 "source_name":"Upper Deck 2025-26 NHL Ultimate Collection checklist",
 "source_url":"https://upperdeck.com/checklist/2025-26-nhl-ultimate-collection-checklist/",
 "key_names":["Matthew Schaefer","Michael Misa","Ivan Demidov","Ryan Leonard","Zeev Buium","Sam Dickinson"],
 "headline_chases":[
   {"card":"Ultimate Rookies Autographs /299","tier":"MYCKET BRA","odds":"serial /299; exakt rookie varierar","why":"Produktens centrala signerade rookie-spår."},
   {"card":"Matthew Schaefer Ultimate Phenoms Gold Auto /25","tier":"MONSTER","odds":"serial /25","why":"Namngiven topprookie på lågnumrerad autograf."},
   {"card":"Matthew Schaefer eller Michael Misa Ultimate Phenoms Purple Auto /5","tier":"JACKPOT","odds":"serial /5","why":"Endast fem exemplar per kort."},
   {"card":"Matthew Schaefer eller Michael Misa Ultimate Phenoms Black Auto 1/1","tier":"JACKPOT","odds":"1/1","why":"Unik signerad rookie-toppträff."}
 ],
 "why_exciting":["Checklistan är byggd kring premiumautografer, memorabilia och lågnumrerade rookies.","Schaefer och Misa har verifierade Ultimate Phenoms-autografer ned till 1/1."],
 "tiers":{"everyday":{"label":"Vanligt men intressant","score":88,"items":["Premiumkort i ett pack"]},"good":{"label":"Bra träff","score":89,"items":["Ultimate Rookies Autograph /299"]},"big":{"label":"Riktigt bra","score":95,"items":["Ultimate Phenoms Gold Auto /25"]},"jackpot":{"label":"Monsterhit","score":98,"items":["Ultimate Phenoms Purple /5 eller Black 1/1"]}},
 "caveat":"Checklistan verifierar att korten finns, men BoxFinder saknar ett officiellt publicerat individuellt boxodds för de namngivna korten och visar därför bara serienumreringen."
},
"cc-2025-26-premier-hobby": {
 "source_name":"Upper Deck 2025-26 Premier checklist",
 "source_url":"https://upperdeck.com/checklist/2025-26-premier-checklist/",
 "key_names":["Ivan Demidov","Matthew Schaefer","Michael Misa","Ryan Leonard","Zeev Buium","Gabe Perreault"],
 "headline_chases":[
   {"card":"Ivan Demidov Acetate Rookie Patch Auto /99","tier":"MONSTER","odds":"serial /99","why":"Premier-seriens klassiska signerade acetate-rookie med patch."},
   {"card":"Matthew Schaefer Premier Gear Rookies Patch /25","tier":"MONSTER","odds":"serial /25","why":"Namngiven topprookie med lågnumrerad memorabilia."},
   {"card":"Matthew Schaefer Premier Gear Rookies Premium Patch /3","tier":"JACKPOT","odds":"serial /3","why":"Endast tre exemplar."},
   {"card":"Matthew Schaefer Viewpoints Auto Patch Gold /5","tier":"JACKPOT","odds":"serial /5","why":"Signerad premiumträff med patch."},
   {"card":"Michael Misa Acetate Rookie Patch Auto Platinum 1/1","tier":"JACKPOT","odds":"1/1","why":"Unik rookieauto-patch."}
 ],
 "why_exciting":["Premier kombinerar namngivna topprookies med autografer och patchar.","Demidov, Schaefer och Misa har verifierade premiumkort från /99 ned till 1/1."],
 "tiers":{"everyday":{"label":"Vanligt men intressant","score":89,"items":["6 premiumkort i ett pack"]},"good":{"label":"Bra träff","score":91,"items":["Rookieauto eller memorabilia"]},"big":{"label":"Riktigt bra","score":96,"items":["Demidov Acetate Rookie Patch Auto /99","Schaefer Patch /25"]},"jackpot":{"label":"Monsterhit","score":99,"items":["Premium Patch /3","Auto Patch /5","Platinum 1/1"]}},
 "caveat":"Serienumreringen är verifierad men inte ett packodds. En box innehåller ett premium-pack, men en viss spelare eller korttyp är inte garanterad."
},
"cc-2025-26-rangers-box-set": {
 "source_name":"Upper Deck 2025-26 New York Rangers Centennial checklist",
 "source_url":"https://upperdeck.com/checklist/2025-26-nhl-new-york-rangers-centennial-checklist/",
 "key_names":["Wayne Gretzky","Mark Messier","Henrik Lundqvist","Brian Leetch","Mike Richter","Igor Shesterkin"],
 "headline_chases":[
   {"card":"Komplett Rangers Centennial base set","tier":"BRA","odds":"1 komplett base set per box","why":"Det garanterade samlarinnehållet."},
   {"card":"Red Parallel","tier":"BRA","odds":"1 per box","why":"Garanterad parallell."},
   {"card":"Blueshirt Best – Gretzky, Messier, Lundqvist eller Shesterkin","tier":"MYCKET BRA","odds":"1 Blueshirt Best per box; exakt spelare varierar","why":"Namngivna Rangers-ikoner och stjärnor."},
   {"card":"Henrik Lundqvist Autograph Parallel","tier":"MONSTER","odds":"Autograph Parallel 1:10 boxar; Lundqvist är SSP inom serien","why":"Signerad klubbikon."},
   {"card":"Mark Messier Autograph Parallel","tier":"JACKPOT","odds":"Autograph Parallel 1:10 boxar; Messier är SSP inom serien","why":"Signerad legend med SSP-status."}
 ],
 "why_exciting":["Varje box ger hela basesetet, en Red Parallel och ett Blueshirt Best-kort.","Autografparallellen ligger på 1:10 boxar och inkluderar flera namngivna Rangers-legender."],
 "tiers":{"everyday":{"label":"Vanligt men intressant","score":86,"items":["Komplett base set","Red Parallel 1/box","Blueshirt Best 1/box"]},"good":{"label":"Bra träff","score":76,"items":["Blueshirt Best på Gretzky, Messier eller Lundqvist"]},"big":{"label":"Riktigt bra","score":88,"items":["Autograph Parallel 1:10 boxar"]},"jackpot":{"label":"Monsterhit","score":82,"items":["Messier eller Lundqvist SSP-autograf"]}},
 "caveat":"1:10 är oddset för valfri Autograph Parallel, inte för en särskild spelare. Messier och Lundqvist är SSP, så deras individuella odds är lägre."
},
"cc-2026-topps-mls-chrome-value": {
 "source_name":"Topps 2026 Chrome MLS official checklist and odds",
 "source_url":"https://www.topps.com/pages/topps-mls-chrome",
 "key_names":["Lionel Messi","Son Heung-Min","Robert Lewandowski","Antoine Griezmann","Zavier Gozo","Mateo Silvetti RC","Julian Hall"],
 "headline_chases":[
   {"card":"Ray Wave Base Parallel","tier":"BRA","odds":"1:2 value-pack","why":"Value Box-exklusivt och återkommande parallelspår."},
   {"card":"Wonderkids – Zavier Gozo och namngivna unga spelare","tier":"BRA","odds":"Wonderkids 1:6 value-pack; exakt spelare ur checklistan","why":"Konkret prospectspår med retailodds."},
   {"card":"Lionel Messi Pearlers P-10","tier":"MYCKET BRA","odds":"Pearlers 1:2 622 value-pack; exakt Messi-kort är mer sällsynt","why":"Namngiven Messi-case-hit i checklistan."},
   {"card":"Chrome Autograph – Messi, Son, Lewandowski eller rookie","tier":"MONSTER","odds":"Chrome Autographs Base 1:342 value-pack; paralleller har separata odds","why":"Verifierad möjlighet till autograf i Value Box-formatet."},
   {"card":"Messi/Beckham Chrome Dual Autograph","tier":"JACKPOT","odds":"Chrome Dual Autographs 1:21 630 value-pack som kortfamilj","why":"Två globala ikoner på samma signerade kort."},
   {"card":"Chrome Anime – Messi eller Son","tier":"JACKPOT","odds":"Chrome Anime 1:78 655 value-pack","why":"Extremt sällsynt namngiven case-hit."}
 ],
 "why_exciting":["Ray Wave 1:2 och Wonderkids 1:6 ger återkommande retailinnehåll.","Autografer finns faktiskt i Value Box-formatet, men basautografen ligger på 1:342 pack och är därför inte nära en boxgaranti."],
 "tiers":{"everyday":{"label":"Vanligt men intressant","score":72,"items":["Ray Wave 1:2","Refractor 1:7"]},"good":{"label":"Bra träff","score":78,"items":["Wonderkids 1:6","Patriotic Passion 1:18"]},"big":{"label":"Riktigt bra","score":84,"items":["Chrome Autograph Base 1:342","Pearlers 1:2 622"]},"jackpot":{"label":"Monsterhit","score":88,"items":["Chrome Dual Auto 1:21 630","Chrome Anime 1:78 655"]}},
 "caveat":"Oddsen gäller kortfamiljer per Value-pack, inte en viss spelare. Hobbyexklusiva Summer Clash- och National Pairings-autografer visas inte som möjliga Value Box-träffar."
},
"cc-2026-topps-chrome-premier-league-hobby": {
 "source_name":"Topps 2026 Chrome Premier League official checklist and odds",
 "source_url":"https://www.topps.com/pages/topps-chrome-premier-league",
 "key_names":["Estêvão Willian RC #68","Rio Ngumoha RC #112","Max Dowman RC #201","Divine Mukasa RC #128","Shea Lacey RC #138","Chris Rigg RC #163"],
 "headline_chases":[
   {"card":"Estêvão Willian Base Rookie #68","tier":"BRA","odds":"Ingår i 200-korts basesetet; individuellt kortodds ej publicerat","why":"En av checklistans centrala rookies."},
   {"card":"Max Dowman Hobby-Exclusive Base Rookie #201","tier":"MONSTER","odds":"1:16 257 hobby-pack","why":"Hobbyexklusivt rookie-kort med publicerat odds."},
   {"card":"Estêvão Willian Helix HX-9","tier":"MONSTER","odds":"Helix 1:1 931 hobby-pack; exakt spelare är mer sällsynt","why":"Namngiven rookie i en premium-SSP-serie."},
   {"card":"Chrome Autograph – Estêvão, Rio Ngumoha eller Max Dowman","tier":"MYCKET BRA","odds":"1 autograf garanterad per hobbybox; Base Chrome Autos 1:123 hobby-pack","why":"Alla tre rookies finns i autografchecklistan."},
   {"card":"Saka/Henry Chrome Dual Autograph","tier":"JACKPOT","odds":"Chrome Dual Autographs 1:6 304 hobby-pack som kortfamilj","why":"Signerad stjärna/legend-kombination."},
   {"card":"Chrome Anime – Saka, Haaland, Estêvão eller Rio","tier":"JACKPOT","odds":"Chrome Anime 1:1 298 hobby-pack","why":"En av produktens viktigaste case-hit-familjer."}
 ],
 "why_exciting":["Varje hobbybox garanterar en autograf och innehåller tio vanliga inserts.","Dowman, Estêvão och Ngumoha finns både i rookie- och autografspåren."],
 "tiers":{"everyday":{"label":"Vanligt men intressant","score":88,"items":["1 autograf per box","10 vanliga inserts per box","6 refractors per box"]},"good":{"label":"Bra träff","score":89,"items":["Estêvão eller Ngumoha rookie","Chrome Autograph"]},"big":{"label":"Riktigt bra","score":94,"items":["Max Dowman #201 1:16 257","Helix 1:1 931"]},"jackpot":{"label":"Monsterhit","score":97,"items":["Chrome Anime 1:1 298","Dual/Triple Autograph","Superfractor 1/1"]}},
 "caveat":"Boxgarantin är en autograf från produktens samlade autografprogram, inte en garanterad topprookie. Angivna insertodds gäller serien som helhet."
},
"cc-2026-topps-finest-premier-league-wave2": {
 "source_name":"Topps Finest Premier League 2026 official checklist and odds",
 "source_url":"https://www.topps.com/pages/topps-finest-premier-league",
 "key_names":["Estêvão Willian RC","Max Dowman RC","Rio Ngumoha RC","Harry Gray RC","Shea Lacey RC","Chris Rigg RC"],
 "headline_chases":[
   {"card":"Estêvão Willian Finest Autograph FA-EW","tier":"MYCKET BRA","odds":"2 Chrome Autographs per box; exakt spelare ur autografchecklistan","why":"Namngiven rookieautograf."},
   {"card":"Max Dowman Arrivals Autograph AA-MD","tier":"MONSTER","odds":"2 Chrome Autographs per box över hela autografprogrammet","why":"Särskilt rookieautografspår."},
   {"card":"Max Dowman Polka PK-15","tier":"MONSTER","odds":"Polka 1:437 pack; exakt spelare är mer sällsynt","why":"Sällsynt namngiven rookieinsert."},
   {"card":"Estêvão Willian Aura AU-15","tier":"MONSTER","odds":"Aura 1:437 pack; exakt spelare är mer sällsynt","why":"Premiuminsert på en central rookie."},
   {"card":"Finest Autograph Superfractor 1/1","tier":"JACKPOT","odds":"Finest Autographs Superfractor 1:2 508 pack som kortfamilj","why":"Unik signerad toppparallel."}
 ],
 "why_exciting":["Två Chrome-autografer per box ger hög signerad hit density.","300-kortsbasen har Common, Uncommon och Rare tiers, så även basrookies har olika knapphet."],
 "tiers":{"everyday":{"label":"Vanligt men intressant","score":94,"items":["2 autografer per box","60 kort per box"]},"good":{"label":"Bra träff","score":91,"items":["Finest Autograph på stark spelare eller rookie"]},"big":{"label":"Riktigt bra","score":95,"items":["Polka/Aura 1:437","lågnumrerad autograf"]},"jackpot":{"label":"Monsterhit","score":98,"items":["Finest Autograph Superfractor 1/1","Aura eller Polka Superfractor 1/1"]}},
 "caveat":"Två autografer är garanterade men spelarna är inte det. Ett odds som 1:437 gäller hela insertfamiljen, inte Dowman eller Estêvão individuellt."
},
"cc-2025-26-topps-chrome-arsenal-hobby": {
 "source_name":"Topps Chrome Arsenal 2025/26 official product and checklist",
 "source_url":"https://uk.topps.com/pages/topps-chrome-arsenal",
 "key_names":["Max Dowman RC #49/#99","Josh Nichols RC #6/#56","Andre Harriman-Annous RC #24/#74","Olivia Smith RC #33/#83","Taylor Hinds RC #27/#77","Bukayo Saka","Thierry Henry"],
 "headline_chases":[
   {"card":"Max Dowman Base Rookie #49 och image variation #99","tier":"BRA","odds":"Ingår i 100-kortsbasen; individuellt kortodds ej publicerat","why":"Produktens tydligaste unga herrrookie."},
   {"card":"Max Dowman Base Card Autograph BC-MD","tier":"MYCKET BRA","odds":"2 autografer per box över hela autografprogrammet","why":"Namngiven rookieautograf."},
   {"card":"Olivia Smith Arsenal All Stars Rookie Autograph AA-OS","tier":"MYCKET BRA","odds":"Ingår i autografprogrammet; individuellt odds ej publicerat","why":"Namngiven rookie från damlaget."},
   {"card":"Thierry Henry Golden Title GT-7 /49","tier":"MONSTER","odds":"Golden Title /49; insertfamiljen förekommer i snitt en gång per två case","why":"Lågnumrerad Invincibles-chase."},
   {"card":"Thierry Henry 228 & Out Autograph BB-TH","tier":"JACKPOT","odds":"Ingen individuell frekvens publicerad","why":"Specialautograf för klubbens rekordmålskytt."},
   {"card":"Bukayo Saka The Arsenal Away Autograph 1/1","tier":"JACKPOT","odds":"1/1","why":"Unik signerad förstakortsträff."}
 ],
 "why_exciting":["Varje box innehåller två autografer och fem numrerade paralleller.","Checklistan täcker herrar, damer, unga spelare och Arsenal-legender."],
 "tiers":{"everyday":{"label":"Vanligt men intressant","score":94,"items":["2 autografer per box","5 numrerade paralleller per box"]},"good":{"label":"Bra träff","score":91,"items":["Dowman eller Olivia Smith rookieauto"]},"big":{"label":"Riktigt bra","score":95,"items":["Golden Title /49","stjärn-/legendautograf"]},"jackpot":{"label":"Monsterhit","score":98,"items":["The Arsenal Away Auto 1/1","Thierry Henry 228 & Out Auto"]}},
 "caveat":"Två autografer per box gäller hela checklistan. The Arsenal Away är ett 1/1-spår men en specifik spelare är extremt mycket svårare än boxgarantin."
},
"cc-2026-topps-argentina-team-set": {
 "source_name":"Topps Argentina Team Set 2026 official product and checklist",
 "source_url":"https://es.topps.com/pages/argentina-team-set",
 "key_names":["Franco Mastantuono #8","Nico Paz #9","Lionel Messi #16","Máximo Perrone National Debut #12","Joaquín Panichelli National Debut #20"],
 "headline_chases":[
   {"card":"Franco Mastantuono Base #8","tier":"BRA","odds":"Ingår i 50-kortsbasen; individuellt kortodds ej publicerat","why":"En av produktens främsta unga spelare."},
   {"card":"Rainbow Flick – Messi, Mastantuono eller Nico Paz","tier":"MYCKET BRA","odds":"1 Rainbow Flick per box; exakt spelare ur 25-kortsgruppen","why":"Garanterat insertspår med både stjärnor och unga spelare."},
   {"card":"Franco Mastantuono Base Autograph BC-FM","tier":"MONSTER","odds":"1 autograf i varannan box över hela autografprogrammet","why":"Namngiven ung spelarautograf."},
   {"card":"Lionel Messi Bona Fide Baller eller Golden Sun Autograph","tier":"JACKPOT","odds":"Autograf 1:2 boxar som familj; individuellt Messi-odds ej publicerat","why":"Messi finns i två verifierade autografserier."},
   {"card":"Lionel Messi Vis10nary Autograph VI-LM","tier":"JACKPOT","odds":"Ultra-rare; exakt odds ej publicerat","why":"Exklusiv autografserie med endast Messi."}
 ],
 "why_exciting":["Autograf kommer i varannan box och två numrerade paralleller per box.","Messi, Mastantuono och Nico Paz finns i konkreta chase-spår."],
 "tiers":{"everyday":{"label":"Vanligt men intressant","score":86,"items":["2 numrerade paralleller","1 Rainbow Flick per box","3 Halo parallels"]},"good":{"label":"Bra träff","score":84,"items":["Mastantuono/Nico Paz parallel eller Rainbow Flick"]},"big":{"label":"Riktigt bra","score":93,"items":["Autograf 1:2 boxar","Mastantuono auto"]},"jackpot":{"label":"Monsterhit","score":98,"items":["Messi Golden Sun/Bona Fide Baller Auto","Vis10nary Messi Auto"]}},
 "caveat":"1:2 avser valfri autograf, inte Messi. Vis10nary beskrivs officiellt som ultra-rare men Topps publicerar inget exakt odds."
},
"cc-2025-26-topps-real-madrid-team-set": {
 "source_name":"Topps Real Madrid Team Set 2025/26 official product and checklist",
 "source_url":"https://uk.topps.com/pages/topps-real-madrid-2025-26-team-set",
 "key_names":["Franco Mastantuono RC #14","Víctor Valdepeñas RC #5","Thiago Pitarch RC #9","Kylian Mbappé #17","Vini Jr. #16","Jude Bellingham #10"],
 "headline_chases":[
   {"card":"Franco Mastantuono Base Rookie #14","tier":"BRA","odds":"Ingår i 50-kortsbasen; individuellt kortodds ej publicerat","why":"Produktens starkaste namngivna rookie."},
   {"card":"Rainbow Flick – Mastantuono, Mbappé, Vini eller Bellingham","tier":"MONSTER","odds":"1 Rainbow Flick per case; exakt spelare ur 25-kortsgruppen","why":"Verifierad case hit med toppnamn."},
   {"card":"Franco Mastantuono Base Autograph BC-MA","tier":"MONSTER","odds":"1 autograf i varannan box över hela autografprogrammet","why":"Namngiven rookieautograf."},
   {"card":"Jude Bellingham Base Autograph BC-JB","tier":"MONSTER","odds":"Autograf 1:2 boxar som familj; individuellt odds ej publicerat","why":"Signerad världsstjärna."},
   {"card":"Vini Jr. Bona Fide Baller Autograph BB-VJ","tier":"JACKPOT","odds":"Autograf 1:2 boxar som familj; individuellt odds ej publicerat","why":"En av produktens största signerade träffar."}
 ],
 "why_exciting":["Autograf i varannan box, två numrerade paralleller och en Static Foil per box.","Mastantuono, Mbappé, Vini och Bellingham ger både rookie- och stjärnspår."],
 "tiers":{"everyday":{"label":"Vanligt men intressant","score":84,"items":["2 numrerade paralleller","1 Static Foil","3 Halo parallels"]},"good":{"label":"Bra träff","score":84,"items":["Mastantuono rookieparallel","Mbappé/Vini/Bellingham insert"]},"big":{"label":"Riktigt bra","score":93,"items":["Autograf 1:2 boxar","Rainbow Flick case hit"]},"jackpot":{"label":"Monsterhit","score":97,"items":["Mastantuono rookieauto","Bellingham eller Vini auto"]}},
 "caveat":"Autografoddset gäller vilken autograf som helst. Rainbow Flick är en case hit som familj och inte en garanterad viss spelare."
},
"cc-2025-26-topps-ucc-flagship-hanger": {
 "source_name":"Topps 2025-26 UEFA Club Competitions official checklist and odds",
 "source_url":"https://www.topps.com/pages/uefa-club-competitions",
 "key_names":["Estêvão Willian RC #66","Franco Mastantuono RC #172","Rio Ngumoha RC #191","Lennart Karl RC #187","Jobe Bellingham RC #5","Konstantinos Karetsas RC #150"],
 "headline_chases":[
   {"card":"Estêvão Willian Base Rookie #66","tier":"BRA","odds":"Ingår i 200-kortsbasen; individuellt kortodds ej publicerat","why":"Central rookie i UCC Flagship."},
   {"card":"Trophy Chasers","tier":"BRA","odds":"1:2 hanger-pack","why":"Vanligaste namngivna insertfamiljen i hangerformatet."},
   {"card":"Base Card Short Print – Estêvão eller Rio Ngumoha","tier":"MYCKET BRA","odds":"Base Short Prints 1:527 hanger-pack; exakt spelare är mer sällsynt","why":"Verifierad SP-lista med namngivna rookies."},
   {"card":"Estêvão Willian eller Rio Ngumoha Base Autograph","tier":"MONSTER","odds":"Base Autos 1:112 hanger-pack som familj","why":"Båda rookies finns i Base Auto-checklistan."},
   {"card":"Base Card Super Short Print – Estêvão Willian","tier":"JACKPOT","odds":"Base SSP 1:9 453 hanger-pack; exakt Estêvão-kort är mer sällsynt","why":"Extremt sällsynt rookievariation."},
   {"card":"Future Stars Autograph – Endrick, Nwaneri eller Rodrigo Mora","tier":"JACKPOT","odds":"Future Stars Autos 1:1 319 hanger-pack som familj","why":"Verifierat ungt autografspår i hangerformatet."}
 ],
 "why_exciting":["Hangerformatet har Base Autos 1:112 pack och flera vanliga inserts mellan 1:2 och 1:6.","Checklistan innehåller Estêvão, Mastantuono, Ngumoha, Karl och andra tydligt namngivna rookies."],
 "tiers":{"everyday":{"label":"Vanligt men intressant","score":74,"items":["Trophy Chasers 1:2","Roots 1:3","Born Champ 1:4"]},"good":{"label":"Bra träff","score":80,"items":["Stark rookie","Holo-parallel","SP 1:527"]},"big":{"label":"Riktigt bra","score":88,"items":["Base Auto 1:112","Future Stars Auto 1:1 319"]},"jackpot":{"label":"Monsterhit","score":91,"items":["Rookie SSP 1:9 453","lågnumrerad autograf eller Foilfractor"]}},
 "caveat":"Oddsen gäller ett 35-korts hanger-pack. De gäller hela kortfamiljen, så en viss rookie eller autograf är mer sällsynt än familjeoddset."
},
"cc-2025-26-pitch-kings-la-liga": {
 "source_name":"Panini Pitch Kings La Liga 2025/26 official product details and verified checklist",
 "source_url":"https://www.paniniamerica.net/2025-26-panini-pitch-kings-soccer-trading-card-box-hobby-international",
 "key_names":["Karl Etta Eyong RC #93","Carlos Macia RC #25","Pablo Garcia RC #26","Jan Virgili RC #47","Lamine Yamal","Kylian Mbappé","Jude Bellingham"],
 "headline_chases":[
   {"card":"Karl Etta Eyong Base Rookie #93 eller Blackout #3","tier":"MYCKET BRA","odds":"3 Rookies I-IV per box i snitt; Blackout är ultra-rare utan publicerat odds","why":"Namngiven rookie med både bas- och SSP-spår."},
   {"card":"Lamine Yamal Le Cinque Più Belle #1","tier":"MONSTER","odds":"Ultra-rare insert; individuellt odds ej publicerat","why":"Femkorts-SSP med checklistans största namn."},
   {"card":"Kylian Mbappé Le Cinque Più Belle #2","tier":"MONSTER","odds":"Ultra-rare insert; individuellt odds ej publicerat","why":"Namngiven premiuminsert på Real Madrid-stjärnan."},
   {"card":"Lamine Yamal Fresh Paint Autograph #7","tier":"JACKPOT","odds":"1 autograf per box över hela autografprogrammet","why":"Verifierad Yamal-signatur i Fresh Paint."},
   {"card":"Kylian Mbappé Legacy Portrait Signatures #9","tier":"JACKPOT","odds":"1 autograf per box; individuellt Mbappé-odds ej publicerat","why":"Legends/stars-autograf på checklistans toppnamn."},
   {"card":"Masterpiece Parallel 1/1","tier":"JACKPOT","odds":"1/1; exakt spelare och kortserie varierar","why":"Produktens unika toppparallel."}
 ],
 "why_exciting":["Varje hobbybox ger en autograf och tre rookie-kort från Rookies I-IV i snitt.","La Liga-checklistan kombinerar Yamal, Mbappé och Bellingham med ultra-rare Blackout/Le Cinque Più Belle och 1/1-paralleller."],
 "tiers":{"everyday":{"label":"Vanligt men intressant","score":92,"items":["1 autograf per box","3 Rookies I-IV","2 base-paralleller"]},"good":{"label":"Bra träff","score":89,"items":["Karl Etta Eyong eller annan namngiven rookie","numrerad parallel"]},"big":{"label":"Riktigt bra","score":95,"items":["Blackout","Le Cinque Più Belle","stjärnauto"]},"jackpot":{"label":"Monsterhit","score":98,"items":["Yamal eller Mbappé-auto","Masterpiece 1/1"]}},
 "caveat":"Boxinnehållet anges som genomsnitt. Autografen är inte garanterat Yamal eller Mbappé, och Panini publicerar inget exakt odds för Blackout eller Le Cinque Più Belle."
},
"cc-2026-futera-world-football-fx3": {
 "source_name":"Futera FX World Football Series 3 official checklist",
 "source_url":"https://www.futera.com/checklists",
 "key_names":["Lamine Yamal","Lionel Messi","Cristiano Ronaldo","Kylian Mbappé","Jude Bellingham","Ethan Nwaneri","Pau Cubarsí"],
 "headline_chases":[
   {"card":"Lamine Yamal Portrait Base FXB160 Diamond","tier":"MONSTER","odds":"Base parallel 1/1; individuellt boxodds ej publicerat","why":"Checklistans högsta basparallel på ett toppnamn."},
   {"card":"Lionel Messi Gamechanger GC27 Diamond","tier":"MONSTER","odds":"Gamechanger Diamond 1/1; övriga paralleller /6 eller lägre","why":"Numrerat rare insert på Messi."},
   {"card":"Messi / Cristiano Ronaldo Versus Memorabilia VS11","tier":"JACKPOT","odds":"Numrerad dual memorabilia; exakt print run/boxodds ej publicerat i checklistan","why":"Båda moderna ikonerna på samma memorabilia-kort."},
   {"card":"Lionel Messi Modern On-Card Autograph MDA19","tier":"JACKPOT","odds":"1 autograf, memorabilia eller numrerat rare insert per box som gemensam hitgrupp","why":"Verifierad on-card Messi-signatur."},
   {"card":"Lamine Yamal Modern On-Card Autograph MDA18","tier":"JACKPOT","odds":"Ingår i on-card-autografprogrammet; individuellt odds ej publicerat","why":"Namngiven ung superstjärna på hard-signed kort."},
   {"card":"Yamal OFOA01 eller Messi OFOA03 Unique Auto","tier":"JACKPOT","odds":"1/1","why":"Unik on-card-autograf och produktens tydligaste toppträff."}
 ],
 "why_exciting":["Checklistan innehåller on-card-autografer, numrerad memorabilia och rare inserts på världsstjärnor.","Två numrerade paralleller plus en autograph/relic/rare insert per box i snitt ger flera separata chase-vägar."],
 "tiers":{"everyday":{"label":"Vanligt men intressant","score":87,"items":["2 numrerade paralleller per box","1 ytterligare insert"]},"good":{"label":"Bra träff","score":90,"items":["Gamechanger/Heroes/Maestro","stjärnparallel /29 eller lägre"]},"big":{"label":"Riktigt bra","score":95,"items":["On-card autograph","numrerad memorabilia"]},"jackpot":{"label":"Monsterhit","score":99,"items":["Messi/Yamal auto","Messi–Ronaldo memorabilia","Unique Auto 1/1"]}},
 "caveat":"Boxens huvudhit kan vara autograf, memorabilia eller ett numrerat rare insert; autograf är alltså inte garanterad. Futeras checklista verifierar namn och serienummer men publicerar inte individuella boxodds."
},
"cc-2025-26-panini-prizm-fifa-retail": {
 "source_name":"Panini Prizm FIFA 2025/26 retail configuration and checklist",
 "source_url":"https://www.collectosk.com/2025-26-panini-prizm-fifa-soccer-cards/",
 "key_names":["Rio Ngumoha #106","Franco Mastantuono #194","Pio Esposito #78","Lamine Yamal","Lionel Messi","Kylian Mbappé","Vini Jr."],
 "headline_chases":[
   {"card":"Rio Ngumoha Base #106 eller Emergent #8","tier":"BRA","odds":"24 retail-pack per box; individuellt kortodds ej publicerat","why":"Namngivet ungt Liverpool-spår."},
   {"card":"Franco Mastantuono Base #194 eller Flashback 2015 #4","tier":"BRA","odds":"Ingår i retailchecklistan; individuellt kortodds ej publicerat","why":"Namngivet Real Madrid-prospect."},
   {"card":"Numrerad Pulsar Parallel","tier":"MYCKET BRA","odds":"1 per retailbox i snitt","why":"Garanterad numrerad chase på boxnivå i snitt."},
   {"card":"Red Pulsar Autograph – Yamal, Messi, Mbappé eller annan signerare","tier":"MONSTER","odds":"1 Red Pulsar Autograph per 2 retailboxar i snitt; exakt spelare är mer sällsynt","why":"Retailformatets tydliga autografspår."},
   {"card":"Lamine Yamal Manga #5 eller Color Blast #1","tier":"JACKPOT","odds":"SSP; exakt retailodds ej publicerat","why":"Två av produktens mest eftertraktade Yamal-inserts."},
   {"card":"Lionel Messi Manga #19 eller Club Legend Signatures #1","tier":"JACKPOT","odds":"SSP/autograf; individuellt retailodds ej publicerat","why":"Namngivna Messi-toppträffar i checklistan."}
 ],
 "why_exciting":["Retaildisplayen har en Red Pulsar-autograf i varannan box i snitt, plus en numrerad Pulsar per box.","96 kort per box ger betydligt fler chanser på basprospects och inserts än Choice-formatets åtta kort."],
 "tiers":{"everyday":{"label":"Vanligt men intressant","score":82,"items":["24 pack","2 Base Silver","6 inserts"]},"good":{"label":"Bra träff","score":86,"items":["1 numrerad Pulsar","Ngumoha/Mastantuono/Pio Esposito"]},"big":{"label":"Riktigt bra","score":92,"items":["Red Pulsar Autograph 1:2 boxar","lågnumrerad stjärnparallel"]},"jackpot":{"label":"Monsterhit","score":96,"items":["Yamal/Messi/Mbappé-autograf","Manga eller Color Blast"]}},
 "caveat":"1:2 gäller valfri Red Pulsar Autograph per retailbox, inte en viss spelare. Choice- och hobbyexklusiva paralleller räknas inte som möjliga retailträffar."
},
"cc-2025-26-panini-prizm-fifa-choice": {
 "source_name":"Panini Prizm FIFA 2025/26 checklist and Choice configuration",
 "source_url":"https://www.collectosk.com/2025-26-panini-prizm-fifa-soccer-cards/",
 "key_names":["Rio Ngumoha #106","Franco Mastantuono #194","Pio Esposito #78","Lamine Yamal","Lionel Messi","Kylian Mbappé","Vini Jr."],
 "headline_chases":[
   {"card":"Rio Ngumoha Base #106 eller Emergent #8","tier":"BRA","odds":"Ingår i 300-kortsbasen/inserts; individuellt kortodds ej publicerat","why":"Namngivet ungt Liverpool-spår."},
   {"card":"Choice Snake Year /48 eller Choice Cherry Blossom /28","tier":"MYCKET BRA","odds":"3 numrerade Choice Prizms per box över Choice-parallellerna","why":"Formatunika, numrerade Choice-paralleller."},
   {"card":"Lamine Yamal Sensational Signatures #1","tier":"MONSTER","odds":"1 autograf per Choice-box över hela autografprogrammet","why":"Namngiven toppstjärna i autografchecklistan."},
   {"card":"Lionel Messi Club Legend Signatures #1","tier":"JACKPOT","odds":"1 autograf per Choice-box; individuellt Messi-odds ej publicerat","why":"En av produktens främsta signerade chaser."},
   {"card":"Kylian Mbappé / Vini Jr. Dual Signatures #3","tier":"JACKPOT","odds":"Ingår i Dual Signatures; individuellt boxodds ej publicerat","why":"Två Real Madrid-stjärnor på samma signerade kort."},
   {"card":"Choice Nebula 1/1","tier":"JACKPOT","odds":"1/1; exakt spelare varierar","why":"Choice-formatets unika toppparallel."}
 ],
 "why_exciting":["En autograf och tre numrerade Choice Prizms per box ger hög hit-koncentration.","Choice har egna paralleller ned till Nebula 1/1 och checklistan innehåller Messi, Yamal, Mbappé och flera unga spelare."],
 "tiers":{"everyday":{"label":"Vanligt men intressant","score":92,"items":["1 autograf per box","3 numrerade Choice Prizms","3 övriga Choice Prizms"]},"good":{"label":"Bra träff","score":88,"items":["Ngumoha/Mastantuono/Pio Esposito","Choice /88 eller /48"]},"big":{"label":"Riktigt bra","score":95,"items":["Yamal eller Mbappé-autograf","Choice /28 eller /18"]},"jackpot":{"label":"Monsterhit","score":98,"items":["Messi-autograf","Dual Signatures","Choice Nebula 1/1"]}},
 "caveat":"Boxgarantin gäller valfri autograf och tre numrerade Choice-paralleller, inte en viss spelare. Manga, Color Blast och andra SSP finns i checklistan men något formatunikt Choice-odds är inte publicerat."
},
"cc-2025-26-topps-bayern-lineage": {
 "source_name":"Topps FC Bayern München Lineage 2025/26 official checklist",
 "source_url":"https://uk.topps.com/pages/topps-lineage-fc-bayern-munchen",
 "key_names":["Lennart Karl RC #17","Jonas Urbig RC #2","Momoko Tanikawa RC #18","Wisdom Mike RC #25","Harry Kane","Jamal Musiala","Thomas Müller","Franz Beckenbauer"],
 "headline_chases":[
   {"card":"Lennart Karl Base Rookie #17","tier":"BRA","odds":"Ingår i 45-kortsbasen; individuellt kortodds ej publicerat","why":"Checklistans centrala Bayern-rookie."},
   {"card":"Lennart Karl Icons On-Card Autograph IA-LK","tier":"MONSTER","odds":"Ingår i on-card-autografprogrammet; individuellt odds ej publicerat","why":"Verifierad rookieautograf."},
   {"card":"Harry Kane Meister Kane On-Card Autograph MKA-HK","tier":"JACKPOT","odds":"Individuellt odds ej publicerat","why":"Produktens uttalade Kane-toppkort."},
   {"card":"Thomas Müller Es Müllert On-Card Autograph EMA-TM","tier":"JACKPOT","odds":"Individuellt odds ej publicerat","why":"Dedikerad on-card-signatur för klubbikonen."},
   {"card":"Kane / Luis Díaz / Michael Olise Triple Red Autograph TRA-KDO","tier":"JACKPOT","odds":"Triple autograph; individuellt odds ej publicerat","why":"Tre offensiva stjärnor på samma signerade kort."},
   {"card":"Davies / Musiala / Lennart Karl Triple Red Autograph TRA-DMK","tier":"JACKPOT","odds":"Triple autograph; individuellt odds ej publicerat","why":"Kopplar ihop klubbens nutid och nästa generation."}
 ],
 "why_exciting":["Tre encased autographs, autograph relics eller relics per box ger extremt hög premium-hit-täthet.","Checklistan har on-card-signaturer, dual/triple autos samt fyra tydligt markerade rookies."],
 "tiers":{"everyday":{"label":"Vanligt men intressant","score":96,"items":["3 encased premiumhits per box","7 kort totalt"]},"good":{"label":"Bra träff","score":94,"items":["On-card autograph","rookieauto eller relic"]},"big":{"label":"Riktigt bra","score":97,"items":["Lennart Karl auto","Musiala/Kane premiumhit"]},"jackpot":{"label":"Monsterhit","score":99,"items":["Meister Kane","Es Müllert","Triple Red/Triple Winner Auto"]}},
 "caveat":"Tre premiumhits per box är verifierat, men Topps publicerar inte individuella odds för Karl, Kane, Müller eller triple-autograferna. En relic kan vara en av de tre träffarna."
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
 "source_name":"Official Pokémon Paradox Rift card list",
 "source_url":"https://assets.pokemon.com/assets/cms2/pdf/trading-card-game/checklist/par_web_cardlist_en.pdf",
 "key_names":["Roaring Moon ex #251","Iron Valiant ex #249","Groudon #199","Garchomp ex #245","Professor Sada's Vitality #256"],
 "headline_chases":[
   {"card":"Groudon #199 / Illustration Rare","tier":"BRA","odds":"Finns i Paradox Rift; officiella packodds ej publicerade","why":"Namngiven Illustration Rare med stark samlarefterfrågan."},
   {"card":"Garchomp ex #245 / Special Illustration Rare","tier":"MYCKET BRA","odds":"Finns i Paradox Rift; officiella packodds ej publicerade","why":"Special Illustration Rare av en populär Pokémon."},
   {"card":"Iron Valiant ex #249 / Special Illustration Rare","tier":"MONSTER","odds":"Finns i Paradox Rift; officiella packodds ej publicerade","why":"En av setets två centrala Paradox-chaser."},
   {"card":"Roaring Moon ex #251 / Special Illustration Rare","tier":"JACKPOT","odds":"Finns i Paradox Rift; officiella packodds ej publicerade","why":"Setets tydligaste namngivna chase."},
   {"card":"Roaring Moon ex #262 / Hyper Rare","tier":"MONSTER","odds":"Finns i Paradox Rift; officiella packodds ej publicerade","why":"Guldversionen av huvudkaraktären."}
 ],
 "why_exciting":[
   "18 boosterpaket ger många separata chanser att träffa setets illustration- och rarity-chaser.",
   "Förseglad display passar bättre för ren packöppning än collection-produkter där en del av priset ligger i promos/tillbehör."
 ],
 "tiers":{
   "everyday":{"label":"Vanligt men intressant","score":78,"items":["18 boosterpaket"]},
   "good":{"label":"Bra träff","score":72,"items":["Groudon #199","Garchomp ex #245"]},
   "big":{"label":"Riktigt bra","score":78,"items":["Iron Valiant ex #249","Roaring Moon ex #262"]},
   "jackpot":{"label":"Monsterhit","score":84,"items":["Roaring Moon ex #251 SIR"]}
 },
 "caveat":"Kortens närvaro verifieras i den officiella checklistan. Pokémon publicerar inte kortspecifika packodds, så BoxFinder visar inga uppskattade odds som fakta."
},
"cc-pokemon-temporal-forces-18": {
 "source_name":"Official Pokémon Temporal Forces card database",
 "source_url":"https://www.pokemon.com/us/pokemon-tcg/pokemon-cards/series/sv05/",
 "key_names":["Raging Bolt ex #208","Iron Crown ex #206","Walking Wake ex #205","Iron Leaves ex #203","Morty's Conviction #211"],
 "headline_chases":[
   {"card":"Iron Leaves ex #203 / Special Illustration Rare","tier":"MYCKET BRA","odds":"Finns i Temporal Forces; officiella packodds ej publicerade","why":"Namngiven SIR i Future-spåret."},
   {"card":"Walking Wake ex #205 / Special Illustration Rare","tier":"MYCKET BRA","odds":"Finns i Temporal Forces; officiella packodds ej publicerade","why":"Illustrationschase med legendarisk Paradox-Pokémon."},
   {"card":"Iron Crown ex #206 / Special Illustration Rare","tier":"MONSTER","odds":"Finns i Temporal Forces; officiella packodds ej publicerade","why":"En av setets främsta Future-chaser."},
   {"card":"Raging Bolt ex #208 / Special Illustration Rare","tier":"JACKPOT","odds":"Finns i Temporal Forces; officiella packodds ej publicerade","why":"En central samlar- och spelchase i setet."},
   {"card":"Morty's Conviction #211 / Special Illustration Rare","tier":"MONSTER","odds":"Finns i Temporal Forces; officiella packodds ej publicerade","why":"Namngiven supporter-SIR med Gengar i motivet."}
 ],
 "why_exciting":["18 boosterpaket ger många försök på fyra namngivna Paradox-SIR och Morty's Conviction.","Displayformatet lägger hela inköpet på packinnehåll i stället för promos och tillbehör."],
 "tiers":{"everyday":{"label":"Vanligt men intressant","score":78,"items":["18 boosterpaket"]},"good":{"label":"Bra träff","score":73,"items":["Iron Leaves ex #203","Walking Wake ex #205"]},"big":{"label":"Riktigt bra","score":81,"items":["Iron Crown ex #206","Morty's Conviction #211"]},"jackpot":{"label":"Monsterhit","score":87,"items":["Raging Bolt ex #208 SIR"]}},
 "caveat":"Checklistan verifierar korten men inte hur ofta de ligger i pack. Inga internetuppskattningar presenteras som officiella Pokémon-odds."
},
"cc-pokemon-shrouded-fable-kingambit": {
 "source_name":"Official Pokémon Shrouded Fable card database",
 "source_url":"https://www.pokemon.com/us/pokemon-tcg/scarlet-violet-shrouded-fable",
 "key_names":["Cassiopeia #94","Pecharunt ex #93","Fezandipiti ex #92","Munkidori ex #91","Persian #78"],
 "headline_chases":[
   {"card":"Persian #78 / Illustration Rare","tier":"BRA","odds":"Ur fyra Shrouded Fable-pack; officiella packodds ej publicerade","why":"Populär namngiven Illustration Rare."},
   {"card":"Munkidori ex #91 / Special Illustration Rare","tier":"MYCKET BRA","odds":"Ur fyra Shrouded Fable-pack; officiella packodds ej publicerade","why":"En av Loyal Three-SIR-korten."},
   {"card":"Fezandipiti ex #92 / Special Illustration Rare","tier":"MONSTER","odds":"Ur fyra Shrouded Fable-pack; officiella packodds ej publicerade","why":"Eftertraktad SIR och välkänd spelpjäs."},
   {"card":"Pecharunt ex #93 / Special Illustration Rare","tier":"MONSTER","odds":"Ur fyra Shrouded Fable-pack; officiella packodds ej publicerade","why":"Setets centrala mytiska Pokémon."},
   {"card":"Cassiopeia #94 / Special Illustration Rare","tier":"JACKPOT","odds":"Ur fyra Shrouded Fable-pack; officiella packodds ej publicerade","why":"En av setets tydligaste toppträffar."}
 ],
 "why_exciting":["Tre promo-kort ger säkert innehåll och fyra pack ger chans på namngivna SIR-kort.","Lägre inköpspris än full display, men bara fyra pack gör utfallet mycket variansrikt."],
 "tiers":{"everyday":{"label":"Vanligt men intressant","score":66,"items":["3 promo-kort","4 boosterpaket"]},"good":{"label":"Bra träff","score":62,"items":["Persian #78","Munkidori ex #91"]},"big":{"label":"Riktigt bra","score":70,"items":["Fezandipiti ex #92","Pecharunt ex #93"]},"jackpot":{"label":"Monsterhit","score":73,"items":["Cassiopeia #94 SIR"]}},
 "caveat":"Promokorten är garanterade men chase-korten kommer bara från de fyra slumpmässiga boostersen. Officiella packodds saknas."
},
"cc-pokemon-go-etb": {
 "source_name":"Official Pokémon GO card list",
 "source_url":"https://assets.pokemon.com/assets/cms2/pdf/trading-card-game/checklist/pgo_web_cardlist_en.pdf",
 "key_names":["Mewtwo V #72","Mewtwo VSTAR #79","Mewtwo VSTAR #86","Radiant Charizard #11","Dragonite VSTAR #81"],
 "headline_chases":[
   {"card":"Radiant Charizard #11","tier":"BRA","odds":"Finns i Pokémon GO; officiella packodds ej publicerade","why":"Charizard och Radiant-rarity ger tydlig samlarchase."},
   {"card":"Mewtwo V #72 / Ultra Rare","tier":"MYCKET BRA","odds":"Finns i Pokémon GO; officiella packodds ej publicerade","why":"Alternativ Mewtwo-bild i setets numrerade slutdel."},
   {"card":"Dragonite VSTAR #81 / Rainbow Rare","tier":"MONSTER","odds":"Finns i Pokémon GO; officiella packodds ej publicerade","why":"Numrerad toppversion av Dragonite VSTAR."},
   {"card":"Mewtwo VSTAR #79 / Rainbow Rare","tier":"MONSTER","odds":"Finns i Pokémon GO; officiella packodds ej publicerade","why":"Rainbow-version av setets huvudchase."},
   {"card":"Mewtwo VSTAR #86 / Gold Rare","tier":"JACKPOT","odds":"Finns i Pokémon GO; officiella packodds ej publicerade","why":"Guldversionen av Mewtwo VSTAR."}
 ],
 "why_exciting":["Mewtwo, Dragonite och Radiant Charizard ger flera igenkännbara säljspår.","ETB:n är öppningsbar men priset måste vägas mot att en del av kostnaden ligger i tillbehör."],
 "tiers":{"everyday":{"label":"Vanligt men intressant","score":70,"items":["Pokémon GO-pack","ETB-tillbehör"]},"good":{"label":"Bra träff","score":68,"items":["Radiant Charizard #11","Mewtwo V #72"]},"big":{"label":"Riktigt bra","score":75,"items":["Dragonite VSTAR #81","Mewtwo VSTAR #79"]},"jackpot":{"label":"Monsterhit","score":79,"items":["Mewtwo VSTAR #86 Gold"]}},
 "caveat":"Boxens packantal behöver verifieras på den aktuella butikssidan. Pokémon publicerar inte kortspecifika pull rates."
},
"cc-pokemon-white-flare-jp-display": {
 "source_name":"Pokémon Card Game White Flare set release and checklist",
 "source_url":"https://asia.pokemon-card.com/card-search/list/?expansionCodes=SV11W",
 "key_names":["Reshiram ex #174","Reshiram ex #168","Hilda #173","Hydreigon ex #171","Keldeo ex #169"],
 "headline_chases":[
   {"card":"Keldeo ex #169 / Special Art Rare","tier":"BRA","odds":"Ur japanska White Flare-pack; officiella packodds ej publicerade","why":"Namngiven SAR i setets secret-del."},
   {"card":"Hydreigon ex #171 / Special Art Rare","tier":"MYCKET BRA","odds":"Ur japanska White Flare-pack; officiella packodds ej publicerade","why":"Populär Pokémon i premiumillustration."},
   {"card":"Hilda #173 / Special Art Rare","tier":"MONSTER","odds":"Ur japanska White Flare-pack; officiella packodds ej publicerade","why":"Setets främsta trainer-chase."},
   {"card":"Reshiram ex #168 / Special Art Rare","tier":"MONSTER","odds":"Ur japanska White Flare-pack; officiella packodds ej publicerade","why":"Premiumillustration av setets huvud-Pokémon."},
   {"card":"Reshiram ex #174 / Black White Rare","tier":"JACKPOT","odds":"BWR i White Flare; officiella packodds ej publicerade","why":"Setets namngivna toppkort och högsta Reshiram-spår."}
 ],
 "why_exciting":["20 pack och 140 kort ger en bredare öppning än collection-boxar.","Reshiram ex finns både som SAR och exklusiv Black White Rare."],
 "tiers":{"everyday":{"label":"Vanligt men intressant","score":80,"items":["20 pack","140 kort"]},"good":{"label":"Bra träff","score":72,"items":["Keldeo ex #169","Hydreigon ex #171"]},"big":{"label":"Riktigt bra","score":84,"items":["Hilda #173","Reshiram ex #168"]},"jackpot":{"label":"Monsterhit","score":94,"items":["Reshiram ex #174 BWR"]}},
 "caveat":"Japanska boxkonfigurationer och rarity-fördelning ska inte översättas till engelska produktodds. Inga kortspecifika officiella pull rates är publicerade."
},
"cc-one-piece-op13-jp-display": {
 "source_name":"Bandai official OP-13 Carrying on His Will product page",
 "source_url":"https://en.onepiece-cardgame.com/products/boosters/op13/",
 "key_names":["Gol.D.Roger OP09-118","Monkey.D.Luffy OP13-118","Portgas.D.Ace OP13-119","Sabo OP13-120","Divine Departure OP13-076"],
 "headline_chases":[
   {"card":"Divine Departure OP13-076 / Gold Foil Event Alt-Art","tier":"MYCKET BRA","odds":"Officiella packodds ej publicerade","why":"Bandai lyfter kortet som särskilt guldfolierat eventkort."},
   {"card":"Monkey.D.Luffy OP13-118 / WANTED Edition","tier":"MONSTER","odds":"Officiella packodds ej publicerade","why":"En av fyra officiellt visade WANTED-varianter."},
   {"card":"Portgas.D.Ace OP13-119 / WANTED Edition","tier":"MONSTER","odds":"Officiella packodds ej publicerade","why":"Namngiven WANTED-chase med stark karaktärsefterfrågan."},
   {"card":"Sabo OP13-120 / WANTED Edition","tier":"MONSTER","odds":"Officiella packodds ej publicerade","why":"Namngiven WANTED-chase i brödratrion."},
   {"card":"Gol.D.Roger OP09-118 / WANTED Edition","tier":"JACKPOT","odds":"Officiella packodds ej publicerade","why":"Roger är den mest ikoniska av de fyra visade WANTED-korten."}
 ],
 "why_exciting":["24 pack ger många öppningschanser och checklistan har fyra exakt namngivna WANTED-kort.","Gold Foil Divine Departure är ytterligare en officiellt verifierad specialfinish."],
 "tiers":{"everyday":{"label":"Vanligt men intressant","score":80,"items":["24 pack","144 japanska kort"]},"good":{"label":"Bra träff","score":74,"items":["Alternate Art eller Secret Rare"]},"big":{"label":"Riktigt bra","score":88,"items":["Luffy/Ace/Sabo WANTED"]},"jackpot":{"label":"Monsterhit","score":96,"items":["Gol.D.Roger WANTED Edition"]}},
 "caveat":"Bandai verifierar checklistans specialkort men publicerar inte numeriska packodds. Japanska och engelska boxar har olika konfiguration och jämförs inte som samma SKU."
},
"cc-2025-topps-marvel-studios-chrome-hobby": {
 "source_name":"Topps official 2025 Marvel Studios Chrome checklist and hobby odds",
 "source_url":"https://www.topps.com/pages/topps-marvel-studios-chrome",
 "key_names":["Hugh Jackman Wolverine Autograph","Ryan Reynolds Deadpool Autograph","Chris Evans Captain America Autograph","Pedro Pascal Mister Fantastic Autograph","Elizabeth Olsen Scarlet Witch Autograph"],
 "headline_chases":[
   {"card":"Single Autograph – exempelvis Hugh Jackman, Ryan Reynolds eller Chris Evans","tier":"MYCKET BRA","odds":"1:25 hobby-pack för valfri Single Auto; en viss skådespelare är mycket mer sällsynt","why":"Äkta skådespelarsignaturer, inte facsimile."},
   {"card":"Pedro Pascal / Vanessa Kirby Dual Autograph DA-PK","tier":"MONSTER","odds":"Dual Autos 1:3 305 hobby-pack över hela dual-checklistan","why":"Två Fantastic Four-huvudroller på samma kort."},
   {"card":"Hugh Jackman / Ryan Reynolds Dual Autograph DA-JR","tier":"JACKPOT","odds":"Dual Autos 1:3 305 hobby-pack över hela dual-checklistan","why":"Wolverine och Deadpool med äkta signaturer."},
   {"card":"Fantastic Four: First Steps Auto Version","tier":"MONSTER","odds":"1:1 520 hobby-pack över insert-autografserien","why":"Dedikerat filmspår med Pedro Pascal, Vanessa Kirby och övriga huvudroller."},
   {"card":"Standard Sketch Card Silver Foil","tier":"MONSTER","odds":"1:143 hobby-pack","why":"Handritad sketch; motiv och artist varierar."},
   {"card":"Trio Autograph – exempelvis Fantastic Four TA-PIK","tier":"JACKPOT","odds":"Trio Autos 1:9 500 hobby-pack över hela trio-checklistan","why":"Tre äkta signaturer på samma kort."}
 ],
 "why_exciting":["Officiella Topps-odds visar Single Autos i 1:25 hobby-pack och sketchkort i 1:143.","Checklistan innehåller äkta signaturer från bland andra Hugh Jackman, Ryan Reynolds, Chris Evans, Elizabeth Olsen och Pedro Pascal."],
 "tiers":{"everyday":{"label":"Vanligt men intressant","score":84,"items":["10 pack","Rainbow Refractor 1:2 pack","Prism Refractor 1:6 pack"]},"good":{"label":"Bra träff","score":79,"items":["Single Auto 1:25 pack","numrerad refractor"]},"big":{"label":"Riktigt bra","score":91,"items":["Sketch 1:143 pack","Fantastic Four Auto 1:1 520"]},"jackpot":{"label":"Monsterhit","score":98,"items":["Jackman/Reynolds Dual Auto","Trio Auto","Superfractor 1/1"]}},
 "caveat":"Oddsen gäller kortfamiljen per hobby-pack, inte en särskild skådespelare. Tio pack innebär inte en garanterad autograf."
},
"cc-2026-topps-disney-chrome-value": {
 "source_name":"Topps official 2026 Chrome Disney checklist and Value Box odds",
 "source_url":"https://www.topps.com/pages/topps-chrome-disney",
 "key_names":["Mickey Mouse","Miley Cyrus Hannah Montana Autograph","Owen Wilson Lightning McQueen Autograph","Jodi Benson Ariel Autograph","Ming-Na Wen Mulan Autograph"],
 "headline_chases":[
   {"card":"Mickey Mouse, Donald Duck eller annan Base Refractor","tier":"BRA","odds":"1:4 value-pack över hela baschecklistan","why":"Officiellt formatodds och igenkännbara Disney-karaktärer."},
   {"card":"Mickey Mouse Red and Black Refractor /28","tier":"MONSTER","odds":"1:1 761 value-pack över hela base-parallellen","why":"Lågnumrerad Mickey-specifik parallelfamilj."},
   {"card":"Miley Cyrus / Hannah Montana Authentic Autograph DCA-MC","tier":"JACKPOT","odds":"Authentic Autographs 1:2 261 value-pack över hela autografchecklistan","why":"Äkta signerad Disney Channel-chase."},
   {"card":"Owen Wilson / Lightning McQueen Authentic Autograph AA-OW","tier":"JACKPOT","odds":"Authentic Autographs 1:2 261 value-pack över hela autografchecklistan","why":"Äkta röstskådespelarsignatur från Cars."},
   {"card":"Jodi Benson / Ariel eller Ming-Na Wen / Mulan Princess Autograph","tier":"JACKPOT","odds":"Authentic Autographs 1:2 261 value-pack över hela autografchecklistan","why":"Äkta Disney Princess-röstsignaturer."},
   {"card":"Sketch Card Gold Base","tier":"MONSTER","odds":"1:2 564 value-pack","why":"Handritad originalsketch; motiv och artist varierar."},
   {"card":"Mickey/Minnie/Goofy/Pluto Quad Facsimile Autograph QD-1","tier":"MYCKET BRA","odds":"Quad Facsimile Autographs 1:115 840 value-pack","why":"Extremt sällsynt men tryckta signaturer – inte handskrivna autografer."}
 ],
 "why_exciting":["Två exklusiva Raywave-paralleller per box ger garanterat boxspecifikt innehåll.","Topps publicerar separata Value Box-odds för äkta autografer, sketchkort och numrerade paralleller."],
 "tiers":{"everyday":{"label":"Vanligt men intressant","score":82,"items":["2 Raywave per box","Base Refractor 1:4 pack"]},"good":{"label":"Bra träff","score":70,"items":["numrerad Disney-parallel","Mickey/Pooh/Stitch image variation"]},"big":{"label":"Riktigt bra","score":78,"items":["Authentic Auto 1:2 261 pack","Sketch 1:2 564 pack"]},"jackpot":{"label":"Monsterhit","score":93,"items":["Mickey /28","stjärnautograf","Superfractor 1/1"]}},
 "caveat":"Oddsen är per Value Box-pack och gäller hela kortfamiljen, inte ett visst namn. Facsimile Autographs har tryckta signaturer och ska inte förväxlas med Authentic Autographs."
},
"cc-pokemon-ninja-spinner-m4-display": {
 "source_name":"Ninja Spinner M4 card checklist",
 "source_url":"https://www.serebii.net/card/ninjaspinner/",
 "key_names":["Mega Greninja ex MUR #120/083","Mega Greninja ex SAR","Emma SAR","Roxie's Performance SAR","Mega Pyroar ex"],
 "headline_chases":[
  {"card":"Mega Greninja ex MUR #120/083","tier":"JACKPOT","odds":"MUR rarity; officiella packodds ej publicerade","why":"Setets toppspår och omslags-Pokémon i särskild MUR-rarity."},
  {"card":"Mega Greninja ex Special Art Rare","tier":"MONSTER","odds":"SAR; officiella packodds ej publicerade","why":"Alternativ illustration av setets huvudchase."},
  {"card":"Emma Special Art Rare","tier":"MONSTER","odds":"SAR; officiella packodds ej publicerade","why":"Namngivet tränarkort i den verifierade setlistan."},
  {"card":"Roxie's Performance Special Art Rare","tier":"MYCKET BRA","odds":"SAR; officiella packodds ej publicerade","why":"Tränarvariant med stark karaktärsigenkänning."},
  {"card":"Mega Pyroar ex Special Art Rare","tier":"MYCKET BRA","odds":"SAR; officiella packodds ej publicerade","why":"Ytterligare Mega-evolution i setets höga rarity-spår."}
 ],
 "why_exciting":["30-pack-displayen ger fler försök än ett löst paket.","Checklistan har ett tydligt toppkort i Mega Greninja ex MUR och flera separata SAR-jakter."],
 "tiers":{"everyday":{"label":"Vanligt men intressant","score":68,"items":["5 kort per pack","Mega ex och illustration rares i setet"]},"good":{"label":"Bra träff","score":73,"items":["AR eller vanlig SAR"]},"big":{"label":"Riktigt bra","score":83,"items":["Mega Greninja ex SAR","Emma SAR"]},"jackpot":{"label":"Monsterhit","score":94,"items":["Mega Greninja ex MUR #120/083"]}},
 "caveat":"Checklistan och rariteterna är kartlagda; Pokémon anger inte officiella kortspecifika pull rates. Betygen beskriver chase-tak, inte garanterat värde eller träffchans."
},
"cc-pokemon-storm-emeralda-m6-display": {
 "source_name":"Storm Emeralda M6 card checklist",
 "source_url":"https://www.fujicardshop.com/card-lists/storm-emeralda/",
 "key_names":["Mega Rayquaza ex MUR #113/076","Mega Rayquaza ex SAR","Mega Golisopod ex SAR","Wishiwashi ex SAR","Groudon AR"],
 "headline_chases":[
  {"card":"Mega Rayquaza ex MUR #113/076","tier":"JACKPOT","odds":"MUR rarity; officiella packodds ej publicerade","why":"Setets högsta namngivna rarity-spår och huvud-Pokémon."},
  {"card":"Mega Rayquaza ex Special Art Rare","tier":"MONSTER","odds":"SAR; officiella packodds ej publicerade","why":"Alternativ illustration av den centrala chase-Pokémon."},
  {"card":"Mega Golisopod ex Special Art Rare","tier":"MYCKET BRA","odds":"SAR; officiella packodds ej publicerade","why":"Namngiven Mega-chase från setets SAR-del."},
  {"card":"Wishiwashi ex Special Art Rare","tier":"MYCKET BRA","odds":"SAR; officiella packodds ej publicerade","why":"Separat SAR-spår utöver Rayquaza."},
  {"card":"Groudon Art Rare","tier":"BRA","odds":"AR; officiella packodds ej publicerade","why":"Legendarisk Pokémon i setets illustrerade rarity-spår."}
 ],
 "why_exciting":["Displayen innehåller 30 japanska pack.","Mega Rayquaza finns i flera höga rarity-versioner, med MUR som tydligt toppkort."],
 "tiers":{"everyday":{"label":"Vanligt men intressant","score":67,"items":["5 kort per pack","AR-spår i setet"]},"good":{"label":"Bra träff","score":73,"items":["Groudon AR eller annan AR"]},"big":{"label":"Riktigt bra","score":84,"items":["Mega Golisopod ex eller Wishiwashi ex SAR"]},"jackpot":{"label":"Monsterhit","score":96,"items":["Mega Rayquaza ex MUR #113/076"]}},
 "caveat":"Setlistan verifierar kort och rarity, men inga officiella kortspecifika pull rates är publicerade. Värdet varierar mellan språk, skick och marknad."
},
"cc-one-piece-op14-jp-display": {
 "source_name":"Bandai official OP14-EB04 card list",
 "source_url":"https://en.onepiece-cardgame.com/cardlist/?series=569114",
 "key_names":["Boa Hancock OP14-112","Dracule Mihawk OP14-119","Trafalgar Law OP14-001","Boa Hancock SP card","Buggy SP card"],
 "headline_chases":[
  {"card":"Boa Hancock OP14-112 / SP variant","tier":"JACKPOT","odds":"SP/parallel; Bandai publicerar inte packodds","why":"Officiellt listad karaktär och specialvariant i setlistan."},
  {"card":"Dracule Mihawk OP14-119 / parallel","tier":"MONSTER","odds":"Parallel; Bandai publicerar inte packodds","why":"Namngiven karaktär från setets Seven Warlords-tema."},
  {"card":"Trafalgar Law OP14-001 Leader parallel","tier":"MYCKET BRA","odds":"Leader parallel; Bandai publicerar inte packodds","why":"Leader-kort med separat parallelvariant."},
  {"card":"Buggy OP09-051 SP variant","tier":"MYCKET BRA","odds":"SP; Bandai publicerar inte packodds","why":"SP-kort som förekommer i den officiella OP14-EB04 listan."}
 ],
 "why_exciting":["24-packdisplay ger 24 öppningar; ett löst paket är en mindre, separat chans.","Officiella checklistan visar namngivna leaders, karaktärer och SP/parallel-varianter."],
 "tiers":{"everyday":{"label":"Vanligt men intressant","score":63,"items":["6 kort per japanskt paket","Leader- och character-kort"]},"good":{"label":"Bra träff","score":70,"items":["Leader parallel eller stark SR"]},"big":{"label":"Riktigt bra","score":81,"items":["Mihawk eller Law parallel"]},"jackpot":{"label":"Monsterhit","score":90,"items":["Boa Hancock SP/parallel"]}},
 "caveat":"Checklistan verifieras av Bandai. Korten ovan är chase-kandidater, inte en värderingsgaranti; exakta packodds publiceras inte. Japansk boxkonfiguration ska inte blandas med engelska utgåvor."
},
"cc-one-piece-op16-jp-display": {
 "source_name":"Bandai official The Time of Battle OP16 product and card list",
 "source_url":"https://en.onepiece-cardgame.com/products/op16.html",
 "key_names":["Portgas.D.Ace OP16-001","Monkey.D.Luffy OP16-022","Yamato OP16-079","Portgas.D.Ace OP16-118 SEC","Vista Treasure Rare"],
 "headline_chases":[
  {"card":"Portgas.D.Ace OP16-118 Secret Rare","tier":"JACKPOT","odds":"Secret Rare; Bandai publicerar inte packodds","why":"Centralt namn i Paramount War-temat och en av setets Secret Rare-jakter."},
  {"card":"Yamato OP16-079 Leader/parallel","tier":"MONSTER","odds":"Parallel; Bandai publicerar inte packodds","why":"Namngiven leader i produktens officiella presentation."},
  {"card":"Monkey.D.Luffy OP16-022 Leader/parallel","tier":"MONSTER","odds":"Parallel; Bandai publicerar inte packodds","why":"En av setets officiellt presenterade leaders."},
  {"card":"Portgas.D.Ace ST15-005 SP parallel","tier":"MYCKET BRA","odds":"SP; Bandai publicerar inte packodds","why":"Ace-temat knyter in ett SP-kort i listan."},
  {"card":"Vista special rarity variant","tier":"MONSTER","odds":"Special rarity; Bandai publicerar inte packodds","why":"Ytterligare en separat variant att hålla utkik efter i OP-16 checklistan."}
 ],
 "why_exciting":["24 japanska pack per display och sex kort per pack.","Paramount War-temat samlar Ace, Luffy, Buggy, Sengoku, Yamato och Teach; checklistan har Secret Rare, paralleller och Treasure Rare-spår."],
 "tiers":{"everyday":{"label":"Vanligt men intressant","score":62,"items":["6 kort per japanskt paket","Nytt Paramount War-tema"]},"good":{"label":"Bra träff","score":70,"items":["Leader parallel eller SR parallel"]},"big":{"label":"Riktigt bra","score":81,"items":["Ace SEC eller en namngiven SP-variant"]},"jackpot":{"label":"Monsterhit","score":88,"items":["Sällsynt parallellvariant av populär huvudkaraktär"]}},
 "caveat":"Bandai bekräftar temat och leader-namn men publicerar inte packodds. Kontrollera språk och kortnummer; produktprofilen avser japansk OP-16."
}
}

CHASE_PROFILES.update({
"cc-2025-26-topps-chrome-update-basketball-pack": {
 "source_name":"Topps official 2025-26 Chrome Updates Basketball product page",
 "source_url":"https://www.topps.com/pages/topps-chrome-updates-basketball",
 "key_names":["Cooper Flagg Rookie Debut Patch Autograph 1/1","Kon Knueppel Rookie Debut Patch Autograph 1/1","Dylan Harper Rookie Debut Patch Autograph 1/1","Victor Wembanyama","LeBron James"],
 "headline_chases":[
  {"card":"Cooper Flagg Rookie Debut Patch Autograph 1/1","tier":"JACKPOT","odds":"1/1; individuellt packodds ej publicerat","why":"Matchanvänd NBA-debutpatch och rookieautograf i ett unikt exemplar."},
  {"card":"Kon Knueppel Rookie Debut Patch Autograph 1/1","tier":"JACKPOT","odds":"1/1; individuellt packodds ej publicerat","why":"Verifierad RDPA-rookie i produktens främsta chase-familj."},
  {"card":"Dylan Harper Rookie Debut Patch Autograph 1/1","tier":"JACKPOT","odds":"1/1; individuellt packodds ej publicerat","why":"En av tre officiellt framlyfta rookie-grails."},
  {"card":"Alter Egos eller Minions NBA SSP","tier":"MONSTER","odds":"SSP; exakt packodds ej publicerat","why":"Produktens namngivna short-print-spår."}
 ],
 "why_exciting":["Ett löst pack kan innehålla NBA:s nya Rookie Debut Patch Autographs.","Checklistan har Cooper Flagg, Kon Knueppel, Dylan Harper och stora NBA-stjärnor."],
 "tiers":{"everyday":{"label":"Vanligt men intressant","score":58,"items":["4 Chrome-kort"]},"good":{"label":"Bra träff","score":73,"items":["rookie refractor eller numrerad parallel"]},"big":{"label":"Riktigt bra","score":88,"items":["Alter Egos/Minions SSP","rookieautograf"]},"jackpot":{"label":"Monsterhit","score":100,"items":["Rookie Debut Patch Auto 1/1"]}},
 "caveat":"Ett löst pack har ingen autograf- eller SSP-garanti. 1/1 beskriver upplagan på kortet, inte sannolikheten att dra det."
},
"cc-2025-26-topps-nba-hoops-hobby-pack": {
 "source_name":"Topps/Coolcard 2025-26 NBA Hoops product information",
 "source_url":"https://www.coolcard.se/en/product/1-pack-2025-26-topps-nba-hoops-basketball-hobby",
 "key_names":["Cooper Flagg Rookie Signatures","Dylan Harper Rookie Signatures","Victor Wembanyama","LeBron James","Oasis case hit"],
 "headline_chases":[
  {"card":"Cooper Flagg Rookie Signatures","tier":"JACKPOT","odds":"Hobbyboxen har 1 autograf; viss spelare ej garanterad","why":"Rookieklassens tydligaste namn i ett signerat spår."},
  {"card":"Dylan Harper Rookie Signatures","tier":"MONSTER","odds":"Hobbyboxen har 1 autograf över hela autografprogrammet","why":"Namngiven topprookie i signerad form."},
  {"card":"Oasis, Joy, Checkmate eller Hoopnotic case hit","tier":"MONSTER","odds":"Case hit; exakt frekvens ej publicerad på butikssidan","why":"Fyra uttryckligen namngivna sällsynta insertfamiljer."}
 ],
 "why_exciting":["Tillgängligare packpris än Chrome Updates.","Rookieautografer och fyra case-hit-familjer ger ett tydligt men mycket varierande tak."],
 "tiers":{"everyday":{"label":"Vanligt men intressant","score":64,"items":["8 kort","rookies och inserts"]},"good":{"label":"Bra träff","score":70,"items":["stark rookieparallel"]},"big":{"label":"Riktigt bra","score":84,"items":["case hit eller veteran-autograf"]},"jackpot":{"label":"Monsterhit","score":94,"items":["Cooper Flagg Rookie Signature"]}},
 "caveat":"En autograf gäller per hel hobbybox, inte per löst pack. Lösa pack kan komma från en box där boxhiten redan dragits."
},
"cc-2026-topps-baseball-series2-hobby": {
 "source_name":"Topps official 2026 Series 2 Baseball release and chase guide",
 "source_url":"https://www.topps.com/pages/series-2",
 "key_names":["Roman Anthony Rookie","Trey Yesavage Rookie","Tatsuya Imai Rookie","Shohei Ohtani Autograph","Aaron Judge Autograph"],
 "headline_chases":[
  {"card":"Roman Anthony rookie parallel eller autograph","tier":"MYCKET BRA","odds":"Ingår i Series 2; individuellt odds varierar med parallel","why":"Officiellt framlyft rookie-namn i 2026 Series 2."},
  {"card":"Trey Yesavage eller Tatsuya Imai rookie autograph","tier":"MYCKET BRA","odds":"Autografprogram; specifik spelare ej garanterad","why":"Två verifierade rookie-jakter."},
  {"card":"Shohei Ohtani eller Aaron Judge autograph/parallel","tier":"MONSTER","odds":"Ingår i produktens stjärn- och autografspår; individuellt odds ej publicerat här","why":"Två av produktens största aktiva namn."},
  {"card":"Flagship Autograph Patch eller 1/1 In the Name relic","tier":"JACKPOT","odds":"Lågnumrerad/1/1; inte boxgaranti","why":"Produktens högsta autograph- och memorabilia-tak."}
 ],
 "why_exciting":["Hobbyboxen ger 20 pack och en autograf eller relic per box.","Checklistan kombinerar rookies med Ohtani, Judge och flera extremt lågnumrerade hitspår."],
 "tiers":{"everyday":{"label":"Vanligt men intressant","score":82,"items":["240 kort","1 promo-pack"]},"good":{"label":"Bra träff","score":77,"items":["rookieparallel eller Home Field"]},"big":{"label":"Riktigt bra","score":87,"items":["stjärnautograf eller Flagship Patch"]},"jackpot":{"label":"Monsterhit","score":97,"items":["1/1 In the Name relic eller topprookie-auto"]}},
 "caveat":"Boxgarantin är en valfri autograf eller relic, inte en toppspelare. Ett löst pack saknar boxgarantin."
},
"cc-2026-topps-chrome-baseball-value": {
 "source_name":"Topps/Coolcard 2026 Chrome Baseball Value Box product breakdown",
 "source_url":"https://www.coolcard.se/product/hel-value-box-2026-topps-chrome-mlb-7-paket",
 "key_names":["Retail Rookie Autograph","Gold Logoman Autograph Relic","Helix","Ultraviolet","Jerry Seinfeld Autograph"],
 "headline_chases":[
  {"card":"Retail Rookie Autograph – färgparallell ned till 1/1","tier":"MONSTER","odds":"Autograf finns men är inte garanterad; paralleller /499 till 1/1","why":"Retail-specifikt signerat rookiespår."},
  {"card":"Helix, Ultraviolet eller Static Noise case hit","tier":"MYCKET BRA","odds":"Case hit; exakt value-box-odds ej angivet på butikssidan","why":"Tre verifierade sällsynta insertfamiljer."},
  {"card":"Gold Logoman autograph/relic","tier":"JACKPOT","odds":"Extremt sällsynt; ingen boxgaranti","why":"Premium memorabilia och möjlig autograf kring 2025 års prisvinnare."},
  {"card":"SuperFractor 1/1 eller Frozen Fractor /0","tier":"JACKPOT","odds":"1/1 respektive serial /0","why":"Produktens lägsta numrerade parallelspår."}
 ],
 "why_exciting":["Sju pack till lägre pris än hobbyformatet.","Retail Rookie Autos, case hits och paralleller ned till 1/1 finns faktiskt i formatet."],
 "tiers":{"everyday":{"label":"Vanligt men intressant","score":72,"items":["28 Chrome-kort","Value-exklusiva refractors"]},"good":{"label":"Bra träff","score":75,"items":["numrerad Raywave"]},"big":{"label":"Riktigt bra","score":86,"items":["case hit eller rookieauto"]},"jackpot":{"label":"Monsterhit","score":98,"items":["Gold Logoman eller SuperFractor 1/1"]}},
 "caveat":"Ingen autograf, numrerad parallel eller case hit är garanterad i en Value Box."
},
"cc-2026-topps-flagship-nfl-pack": {
 "source_name":"Topps official 2026 Flagship Football product page",
 "source_url":"https://www.topps.com/pages/topps-flagship-football",
 "key_names":["Fernando Mendoza Rookie","Jeremiyah Love Rookie","Carnell Tate Rookie","Patrick Mahomes Autograph","Tom Brady Autograph"],
 "headline_chases":[
  {"card":"Fernando Mendoza 1957 Rookie Variation","tier":"MYCKET BRA","odds":"SSP/variation; individuellt odds ej publicerat här","why":"En av tre officiellt framlyfta rookies."},
  {"card":"Jeremiyah Love eller Carnell Tate rookie parallel","tier":"BRA","odds":"Parallel/SSP-spår; exakt packodds varierar","why":"Namngivna rookies i den licensierade baschecklistan."},
  {"card":"Patrick Mahomes eller Tom Brady signature","tier":"JACKPOT","odds":"Autografprogram; individuell spelare ej garanterad","why":"Produktens största verifierade veteran/legend-namn."},
  {"card":"Topps Patch Autograph","tier":"JACKPOT","odds":"Extremt sällsynt; inget individuellt packodds publicerat","why":"Kombinerar premium patch och autograf."}
 ],
 "why_exciting":["Första fullt licensierade Topps Flagship Football på mer än ett decennium.","Rookies, SSP, autografer och premium memorabilia kan dras ur hobbyformatet."],
 "tiers":{"everyday":{"label":"Vanligt men intressant","score":68,"items":["12 licensierade NFL-kort"]},"good":{"label":"Bra träff","score":72,"items":["rookieparallel eller Team Color"]},"big":{"label":"Riktigt bra","score":86,"items":["SSP eller autograf"]},"jackpot":{"label":"Monsterhit","score":98,"items":["Mahomes/Brady auto eller Patch Auto"]}},
 "caveat":"Detta är ett löst hobby-pack. Ingen rookie, autograf, relic eller SSP är garanterad."
},
"cc-2026-topps-universe-wwe-pack": {
 "source_name":"Topps official 2026 Universe WWE checklist and product page",
 "source_url":"https://www.topps.com/pages/topps-universe-wwe",
 "key_names":["Roman Reigns Superstar Relic Signature","Rhea Ripley Echoes","Seth Rollins Alias","WWE Authentics","Ringside Relics"],
 "headline_chases":[
  {"card":"Roman Reigns Superstar Relic Signature","tier":"JACKPOT","odds":"Autograph relic; individuellt packodds ej publicerat här","why":"Officiellt visad premiumträff med signatur och memorabilia."},
  {"card":"Rhea Ripley Echoes parallel","tier":"MYCKET BRA","odds":"Numrerade paralleller finns; exakt variantodds varierar","why":"Officiellt visat stjärnkort i en namngiven insertserie."},
  {"card":"Seth Rollins Alias parallel","tier":"MYCKET BRA","odds":"Short-print/parallel-spår; exakt odds varierar","why":"Officiellt visad WWE-stjärna i Alias-serien."},
  {"card":"WWE Authentics eller Ringside Relic","tier":"MONSTER","odds":"Hobbyboxen har 1 relic; löst pack saknar garanti","why":"Superstar-använt eller matchanvänt memorabilia."}
 ],
 "why_exciting":["Hela hobbyboxen ger två autografer och en relic.","Roman Reigns, Rhea Ripley och Seth Rollins finns i konkreta chase-spår."],
 "tiers":{"everyday":{"label":"Vanligt men intressant","score":67,"items":["12 WWE-kort"]},"good":{"label":"Bra träff","score":73,"items":["numrerad stjärnparallel"]},"big":{"label":"Riktigt bra","score":87,"items":["autograf eller matchanvänd relic"]},"jackpot":{"label":"Monsterhit","score":96,"items":["Roman Reigns Relic Auto"]}},
 "caveat":"Två autografer och en relic gäller en hel 10-pack hobbybox, inte ett enskilt pack."
},
"cc-star-wars-unlimited-shadows-display": {
 "source_name":"Fantasy Flight Games official Shadows of the Galaxy product page",
 "source_url":"https://starwarsunlimited.com/products/set-2-shadows-of-the-galaxy",
 "key_names":["The Mandalorian Leader Showcase","Moff Gideon Leader Showcase","Boba Fett Collecting the Bounty","Jabba the Hutt","Bossk"],
 "headline_chases":[
  {"card":"The Mandalorian Leader Showcase","tier":"JACKPOT","odds":"Showcase; officiellt individuellt odds ej publicerat","why":"Setets officiellt framlyfta hjälteledare i sällsynt Showcase-variant."},
  {"card":"Moff Gideon Leader Showcase","tier":"MONSTER","odds":"Showcase; officiellt individuellt odds ej publicerat","why":"Setets officiellt framlyfta skurkledare."},
  {"card":"Boba Fett: Collecting the Bounty – Hyperspace/Foil","tier":"MYCKET BRA","odds":"Parallelvariant; exakt packodds ej publicerat","why":"Namngivet Boba Fett-kort från setet."}
 ],
 "why_exciting":["Varje pack har en rare/legendary-plats och en foil-plats.","24 pack ger fler försök på Showcase-ledare, hyperspace och foil än ett löst pack."],
 "tiers":{"everyday":{"label":"Vanligt men intressant","score":82,"items":["24 rare/legendary-platser","24 foil-platser"]},"good":{"label":"Bra träff","score":72,"items":["stark Legendary eller hyperspace foil"]},"big":{"label":"Riktigt bra","score":84,"items":["populär ledare i premiumvariant"]},"jackpot":{"label":"Monsterhit","score":93,"items":["Mandalorian/Moff Gideon Showcase"]}},
 "caveat":"Showcase-ledare är extremt sällsynta och inte garanterade per display. Kortens spelvärde och andrahandsvärde kan förändras."
},
"cc-star-wars-unlimited-twilight-display": {
 "source_name":"Fantasy Flight Games official Twilight of the Republic product page",
 "source_url":"https://starwarsunlimited.com/products/set-3-twilight-of-the-republic",
 "key_names":["Ahsoka Tano Leader Showcase","General Grievous Leader Showcase","Anakin Skywalker #147","Count Dooku Leader","Darth Maul"],
 "headline_chases":[
  {"card":"Ahsoka Tano Leader Showcase","tier":"JACKPOT","odds":"Showcase; officiellt individuellt odds ej publicerat","why":"Setets officiellt framlyfta republikledare i premiumvariant."},
  {"card":"General Grievous Leader Showcase","tier":"JACKPOT","odds":"Showcase; officiellt individuellt odds ej publicerat","why":"Setets officiellt framlyfta separatistledare."},
  {"card":"Anakin Skywalker #147 – Hyperspace/Foil","tier":"MYCKET BRA","odds":"Parallelvariant; exakt packodds ej publicerat","why":"Officiellt namngivet Anakin-kort i setet."},
  {"card":"Count Dooku eller Darth Maul premiumvariant","tier":"MONSTER","odds":"Rare/legendary/parallel; exakt odds varierar","why":"Verifierade huvudkaraktärer i Clone Wars-temat."}
 ],
 "why_exciting":["Över 250 Clone Wars-kort och 24 rare/legendary-platser per display.","Ahsoka, Grievous, Anakin, Dooku och Maul ger flera tydliga karaktärsjakter."],
 "tiers":{"everyday":{"label":"Vanligt men intressant","score":82,"items":["24 rare/legendary-platser","24 foil-platser"]},"good":{"label":"Bra träff","score":73,"items":["Anakin/Ahsoka parallel"]},"big":{"label":"Riktigt bra","score":85,"items":["Legendary hyperspace foil"]},"jackpot":{"label":"Monsterhit","score":94,"items":["Ahsoka eller Grievous Showcase"]}},
 "caveat":"Ett Showcase-kort är inte en displaygaranti. Namnen verifieras i officiellt setmaterial, men individuella packodds är inte publicerade."
}
})

CHASE_PROFILES.update({
"cs-2025-26-panini-prizm-basketball-blaster": {
 "source_name":"Beckett 2025-26 Prizm checklist, cross-checked with Panini product family",
 "source_url":"https://www.beckett.com/news/2025-26-panini-prizm-basketball-cards/",
 "key_names":["Cooper Flagg Rookie","Dylan Harper Rookie","Kon Knueppel Rookie","Uptown SSP","Black Color Blast SSP"],
 "headline_chases":[
  {"card":"Cooper Flagg Rookie Purple Wave Prizm","tier":"MONSTER","odds":"Purple Wave-familjen: 3 per blaster i snitt; spelaroddset är okänt","why":"Toppnamn i rookieklassen kombinerat med blaster-exklusiv parallel."},
  {"card":"Dylan Harper eller Kon Knueppel Rookie Prizm","tier":"MYCKET BRA","odds":"Kan dras i retail; exakt spelaroddset är inte publicerat","why":"Två namngivna rookies i den verifierade checklistan."},
  {"card":"Uptown SSP – stjärna eller rookie","tier":"MONSTER","odds":"Retail-exklusiv SSP; exakt packodds ej publicerat","why":"Ett av retailformatets tydligaste sällsynta insertspår."},
  {"card":"Black Color Blast SSP – stjärna eller rookie","tier":"JACKPOT","odds":"Retail-exklusiv SSP; exakt packodds ej publicerat","why":"Extremt sällsynt korttak i ett billigt retailformat."},
  {"card":"Rookie autograph","tier":"MONSTER","odds":"Autografer kan dras men är inte garanterade","why":"Signatur av topprookie är boxens starkaste autograph-utfall."}
 ],
 "why_exciting":["Tre Purple Wave Prizms per box i snitt ger återkommande parallelträffar.","Cooper Flagg, Dylan Harper och Kon Knueppel ger ett starkt rookie-tak, samtidigt som Uptown och Black Color Blast finns i retail."],
 "tiers":{"everyday":{"label":"Retailgolv","score":75,"items":["30 kort","3 Purple Wave i snitt"]},"good":{"label":"Bra träff","score":76,"items":["topp-rookie Prizm"]},"big":{"label":"Riktigt bra","score":88,"items":["numrerad rookie eller autograf"]},"jackpot":{"label":"Monsterhit","score":96,"items":["Black Color Blast SSP"]}},
 "caveat":"Blastern garanterar inte autograf, numrerat kort eller SSP. Purple Wave-siffran gäller hela parallelfamiljen, inte Cooper Flagg eller någon annan viss spelare; hobbyboxens garantier gäller inte retailformatet."
},
"cs-2025-26-topps-chrome-uwcl-hobby": {
 "source_name":"Topps official 2025-26 Chrome UWCL checklist and hobby odds",
 "source_url":"https://it-next.topps.com/products/topps-chrome%C2%AE-uefa-womens-champions-league-2025-26-hobby-box",
 "key_names":["Aitana Bonmatí Autograph","Alexia Putellas Autograph","Sam Kerr Autograph","Bonmatí / Putellas / Guijarro Triple Autograph","UWCL Chrome Trophy"],
 "headline_chases":[
  {"card":"Aitana Bonmatí / Alexia Putellas / Patri Guijarro Triple Autograph","tier":"JACKPOT","odds":"Triple Autograph Black 1:11,020, Red 1:22,420 och SuperFractor 1:108,360 hobby-pack över familjen","why":"Tre Barcelona-stjärnor på samma officiellt listade kort."},
  {"card":"Aitana Bonmatí eller Alexia Putellas Chrome Autograph","tier":"MONSTER","odds":"Veterans and Rookies Autograph-familjen 1:57 hobby-pack; inte spelarodds","why":"Två av checklistans största namn i det garanterade autograph-programmet."},
  {"card":"Sam Kerr Chrome Autograph","tier":"MONSTER","odds":"Veterans and Rookies Autograph-familjen 1:57 hobby-pack; inte spelarodds","why":"Namngiven stjärnsignatur i officiella checklistan."},
  {"card":"Aitana Bonmatí Chrome Premium Autograph Relic","tier":"JACKPOT","odds":"Premium Autograph Relic-paralleller: 1:584 till 1:28,268 hobby-pack beroende på färg, över hela familjen","why":"Autograf och spelar-/matchanvänt memorabilia i samma kortfamilj."},
  {"card":"UWCL Chrome Trophy","tier":"JACKPOT","odds":"1:650,160 hobby-pack","why":"Produktens mest extrema publicerade insertodds."},
  {"card":"Olivia Smith Rookie Helix","tier":"MYCKET BRA","odds":"Helix-familjen 1:1,364 hobby-pack; inte spelaroddset","why":"Namngiven rookie i ett ultra-sällsynt insertspår."}
 ],
 "why_exciting":["Två autografer per box och en checklista med Bonmatí, Putellas, Kerr och starka rookies ger både träfffrekvens och korttak.","Topps publicerar formatsspecifika hobbyodds för refractors, inserts, duals, triples och autograph relics."],
 "tiers":{"everyday":{"label":"Stark hobbybox","score":91,"items":["80 kort","2 autografer","Refractor 1:3 pack"]},"good":{"label":"Bra träff","score":82,"items":["numrerad stjärnparallel"]},"big":{"label":"Riktigt bra","score":93,"items":["toppnamnsautograf eller Helix"]},"jackpot":{"label":"Monsterhit","score":99,"items":["triple auto, auto relic eller Trophy"]}},
 "caveat":"Två autografer per box gäller hobbyformatet, men ingen viss spelare eller autograph-familj garanteras. Publicerade odds gäller familjer över produktionen, inte en särskild spelare."
},
"cc-2026-topps-universe-wwe-hobby": {
 "source_name":"Topps official 2026 Universe WWE checklist and hobby configuration",
 "source_url":"https://www.topps.com/pages/topps-universe-wwe",
 "key_names":["Roman Reigns Superstar Relic Signature","Rhea Ripley Echoes","Seth Rollins Alias","WWE Authentics","Ringside Relics"],
 "headline_chases":[
  {"card":"Roman Reigns Superstar Relic Signature","tier":"JACKPOT","odds":"Autograph-relic-program; exakt kortodds ej publicerat","why":"Signatur och memorabilia av en av checklistans största stjärnor."},
  {"card":"Tag Team Dual Autograph Relic","tier":"JACKPOT","odds":"Extremt sällsynt; exakt odds ej publicerat","why":"Två signaturer och flera memorabilia-bitar på samma kort."},
  {"card":"Rhea Ripley Echoes eller Seth Rollins Alias parallel","tier":"MYCKET BRA","odds":"Case-hit/parallel-spår; exakt variantodds varierar","why":"Två officiellt visade stjärnkort."},
  {"card":"WWE Authentics eller Ringside Relic","tier":"MONSTER","odds":"1 relic per hobbybox över hela relic-programmet","why":"Superstar-använt eller matchanvänt material."}
 ],
 "why_exciting":["Två autografer och en relic per box ger tre tydliga premiumträffar.","Checklistan kombinerar legender, mästare och nya namn med case hits och 1/1-paralleller."],
 "tiers":{"everyday":{"label":"Stabil box","score":90,"items":["120 kort","2 autografer","1 relic"]},"good":{"label":"Bra träff","score":80,"items":["numrerad stjärnparallel"]},"big":{"label":"Riktigt bra","score":91,"items":["stjärnautograf eller matchanvänd relic"]},"jackpot":{"label":"Monsterhit","score":98,"items":["Roman Reigns Relic Auto eller dual auto"]}},
 "caveat":"Boxen garanterar två autografer och en relic, men inte en viss wrestler eller ett autograph-relic-kort."
},
"cc-2026-topps-universe-wwe-value": {
 "source_name":"Topps official 2026 Universe WWE value-box page",
 "source_url":"https://www.topps.com/pages/topps-universe-wwe",
 "key_names":["Roman Reigns Superstar Relic Signature","Rhea Ripley Echoes","Seth Rollins Alias","WWE Authentics","Ringside Relics"],
 "headline_chases":[
  {"card":"Roman Reigns Superstar Relic Signature","tier":"JACKPOT","odds":"Kan dras; exakt value-pack-odds ej publicerat","why":"Produktens tydligaste namngivna premiumträff."},
  {"card":"Alias, Echoes, Flashpoint eller Slammed short print","tier":"MONSTER","odds":"Short print; exakt value-odds ej publicerat","why":"Fyra verifierade sällsynta insertspår."},
  {"card":"Numrerad stjärnparallel eller autograph","tier":"MYCKET BRA","odds":"Finns i value-formatet men är inte garanterad","why":"Lågt inköpspris med tillgång till produktens premiumspår."}
 ],
 "why_exciting":["Sex pack ger en billigare väg in i samma checklistuniversum.","Value-formatet kan innehålla autografer, relics, numrerade kort och short prints."],
 "tiers":{"everyday":{"label":"Öppningsinnehåll","score":76,"items":["36 kort","value-exklusiva paralleller"]},"good":{"label":"Bra träff","score":71,"items":["numrerad stjärnparallel"]},"big":{"label":"Riktigt bra","score":85,"items":["short print eller autograph"]},"jackpot":{"label":"Monsterhit","score":96,"items":["Roman Reigns Relic Auto"]}},
 "caveat":"Value Box har ingen garanti på autograf eller relic; hobbyboxens två autografer och en relic gäller inte här."
},
"cc-2026-topps-baseball-series2-value": {
 "source_name":"Topps official 2026 Series 2 checklist and Coolcard value configuration",
 "source_url":"https://www.topps.com/pages/series-2",
 "key_names":["Roman Anthony Rookie","Trey Yesavage Rookie","Tatsuya Imai Rookie","Shohei Ohtani Autograph","Aaron Judge Autograph"],
 "headline_chases":[
  {"card":"Roman Anthony rookie parallel eller autograph","tier":"MYCKET BRA","odds":"Finns i Series 2; specifikt value-odds varierar","why":"Officiellt framlyft rookie-namn."},
  {"card":"Shohei Ohtani eller Aaron Judge autograph/parallel","tier":"MONSTER","odds":"Kan dras; ingen autografgaranti i value-formatet","why":"Två av checklistans största aktiva namn."},
  {"card":"Home Field eller Heavy Lumber","tier":"MYCKET BRA","odds":"Sällsynt insert; exakt value-odds ej angivet","why":"Två populära och verifierade insertfamiljer."},
  {"card":"Flagship Autograph Patch eller 1/1 In the Name relic","tier":"JACKPOT","odds":"Extremt sällsynt; inte boxgaranti","why":"Produktens högsta signerade och memorabilia-baserade tak."}
 ],
 "why_exciting":["72 kort och sex insertplatser till låg kostnad.","Holiday-varianter är exklusiva för value-formatet samtidigt som stora autograf- och relicspår finns."],
 "tiers":{"everyday":{"label":"Öppningsinnehåll","score":79,"items":["72 kort","6 Stars of MLB/Titans-platser"]},"good":{"label":"Bra träff","score":73,"items":["Holiday-variation eller rookieparallel"]},"big":{"label":"Riktigt bra","score":86,"items":["Home Field eller stjärnautograf"]},"jackpot":{"label":"Monsterhit","score":97,"items":["1/1 relic eller topprookie-auto"]}},
 "caveat":"Hobbyboxens autograf-eller-relic-garanti gäller inte denna Value Box."
},
"cc-2026-topps-chrome-ufc-value": {
 "source_name":"Topps official 2026 Chrome UFC checklist and value configuration",
 "source_url":"https://www.topps.com/pages/topps-chrome-ufc",
 "key_names":["Jon Jones In Your Face","Conor McGregor Kings and Queens","Amanda Nunes Kings and Queens","Octagon Legends Autographs","Radiating Rookies"],
 "headline_chases":[
  {"card":"Let's Go case hit – UFC-stjärna","tier":"MONSTER","odds":"Case hit; exakt value-odds ej publicerat","why":"Femkortsfamilj med SuperFractor 1/1-parallell."},
  {"card":"Conor McGregor eller Amanda Nunes Kings and Queens","tier":"MYCKET BRA","odds":"20-korts insertfamilj; exakt value-odds ej publicerat","why":"Två verifierade toppnamn i ett namngivet chase-spår."},
  {"card":"Jon Jones In Your Face SuperFractor 1/1","tier":"JACKPOT","odds":"1/1; sannolikhet att dra kortet ej publicerad","why":"Unikt kort av en av sportens största profiler."},
  {"card":"Octagon Legends Autograph","tier":"MONSTER","odds":"Autografer finns men är inte garanterade i value-formatet","why":"Signerade legender är produktens tydliga premiumspår."}
 ],
 "why_exciting":["Två Base Refractors och tre UFC Glove Refractors per box ger återkommande parallelträffar.","Checklistan har case hits, autografer, legender och rookies."],
 "tiers":{"everyday":{"label":"Stabilt öppningsinnehåll","score":81,"items":["24 kort","5 garanterade refractor-typer"]},"good":{"label":"Bra träff","score":74,"items":["numrerad fighterparallel"]},"big":{"label":"Riktigt bra","score":87,"items":["case hit eller autograf"]},"jackpot":{"label":"Monsterhit","score":98,"items":["Jon Jones SuperFractor 1/1"]}},
 "caveat":"De fem refractor-träffarna gäller parallellfamiljer, inte en viss fighter. Autograf och case hit är inte garanterade."
},
"cc-2026-topps-stadium-club-ufc-hobby": {
 "source_name":"Topps official 2026 Stadium Club UFC checklist and collector guide",
 "source_url":"https://www.topps.com/pages/topps-stadium-club-ufc",
 "key_names":["Jon Jones Beam Team","Conor McGregor Triumvirates Nicknames","Alex Pereira","Islam Makhachev","Ateba Gautier Rookie"],
 "headline_chases":[
  {"card":"Conor McGregor, Jon Jones eller Charles Oliveira autograph","tier":"JACKPOT","odds":"2 autografer per hobbybox över hela autograph-programmet","why":"Officiellt framlyfta stjärnnamn i boxens signerade spår."},
  {"card":"Fight Motion eller Abstract Autograph","tier":"MONSTER","odds":"On-card autograph-familj; exakt fighterodds ej publicerat","why":"Premiumdesign med on-card-signatur."},
  {"card":"Eight-card Dual Autograph Gold Rainbow Foilboard 1/1","tier":"JACKPOT","odds":"1/1; individuellt boxodds ej publicerat","why":"Två fighters och produktens lägsta parallellnivå."},
  {"card":"Jon Jones Beam Team eller Conor McGregor Triumvirates Nicknames","tier":"MYCKET BRA","odds":"Insert/parallel; exakt odds varierar","why":"Två konkreta stjärnjakter i fan-favoritspåren."},
  {"card":"Ateba Gautier eller Quillan Salkilld rookie parallel","tier":"BRA","odds":"Rookie/parallel; exakt odds varierar","why":"Två officiellt framlyfta rookies."}
 ],
 "why_exciting":["Två autografer per box i snitt och on-card-autografer.","Checklistan täcker McGregor, Jones, Pereira, Makhachev samt namngivna rookies."],
 "tiers":{"everyday":{"label":"Stabil hobbybox","score":91,"items":["128 kort","2 autografer i snitt"]},"good":{"label":"Bra träff","score":79,"items":["rookieparallel eller Gold Minted"]},"big":{"label":"Riktigt bra","score":91,"items":["stjärnautograf eller Beam Team"]},"jackpot":{"label":"Monsterhit","score":99,"items":["McGregor/Jones auto eller Dual Auto 1/1"]}},
 "caveat":"Två autografer anges per box i snitt; en viss fighter, insert eller parallel är aldrig garanterad."
},
"cc-2026-topps-stadium-club-ufc-pack": {
 "source_name":"Topps official 2026 Stadium Club UFC checklist",
 "source_url":"https://www.topps.com/pages/topps-stadium-club-ufc",
 "key_names":["Jon Jones Beam Team","Conor McGregor Triumvirates Nicknames","Alex Pereira","Islam Makhachev","Ateba Gautier Rookie"],
 "headline_chases":[
  {"card":"Conor McGregor, Jon Jones eller Charles Oliveira autograph","tier":"JACKPOT","odds":"Hobbyboxen har 2 autografer i snitt; löst pack saknar garanti","why":"Tre officiellt framlyfta stjärnnamn i autograph-programmet."},
  {"card":"Jon Jones Beam Team eller Conor McGregor Triumvirates Nicknames","tier":"MONSTER","odds":"Insert/parallel; exakt packodds varierar","why":"Tydliga namngivna stjärnjakter."},
  {"card":"Ateba Gautier eller Quillan Salkilld rookie parallel","tier":"BRA","odds":"Rookie/parallel; exakt packodds varierar","why":"Två verifierade rookies i checklistan."}
 ],
 "why_exciting":["Löst hobby-pack under 100 kr med tillgång till on-card-autografer och stjärninserts.","Full-bleed-foto och en stark mix av legender, mästare och rookies."],
 "tiers":{"everyday":{"label":"Låg insats","score":65,"items":["8 kort"]},"good":{"label":"Bra träff","score":72,"items":["rookie- eller stjärnparallel"]},"big":{"label":"Riktigt bra","score":86,"items":["Beam Team eller autograph"]},"jackpot":{"label":"Monsterhit","score":98,"items":["stjärnauto eller Dual Auto 1/1"]}},
 "caveat":"Boxens två autografer i snitt gäller inte ett löst pack; en boxhit kan redan ha dragits ur ursprungsboxen."
},
"cc-2025-26-spx-hobby": {
 "source_name":"Upper Deck official 2025-26 SPx checklist",
 "source_url":"https://upperdeck.com/checklist/2025-2026-spx-checklist/",
 "key_names":["Matthew Schaefer Rookie #109","Matthew Schaefer Rookie SuperScripts","Connor McDavid SuperScripts Gold /10","Wayne Gretzky Salute Auto /25","Sidney Crosby Salute Auto /25"],
 "headline_chases":[
  {"card":"Matthew Schaefer Black Rookie Auto 1/1","tier":"JACKPOT","odds":"1/1; slumpmässigt infogat","why":"Unik rookieautograf av checklistans främsta rookie-namn."},
  {"card":"Connor McDavid SuperScripts Gold Auto /10","tier":"JACKPOT","odds":"/10; slumpmässigt infogat","why":"Lågnumrerad autograf av checklistans största aktiva namn."},
  {"card":"Wayne Gretzky eller Sidney Crosby Salute Auto /25","tier":"MONSTER","odds":"/25; slumpmässigt infogat","why":"Två ikoniska namn i verifierade signerade spår."},
  {"card":"Matthew Schaefer Rookie SuperScripts","tier":"MONSTER","odds":"Rookie SuperScripts 1:120 hobby-pack över checklistan","why":"Namngiven rookieauto med publicerat familjeodds."},
  {"card":"Matthew Schaefer Rookie Hologram","tier":"MYCKET BRA","odds":"Rookie Holograms 1:86 hobby-pack","why":"Topprookie i produktens hologramspår."}
 ],
 "why_exciting":["Officiell checklist visar McDavid-, Gretzky- och Crosby-autografer samt starka rookieautos.","Boxen ger i snitt fyra rookies, tre Silver och en Gold parallel."],
 "tiers":{"everyday":{"label":"Koncentrerad box","score":87,"items":["24 kort","4 rookies","3 Silver + 1 Gold"]},"good":{"label":"Bra träff","score":78,"items":["stark rookieparallel"]},"big":{"label":"Riktigt bra","score":90,"items":["Rookie SuperScripts eller stjärnauto"]},"jackpot":{"label":"Monsterhit","score":99,"items":["Schaefer 1/1 eller McDavid /10 auto"]}},
 "caveat":"Boxens rookie- och parallelltal är genomsnitt. Autograf, Hologram Rookie eller ett visst namn är inte garanterat."
},
"cc-2025-26-spx-hobby-pack": {
 "source_name":"Upper Deck official 2025-26 SPx checklist",
 "source_url":"https://upperdeck.com/checklist/2025-2026-spx-checklist/",
 "key_names":["Matthew Schaefer Rookie #109","Matthew Schaefer Rookie SuperScripts","Connor McDavid SuperScripts Gold /10","Wayne Gretzky Salute Auto /25","Sidney Crosby Salute Auto /25"],
 "headline_chases":[
  {"card":"Matthew Schaefer Black Rookie Auto 1/1","tier":"JACKPOT","odds":"1/1; individuellt packodds ej publicerat","why":"Produktens unika topprookieauto."},
  {"card":"Connor McDavid SuperScripts Gold Auto /10","tier":"JACKPOT","odds":"/10; slumpmässigt infogat","why":"Lågnumrerad McDavid-autograf."},
  {"card":"Matthew Schaefer Rookie SuperScripts","tier":"MONSTER","odds":"Rookie SuperScripts 1:120 hobby-pack över checklistan","why":"Namngiven rookieauto med användbart familjeodds."},
  {"card":"Matthew Schaefer Rookie Hologram","tier":"MYCKET BRA","odds":"Rookie Holograms 1:86 hobby-pack","why":"Sällsynt rookieinsert av ett verifierat toppnamn."}
 ],
 "why_exciting":["Tre kort men mycket högt tak med signerade stjärnor och rookies.","Upper Deck publicerar checklist- och familjeodds för flera centrala chase-spår."],
 "tiers":{"everyday":{"label":"Tunn pack","score":55,"items":["3 kort"]},"good":{"label":"Bra träff","score":72,"items":["rookie eller numrerad parallel"]},"big":{"label":"Riktigt bra","score":89,"items":["Rookie SuperScripts"]},"jackpot":{"label":"Monsterhit","score":99,"items":["Schaefer 1/1 eller McDavid /10 auto"]}},
 "caveat":"Ett löst pack har ingen boxgaranti och kan komma från en box där de bästa träffarna redan dragits."
},
"cc-2025-topps-disney-wonder-pack": {
 "source_name":"Topps official 2025 Disney Wonder checklist and odds",
 "source_url":"https://www.topps.com/pages/topps-disney-wonder",
 "key_names":["PrincessFractor 1/1","Cinderella Glass Slipper /75","Enchanted Autographs","Princess Sketch Cards","SHINY SuperFractor 1/1"],
 "headline_chases":[
  {"card":"Disney Princess PrincessFractor 1/1","tier":"JACKPOT","odds":"1/1; individuellt packodds ej publicerat","why":"Unikt kort ur produktens främsta prinsesspår."},
  {"card":"Enchanted Autograph SuperFractor 1/1","tier":"JACKPOT","odds":"1/1; autograffamiljen är extremt sällsynt","why":"Signatur och produktens lägsta parallellnivå."},
  {"card":"Princess eller Build a Snowman Sketch Card","tier":"MONSTER","odds":"Original sketch; exakt packodds varierar","why":"Ett handgjort originalkort snarare än en massproducerad parallel."},
  {"card":"Cinderella Glass Slipper Chrome /75","tier":"MYCKET BRA","odds":"/75; individuellt packodds ej publicerat","why":"Namngiven jubileums-chase med låg upplaga."},
  {"card":"Tapestries eller Cinderella 75th Anniversary","tier":"BRA","odds":"1:9 hobby-pack per insertfamilj","why":"Officiellt publicerade och återkommande Disney-inserts."}
 ],
 "why_exciting":["Ett Tier 2-kort per pack och flera publicerade insertodds.","Autografer, originalskisser och 1/1-prinsesskort ger ett mycket högt tak för ett 99-kronorspaket."],
 "tiers":{"everyday":{"label":"Något samlarbart","score":68,"items":["6 kort","1 Tier 2"]},"good":{"label":"Bra träff","score":74,"items":["Tapestries/Cinderella insert"]},"big":{"label":"Riktigt bra","score":90,"items":["sketch eller Enchanted Auto"]},"jackpot":{"label":"Monsterhit","score":99,"items":["PrincessFractor eller autograph 1/1"]}},
 "caveat":"Ett löst pack garanterar bara kortkonfigurationen; autograf, sketch, numrerat kort eller specifik Disneyfigur är inte garanterad."
},
"cc-2025-topps-chrome-deadpool-hobby": {
 "source_name":"Topps official 2025 Chrome Deadpool checklist and odds",
 "source_url":"https://www.topps.com/pages/deadpool-chrome",
 "key_names":["Ryan Reynolds Autograph","Hugh Jackman Autograph","Deadpool SuperFractor 1/1","Wolverine SuperFractor 1/1","Original Sketch Card"],
 "headline_chases":[
  {"card":"Ryan Reynolds Deadpool Autograph","tier":"JACKPOT","odds":"Autograph-program; exakt signer-odds varierar","why":"Autentisk signatur från filmens huvudroll."},
  {"card":"Hugh Jackman Wolverine Autograph","tier":"JACKPOT","odds":"Autograph-program; exakt signer-odds varierar","why":"Autentisk Wolverine-signatur i samma produkt."},
  {"card":"Deadpool eller Wolverine SuperFractor 1/1","tier":"JACKPOT","odds":"1/1; individuellt boxodds ej publicerat","why":"Unik Chrome-parallel av produktens två största karaktärer."},
  {"card":"Original Sketch Card","tier":"MONSTER","odds":"Sketch-program; exakt boxodds varierar","why":"Unikt originalverk snarare än ett vanligt tryckt kort."},
  {"card":"The Void Shadowbox eller Comic Book Gold","tier":"MYCKET BRA","odds":"Case-hit/insert-spår; exakt odds varierar","why":"Två officiellt namngivna visuella chase-familjer."}
 ],
 "why_exciting":["Ryan Reynolds- och Hugh Jackman-autografer är verifierade i checklistmaterialet.","Originalskisser, case hits och 1/1-SuperFractors ger flera vägar till ett riktigt stort kort."],
 "tiers":{"everyday":{"label":"Mycket öppningsinnehåll","score":86,"items":["80 Chrome-kort"]},"good":{"label":"Bra träff","score":76,"items":["numrerad karaktärsparallel"]},"big":{"label":"Riktigt bra","score":91,"items":["sketch eller case hit"]},"jackpot":{"label":"Monsterhit","score":100,"items":["Reynolds/Jackman auto eller SuperFractor 1/1"]}},
 "caveat":"Butiken och Topps bekräftar att autografer och sketches finns, men anger ingen garanti för en per hobbybox."
}
})

CHASE_PROFILES["cc-2026-fleer-ultra-golf-pack"] = {
 "source_name":"Upper Deck official 2026 Fleer Ultra Golf checklist",
 "source_url":"https://upperdeck.com/checklist/2026-fleer-ultra-golf/",
 "key_names":["Tiger Woods #35","Nelly Korda Rookie #40","Lydia Ko Rookie #50","Hideki Matsuyama Rookie #65","Viktor Hovland #1"],
 "headline_chases":[
  {"card":"Tiger Woods Gold Spectrum Parallel 1/1","tier":"JACKPOT","odds":"1/1; individuellt packodds ej publicerat","why":"Unik parallel av checklistans mest ikoniska golfnamn."},
  {"card":"Nelly Korda Rookie Gold Rainbow Foilboard Auto /25","tier":"JACKPOT","odds":"Rookie-auto-familjen 1:60 pack; Gold /25","why":"Signerad lågnumrerad rookie av ett verifierat toppnamn."},
  {"card":"Lydia Ko eller Hideki Matsuyama Rookie Auto","tier":"MONSTER","odds":"Rookie Rainbow Foilboard Auto 1:60 pack över hela rookielistan","why":"Två stora namn markerade som rookies i den officiella checklistan."},
  {"card":"Hole in One eller Thunderclap insert","tier":"MYCKET BRA","odds":"1:188 pack för respektive insertfamilj","why":"Två officiellt oddsatta ultra-rare/case-hit-spår."},
  {"card":"Medallions – Tiger Woods, Nelly Korda eller annan stjärna","tier":"BRA","odds":"Medallions 1:4 pack; exakt golfare ur checklistan","why":"Återkommande foilinsert med paralleller ned till 1/1."}
 ],
 "why_exciting":["Officiella checklistan innehåller Tiger Woods, Nelly Korda, Lydia Ko, Hideki Matsuyama och Viktor Hovland.","Upper Deck publicerar användbara odds: rookieauto 1:60, Hole in One 1:188 och Medallions 1:4 pack."],
 "tiers":{"everyday":{"label":"Vanligt men intressant","score":74,"items":["1–2 rookies per pack","Medallions 1:4"]},"good":{"label":"Bra träff","score":77,"items":["numrerad stjärnparallel"]},"big":{"label":"Riktigt bra","score":88,"items":["rookieauto 1:60","Hole in One 1:188"]},"jackpot":{"label":"Monsterhit","score":97,"items":["Tiger Woods 1/1","Nelly Korda Auto /25"]}},
 "caveat":"1:60 och 1:188 gäller hela kortfamiljen, inte en viss golfare. Ett löst pack har ingen garanterad autograf."
}

_nba_retail_profile = {
 "source_name":"Topps official 2025-26 NBA Hoops checklist and retail format guide",
 "source_url":"https://www.topps.com/pages/topps-hoops-basketball",
 "key_names":["Cooper Flagg Hoops Rookie First Signs","Dylan Harper Hoops Rookie First Signs","Victor Wembanyama","LeBron James","Block by Block case hit"],
 "headline_chases":[
  {"card":"Cooper Flagg Hoops Rookie First Signs","tier":"JACKPOT","odds":"Retail-autograf; kortspecifikt odds ej publicerat","why":"Verifierad topprookie i retailformatets signerade spår."},
  {"card":"Dylan Harper Hoops Rookie First Signs","tier":"MONSTER","odds":"Retail-autograf; kortspecifikt odds ej publicerat","why":"Namngiven topprookie i retail-autografprogrammet."},
  {"card":"Block by Block eller Boom Shaka Laka case hit","tier":"MONSTER","odds":"Retail-only case hit; exakt formatodds ej publicerat","why":"Två case-hit-familjer som Topps uttryckligen avgränsar till retail."},
  {"card":"Victor Wembanyama eller LeBron James retail parallel","tier":"MYCKET BRA","odds":"Parallelfamilj; kortspecifikt odds ej publicerat","why":"Två av checklistans mest etablerade stjärnnamn."}
 ],
 "why_exciting":["Retailformatet har egna case hits och signerade kort, inte hobbyformatets innehållskonfiguration.","Cooper Flagg och Dylan Harper ger tydliga namngivna rookie-jakter."],
 "tiers":{"everyday":{"label":"Retailöppning","score":72,"items":["retailparalleller och inserts"]},"good":{"label":"Bra träff","score":72,"items":["stjärn- eller rookieparallel"]},"big":{"label":"Riktigt bra","score":84,"items":["retail case hit eller autograph"]},"jackpot":{"label":"Monsterhit","score":94,"items":["Cooper Flagg retail-autograf"]}},
 "caveat":"Topps publicerar inget löfte om autograf eller case hit per Value/Hanger Box. Hobbyboxens autografinnehåll gäller inte retailformaten."
}
CHASE_PROFILES["cc-2025-26-topps-nba-hoops-value"] = copy.deepcopy(_nba_retail_profile)
CHASE_PROFILES["cc-2025-26-topps-nba-hoops-value"]["tiers"]["everyday"]["items"] = ["56 kort", "Green Hoops-paralleller"]
CHASE_PROFILES["cc-2025-26-topps-nba-hoops-value"]["why_exciting"][0] = "Sju pack och Green Hoops-paralleller ger fler retailförsök än en Hanger Box."
CHASE_PROFILES["cc-2025-26-topps-nba-hoops-hanger"] = copy.deepcopy(_nba_retail_profile)
CHASE_PROFILES["cc-2025-26-topps-nba-hoops-hanger"]["tiers"]["everyday"] = {"label":"Kort retailöppning","score":63,"items":["25 kort", "Orange Hoops-paralleller"]}
CHASE_PROFILES["cc-2025-26-topps-nba-hoops-hanger"]["why_exciting"][0] = "Ett 25-kortspack och Orange Hoops-paralleller ger en billigare retailöppning."

_nfl_family_chases = copy.deepcopy(CHASE_PROFILES["cc-2026-topps-flagship-nfl-pack"])
CHASE_PROFILES["cc-2026-topps-flagship-nfl-hobby"] = copy.deepcopy(_nfl_family_chases)
CHASE_PROFILES["cc-2026-topps-flagship-nfl-hobby"].update({
 "source_name":"Topps official 2026 Flagship Football checklist and hobby format guide",
 "why_exciting":["20 hobby-pack och 240 kort ger bred tillgång till rookies, paralleller, autografer och memorabilia.","Fernando Mendoza, Jeremiyah Love, Carnell Tate, Mahomes och Brady är verifierade checklistnamn."],
 "tiers":{"everyday":{"label":"Bred hobbyöppning","score":86,"items":["240 kort", "Aqua Rainbow och inserts"]},"good":{"label":"Bra träff","score":78,"items":["numrerad rookie- eller stjärnparallel"]},"big":{"label":"Riktigt bra","score":88,"items":["1957 Rookie Variation, SSP eller autograph"]},"jackpot":{"label":"Monsterhit","score":98,"items":["Mahomes/Brady auto eller Patch Auto"]}},
 "caveat":"Butikssidan anger ingen garanterad autograf eller relic per hobbybox. Ett specifikt namn, SSP eller premiumkort är inte garanterat."
})
CHASE_PROFILES["cc-2026-topps-flagship-nfl-mega"] = copy.deepcopy(_nfl_family_chases)
CHASE_PROFILES["cc-2026-topps-flagship-nfl-mega"].update({
 "source_name":"Topps official 2026 Flagship Football checklist and Coolcard Mega configuration",
 "why_exciting":["12 retail-pack och 180 kort med Aqua Holo och 1991 Crackle-paralleller.","Den breda checklistan ger många rookie- och stjärnchanser utan att påstå en hobbygaranti."],
 "tiers":{"everyday":{"label":"Stor retailöppning","score":83,"items":["180 kort", "Aqua Holo och Crackle-paralleller"]},"good":{"label":"Bra träff","score":76,"items":["numrerad rookie- eller stjärnparallel"]},"big":{"label":"Riktigt bra","score":82,"items":["sällsynt variation eller premiumparallel"]},"jackpot":{"label":"Monsterhit","score":91,"items":["extremt sällsynt toppnamnsträff"]}},
 "caveat":"Mega Box-sidan lovar ingen autograf, relic eller SSP. Hobbyformatets eventuella hitfördelning får inte överföras till retail."
})
CHASE_PROFILES["cc-2026-topps-flagship-nfl-fat-pack"] = copy.deepcopy(_nfl_family_chases)
CHASE_PROFILES["cc-2026-topps-flagship-nfl-fat-pack"].update({
 "source_name":"Topps official 2026 Flagship Football checklist and Coolcard Fat Pack configuration",
 "why_exciting":["36 kort under 100 kr med retail-exklusiva inserts och paralleller.","Ett billigt format för rookiejakt, men mycket lägre träfftäthet än en hel box."],
 "tiers":{"everyday":{"label":"Låg insats","score":68,"items":["36 kort", "retail-exklusiva inserts"]},"good":{"label":"Bra träff","score":68,"items":["rookie- eller stjärnparallel"]},"big":{"label":"Riktigt bra","score":76,"items":["numrerad topprookie"]},"jackpot":{"label":"Monsterhit","score":88,"items":["extremt sällsynt premiumträff"]}},
 "caveat":"Ett löst Fat Pack garanterar inte autograf, relic, SSP eller ett visst rookiekort. Hobbyboxens konfiguration gäller inte detta pack."
})

CHASE_PROFILES["cc-yugioh-phantom-revenge-display"] = {
 "source_name":"Konami official Phantom Revenge product page and card database",
 "source_url":"https://www.yugioh-card.com/eu/product/phantom-revenge/",
 "key_names":["Hecahands Ibtel Starlight Rare","Hecahands Jauzah Starlight Rare","Enneacraft - Atori.MAR Starlight Rare","Kewl Tune Mix Starlight Rare","Kewl Tune Synchro Starlight Rare"],
 "headline_chases":[
  {"card":"Hecahands Ibtel Starlight Rare","tier":"JACKPOT","odds":"Starlight Rare; Konami publicerar inte kortspecifikt packodds","why":"Officiella kortdatabasen bekräftar Starlight- och Collector's Rare-versioner."},
  {"card":"Hecahands Jauzah Starlight Rare","tier":"MONSTER","odds":"Starlight Rare; exakt packodds ej publicerat","why":"Fusionkort i setets centrala Hecahands-tema."},
  {"card":"Enneacraft - Atori.MAR Starlight Rare","tier":"MONSTER","odds":"Starlight Rare; exakt packodds ej publicerat","why":"Officiellt verifierad Starlight-uppgradering."},
  {"card":"Kewl Tune Mix eller Kewl Tune Synchro Starlight Rare","tier":"MONSTER","odds":"Starlight Rare; exakt packodds ej publicerat","why":"Två namngivna premiumvarianter från Kewl Tune-temat."}
 ],
 "why_exciting":["24 engelska pack ger flera försök på ett kompakt 60-kortsset.","Konami bekräftar 15 Collector's Rare- och 10 Starlight Rare-uppgraderingar."],
 "tiers":{"everyday":{"label":"Full display","score":79,"items":["168 kort", "24 pack"]},"good":{"label":"Bra träff","score":70,"items":["Ultra Rare eller stark Super Rare"]},"big":{"label":"Riktigt bra","score":82,"items":["Collector's Rare"]},"jackpot":{"label":"Monsterhit","score":91,"items":["namngiven Starlight Rare"]}},
 "caveat":"Konami publicerar rarity-fördelningen men inga kortspecifika pack- eller displayodds. Starlight Rare är en rarity, inte en garanti per display."
}

CHASE_PROFILES["as-yugioh-phantom-revenge-pack"] = copy.deepcopy(
    CHASE_PROFILES["cc-yugioh-phantom-revenge-display"]
)
CHASE_PROFILES["as-yugioh-phantom-revenge-pack"].update({
 "why_exciting":["Ett billigt engelskt löspaket med en verifierad foilplats.","Collector's Rare- och Starlight Rare-versioner finns i checklistan, men är mycket sällsynta och saknar publicerade odds."],
 "tiers":{"everyday":{"label":"Ett löst paket","score":48,"items":["7 kort","1 foil och 6 Rare"]},"good":{"label":"Bra träff","score":57,"items":["Ultra Rare eller stark Super Rare"]},"big":{"label":"Riktigt bra","score":70,"items":["Collector's Rare"]},"jackpot":{"label":"Monsterhit","score":84,"items":["namngiven Starlight Rare"]}},
 "caveat":"Detta är ett löst paket, inte en förseglad display. Den enda verifierade packkonfigurationen är 1 foil och 6 Rare; Collector's Rare, Starlight Rare och ett visst kort saknar publicerade odds och är inte garanterade."
})

_maze_muertos_profile = {
 "source_name":"Konami official Maze of Muertos product page and card database",
 "source_url":"https://www.db.yugioh-card.com/yugiohdb/card_search.action?ope=1&pid=2000001596000&request_locale=en&rp=99999",
 "key_names":["Uria, Lord of Searing Flames Starlight Rare","Dark Magician of Destruction Collector's Rare","Pumpking the King of Grave Ghosts Collector's Rare","Darkuriboh Collector's Rare","Albion the Sanctifire Dragon Starlight Rare"],
 "headline_chases":[
  {"card":"Uria, Lord of Searing Flames Starlight Rare","tier":"JACKPOT","odds":"Starlight Rare; exakt packodds ej publicerat","why":"Officiella kortdatabasen bekräftar den namngivna Starlight-versionen."},
  {"card":"Albion the Sanctifire Dragon Starlight Rare","tier":"MONSTER","odds":"Starlight Rare; exakt packodds ej publicerat","why":"Verifierad premiumversion av ett etablerat fusionkort."},
  {"card":"Dark Magician of Destruction Collector's Rare","tier":"MONSTER","odds":"Collector's Rare; exakt packodds ej publicerat","why":"Namngiven premiumversion i Dark Magician-spåret."},
  {"card":"Pumpking the King of Grave Ghosts Collector's Rare","tier":"MYCKET BRA","odds":"Collector's Rare; exakt packodds ej publicerat","why":"Setets officiellt profilerade huvudkaraktär i premiumrarity."},
  {"card":"Darkuriboh Collector's Rare","tier":"MYCKET BRA","odds":"Collector's Rare; exakt packodds ej publicerat","why":"Animebaserad, namngiven Collector's Rare enligt Konamis databas."}
 ],
 "why_exciting":["Checklistan har verifierade Starlight-, Collector's- och Secret Rare-spår med välkända Yu-Gi-Oh-namn.","Varje paket innehåller en foil och sex Rare, vilket ger ett tydligt innehållsgolv utan att lova hög rarity."],
 "tiers":{"everyday":{"label":"Full display","score":80,"items":["24 pack","168 kort","24 foilplatser"]},"good":{"label":"Bra träff","score":71,"items":["stark foil eller Secret Rare"]},"big":{"label":"Riktigt bra","score":83,"items":["Collector's Rare"]},"jackpot":{"label":"Monsterhit","score":92,"items":["namngiven Starlight Rare"]}},
 "caveat":"Konami verifierar 1 foil och 6 Rare per paket samt checklistans rarities, men publicerar inte exakta Starlight-, Collector's- eller kortspecifika odds. Ingen premiumrarity är garanterad per display."
}
CHASE_PROFILES["as-yugioh-maze-muertos-display"] = copy.deepcopy(_maze_muertos_profile)
CHASE_PROFILES["as-yugioh-maze-muertos-pack"] = copy.deepcopy(_maze_muertos_profile)
CHASE_PROFILES["as-yugioh-maze-muertos-pack"].update({
 "why_exciting":["Ett engelskt sjukortspaket under 50 kr med en verifierad foilplats.","Starlight- och Collector's Rare-spåren ger högt korttak, men utfallet i ett löst paket är mycket variansrikt."],
 "tiers":{"everyday":{"label":"Ett löst paket","score":47,"items":["7 kort","1 foil och 6 Rare"]},"good":{"label":"Bra träff","score":56,"items":["stark foil eller Secret Rare"]},"big":{"label":"Riktigt bra","score":69,"items":["Collector's Rare"]},"jackpot":{"label":"Monsterhit","score":84,"items":["namngiven Starlight Rare"]}},
 "caveat":"Detta är ett löst paket. 1 foil och 6 Rare är verifierat, men inga premiumrarities eller namngivna kort är garanterade och Konami publicerar inte kortspecifika odds."
})

CHASE_PROFILES["as-yugioh-blazing-dominion-pack"] = {
 "source_name":"Konami official Blazing Dominion product page and card database",
 "source_url":"https://www.db.yugioh-card.com/yugiohdb/card_search.action?ope=1&pid=2000001614000&request_locale=en&rp=99999",
 "key_names":["The Crimson King Starlight Rare","Power Vice Dragon Starlight Rare","Superdreadnought Rail Cannon Gustav Rocket Starlight Rare","Superdreadnought Rail Cannon Flying Launcher Starlight Rare","Dominus Spark Starlight Rare"],
 "headline_chases":[
  {"card":"The Crimson King Starlight Rare","tier":"JACKPOT","odds":"Starlight Rare; exakt packodds ej publicerat","why":"Officiellt verifierad Starlight-version av setets Red Dragon Archfiend-huvudkort."},
  {"card":"Power Vice Dragon Starlight Rare","tier":"MONSTER","odds":"Starlight Rare; exakt packodds ej publicerat","why":"Secret Rare som också finns i en verifierad Starlight-version."},
  {"card":"Superdreadnought Rail Cannon Gustav Rocket Starlight Rare","tier":"MONSTER","odds":"Starlight Rare; exakt packodds ej publicerat","why":"Namngivet Rank 10-tågkort i premiumrarity."},
  {"card":"Superdreadnought Rail Cannon Flying Launcher Starlight Rare","tier":"MONSTER","odds":"Starlight Rare; exakt packodds ej publicerat","why":"Ytterligare officiellt verifierad Rank 10 Starlight-chase."},
  {"card":"Dominus Spark Starlight Rare","tier":"MYCKET BRA","odds":"Starlight Rare; exakt packodds ej publicerat","why":"Verifierad premiumversion i setets 25-korts Starlight-spår."}
 ],
 "why_exciting":["Den officiella 101-kortslistan har 25 kort som Starlight Rare och flera exakt namngivna premiumträffar.","Paketet kostar under 50 kr, men butikssidan anger inte antalet kort och inget högrarity-kort är garanterat."],
 "tiers":{"everyday":{"label":"Ett löst paket","score":43,"items":["1 engelskt boosterpaket"]},"good":{"label":"Bra träff","score":54,"items":["Super, Ultra eller Secret Rare"]},"big":{"label":"Riktigt bra","score":67,"items":["stark Secret Rare"]},"jackpot":{"label":"Monsterhit","score":83,"items":["namngiven Starlight Rare"]}},
 "caveat":"Starlight Rare är en kortversion, inte en dragchans. Konami publicerar inga kortspecifika odds och den aktuella butikssidan anger inte antal kort i paketet, så BoxFinder lämnar den uppgiften okänd."
}

_azurite_sea_profile = {
 "source_name":"Ravensburger official Azurite Sea product page and published complete card list",
 "source_url":"https://www.disneylorcana.com/en-US/product/azurite-sea",
 "key_names":["Tigger - In the Crow's Nest #215 Enchanted","Baymax - Personal Healthcare Companion #218 Enchanted","You Came Back #213 Enchanted","Tiana - Restaurant Owner #206 Enchanted","Chip 'n' Dale - Recovery Rangers #205 Enchanted"],
 "headline_chases":[
  {"card":"Tigger - In the Crow's Nest #215 Enchanted","tier":"JACKPOT","odds":"Enchanted; officiellt kortspecifikt packodds ej publicerat","why":"Namngiven Enchanted i den kompletta Azurite Sea-listan."},
  {"card":"Baymax - Personal Healthcare Companion #218 Enchanted","tier":"JACKPOT","odds":"Enchanted; officiellt kortspecifikt packodds ej publicerat","why":"Big Hero 6-huvudkaraktär i setets premiumrarity."},
  {"card":"You Came Back #213 Enchanted","tier":"MONSTER","odds":"Enchanted; officiellt kortspecifikt packodds ej publicerat","why":"Namngivet Enchanted action-kort."},
  {"card":"Tiana - Restaurant Owner #206 Enchanted","tier":"MONSTER","odds":"Enchanted; officiellt kortspecifikt packodds ej publicerat","why":"Namngiven prinsesskaraktär i Enchanted-rarity."},
  {"card":"Chip 'n' Dale - Recovery Rangers #205 Enchanted","tier":"MONSTER","odds":"Enchanted; officiellt kortspecifikt packodds ej publicerat","why":"Setets första numrerade Enchanted och centralt Rescue Rangers-spår."}
 ],
 "why_exciting":["Azurite Sea har 18 namngivna Enchanted-kort utöver 204-kortsbasen.","Ravensburger verifierar 12 slumpade kort per paket och 24 paket per display."],
 "tiers":{"everyday":{"label":"Full display","score":82,"items":["24 pack","288 kort"]},"good":{"label":"Bra träff","score":70,"items":["Legendary eller stark foil"]},"big":{"label":"Riktigt bra","score":80,"items":["namngiven Enchanted"]},"jackpot":{"label":"Monsterhit","score":89,"items":["Tigger eller Baymax Enchanted"]}},
 "caveat":"Ravensburger publicerar ingen Enchanted-garanti per display och inga kortspecifika packodds. Namngivna Enchanted-kort kommer från en publicerad komplett checklista; BoxFinder påstår inte verifierad ekonomisk avkastning."
}
CHASE_PROFILES["dl-lorcana-azurite-display"] = copy.deepcopy(_azurite_sea_profile)
CHASE_PROFILES["cc-lorcana-azurite-pack"] = copy.deepcopy(_azurite_sea_profile)
CHASE_PROFILES["cc-lorcana-azurite-pack"].update({
 "why_exciting":["Ett tolkkortspaket ger en billig chans på 18 namngivna Enchanted-kort.","Den verifierade foilplatsen kan ha slumpad rarity, men inget visst kort är garanterat."],
 "tiers":{"everyday":{"label":"Ett löst paket","score":49,"items":["12 kort","1 foil med slumpad rarity"]},"good":{"label":"Bra träff","score":57,"items":["Legendary eller stark foil"]},"big":{"label":"Riktigt bra","score":69,"items":["namngiven Enchanted"]},"jackpot":{"label":"Monsterhit","score":82,"items":["Tigger eller Baymax Enchanted"]}},
 "caveat":"Detta är ett löst paket, inte en display. Ravensburger publicerar inga kortspecifika packodds och ingen Enchanted är garanterad."
})

CHASE_PROFILES["cc-2023-panini-chronicles-racing-hobby"] = {
 "source_name":"Panini official checklist, Coolcard box configuration and published checklist index",
 "source_url":"https://www.paniniamerica.net/2023-chronicles-racing-nascar-trading-cards-hobby.html",
 "key_names":["Jimmie Johnson Immaculate Auto Relic","Dale Earnhardt Jr. Spectra Color Blast","Jeff Gordon Lightning Autograph","Chase Elliott Contenders Optic Autograph","Kyle Busch Cornerstones Materials Auto"],
 "headline_chases":[
  {"card":"Jimmie Johnson Immaculate Auto Relic","tier":"JACKPOT","odds":"3 autografer och 1 memorabilia per box över hela checklistan; specifikt kort ej garanterat","why":"Verifierat toppnamn i produktens premium auto/relic-spår."},
  {"card":"Dale Earnhardt Jr. Spectra Color Blast","tier":"MONSTER","odds":"SSP; exakt boxodds ej publicerat","why":"Namngiven sällsynt Spectra-variant av en NASCAR-ikon."},
  {"card":"Jeff Gordon Lightning Autograph","tier":"MONSTER","odds":"Autografprogram; specifik förare ej garanterad","why":"Legendnamn i ett separat signerat spår."},
  {"card":"Chase Elliott Contenders Optic Autograph","tier":"MYCKET BRA","odds":"Autografprogram; specifik förare ej garanterad","why":"En av checklistans största aktiva förare."},
  {"card":"Kyle Busch Cornerstones Materials Auto","tier":"MONSTER","odds":"Auto/memorabilia-program; specifikt kort ej garanterat","why":"Kombinerar signatur och racingmemorabilia."}
 ],
 "why_exciting":["Tre autografer och en memorabilia per box i snitt ger hög dokumenterad hit density.","Sex pack blandar Chronicles, Immaculate, Spectra, Contenders Optic och flera andra varumärken."],
 "tiers":{"everyday":{"label":"Hit-koncentrerad hobbybox","score":93,"items":["3 autografer i snitt", "1 memorabilia i snitt", "2 Immaculate-kort"]},"good":{"label":"Bra träff","score":84,"items":["numrerad förare eller stark auto"]},"big":{"label":"Riktigt bra","score":93,"items":["legendauto, Color Blast eller auto/relic"]},"jackpot":{"label":"Monsterhit","score":97,"items":["lågnumrerad legend-auto/relic"]}},
 "caveat":"Boxinnehållet är genomsnitt över produktionen. Ingen viss förare, kortfamilj eller numrering är garanterad; andrahandsvärden ingår inte i profilen."
}

_msh_play_profile = {
 "source_name":"Wizards official Collecting Magic: The Gathering | Marvel Super Heroes guide",
 "source_url":"https://magic.wizards.com/en/news/feature/collecting-marvel-super-heroes",
 "key_names":["The Mind Stone","Iron Man, Titan of Innovation","Mjölnir, Hammer of Thor","Captain America, Super-Soldier","Thor, God of Thunder","Black Panther, Vanguard"],
 "headline_chases":[
  {"card":"The Mind Stone – main-set version","tier":"MYCKET BRA","odds":"Kan dras non-foil eller traditional foil i Play Boosters; kortspecifikt odds ej publicerat","why":"Det verifierade Infinity Stone-spåret som faktiskt finns i Play Booster-formatet."},
  {"card":"Iron Man, Titan of Innovation – Source Material","tier":"MONSTER","odds":"Source Material-familjen 1:24 Play Boosters; detta är 1 av 60 likafrekventa kort","why":"Namngiven Marvel/Magic-chase med officiellt familjeodds."},
  {"card":"Mjölnir, Hammer of Thor – Showcase Panel","tier":"MYCKET BRA","odds":"Panel rare/mythic kan förekomma i Play Booster-slots; specifikt kortodds ej publicerat","why":"Namngivet premiumutförande tillgängligt i rätt format."},
  {"card":"Captain America, Super-Soldier – Borderless Scene","tier":"MYCKET BRA","odds":"Scene rare/mythic kan förekomma i Play Boosters; specifikt kortodds ej publicerat","why":"En officiellt namngiven scen-chase."},
  {"card":"Thor, God of Thunder – Borderless Scene","tier":"MYCKET BRA","odds":"Scene rare/mythic kan förekomma i Play Boosters; specifikt kortodds ej publicerat","why":"Namngiven Thor-träff från Play Booster-poolen."}
 ],
 "why_exciting":["Play Boosters har en garanterad rare/mythic-plats och en traditional foil-plats.","Officiella slotodds och 1:24 för Source Material gör formatet mer transparent än de flesta TCG-produkter."],
 "tiers":{"everyday":{"label":"Full Play Booster-display","score":86,"items":["30 pack","30+ rare/mythic","30 traditional foils"]},"good":{"label":"Bra träff","score":75,"items":["rare/mythic Marvel-kort","foil rare eller mythic"]},"big":{"label":"Riktigt bra","score":83,"items":["Source Material","scene-, logo- eller panel-mythic"]},"jackpot":{"label":"Play Booster-toppträff","score":88,"items":["The Mind Stone premiumutförande","namngiven mythic Booster Fun"]}},
 "caveat":"Cosmic Foil Mind Stone, Gauntlet Mind Stone och Classic Comic-korten är Collector Booster-exklusiva och ingår inte här. 1:24 gäller hela Source Material-familjen, inte Iron Man specifikt."
}
CHASE_PROFILES["cc-mtg-marvel-superheroes-play-display"] = copy.deepcopy(_msh_play_profile)

CHASE_PROFILES["dl-mtg-marvel-superheroes-play-pack"] = copy.deepcopy(_msh_play_profile)
CHASE_PROFILES["dl-mtg-marvel-superheroes-play-pack"]["why_exciting"] = ["Ett 14-kortspack under 100 kr ger minst en rare/mythic och en traditional foil.","Source Material, scene, logo och panel kan dras, men premiumutförandena är sällsynta."]
CHASE_PROFILES["dl-mtg-marvel-superheroes-play-pack"]["tiers"]["everyday"] = {"label":"Ett löst Play Booster","score":53,"items":["14 kort","1–4 rare/mythic","1 traditional foil"]}
CHASE_PROFILES["dl-mtg-marvel-superheroes-play-pack"]["caveat"] = "Detta är ett löst Play Booster. Source Material 1:24 gäller familjen över produktionen; Cosmic Foil-, Gauntlet- och Classic Comic-kort är Collector Booster-exklusiva."

CHASE_PROFILES["dl-mtg-marvel-superheroes-bundle"] = copy.deepcopy(_msh_play_profile)
CHASE_PROFILES["dl-mtg-marvel-superheroes-bundle"]["headline_chases"].insert(0, {"card":"The Scarlet Witch – alternate-art traditional foil promo","tier":"BRA","odds":"1 garanterad promo per Bundle","why":"Verifierat fast innehåll som ger ett tydligt golv."})
CHASE_PROFILES["dl-mtg-marvel-superheroes-bundle"]["why_exciting"] = ["Nio Play Boosters ger nio chanser på setets tillåtna Booster Fun-spår.","Scarlet Witch-promon och 30 basic lands är garanterade, men en del av priset går till tillbehör."]
CHASE_PROFILES["dl-mtg-marvel-superheroes-bundle"]["tiers"]["everyday"] = {"label":"Bundle-innehåll","score":70,"items":["9 Play Boosters","Scarlet Witch foil promo","30 basic lands"]}
CHASE_PROFILES["dl-mtg-marvel-superheroes-bundle"]["caveat"] = "Bundle ger färre öppningsförsök per krona än en display och innehåller tillbehör. Cosmic Foil Mind Stone och övriga Collector Booster-exklusiva behandlingar kan inte dras."

_spiderman_play_profile = {
 "source_name":"Wizards official Collecting Magic: The Gathering | Marvel's Spider-Man guide",
 "source_url":"https://magic.wizards.com/en/news/feature/collecting-marvels-spider-man",
 "key_names":["The Soul Stone","Peter Parker","Miles Morales","Gwen Stacy","Venom, Deadly Devourer","Spectacular Spider-Man","Spider-Punk"],
 "headline_chases":[
  {"card":"The Soul Stone – main-set version","tier":"MYCKET BRA","odds":"Kan dras non-foil eller traditional foil i Play Boosters; kortspecifikt odds ej publicerat","why":"Infinity Stone-versionen som faktiskt finns i Play Booster-formatet."},
  {"card":"Peter Parker – Borderless Web-Slinger","tier":"MONSTER","odds":"Rare Web-Slinger 1,2% i rare/mythic-platsen; specifikt Peter Parker-odds lägre","why":"Namngiven alternativ behandling av huvudkaraktären."},
  {"card":"Miles Morales – Borderless Scene","tier":"MONSTER","odds":"Scene rare 1% eller mythic <1% i rare/mythic-platsen över familjen","why":"Namngiven scen-chase på en central Spider-Man-karaktär."},
  {"card":"Gwen Stacy – Borderless Scene","tier":"MYCKET BRA","odds":"Scene-familj; specifikt kortodds ej publicerat","why":"Officiellt verifierad Play Booster-träff."},
  {"card":"Spectacular Spider-Man – borderless main-set version","tier":"MYCKET BRA","odds":"Finns non-foil och traditional foil i Play Boosters; specifikt odds ej publicerat","why":"Rätt Play Booster-version av Costume Change-spåret."},
  {"card":"Borderless Source Material – en av 40","tier":"MYCKET BRA","odds":"1:24 Play Boosters för Source Material-familjen","why":"Officiellt publicerad familjefrekvens."}
 ],
 "why_exciting":["Play Boosters har minst en rare/mythic och en traditional foil per paket.","Wizards publicerar slotfördelning och 1:24 för Source Material-familjen."],
 "tiers":{"everyday":{"label":"Full Play Booster-display","score":85,"items":["30 pack","30+ rare/mythic","30 traditional foils"]},"good":{"label":"Bra träff","score":74,"items":["rare/mythic Spider-Man-kort","foil rare eller mythic"]},"big":{"label":"Riktigt bra","score":82,"items":["Source Material","Web-Slinger, Panel eller Scene mythic"]},"jackpot":{"label":"Play Booster-toppträff","score":87,"items":["The Soul Stone premiumutförande","Peter Parker eller Miles Morales Booster Fun"]}},
 "caveat":"Cosmic Foil Soul Stone, Gauntlet Soul Stone, Classic Comic, textured Costume Change och extended-art är Collector Booster-exklusiva. Familjeodds är inte odds för en viss karaktär."
}
CHASE_PROFILES["dl-mtg-spiderman-play-display"] = copy.deepcopy(_spiderman_play_profile)
CHASE_PROFILES["dl-mtg-spiderman-play-pack"] = copy.deepcopy(_spiderman_play_profile)
CHASE_PROFILES["dl-mtg-spiderman-play-pack"]["why_exciting"] = ["Ett engelskt 14-kortspack under 100 kr ger minst en rare/mythic och en foil.","Web-Slinger, Panel, Scene och Source Material kan dras i Play Booster-formatet."]
CHASE_PROFILES["dl-mtg-spiderman-play-pack"]["tiers"]["everyday"] = {"label":"Ett löst Play Booster","score":52,"items":["14 kort","minst 1 rare/mythic","1 traditional foil"]}
CHASE_PROFILES["dl-mtg-spiderman-play-pack"]["caveat"] = "Detta är ett löst Play Booster. 1:24 gäller hela Source Material-familjen; Cosmic Foil-, Gauntlet-, Classic Comic- och textured Costume Change-kort är Collector Booster-exklusiva och kan inte dras."

CHASE_PROFILES["ad-pokemon-abyss-eye-m5-display"] = {
 "source_name":"Pokémon Card Game Japan official Abyss Eye product page and card list",
 "source_url":"https://www.pokemon-card.com/ex/m5/",
 "key_names":["Mega Darkrai ex","Mega Zeraora ex","Mega Chandelure ex SAR","Muku SAR","Malamar","Zarude"],
 "headline_chases":[
  {"card":"Mega Chandelure ex SAR","tier":"JACKPOT","odds":"Officiellt visad SAR; kortspecifikt packodds ej publicerat","why":"En av de två SAR-träffar som lyfts på Pokémons officiella setpresentation."},
  {"card":"Muku SAR","tier":"MONSTER","odds":"Officiellt visad SAR; kortspecifikt packodds ej publicerat","why":"Den andra officiellt namngivna SAR-träffen i setpresentationen."},
  {"card":"Mega Darkrai ex","tier":"MYCKET BRA","odds":"Finns i setet; exakt rarity- och kortspecifikt packodds ej angivet här","why":"Setets huvud-Pokémon och namngivna Mega Evolution ex."},
  {"card":"Mega Zeraora ex","tier":"MYCKET BRA","odds":"Finns i setet; kortspecifikt packodds ej publicerat","why":"Officiellt framlyft Mega Evolution ex i checklistan."}
 ],
 "why_exciting":["30 japanska pack ger många öppningsförsök på setets Mega Evolution- och SAR-spår.","Pokémons officiella presentation bekräftar både namngivna huvudkort och två SAR-kort."],
 "tiers":{"everyday":{"label":"Japansk display","score":78,"items":["30 pack","150 kort"]},"good":{"label":"Bra träff","score":70,"items":["Mega Evolution ex eller illustration rare"]},"big":{"label":"Riktigt bra","score":82,"items":["namngiven hög rarity"]},"jackpot":{"label":"Setets toppspår","score":91,"items":["Mega Chandelure ex SAR eller Muku SAR"]}},
 "caveat":"Pokémon anger 5 slumpmässiga kort per pack men publicerar inga kortspecifika pack- eller boxodds. En hel display garanterar inte ett visst SAR-kort."
}

CHASE_PROFILES["tcgs-pokemon-destined-rivals-pack"] = {
 "source_name":"The Pokémon Company official Scarlet & Violet—Destined Rivals expansion gallery",
 "source_url":"https://tcg.pokemon.com/en-us/expansions/destined-rivals/",
 "key_names":["Team Rocket's Mewtwo ex","Cynthia's Garchomp ex","Ethan's Ho-Oh ex","Team Rocket's Crobat ex"],
 "headline_chases":[
  {"card":"Team Rocket's Mewtwo ex","tier":"JACKPOT","odds":"Finns i det officiella setgalleriet; kortspecifikt packodds ej publicerat","why":"Setets centrala Team Rocket- och Mewtwo-träff."},
  {"card":"Cynthia's Garchomp ex","tier":"MONSTER","odds":"Finns i det officiella setgalleriet; kortspecifikt packodds ej publicerat","why":"Namngiven Champion/Pokémon-kombination."},
  {"card":"Ethan's Ho-Oh ex","tier":"MYCKET BRA","odds":"Finns i det officiella setgalleriet; kortspecifikt packodds ej publicerat","why":"Officiellt namngivet Trainer's Pokémon ex."},
  {"card":"Team Rocket's Crobat ex","tier":"MYCKET BRA","odds":"Finns i det officiella setgalleriet; kortspecifikt packodds ej publicerat","why":"Ytterligare konkret Team Rocket-chase."}
 ],
 "why_exciting":["Stark namngiven checklista med Team Rocket, Mewtwo, Cynthia och Ho-Oh.","Ett engelskt pack ger billigare tillgång till setet än en box men bara ett öppningsförsök."],
 "tiers":{"everyday":{"label":"Ett löst boosterpaket","score":48,"items":["10 kort","1 Basic Energy"]},"good":{"label":"Bra träff","score":65,"items":["Trainer's Pokémon ex eller illustration rare"]},"big":{"label":"Riktigt bra","score":76,"items":["namngiven specialillustration"]},"jackpot":{"label":"Setets toppnamn","score":88,"items":["Team Rocket's Mewtwo ex i hög rarity"]}},
 "caveat":"Detta är ett löst engelskt boosterpaket. Pokémon publicerar inga kortspecifika packodds, och inget namngivet ex- eller specialillustrationskort är garanterat."
}

CHASE_PROFILES["sos-pokemon-journey-together-pack"] = {
 "source_name":"The Pokémon Company official Scarlet & Violet—Journey Together expansion page",
 "source_url":"https://www.pokemon.com/us/pokemon-tcg/scarlet-violet-journey-together",
 "key_names":["N's Zoroark ex","Lillie's Clefairy ex","Iono's Bellibolt ex","Hop's Zacian ex"],
 "headline_chases":[
  {"card":"N's Zoroark ex","tier":"JACKPOT","odds":"Finns i setet; kortspecifikt packodds ej publicerat","why":"Ett av expansionens fyra officiellt framlyfta Trainer's Pokémon ex."},
  {"card":"Lillie's Clefairy ex","tier":"MONSTER","odds":"Finns i setet; kortspecifikt packodds ej publicerat","why":"Namngiven Lillie-chase i Trainer's Pokémon-temat."},
  {"card":"Iono's Bellibolt ex","tier":"MYCKET BRA","odds":"Finns i setet; kortspecifikt packodds ej publicerat","why":"Officiellt framlyft Trainer's Pokémon ex."},
  {"card":"Hop's Zacian ex","tier":"MYCKET BRA","odds":"Finns i setet; kortspecifikt packodds ej publicerat","why":"Officiellt framlyft legendariskt Trainer's Pokémon ex."}
 ],
 "why_exciting":["Över 40 Trainer's Pokémon och över 30 specialillustrationer ger checklistan flera tydliga karaktärsspår.","Priset ligger under 100 kr, men ett löst pack innebär låg hit density."],
 "tiers":{"everyday":{"label":"Ett löst boosterpaket","score":47,"items":["10 kort","1 Basic Energy"]},"good":{"label":"Bra träff","score":64,"items":["Trainer's Pokémon ex eller illustration rare"]},"big":{"label":"Riktigt bra","score":75,"items":["namngiven specialillustration"]},"jackpot":{"label":"Setets toppnamn","score":87,"items":["N eller Lillie i hög rarity"]}},
 "caveat":"Detta är ett löst engelskt boosterpaket. Inga specifika Trainer's Pokémon, specialillustrationer eller ex-kort är garanterade, och officiella kortspecifika packodds saknas."
}

def _loose_pack_profile(base_slug, *, everyday_items, why, caveat):
    """Copy checklist content while replacing display/box opening claims."""
    profile = copy.deepcopy(CHASE_PROFILES[base_slug])
    profile["why_exciting"] = why
    profile["tiers"]["everyday"] = {"label":"Ett löst paket","score":50,"items":everyday_items}
    profile["caveat"] = caveat
    return profile

CHASE_PROFILES["cc-2026-topps-baseball-series2-pack"] = _loose_pack_profile(
    "cc-2026-topps-baseball-series2-hobby",
    everyday_items=["12 kort"],
    why=["Ett 12-kortspack ger en billig chans på Series 2-rookies och inserts.","Checklistans tak finns kvar, men hobbyboxens autograf/relic-löfte gör det inte."],
    caveat="Ett löst pack saknar hobbyboxens autograf-eller-relic-garanti och kan komma från en box där boxhiten redan dragits.",
)
CHASE_PROFILES["cc-star-wars-unlimited-shadows-pack"] = _loose_pack_profile(
    "cc-star-wars-unlimited-shadows-display",
    everyday_items=["1 rare/legendary-plats", "1 foil-plats"],
    why=["Ett pack har en rare/legendary-plats och en foil-plats.","Showcase-ledare kan finnas men är extremt sällsynta."],
    caveat="Detta är ett löst pack, inte en 24-packdisplay. Showcase eller en viss karaktär är inte garanterad.",
)
CHASE_PROFILES["cc-star-wars-unlimited-twilight-pack"] = _loose_pack_profile(
    "cc-star-wars-unlimited-twilight-display",
    everyday_items=["1 rare/legendary-plats", "1 foil-plats"],
    why=["Ett pack ger en liten Clone Wars-öppning med rare/legendary- och foilplats.","Ahsoka, Grievous och Anakin finns i setet men inte som garanti."],
    caveat="Detta är ett löst pack, inte en 24-packdisplay. Showcase eller en viss karaktär är inte garanterad.",
)
CHASE_PROFILES["cc-pokemon-ninja-spinner-m4-pack"] = _loose_pack_profile(
    "cc-pokemon-ninja-spinner-m4-display",
    everyday_items=["5 kort"],
    why=["Ett japanskt femkortspack ger en enstaka chans på Mega Greninja-spåren.","Ingen rarity eller ett visst kort är garanterat."],
    caveat="Detta är ett löst femkortspack, inte en 30-packdisplay. Pokémon publicerar inga kortspecifika pull rates.",
)
CHASE_PROFILES["cc-pokemon-storm-emeralda-m6-pack"] = _loose_pack_profile(
    "cc-pokemon-storm-emeralda-m6-display",
    everyday_items=["5 kort"],
    why=["Ett japanskt femkortspack ger en enstaka chans på Mega Rayquaza-spåren.","Ingen rarity eller ett visst kort är garanterat."],
    caveat="Detta är ett löst femkortspack, inte en 30-packdisplay. Pokémon publicerar inga kortspecifika pull rates.",
)
CHASE_PROFILES["cc-one-piece-op14-jp-pack"] = _loose_pack_profile(
    "cc-one-piece-op14-jp-display",
    everyday_items=["6 japanska kort"],
    why=["Ett japanskt sexkortspack ger en enstaka chans på OP-14:s paralleller.","Boa Hancock, Mihawk och Law finns i setet men är inte garanterade."],
    caveat="Detta är ett löst japanskt pack, inte en 24-packdisplay. Bandai publicerar inte kortspecifika packodds.",
)
CHASE_PROFILES["cc-one-piece-op16-jp-pack"] = _loose_pack_profile(
    "cc-one-piece-op16-jp-display",
    everyday_items=["6 japanska kort"],
    why=["Ett japanskt sexkortspack ger en enstaka chans på OP-16:s paralleller.","Ace, Luffy och Yamato finns i setet men är inte garanterade."],
    caveat="Detta är ett löst japanskt pack, inte en 24-packdisplay. Bandai publicerar inte kortspecifika packodds.",
)

CHASE_PROFILES["kv-one-piece-op10-jp-box"] = {
 "source_name":"Bandai official Royal Blood OP-10 product page and card list",
 "source_url":"https://en.onepiece-cardgame.com/products/boosters/op10.php",
 "key_names":["Trafalgar Law OP10-119","Donquixote Doflamingo","Caesar Clown","Charlotte Pudding","Usopp"],
 "headline_chases":[
  {"card":"Trafalgar Law OP10-119 Secret Rare / parallel","tier":"JACKPOT","odds":"Secret Rare/parallel; Bandai publicerar inte packodds","why":"Officiell OP-10 Secret Rare med ett av seriens starkaste samlarnamn."},
  {"card":"Donquixote Doflamingo Leader parallel","tier":"MONSTER","odds":"Leader parallel; exakt packodds ej publicerat","why":"Royal Blood återvänder till Dressrosa och Donquixote Pirates."},
  {"card":"Charlotte Pudding Special Card","tier":"MYCKET BRA","odds":"Special Card; exakt packodds ej publicerat","why":"Namngiven populär karaktär i setets specialkortsspår."},
  {"card":"Treasure Rare","tier":"MONSTER","odds":"1 Treasure Rare-design finns i setet; packodds ej publicerat","why":"Separat officiell premiumrarity utöver Secret Rares och Special Cards."}
 ],
 "why_exciting":["24 japanska pack ger fler försök än ett löst sexkortspack.","Setet har två Secret Rares, sex Special Cards och en Treasure Rare enligt Bandai."],
 "tiers":{"everyday":{"label":"Japansk display","score":71,"items":["24 pack","144 kort"]},"good":{"label":"Bra träff","score":70,"items":["SR eller parallel"]},"big":{"label":"Riktigt bra","score":82,"items":["Leader parallel eller Special Card"]},"jackpot":{"label":"Setets toppspår","score":91,"items":["Trafalgar Law SEC/parallel eller Treasure Rare"]}},
 "caveat":"Detta är den japanska boxkonfigurationen med 6 kort per pack. Bandai publicerar inte kortspecifika packodds och ingen viss rarity eller karaktär är garanterad."
}
CHASE_PROFILES["kv-one-piece-op10-jp-pack"] = _loose_pack_profile(
    "kv-one-piece-op10-jp-box",
    everyday_items=["6 japanska kort"],
    why=["35 kr ger en billig enstaka chans på Royal Blood-spåren.","Ett löst paket ska inte bedömas som en hel 24-packbox."],
    caveat="Detta är ett löst japanskt sexkortspack. Secret Rare, Treasure Rare, Special Card eller viss karaktär är inte garanterad; Bandai publicerar inte kortspecifika packodds.",
)

CHASE_PROFILES["as-one-piece-op14-en-pack"] = _loose_pack_profile(
    "cc-one-piece-op14-jp-display",
    everyday_items=["12 engelska kort"],
    why=["Det engelska paketet ger 12 kort och kostar från 79 kr hos verifierade svenska butiker.","Mihawk, Crocodile, Boa Hancock och Trafalgar Law är namngivna chase-spår, men ett löst pack ger bara ett försök."],
    caveat="Detta är ett löst engelskt 12-kortspack, inte den japanska 24-packdisplay som basprofilen ursprungligen kartlades från. Ingen viss rarity eller karaktär är garanterad; språkformatens boxkonfiguration får inte blandas och Bandai publicerar inga kortspecifika packodds.",
)

CHASE_PROFILES["aq-one-piece-op15-eb04-en-pack"] = {
 "source_name":"Bandai official Adventure on KAMI's Island OP15-EB04 product page",
 "source_url":"https://en.onepiece-cardgame.com/products/boosters/op15-eb04.php",
 "key_names":["Monkey.D.Luffy Secret Rare","Enel Secret Rare","Enel Super Alternate Art","Krieg","Lucy","Rebecca"],
 "headline_chases":[
  {"card":"Enel Super Alternate Art","tier":"JACKPOT","odds":"Super Alternate Art; Bandai publicerar inte packodds","why":"Bandai pekar uttryckligen ut Enel som släppets Super Alternate Art."},
  {"card":"Monkey.D.Luffy Secret Rare","tier":"MONSTER","odds":"Secret Rare; exakt packodds ej publicerat","why":"Officiellt namngiven Secret Rare och setets mest kända huvudkaraktär."},
  {"card":"Enel Secret Rare","tier":"MONSTER","odds":"Secret Rare; exakt packodds ej publicerat","why":"Skypiea-setets andra officiellt namngivna Secret Rare."},
  {"card":"Alternate-art Event Card","tier":"MYCKET BRA","odds":"Två Event-kort har alternate art; familjeodds ej publicerat","why":"Separat illustrationsspår bekräftat av Bandai."}
 ],
 "why_exciting":["Skypiea-duellen Luffy mot Enel ger checklistan två tydliga Secret Rare-spår.","Enel Super Alternate Art ger ett konkret högt korttak även om sannolikheten är okänd."],
 "tiers":{"everyday":{"label":"Ett löst engelskt pack","score":53,"items":["12 kort"]},"good":{"label":"Bra träff","score":69,"items":["SR eller parallel"]},"big":{"label":"Riktigt bra","score":82,"items":["Luffy/Enel Secret Rare"]},"jackpot":{"label":"Setets toppspår","score":94,"items":["Enel Super Alternate Art"]}},
 "caveat":"Detta är ett löst engelskt 12-kortspack. Ingen Secret Rare, alternate art eller viss karaktär är garanterad och Bandai publicerar inte kortspecifika packodds."
}

CHASE_PROFILES["kl-one-piece-eb03-en-pack"] = {
 "source_name":"Bandai official One Piece Heroines Edition EB-03 product page and card list",
 "source_url":"https://en.onepiece-cardgame.com/products/boosters/eb03.php",
 "key_names":["Nefeltari Vivi","Uta","Nami","Nico Robin","Boa Hancock","Charlotte Linlin"],
 "headline_chases":[
  {"card":"Nefeltari Vivi Leader alternate art","tier":"MONSTER","odds":"Leader alternate art; packodds ej publicerat","why":"Vivi debuterar officiellt som setets nya Leader."},
  {"card":"Heroines SP Card – exempelvis Uta, Nami eller Boa Hancock","tier":"JACKPOT","odds":"9 SP-kort finns; inget familje- eller kortspecifikt packodds publicerat","why":"Bandai bekräftar nio separat designade SP-kort."},
  {"card":"Alternate-art DON!! Card","tier":"MYCKET BRA","odds":"Fyra motiv med alternate-art-versioner; packodds ej publicerat","why":"Officiellt bekräftat specialspår utöver vanliga DON!!-kort."},
  {"card":"Secret Rare heroine","tier":"MONSTER","odds":"Secret Rare finns i raritylistan; exakt kort- och packodds ej publicerat","why":"Setets högsta normala rarity-spår."}
 ],
 "why_exciting":["Fokuserad karaktärschecklista med Vivi, Uta, Nami, Robin och Boa Hancock.","Nio SP-kort och fyra DON!!-motiv med alternate art ger flera premiumspår."],
 "tiers":{"everyday":{"label":"Ett löst engelskt pack","score":52,"items":["12 kort"]},"good":{"label":"Bra träff","score":68,"items":["SR eller alternate-art DON!!"]},"big":{"label":"Riktigt bra","score":81,"items":["Leader alternate art eller Secret Rare"]},"jackpot":{"label":"Setets toppspår","score":92,"items":["Namngiven heroine SP"]}},
 "caveat":"Detta är ett löst engelskt 12-kortspack. Nio SP-kort i checklistan betyder inte att ett SP-kort är garanterat; Bandai publicerar inga kortspecifika packodds."
}

CHASE_PROFILES["bp-one-piece-op17-en-display"] = {
 "source_name":"Bandai official The World's Strongest Warriors OP-17 product page",
 "source_url":"https://en.onepiece-cardgame.com/products/boosters/op17/",
 "key_names":["Monkey.D.Luffy OP17-079 Super Leader Alt-Art","Rocks.D.Xebec OP17-118","Shanks","Kaido","Edward.Newgate","Charlotte Linlin"],
 "headline_chases":[
  {"card":"Monkey.D.Luffy OP17-079 Super Leader Alt-Art","tier":"JACKPOT","odds":"Super Leader Alt-Art; Bandai publicerar inte packodds","why":"Bandai visar Luffys mangaillustrerade premium-Leader som ett centralt toppspår."},
  {"card":"Rocks.D.Xebec OP17-118 high-rarity variant","tier":"MONSTER","odds":"Rarity/parallel varierar; kortspecifikt packodds ej publicerat","why":"Nyckelkaraktär och officiellt namngiven central chase i Rocks Pirates-spåret."},
  {"card":"Four Emperors Special Card – Shanks, Kaido, Edward.Newgate eller Charlotte Linlin","tier":"MONSTER","odds":"Special Card-familj; exakt familje- och kortodds ej publicerat","why":"Fyra officiellt presenterade ikoniska kejsarspår."},
  {"card":"Color of the Supreme King Haki SP","tier":"MYCKET BRA","odds":"Special Card-familj; packodds ej publicerat","why":"Ett separat jubileumsfinish-spår som Bandai lyfter i produktpresentationen."}
 ],
 "why_exciting":["24 engelska 12-kortspack ger 288 kort och fler försök på jubileumsspåren.","Luffy Super Leader Alt-Art, Rocks.D.Xebec och Four Emperors ger checklistan flera namngivna toppteman."],
 "tiers":{"everyday":{"label":"Engelsk display","score":78,"items":["24 pack","288 kort"]},"good":{"label":"Bra träff","score":72,"items":["SR eller parallel"]},"big":{"label":"Riktigt bra","score":86,"items":["Special Card eller hög Rocks-variant"]},"jackpot":{"label":"Setets toppspår","score":97,"items":["Luffy Super Leader Alt-Art"]}},
 "caveat":"Bandai publicerar rarityfamiljer men inga kortspecifika pack- eller boxodds. Displayen garanterar inte Luffy, Rocks.D.Xebec eller en viss Special Card. Priset 4 299 kr är högt och ska inte beskrivas som verifierad ekonomisk avkastning."
}
CHASE_PROFILES["kl-one-piece-op17-en-pack"] = _loose_pack_profile(
    "bp-one-piece-op17-en-display",
    everyday_items=["12 engelska kort"],
    why=["Ett löst pack ger en enstaka chans på OP-17:s jubileums- och alt-artspår.","Det lägre inköpspriset innebär också bara ett öppningsförsök."],
    caveat="Detta är ett löst engelskt 12-kortspack, inte en 24-packdisplay. Ingen Luffy Super Leader Alt-Art, Special Card eller annan rarity är garanterad; Bandai publicerar inte kortspecifika packodds.",
)


CHASE_CARD_DB = [

    # Pitch Kings International Hobby: box guarantees and named La Liga chases.
    dict(slug="cc-2025-26-pitch-kings-la-liga", key="football:2025-26:pitch-kings:93:karl-etta-eyong:blackout", player="Karl Etta Eyong", card="Blackout Rookie", number="3", rookie=True, tier="MONSTER", odds="Ultra-rare; individual odds not published", source="https://www.paniniamerica.net/2025-26-panini-pitch-kings-soccer-trading-card-box-hobby-international"),
    dict(slug="cc-2025-26-pitch-kings-la-liga", key="football:2025-26:pitch-kings:lamine-yamal:le-cinque", player="Lamine Yamal", card="Le Cinque Più Belle", number="1", rookie=False, tier="MONSTER", odds="Ultra-rare; individual odds not published", source="https://www.paniniamerica.net/2025-26-panini-pitch-kings-soccer-trading-card-box-hobby-international"),
    dict(slug="cc-2025-26-pitch-kings-la-liga", key="football:2025-26:pitch-kings:lamine-yamal:fresh-paint-auto", player="Lamine Yamal", card="Fresh Paint Autograph", number="7", rookie=False, tier="JACKPOT", odds="1 autograph per box across autograph program", source="https://www.collectosk.com/2025-26-panini-pitch-kings-laliga-soccer-cards/"),
    dict(slug="cc-2025-26-pitch-kings-la-liga", key="football:2025-26:pitch-kings:kylian-mbappe:legacy-auto", player="Kylian Mbappé", card="Legacy Portrait Signatures", number="9", rookie=False, tier="JACKPOT", odds="1 autograph per box; individual player odds not published", source="https://www.collectosk.com/2025-26-panini-pitch-kings-laliga-soccer-cards/"),

    # Prizm FIFA Choice uses Choice-only parallels and a one-auto box average.
    dict(slug="cc-2025-26-panini-prizm-fifa-choice", key="football:2025-26:prizm-fifa:106:rio-ngumoha:choice", player="Rio Ngumoha", card="Base Choice Parallel", number="106", rookie=True, tier="BRA", odds="3 numbered Choice Prizms per box across checklist", source="https://www.collectosk.com/2025-26-panini-prizm-fifa-soccer-cards/"),
    dict(slug="cc-2025-26-panini-prizm-fifa-choice", key="football:2025-26:prizm-fifa:194:franco-mastantuono:choice", player="Franco Mastantuono", card="Base Choice Parallel", number="194", rookie=True, tier="MYCKET BRA", odds="3 numbered Choice Prizms per box across checklist", source="https://www.collectosk.com/2025-26-panini-prizm-fifa-soccer-cards/"),
    dict(slug="cc-2025-26-panini-prizm-fifa-choice", key="football:2025-26:prizm-fifa:lamine-yamal:sensational-auto", player="Lamine Yamal", card="Sensational Signatures", number="1", rookie=False, tier="MONSTER", odds="1 autograph per Choice box across autograph program", source="https://www.collectosk.com/2025-26-panini-prizm-fifa-soccer-cards/"),
    dict(slug="cc-2025-26-panini-prizm-fifa-choice", key="football:2025-26:prizm-fifa:lionel-messi:club-legend-auto", player="Lionel Messi", card="Club Legend Signatures", number="1", rookie=False, tier="JACKPOT", odds="1 autograph per Choice box; individual player odds not published", source="https://www.collectosk.com/2025-26-panini-prizm-fifa-soccer-cards/"),

    # Prizm FIFA retail: retail box odds stay separate from Choice and Hobby.
    dict(slug="cc-2025-26-panini-prizm-fifa-retail", key="football:2025-26:prizm-fifa:106:rio-ngumoha:base", player="Rio Ngumoha", card="Base", number="106", rookie=True, tier="BRA", odds="24 retail packs per box; individual card odds not published", source="https://www.collectosk.com/2025-26-panini-prizm-fifa-soccer-cards/"),
    dict(slug="cc-2025-26-panini-prizm-fifa-retail", key="football:2025-26:prizm-fifa:194:franco-mastantuono:base", player="Franco Mastantuono", card="Base", number="194", rookie=True, tier="BRA", odds="24 retail packs per box; individual card odds not published", source="https://www.collectosk.com/2025-26-panini-prizm-fifa-soccer-cards/"),
    dict(slug="cc-2025-26-panini-prizm-fifa-retail", key="football:2025-26:prizm-fifa:lamine-yamal:red-pulsar-auto", player="Lamine Yamal", card="Red Pulsar Autograph", number="1", rookie=False, tier="MONSTER", odds="Red Pulsar Autograph family 1:2 retail boxes; exact player is rarer", source="https://www.collectosk.com/2025-26-panini-prizm-fifa-soccer-cards/"),
    dict(slug="cc-2025-26-panini-prizm-fifa-retail", key="football:2025-26:prizm-fifa:lionel-messi:manga", player="Lionel Messi", card="Manga", number="19", rookie=False, tier="JACKPOT", odds="SSP; exact retail odds not published", source="https://www.collectosk.com/2025-26-panini-prizm-fifa-soccer-cards/"),

    # Futera FX Series 3 official checklist: serials are stated, box odds are not.
    dict(slug="cc-2026-futera-world-football-fx3", key="football:2026:futera-fx3:160:lamine-yamal:base-diamond", player="Lamine Yamal", card="Portrait Base Diamond", number="FXB160", rookie=False, tier="MONSTER", odds="1/1", source="https://www.futera.com/checklists"),
    dict(slug="cc-2026-futera-world-football-fx3", key="football:2026:futera-fx3:lionel-messi:modern-auto", player="Lionel Messi", card="Modern On-Card Autograph", number="MDA19", rookie=False, tier="JACKPOT", odds="Main hit is autograph, memorabilia or numbered rare insert; exact odds not published", source="https://www.futera.com/checklists"),
    dict(slug="cc-2026-futera-world-football-fx3", key="football:2026:futera-fx3:messi-ronaldo:versus-memorabilia", player="Lionel Messi / Cristiano Ronaldo", card="Versus Dual Memorabilia", number="VS11", rookie=False, tier="JACKPOT", odds="Numbered memorabilia; exact print run and box odds not published", source="https://www.futera.com/checklists"),
    dict(slug="cc-2026-futera-world-football-fx3", key="football:2026:futera-fx3:lamine-yamal:unique-auto", player="Lamine Yamal", card="Unique On-Card Autograph", number="OFOA01", rookie=False, tier="JACKPOT", odds="1/1", source="https://www.futera.com/checklists"),

    # Bayern Lineage rookies and named on-card/triple autograph programs.
    dict(slug="cc-2025-26-topps-bayern-lineage", key="football:2025-26:bayern-lineage:17:lennart-karl:base-rookie", player="Lennart Karl", card="Base Rookie", number="17", rookie=True, tier="BRA", odds="Part of 45-card base set; individual odds not published", source="https://uk.topps.com/pages/topps-lineage-fc-bayern-munchen"),
    dict(slug="cc-2025-26-topps-bayern-lineage", key="football:2025-26:bayern-lineage:lennart-karl:icons-auto", player="Lennart Karl", card="Icons On-Card Autograph", number="IA-LK", rookie=True, tier="MONSTER", odds="3 encased premium hits per box; exact player not guaranteed", source="https://uk.topps.com/pages/topps-lineage-fc-bayern-munchen"),
    dict(slug="cc-2025-26-topps-bayern-lineage", key="football:2025-26:bayern-lineage:harry-kane:meister-auto", player="Harry Kane", card="Meister Kane On-Card Autograph", number="MKA-HK", rookie=False, tier="JACKPOT", odds="Individual odds not published", source="https://uk.topps.com/pages/topps-lineage-fc-bayern-munchen"),
    dict(slug="cc-2025-26-topps-bayern-lineage", key="football:2025-26:bayern-lineage:thomas-muller:es-muellert-auto", player="Thomas Müller", card="Es Müllert On-Card Autograph", number="EMA-TM", rookie=False, tier="JACKPOT", odds="Individual odds not published", source="https://uk.topps.com/pages/topps-lineage-fc-bayern-munchen"),

    # 2026 MLS Chrome Value Box: only value-format odds are used.
    dict(slug="cc-2026-topps-mls-chrome-value", key="football:2026:mls-chrome:zavier-gozo:wonderkids-25", player="Zavier Gozo", card="Wonderkids", number="WK-25", rookie=False, tier="BRA", odds="Wonderkids 1:6 value packs; exact player is rarer", source="https://www.topps.com/pages/topps-mls-chrome"),
    dict(slug="cc-2026-topps-mls-chrome-value", key="football:2026:mls-chrome:lionel-messi:pearlers-10", player="Lionel Messi", card="Pearlers", number="P-10", rookie=False, tier="MYCKET BRA", odds="Pearlers 1:2,622 value packs; exact player is rarer", source="https://www.topps.com/pages/topps-mls-chrome"),
    dict(slug="cc-2026-topps-mls-chrome-value", key="football:2026:mls-chrome:lionel-messi:chrome-auto", player="Lionel Messi", card="Chrome Autograph", number="CA-LM", rookie=False, tier="MONSTER", odds="Chrome Autographs Base 1:342 value packs; exact player is rarer", source="https://www.topps.com/pages/topps-mls-chrome"),
    dict(slug="cc-2026-topps-mls-chrome-value", key="football:2026:mls-chrome:messi-beckham:dual-auto", player="Lionel Messi / David Beckham", card="Chrome Dual Autograph", number=None, rookie=False, tier="JACKPOT", odds="Chrome Dual Autographs 1:21,630 value packs; exact card is rarer", source="https://www.topps.com/pages/topps-mls-chrome"),

    # 2026 Chrome Premier League Hobby rookies, autos and case hits.
    dict(slug="cc-2026-topps-chrome-premier-league-hobby", key="football:2026:pl-chrome:68:estevao-willian:base-rookie", player="Estêvão Willian", card="Base Rookie", number="68", rookie=True, tier="BRA", odds="Part of 200-card base set; individual card odds not published", source="https://www.topps.com/pages/topps-chrome-premier-league"),
    dict(slug="cc-2026-topps-chrome-premier-league-hobby", key="football:2026:pl-chrome:112:rio-ngumoha:base-rookie", player="Rio Ngumoha", card="Base Rookie", number="112", rookie=True, tier="BRA", odds="Part of 200-card base set; individual card odds not published", source="https://www.topps.com/pages/topps-chrome-premier-league"),
    dict(slug="cc-2026-topps-chrome-premier-league-hobby", key="football:2026:pl-chrome:201:max-dowman:hobby-base-rookie", player="Max Dowman", card="Hobby-Exclusive Base Rookie", number="201", rookie=True, tier="MONSTER", odds="1:16,257 hobby packs", source="https://www.topps.com/pages/topps-chrome-premier-league"),
    dict(slug="cc-2026-topps-chrome-premier-league-hobby", key="football:2026:pl-chrome:estevao-willian:chrome-auto", player="Estêvão Willian", card="Chrome Autograph", number="CA-EV", rookie=True, tier="MYCKET BRA", odds="1 autograph per hobby box across autograph program; exact player is rarer", source="https://www.topps.com/pages/topps-chrome-premier-league"),

    # 2026 Finest Premier League: two autos per box, but no player guarantee.
    dict(slug="cc-2026-topps-finest-premier-league-wave2", key="football:2026:pl-finest:estevao-willian:finest-auto", player="Estêvão Willian", card="Finest Autograph", number="FA-EW", rookie=True, tier="MYCKET BRA", odds="2 Chrome Autographs per box across autograph program", source="https://www.topps.com/pages/topps-finest-premier-league"),
    dict(slug="cc-2026-topps-finest-premier-league-wave2", key="football:2026:pl-finest:max-dowman:arrivals-auto", player="Max Dowman", card="Arrivals Autograph", number="AA-MD", rookie=True, tier="MONSTER", odds="2 Chrome Autographs per box across autograph program", source="https://www.topps.com/pages/topps-finest-premier-league"),
    dict(slug="cc-2026-topps-finest-premier-league-wave2", key="football:2026:pl-finest:max-dowman:polka-15", player="Max Dowman", card="Polka", number="PK-15", rookie=True, tier="MONSTER", odds="Polka 1:437 packs; exact player is rarer", source="https://www.topps.com/pages/topps-finest-premier-league"),

    # Arsenal Chrome exact rookies, legends and one-of-one autograph chase.
    dict(slug="cc-2025-26-topps-chrome-arsenal-hobby", key="football:2025-26:arsenal-chrome:49:max-dowman:base-rookie", player="Max Dowman", card="Base Rookie", number="49", rookie=True, tier="BRA", odds="Part of 100-card base set; individual card odds not published", source="https://uk.topps.com/pages/topps-chrome-arsenal"),
    dict(slug="cc-2025-26-topps-chrome-arsenal-hobby", key="football:2025-26:arsenal-chrome:max-dowman:base-auto", player="Max Dowman", card="Base Card Autograph", number="BC-MD", rookie=True, tier="MYCKET BRA", odds="2 autographs per box across autograph program", source="https://uk.topps.com/pages/topps-chrome-arsenal"),
    dict(slug="cc-2025-26-topps-chrome-arsenal-hobby", key="football:2025-26:arsenal-chrome:thierry-henry:228-and-out-auto", player="Thierry Henry", card="228 & Out Autograph", number="BB-TH", rookie=False, tier="JACKPOT", odds="Individual odds not published", source="https://uk.topps.com/pages/topps-chrome-arsenal"),
    dict(slug="cc-2025-26-topps-chrome-arsenal-hobby", key="football:2025-26:arsenal-chrome:bukayo-saka:away-auto", player="Bukayo Saka", card="The Arsenal Away Autograph", number="AW-BS", rookie=False, tier="JACKPOT", odds="1/1", source="https://uk.topps.com/pages/topps-chrome-arsenal"),

    # Argentina Team Set exact youth and Messi autograph paths.
    dict(slug="cc-2026-topps-argentina-team-set", key="football:2026:argentina-team-set:8:franco-mastantuono:base", player="Franco Mastantuono", card="First Team Base", number="8", rookie=False, tier="BRA", odds="Part of 50-card base set; individual card odds not published", source="https://es.topps.com/pages/argentina-team-set"),
    dict(slug="cc-2026-topps-argentina-team-set", key="football:2026:argentina-team-set:franco-mastantuono:base-auto", player="Franco Mastantuono", card="First Team Base Autograph", number="BC-FM", rookie=False, tier="MONSTER", odds="1 autograph every 2 boxes across autograph program", source="https://es.topps.com/pages/argentina-team-set"),
    dict(slug="cc-2026-topps-argentina-team-set", key="football:2026:argentina-team-set:lionel-messi:vis10nary-auto", player="Lionel Messi", card="Vis10nary Autograph", number="VI-LM", rookie=False, tier="JACKPOT", odds="Ultra-rare; exact odds not published", source="https://es.topps.com/pages/argentina-team-set"),

    # Real Madrid Team Set exact rookie, star and autograph chases.
    dict(slug="cc-2025-26-topps-real-madrid-team-set", key="football:2025-26:real-madrid-team-set:14:franco-mastantuono:base-rookie", player="Franco Mastantuono", card="First Team Base Rookie", number="14", rookie=True, tier="BRA", odds="Part of 50-card base set; individual card odds not published", source="https://uk.topps.com/pages/topps-real-madrid-2025-26-team-set"),
    dict(slug="cc-2025-26-topps-real-madrid-team-set", key="football:2025-26:real-madrid-team-set:franco-mastantuono:base-auto", player="Franco Mastantuono", card="Base Card Autograph", number="BC-MA", rookie=True, tier="MONSTER", odds="1 autograph every 2 boxes across autograph program", source="https://uk.topps.com/pages/topps-real-madrid-2025-26-team-set"),
    dict(slug="cc-2025-26-topps-real-madrid-team-set", key="football:2025-26:real-madrid-team-set:jude-bellingham:base-auto", player="Jude Bellingham", card="Base Card Autograph", number="BC-JB", rookie=False, tier="MONSTER", odds="1 autograph every 2 boxes across autograph program", source="https://uk.topps.com/pages/topps-real-madrid-2025-26-team-set"),
    dict(slug="cc-2025-26-topps-real-madrid-team-set", key="football:2025-26:real-madrid-team-set:vini-jr:bona-fide-auto", player="Vini Jr.", card="Bona Fide Baller Autograph", number="BB-VJ", rookie=False, tier="JACKPOT", odds="1 autograph every 2 boxes across autograph program", source="https://uk.topps.com/pages/topps-real-madrid-2025-26-team-set"),

    # UCC hanger: explicit Hanger-column odds only.
    dict(slug="cc-2025-26-topps-ucc-flagship-hanger", key="football:2025-26:ucc-flagship:66:estevao-willian:base-rookie", player="Estêvão Willian", card="Base Rookie", number="66", rookie=True, tier="BRA", odds="Part of 200-card base set; individual card odds not published", source="https://www.topps.com/pages/uefa-club-competitions"),
    dict(slug="cc-2025-26-topps-ucc-flagship-hanger", key="football:2025-26:ucc-flagship:172:franco-mastantuono:base-rookie", player="Franco Mastantuono", card="Base Rookie", number="172", rookie=True, tier="BRA", odds="Part of 200-card base set; individual card odds not published", source="https://www.topps.com/pages/uefa-club-competitions"),
    dict(slug="cc-2025-26-topps-ucc-flagship-hanger", key="football:2025-26:ucc-flagship:estevao-willian:base-auto", player="Estêvão Willian", card="Base Card Autograph", number="BA-EW", rookie=True, tier="MONSTER", odds="Base Autos 1:112 hanger packs; exact player is rarer", source="https://www.topps.com/pages/uefa-club-competitions"),
    dict(slug="cc-2025-26-topps-ucc-flagship-hanger", key="football:2025-26:ucc-flagship:rio-ngumoha:base-auto", player="Rio Ngumoha", card="Base Card Autograph", number="BA-RN", rookie=True, tier="MONSTER", odds="Base Autos 1:112 hanger packs; exact player is rarer", source="https://www.topps.com/pages/uefa-club-competitions"),

    # Parkhurst loose pack: exact rookies plus one low-numbered autograph patch.
    dict(slug="cc-pack-2025-26-parkhurst-hobby", key="hockey:2025-26:parkhurst:236:ivan-demidov:base-rookie", player="Ivan Demidov", card="Base Rookie", number="236", rookie=True, tier="BRA", odds="Base rookies 1 per hobby pack on average", source="https://upperdeck.com/checklist/2025-26-parkhurst-checklist/"),
    dict(slug="cc-pack-2025-26-parkhurst-hobby", key="hockey:2025-26:parkhurst:211:matthew-schaefer:base-rookie", player="Matthew Schaefer", card="Base Rookie", number="211", rookie=True, tier="BRA", odds="Base rookies 1 per hobby pack on average", source="https://upperdeck.com/checklist/2025-26-parkhurst-checklist/"),
    dict(slug="cc-pack-2025-26-parkhurst-hobby", key="hockey:2025-26:parkhurst:236:ivan-demidov:auto-patch", player="Ivan Demidov", card="Rookie Auto Patch", number="236", rookie=True, tier="JACKPOT", odds="Serial /25; individual pack odds not published", source="https://upperdeck.com/checklist/2025-26-parkhurst-checklist/"),

    # PWHL retail uses format-specific blaster odds.
    dict(slug="cc-2025-26-pwhl-retail-blaster", key="hockey:2025-26:pwhl:51:kristyna-kaltounkova:young-guns", player="Kristyna Kaltounkova", card="Young Guns", number="51", rookie=True, tier="BRA", odds="Young Guns 1:3 blaster packs", source="https://upperdeck.com/checklist/2025-26-ud-pwhl-checklist/"),
    dict(slug="cc-2025-26-pwhl-retail-blaster", key="hockey:2025-26:pwhl:57:casey-obrien:young-guns", player="Casey O'Brien", card="Young Guns", number="57", rookie=True, tier="BRA", odds="Young Guns 1:3 blaster packs", source="https://upperdeck.com/checklist/2025-26-ud-pwhl-checklist/"),
    dict(slug="cc-2025-26-pwhl-retail-blaster", key="hockey:2025-26:pwhl:58:kiara-zanon:young-guns", player="Kiara Zanon", card="Young Guns", number="58", rookie=True, tier="BRA", odds="Young Guns 1:3 blaster packs", source="https://upperdeck.com/checklist/2025-26-ud-pwhl-checklist/"),

    # Fleer Ultra PWHL exact autograph and serial-number chases.
    dict(slug="cc-2025-26-fleer-ultra-pwhl-hobby", key="hockey:2025-26:fleer-ultra-pwhl:casey-obrien:rising-stars-black", player="Casey O'Brien", card="Rising Stars Black", number=None, rookie=True, tier="JACKPOT", odds="1/1", source="https://upperdeck.com/checklist/2025-26-fleer-ultra-pwhl-checklist/"),
    dict(slug="cc-2025-26-fleer-ultra-pwhl-hobby", key="hockey:2025-26:fleer-ultra-pwhl:natalie-spooner:fresh-ink", player="Natalie Spooner", card="Fresh Ink Autograph SP", number=None, rookie=False, tier="MYCKET BRA", odds="Fresh Ink family 1:150 hobby/e-Pack", source="https://upperdeck.com/checklist/2025-26-fleer-ultra-pwhl-checklist/"),

    # SP Authentic Future Watch and Sign of the Times rookie autographs.
    dict(slug="cc-2025-26-sp-authentic-hobby", key="hockey:2025-26:sp-authentic:149:ivan-demidov:future-watch-auto", player="Ivan Demidov", card="Future Watch Autograph /999", number="149", rookie=True, tier="MYCKET BRA", odds="At least 1 Future Watch Autograph per box on average", source="https://upperdeck.com/checklist/2025-26-sp-authentic-checklist/"),
    dict(slug="cc-2025-26-sp-authentic-hobby", key="hockey:2025-26:sp-authentic:168:matthew-schaefer:future-watch-auto", player="Matthew Schaefer", card="Future Watch Autograph /999", number="168", rookie=True, tier="MYCKET BRA", odds="At least 1 Future Watch Autograph per box on average", source="https://upperdeck.com/checklist/2025-26-sp-authentic-checklist/"),
    dict(slug="cc-2025-26-sp-authentic-hobby", key="hockey:2025-26:sp-authentic:matthew-schaefer:sign-of-the-times-black", player="Matthew Schaefer", card="Sign of the Times Rookies Black /25", number=None, rookie=True, tier="MONSTER", odds="Serial /25", source="https://upperdeck.com/checklist/2025-26-sp-authentic-checklist/"),
    dict(slug="cc-2025-26-sp-authentic-hobby", key="hockey:2025-26:sp-authentic:168:matthew-schaefer:fwa-patch-black", player="Matthew Schaefer", card="Future Watch Auto Patch Black", number="168", rookie=True, tier="JACKPOT", odds="1/1", source="https://upperdeck.com/checklist/2025-26-sp-authentic-checklist/"),

    # Ultimate Collection exact low-numbered rookie autographs.
    dict(slug="cc-2025-26-ultimate-hobby", key="hockey:2025-26:ultimate:matthew-schaefer:phenoms-gold-auto", player="Matthew Schaefer", card="Ultimate Phenoms Gold Autograph", number=None, rookie=True, tier="MONSTER", odds="Serial /25", source="https://upperdeck.com/checklist/2025-26-nhl-ultimate-collection-checklist/"),
    dict(slug="cc-2025-26-ultimate-hobby", key="hockey:2025-26:ultimate:matthew-schaefer:phenoms-purple-auto", player="Matthew Schaefer", card="Ultimate Phenoms Purple Autograph", number=None, rookie=True, tier="JACKPOT", odds="Serial /5", source="https://upperdeck.com/checklist/2025-26-nhl-ultimate-collection-checklist/"),
    dict(slug="cc-2025-26-ultimate-hobby", key="hockey:2025-26:ultimate:michael-misa:phenoms-black-auto", player="Michael Misa", card="Ultimate Phenoms Black Autograph", number=None, rookie=True, tier="JACKPOT", odds="1/1", source="https://upperdeck.com/checklist/2025-26-nhl-ultimate-collection-checklist/"),

    # Premier exact acetate rookie auto patches and premium Schaefer memorabilia.
    dict(slug="cc-2025-26-premier-hobby", key="hockey:2025-26:premier:ivan-demidov:acetate-rpa", player="Ivan Demidov", card="Acetate Rookie Patch Autograph", number=None, rookie=True, tier="MONSTER", odds="Serial /99", source="https://upperdeck.com/checklist/2025-26-premier-checklist/"),
    dict(slug="cc-2025-26-premier-hobby", key="hockey:2025-26:premier:matthew-schaefer:viewpoints-auto-patch-gold", player="Matthew Schaefer", card="Viewpoints Auto Patch Gold", number=None, rookie=True, tier="JACKPOT", odds="Serial /5", source="https://upperdeck.com/checklist/2025-26-premier-checklist/"),
    dict(slug="cc-2025-26-premier-hobby", key="hockey:2025-26:premier:michael-misa:acetate-rpa-platinum", player="Michael Misa", card="Acetate Rookie Patch Autograph Platinum", number=None, rookie=True, tier="JACKPOT", odds="1/1", source="https://upperdeck.com/checklist/2025-26-premier-checklist/"),

    # Rangers Centennial guaranteed inserts and autograph family odds.
    dict(slug="cc-2025-26-rangers-box-set", key="hockey:2025-26:rangers-centennial:wayne-gretzky:blueshirt-best", player="Wayne Gretzky", card="Blueshirt Best", number=None, rookie=False, tier="MYCKET BRA", odds="1 Blueshirt Best per box; exact player varies", source="https://upperdeck.com/checklist/2025-26-nhl-new-york-rangers-centennial-checklist/"),
    dict(slug="cc-2025-26-rangers-box-set", key="hockey:2025-26:rangers-centennial:henrik-lundqvist:auto-parallel", player="Henrik Lundqvist", card="Autograph Parallel SSP", number=None, rookie=False, tier="MONSTER", odds="Autograph Parallel family 1:10 boxes; Lundqvist is SSP", source="https://upperdeck.com/checklist/2025-26-nhl-new-york-rangers-centennial-checklist/"),
    dict(slug="cc-2025-26-rangers-box-set", key="hockey:2025-26:rangers-centennial:mark-messier:auto-parallel", player="Mark Messier", card="Autograph Parallel SSP", number=None, rookie=False, tier="JACKPOT", odds="Autograph Parallel family 1:10 boxes; Messier is SSP", source="https://upperdeck.com/checklist/2025-26-nhl-new-york-rangers-centennial-checklist/"),

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

    # Pokémon: exact checklist cards; the manufacturer does not publish pack odds.
    dict(slug="cc-pokemon-paradox-rift-18", key="pokemon:paradox-rift:251:roaring-moon-ex:sir", player="Roaring Moon ex", card="Special Illustration Rare", number="251", rookie=False, tier="JACKPOT", odds="Official pack odds not published", source="https://assets.pokemon.com/assets/cms2/pdf/trading-card-game/checklist/par_web_cardlist_en.pdf"),
    dict(slug="cc-pokemon-paradox-rift-18", key="pokemon:paradox-rift:249:iron-valiant-ex:sir", player="Iron Valiant ex", card="Special Illustration Rare", number="249", rookie=False, tier="MONSTER", odds="Official pack odds not published", source="https://assets.pokemon.com/assets/cms2/pdf/trading-card-game/checklist/par_web_cardlist_en.pdf"),
    dict(slug="cc-pokemon-paradox-rift-18", key="pokemon:paradox-rift:199:groudon:ir", player="Groudon", card="Illustration Rare", number="199", rookie=False, tier="BRA", odds="Official pack odds not published", source="https://assets.pokemon.com/assets/cms2/pdf/trading-card-game/checklist/par_web_cardlist_en.pdf"),
    dict(slug="cc-pokemon-temporal-forces-18", key="pokemon:temporal-forces:208:raging-bolt-ex:sir", player="Raging Bolt ex", card="Special Illustration Rare", number="208", rookie=False, tier="JACKPOT", odds="Official pack odds not published", source="https://www.pokemon.com/us/pokemon-tcg/pokemon-cards/series/sv05/"),
    dict(slug="cc-pokemon-temporal-forces-18", key="pokemon:temporal-forces:206:iron-crown-ex:sir", player="Iron Crown ex", card="Special Illustration Rare", number="206", rookie=False, tier="MONSTER", odds="Official pack odds not published", source="https://www.pokemon.com/us/pokemon-tcg/pokemon-cards/series/sv05/"),
    dict(slug="cc-pokemon-temporal-forces-18", key="pokemon:temporal-forces:211:mortys-conviction:sir", player="Morty's Conviction", card="Special Illustration Rare", number="211", rookie=False, tier="MONSTER", odds="Official pack odds not published", source="https://www.pokemon.com/us/pokemon-tcg/pokemon-cards/series/sv05/"),
    dict(slug="cc-pokemon-shrouded-fable-kingambit", key="pokemon:shrouded-fable:94:cassiopeia:sir", player="Cassiopeia", card="Special Illustration Rare", number="94", rookie=False, tier="JACKPOT", odds="Official pack odds not published", source="https://www.pokemon.com/us/pokemon-tcg/scarlet-violet-shrouded-fable"),
    dict(slug="cc-pokemon-shrouded-fable-kingambit", key="pokemon:shrouded-fable:92:fezandipiti-ex:sir", player="Fezandipiti ex", card="Special Illustration Rare", number="92", rookie=False, tier="MONSTER", odds="Official pack odds not published", source="https://www.pokemon.com/us/pokemon-tcg/scarlet-violet-shrouded-fable"),
    dict(slug="cc-pokemon-shrouded-fable-kingambit", key="pokemon:shrouded-fable:78:persian:ir", player="Persian", card="Illustration Rare", number="78", rookie=False, tier="BRA", odds="Official pack odds not published", source="https://www.pokemon.com/us/pokemon-tcg/scarlet-violet-shrouded-fable"),
    dict(slug="cc-pokemon-go-etb", key="pokemon:pokemon-go:86:mewtwo-vstar:gold", player="Mewtwo VSTAR", card="Gold Rare", number="86", rookie=False, tier="JACKPOT", odds="Official pack odds not published", source="https://assets.pokemon.com/assets/cms2/pdf/trading-card-game/checklist/pgo_web_cardlist_en.pdf"),
    dict(slug="cc-pokemon-go-etb", key="pokemon:pokemon-go:11:radiant-charizard", player="Radiant Charizard", card="Radiant Rare", number="11", rookie=False, tier="BRA", odds="Official pack odds not published", source="https://assets.pokemon.com/assets/cms2/pdf/trading-card-game/checklist/pgo_web_cardlist_en.pdf"),
    dict(slug="cc-pokemon-white-flare-jp-display", key="pokemon:white-flare:174:reshiram-ex:bwr", player="Reshiram ex", card="Black White Rare", number="174/086", rookie=False, tier="JACKPOT", odds="Official pack odds not published", source="https://asia.pokemon-card.com/card-search/list/?expansionCodes=SV11W"),
    dict(slug="cc-pokemon-white-flare-jp-display", key="pokemon:white-flare:173:hilda:sar", player="Hilda", card="Special Art Rare", number="173/086", rookie=False, tier="MONSTER", odds="Official pack odds not published", source="https://asia.pokemon-card.com/card-search/list/?expansionCodes=SV11W"),

    # One Piece OP-13: Bandai verifies the special cards but publishes no numeric pull rates.
    dict(slug="cc-one-piece-op13-jp-display", key="one-piece:op13:op09-118:gol-d-roger:wanted", player="Gol.D.Roger", card="WANTED Edition", number="OP09-118", rookie=False, tier="JACKPOT", odds="Official pack odds not published", source="https://en.onepiece-cardgame.com/products/boosters/op13/"),
    dict(slug="cc-one-piece-op13-jp-display", key="one-piece:op13:118:monkey-d-luffy:wanted", player="Monkey.D.Luffy", card="WANTED Edition", number="OP13-118", rookie=False, tier="MONSTER", odds="Official pack odds not published", source="https://en.onepiece-cardgame.com/products/boosters/op13/"),
    dict(slug="cc-one-piece-op13-jp-display", key="one-piece:op13:119:portgas-d-ace:wanted", player="Portgas.D.Ace", card="WANTED Edition", number="OP13-119", rookie=False, tier="MONSTER", odds="Official pack odds not published", source="https://en.onepiece-cardgame.com/products/boosters/op13/"),
    dict(slug="cc-one-piece-op13-jp-display", key="one-piece:op13:120:sabo:wanted", player="Sabo", card="WANTED Edition", number="OP13-120", rookie=False, tier="MONSTER", odds="Official pack odds not published", source="https://en.onepiece-cardgame.com/products/boosters/op13/"),

    # Marvel Studios Chrome: all odds are the official Hobby column, never Value/Breaker odds.
    dict(slug="cc-2025-topps-marvel-studios-chrome-hobby", key="marvel:2025:studios-chrome:hugh-jackman:single-auto", player="Hugh Jackman", card="Wolverine Single Autograph", number="AA-HJ", rookie=False, tier="MONSTER", odds="Single Autos 1:25 hobby packs across checklist", source="https://www.topps.com/pages/topps-marvel-studios-chrome"),
    dict(slug="cc-2025-topps-marvel-studios-chrome-hobby", key="marvel:2025:studios-chrome:ryan-reynolds:single-auto", player="Ryan Reynolds", card="Deadpool Single Autograph", number="AA-RR", rookie=False, tier="MONSTER", odds="Single Autos 1:25 hobby packs across checklist", source="https://www.topps.com/pages/topps-marvel-studios-chrome"),
    dict(slug="cc-2025-topps-marvel-studios-chrome-hobby", key="marvel:2025:studios-chrome:jackman-reynolds:dual-auto", player="Hugh Jackman / Ryan Reynolds", card="Wolverine / Deadpool Dual Autograph", number="DA-JR", rookie=False, tier="JACKPOT", odds="Dual Autos 1:3,305 hobby packs across checklist", source="https://www.topps.com/pages/topps-marvel-studios-chrome"),
    dict(slug="cc-2025-topps-marvel-studios-chrome-hobby", key="marvel:2025:studios-chrome:pedro-pascal:single-auto", player="Pedro Pascal", card="Mister Fantastic Single Autograph", number="AA-PP", rookie=False, tier="MONSTER", odds="Single Autos 1:25 hobby packs across checklist", source="https://www.topps.com/pages/topps-marvel-studios-chrome"),

    # Disney Chrome Value Box: official Value Box odds and authentic/facsimile separation.
    dict(slug="cc-2026-topps-disney-chrome-value", key="disney:2026:chrome:miley-cyrus:hannah-montana-auto", player="Miley Cyrus", card="Hannah Montana Authentic Autograph", number="DCA-MC", rookie=False, tier="JACKPOT", odds="Authentic Autographs 1:2,261 value packs across checklist", source="https://www.topps.com/pages/topps-chrome-disney"),
    dict(slug="cc-2026-topps-disney-chrome-value", key="disney:2026:chrome:owen-wilson:lightning-mcqueen-auto", player="Owen Wilson", card="Lightning McQueen Authentic Autograph", number="AA-OW", rookie=False, tier="JACKPOT", odds="Authentic Autographs 1:2,261 value packs across checklist", source="https://www.topps.com/pages/topps-chrome-disney"),
    dict(slug="cc-2026-topps-disney-chrome-value", key="disney:2026:chrome:jodi-benson:ariel-auto", player="Jodi Benson", card="Ariel Princess Autograph", number="PA-JB", rookie=False, tier="JACKPOT", odds="Authentic Autographs 1:2,261 value packs across checklist", source="https://www.topps.com/pages/topps-chrome-disney"),
    dict(slug="cc-2026-topps-disney-chrome-value", key="disney:2026:chrome:mickey-minnie-goofy-pluto:quad-facsimile", player="Mickey Mouse / Minnie Mouse / Goofy / Pluto", card="Quad Facsimile Autograph (printed)", number="QD-1", rookie=False, tier="MYCKET BRA", odds="Quad Facsimile Autographs 1:115,840 value packs", source="https://www.topps.com/pages/topps-chrome-disney"),
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
        research_slugs={x["slug"] for x in REAL_RESEARCH_EXPANSION}
        store_expansion_slugs={x["slug"] for x in REAL_STORE_EXPANSION}
        retailer_expansion_slugs={x["slug"] for x in RETAILER_EXPANSION}
        additional_store_slugs={x["slug"] for x in ADDITIONAL_STORE_EXPANSION}
        one_piece_market_slugs={x["slug"] for x in ONE_PIECE_MARKET_EXPANSION}
        tcg_market_slugs={x["slug"] for x in TCG_MARKET_EXPANSION}
        expansion_slugs={x["slug"] for x in REAL_NONSPORT_EXPANSION + REAL_CROSS_CATEGORY_EXPANSION}
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
            row.verified_at=(
                TCG_MARKET_OBSERVED_AT if slug in tcg_market_slugs
                else ONE_PIECE_MARKET_OBSERVED_AT if slug in one_piece_market_slugs
                else ADDITIONAL_STORE_OBSERVED_AT if slug in additional_store_slugs
                else RETAILER_EXPANSION_OBSERVED_AT if slug in retailer_expansion_slugs
                else REAL_STORE_EXPANSION_OBSERVED_AT if slug in store_expansion_slugs
                else REAL_RESEARCH_OBSERVED_AT if slug in research_slugs
                else REAL_EXPANSION_OBSERVED_AT if slug in expansion_slugs
                else REAL_SNAPSHOT_OBSERVED_AT
            )
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
