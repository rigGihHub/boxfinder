SOURCE_PROFILES = {
    "Terratide": {"priority":1,"coverage":["Pokémon","Magic","Fotboll","Lorcana","Digimon","One Piece","Yu-Gi-Oh!","Star Wars Unlimited","Altered"],"strength":"Mycket bred sealed-katalog med tydliga priser och lagersaldon","recommended_ingest":"Kartlägg feed/API; publik HTML först efter uttrycklig policygranskning"},
    "TCG Deals Sverige": {"priority":2,"coverage":["Pokémon","One Piece","Dragon Ball","Lorcana"],"strength":"Kompletterande svensk TCG-källa med flera sealed-format","recommended_ingest":"Feed/CSV eller manuell import tills policy är granskad"},
    "Coolcard": {"priority":1,"coverage":["Hockey","Fotboll","Pokémon","Magic"],"strength":"Bred huvudkälla för sportkort och TCG","recommended_ingest":"CSV/feed först; automatisk HTML endast efter policygranskning"},
    "Samlarhobby": {"priority":1,"coverage":["Hockey"],"strength":"Viktig svensk hockeykälla, särskilt Upper Deck","recommended_ingest":"CSV/feed eller manuell import; HTML efter policygranskning"},
    "Bangerpack": {"priority":1,"coverage":["Fotboll","F1","Pokémon","Marvel","Amerikansk sport"],"strength":"Brett sealed-sortiment över sport, TCG och entertainment","recommended_ingest":"CSV/feed först; HTML efter policygranskning"},
    "Kortlagret": {"priority":1,"coverage":["Pokémon","Magic","One Piece","Lorcana"],"strength":"Stort sealed-sortiment och tydlig lagerstatus","recommended_ingest":"CSV/feed först; HTML efter policygranskning"},
    "Sunshine": {"priority":1,"coverage":["F1","Fotboll","Hockey","Basket","Baseboll","NFL","Pokémon","Vintage"],"strength":"Svensk specialist på sealed sportkort och äldre boxar","recommended_ingest":"Feed/CSV prioriteras; HTML först efter policygranskning"},
    "TCGStore": {"priority":1,"coverage":["Pokémon","One Piece","Magic","Lorcana"],"strength":"Bred svensk TCG-butik","recommended_ingest":"Feed/CSV eller manuell import tills policy är granskad"},
    "Hobbykort": {"priority":1,"coverage":["Pokémon","Magic","Yu-Gi-Oh!","Lorcana","Riftbound"],"strength":"Brett sealed TCG-sortiment","recommended_ingest":"Feed/CSV eller manuell import tills policy är granskad"},
    "Aquitaz": {"priority":1,"coverage":["Pokémon","Magic","Lorcana","Star Wars Unlimited"],"strength":"Stort sealed-sortiment med många box- och caseformat","recommended_ingest":"Feed/CSV eller manuell import tills policy är granskad"},
    "Speltrollet": {"priority":1,"coverage":["Pokémon","Magic","One Piece","Hockey","Fotboll","Övrig sport","Yu-Gi-Oh!","Lorcana","Star Wars Unlimited"],"strength":"Mycket bred svensk samlarkortsbutik","recommended_ingest":"Kartlägg feed/API och importera komplett sealed-sortiment"},
    "NordicSportsCards": {"priority":1,"coverage":["Hockey","Fotboll","Övrig sport"],"strength":"Sportkortsspecialist","recommended_ingest":"Kartlägg feed/API och importera komplett sealed-sortiment"},
    "TCGPoke": {"priority":2,"coverage":["Pokémon"],"strength":"Svensk sealed Pokémon-källa","recommended_ingest":"Manuell CSV tills feed/API är verifierad"},
    "TCGbutik": {"priority":2,"coverage":["Pokémon","One Piece","Lorcana","Riftbound","Magic","Yu-Gi-Oh!"],"strength":"Kurerad svensk TCG-katalog med sealed products","recommended_ingest":"Manuell import; tillgänglighet bekräftas manuellt hos butiken"},
    "AlphaSpel": {"priority":2,"coverage":["Pokémon","Magic","One Piece","Lorcana","Övrig TCG"],"strength":"Stor svensk spelbutik med TCG-sortiment","recommended_ingest":"Kartlägg sealed-kategorier och feed/API"},
    "Dragons Lair": {"priority":2,"coverage":["Pokémon","Magic","Övrig TCG"],"strength":"Etablerad svensk spelbutik","recommended_ingest":"Kartlägg sealed-kategorier och feed/API"},
    "Röda Goblinen": {"priority":2,"coverage":["Pokémon","Magic","Lorcana","Star Wars Unlimited","Yu-Gi-Oh!"],"strength":"Brett TCG-sortiment","recommended_ingest":"Kartlägg sealed-kategorier och feed/API"},
    "ManaTorsk": {"priority":2,"coverage":["Pokémon","Magic","Lorcana","Star Wars Unlimited","Yu-Gi-Oh!"],"strength":"Svensk TCG-butik","recommended_ingest":"Kartlägg sealed-kategorier och feed/API"},
    "Webhallen": {"priority":2,"coverage":["Pokémon","Magic","One Piece","Lorcana","Övrig TCG"],"strength":"Stor svensk återförsäljare med bred tillgänglighet","recommended_ingest":"Kartlägg produktsidor/feed; håll samlarkort separerat från tillbehör"},
    "RA Card": {"priority":2,"coverage":["Pokémon","Magic","Yu-Gi-Oh!"],"strength":"Svensk TCG-butik","recommended_ingest":"Kartlägg sealed-kategorier och feed/API"},
    "SpelOchSånt": {"priority":2,"coverage":["Pokémon","Magic"],"strength":"Svensk spelbutik med TCG","recommended_ingest":"Kartlägg sealed-kategorier och feed/API"},
    "DrakenDavids": {"priority":2,"coverage":["Fotboll"],"strength":"Fotbollskort och boxar","recommended_ingest":"Kartlägg kompletta sealed fotbollssortimentet"},
    "Poketalk": {"priority":2,"coverage":["Pokémon"],"strength":"Pokémon-fokuserad svensk butik","recommended_ingest":"Kartlägg sealed-kategorier och feed/API"},
    "Samlartorget": {"priority":2,"coverage":["Pokémon"],"strength":"Pokémon och samlarprodukter","recommended_ingest":"Kartlägg sealed-kategorier och feed/API"},
    "EllieCollectables": {"priority":2,"coverage":["Pokémon"],"strength":"Svensk butik med fokus på sealed Pokémon","recommended_ingest":"Kartlägg feed/API och sealed-sortiment"},
    "Pardon My Kicks": {"priority":2,"coverage":["Fotboll","Topps"],"strength":"Kompletterande källa för fotboll","recommended_ingest":"Manuell CSV tills feed/API är verifierad"},
    "MajkiPoké": {"priority":2,"coverage":["Pokémon"],"strength":"Kompletterande svensk Pokémon-källa","recommended_ingest":"Manuell CSV tills feed/API är verifierad"},
    "Hatstore": {"priority":1,"coverage":["Samlarkort"],"strength":"Sekundär källa","recommended_ingest":"Manuell import vid behov"},
}

def source_hub_row(store) -> dict:
    p = SOURCE_PROFILES.get(store.name, {
        "priority":3,"coverage":[],"strength":"Ej profilerad källa",
        "recommended_ingest":"Manuell import tills källan är granskad",
    })
    if store.policy_status in {"approved","automatic_allowed","robots_checked","feed_allowed","api_allowed"}:
        automation = "allowed"
    elif store.policy_status == "manual_allowed":
        automation = "manual_only"
    else:
        automation = "blocked_pending_review"
    return {
        "id":store.id,"name":store.name,"country":store.country,
        "homepage_url":store.homepage_url,"source_url":store.source_url,
        "active":store.active,"priority":p["priority"],"coverage":p["coverage"],
        "strength":p["strength"],"recommended_ingest":p["recommended_ingest"],
        "collection_method":store.collection_method,"adapter_key":store.adapter_key,
        "policy_status":store.policy_status,"automation_status":automation,
        "last_attempt_at":store.last_attempt_at.isoformat() if store.last_attempt_at else None,
        "last_success_at":store.last_success_at.isoformat() if store.last_success_at else None,
        "last_error":store.last_error,
    }
