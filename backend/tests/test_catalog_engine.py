from app.services.matching import normalize_title, match_score

def test_specific_sealed_formats_are_detected():
    cases = {
        "2025-26 Upper Deck Series 1 Hobby Box": "hobby box",
        "Pokemon Destined Rivals Elite Trainer Box": "elite trainer box",
        "One Piece OP-12 Booster Box": "booster box",
        "Topps Chrome UEFA Blaster Box": "blaster",
        "Pokemon Booster Bundle": "booster bundle",
        "Sealed Case of 12 Hobby Box": "case",
    }
    for title, expected in cases.items():
        n = normalize_title(title)
        assert n.format == expected
        assert n.sealed_candidate is True

def test_accessories_are_not_sealed_candidates():
    n = normalize_title("Pokemon Pikachu 9-Pocket Album")
    assert n.sealed_candidate is False
    assert n.exclusion_reason.startswith("accessory:")

def test_case_is_strongly_penalized_against_box():
    assert match_score("Upper Deck Series 1 Case of 12", "Upper Deck Series 1 Hobby Box", "hobby box") < .64

def test_category_hints():
    assert normalize_title("Pokemon Mega Evolution Booster Box").category_hint == "Pokémon"
    assert normalize_title("Disney Lorcana Reign of Jafar Display").category_hint == "Lorcana"
