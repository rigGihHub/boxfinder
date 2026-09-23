from app.services.rankings import rank_item, rank_items
from app.services.resale_rankings import rank_resale, resale_rank


def base_item(**kwargs):
    item = dict(price=800, ev_low=550, ev_high=750, box_value_score=82, data_quality=80,
                upside=90, rookie_strength=85, hit_density=78, floor_score=50)
    item.update(kwargs)
    return item


def test_upside_requires_upside_data():
    assert rank_item(base_item(upside=None), "upside").score is None


def test_value_does_not_invent_missing_box_score():
    assert rank_item(base_item(box_value_score=None), "value").score is None


def test_rank_items_orders_profile_score():
    low = base_item(id=1, upside=45)
    high = base_item(id=2, upside=95)
    result = rank_items([low, high], "upside")
    assert result[0]["id"] == 2


def test_balanced_rewards_floor_over_same_other_inputs():
    a = base_item(floor_score=20)
    b = base_item(floor_score=80)
    assert rank_item(b, "balanced").score > rank_item(a, "balanced").score


def resale_item(**kwargs):
    item = dict(
        id=1, price=1000, source_kind="verified_snapshot", data_quality=0,
        ev_low=None, ev_high=None,
        chase_profile={
            "confidence": 90,
            "key_names": ["Star Rookie"],
            "headline_chases": [{"tier": "JACKPOT", "card": "Star Rookie Auto /10", "odds": "1:500"}],
            "tiers": {
                "everyday": {"score": 75, "items": ["Parallels"]},
                "good": {"score": 80, "items": ["Rookies"]},
                "big": {"score": 90, "items": ["Autos"]},
                "jackpot": {"score": 95, "items": ["Star Rookie Auto /10"]},
            },
        },
    )
    item.update(kwargs)
    return item


def test_resale_rank_is_cross_category_and_explicit_about_missing_ev():
    result = resale_rank(resale_item(category="Pokémon"))
    assert result["resale_score"] is not None
    assert result["evidence_grade"].startswith("B")
    assert result["has_market_ev"] is False
    assert "inte förväntad vinst" in result["resale_warning"]


def test_resale_rank_requires_verified_chase_profile():
    result = resale_rank(resale_item(chase_profile=None))
    assert result["resale_score"] is None
    assert result["evidence_grade"] == "Ej rankbar"


def test_jackpot_strategy_rewards_higher_ceiling():
    lower = resale_item(id=1)
    higher = resale_item(id=2)
    higher["chase_profile"] = {**higher["chase_profile"], "tiers": {**higher["chase_profile"]["tiers"], "big": {"score": 100, "items": ["Autos"]}, "jackpot": {"score": 100, "items": ["1/1"]}}}
    assert rank_resale([lower, higher], "jackpot")[0]["id"] == 2
