from app.services.matching import classify_match, match_score, normalize_title

def test_normalizes_hobby_and_season():
    x = normalize_title("Upper Deck Series 1 2025/26 Hobby Box")
    assert x.format == "hobby box"
    assert x.year_season == "2025-26"

def test_rejects_case_as_box_match():
    score = match_score("2025-26 Upper Deck Series 1 Master Case", "2025-26 Upper Deck Series 1", "hobby box")
    assert score < .62
    assert classify_match(score) == "unmatched"

def test_typical_alias_needs_or_passes_review():
    score = match_score("UD Series 1 2025/26 Hobby", "2025-26 Upper Deck Series 1", "hobby box")
    assert score >= .45


def test_display_is_not_booster_box_by_default():
    x = normalize_title("Disney Lorcana Reign of Jafar Display")
    assert x.format == "display"
    assert x.format != "booster box"
