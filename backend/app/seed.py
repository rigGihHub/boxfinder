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
    dict(name="ManaTorsk", homepage_url=None, source_url=None, collection_method="manual", adapter