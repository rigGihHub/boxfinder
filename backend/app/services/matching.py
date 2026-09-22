import re
from dataclasses import dataclass

# Most specific phrases first.  "box" by itself is intentionally not enough.
FORMAT_ALIASES = {
    "case": ["master case", "sealed case", "hobby case", "booster case", "case of"],
    "hobby box": ["hobby box", "hobby-box", "hobbybox", " hobby "],
    "retail box": ["retail box", "retail-box", "retailbox"],
    "mega box": ["mega box", "mega-box", "megabox"],
    "blaster": ["blaster box", "blaster-box", "blaster"],
    "booster bundle": ["booster bundle", "booster-bundle"],
    "elite trainer box": ["elite trainer box", "etb"],
    "display": ["booster display", "display box", " sealed display", " display "],
    "booster box": ["booster box", "booster-box"],
    "collection box": ["collection box", "collection-box", "collection set", "premium collection"],
    "tin": ["mini tin", "collector tin", "tin box", " tin"],
    "hanger": ["hanger box", "hanger pack", "hanger"],
    "fat pack": ["fat pack"],
    "bundle": ["collector bundle", "bundle box", " bundle"],
    "starter deck": ["starter deck", "starter-deck", "structure deck", "theme deck"],
    "single pack": ["booster pack", "single pack", "value pack", "fat pack", " pack"],
}

RANDOMIZED_FORMATS = {
    "case","hobby box","retail box","mega box","blaster","booster bundle",
    "elite trainer box","display","booster box","collection box","tin","hanger","fat pack",
    "bundle","single pack",
}
CATALOG_ONLY_FORMATS = {"starter deck"}

ACCESSORY_TERMS = {
    "sleeve","sleeves","binder","album","portfolio","playmat","play mat","deck box",
    "toploader","top loader","card holder","storage box","pages","pocket pages",
    "dice","token","tokens","display case",
}

CATEGORY_HINTS = {
    "Pokémon": ["pokemon","pokémon"],
    "One Piece": ["one piece"],
    "Magic": ["magic the gathering","mtg"],
    "Lorcana": ["lorcana"],
    "Yu-Gi-Oh!": ["yu-gi-oh","yugioh"],
    "Star Wars Unlimited": ["star wars unlimited"],
    "Dragon Ball": ["dragon ball"],
    "Digimon": ["digimon"],
    "F1": ["formula 1","formula one"," f1 "],
    "Hockey": ["upper deck","nhl","hockey"],
    "Fotboll": ["topps chrome uefa","merlin","match attax","premier league","uefa","football","soccer","fotboll"],
    "Basket": ["nba","basketball","basket"],
    "NFL": ["nfl","football cards"],
    "Baseboll": ["mlb","baseball"],
}

@dataclass
class NormalizedTitle:
    text: str
    year_season: str | None
    format: str | None
    language: str | None
    category_hint: str | None = None
    sealed_candidate: bool = False
    randomized: bool = False
    exclusion_reason: str | None = None

def _detect_format(text: str) -> str | None:
    padded = f" {text} "
    for canonical, aliases in FORMAT_ALIASES.items():
        if any(alias in padded or alias in text for alias in aliases):
            return canonical
    return None

def _category_hint(text: str) -> str | None:
    padded = f" {text} "
    for category, hints in CATEGORY_HINTS.items():
        if any(h in padded for h in hints):
            return category
    return None

def normalize_title(title: str) -> NormalizedTitle:
    text = title.lower().replace("/", "-")
    text = re.sub(r"[^a-z0-9åäöéü+\- ]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    year = None
    m = re.search(r"\b(20\d{2})(?:\s*[-]\s*(\d{2}|20\d{2}))?\b", text)
    if m:
        year = m.group(1) + ("-" + m.group(2) if m.group(2) else "")

    fmt = _detect_format(text)
    language = None
    if any(x in f" {text} " for x in [" japanese ", " japansk ", " jp ", " jpn "]):
        language = "Japanese"
    elif any(x in f" {text} " for x in [" swedish ", " svensk ", " svenska "]):
        language = "Swedish"
    elif any(x in f" {text} " for x in [" english ", " engelsk ", " engelska ", " en "]):
        language = "English"

    accessory = next((term for term in ACCESSORY_TERMS if term in text), None)
    exclusion_reason = f"accessory:{accessory}" if accessory else None
    sealed_candidate = bool(fmt) and not accessory
    randomized = bool(fmt in RANDOMIZED_FORMATS) and not accessory
    return NormalizedTitle(
        text=text,
        year_season=year,
        format=fmt,
        language=language,
        category_hint=_category_hint(text),
        sealed_candidate=sealed_candidate,
        randomized=randomized,
        exclusion_reason=exclusion_reason,
    )

def token_similarity(a: str, b: str) -> float:
    stop = {"box","hobby","retail","cards","card","kort","trading","the","sealed","display","booster","pack"}
    ta = {x for x in normalize_title(a).text.split() if x not in stop and len(x) > 1}
    tb = {x for x in normalize_title(b).text.split() if x not in stop and len(x) > 1}
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)

def match_score(source_title: str, canonical_name: str, expected_format: str | None = None) -> float:
    src = normalize_title(source_title)
    dst = normalize_title(canonical_name)
    score = token_similarity(source_title, canonical_name) * .68
    if src.year_season and src.year_season in dst.text:
        score += .12
    if expected_format and src.format:
        score += .20 if src.format == expected_format.lower() else -.35
    if src.category_hint and dst.category_hint:
        score += .07 if src.category_hint == dst.category_hint else -.18
    # Cases must never accidentally become boxes/packs.
    if src.format == "case" and expected_format and expected_format.lower() != "case":
        score -= .50
    return round(max(0.0, min(score, 1.0)), 3)

def classify_match(score: float) -> str:
    if score >= .84:
        return "auto_matched"
    if score >= .64:
        return "review"
    return "unmatched"
