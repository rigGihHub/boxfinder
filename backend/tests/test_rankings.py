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


def test_rank_uses_precise_score_before_rounded_label():
    lower = resale_item(id=1, price=300)
    higher = resale_item(id=2, price=295)
    assert resale_rank(lower)["resale_score"] == resale_rank(higher)["resale_score"]
    assert rank_resale([lower, higher])[0]["id"] == 2


def test_lone_one_of_one_does_not_beat_broad_premium_chase():
    lone = resale_item(id=1, price=99, format="single pack", packs=1)
    lone["chase_profile"] = {**lone["chase_profile"],
        "key_names": ["One star"],
        "headline_chases": [{"tier": "JACKPOT", "card": "One star 1/1", "odds": "1/1; packodds ej publicerat"}],
        "tiers": {"everyday": {"score": 35}, "good": {"score": 40},
                  "big": {"score": 65}, "jackpot": {"score": 100}}}
    premium = resale_item(id=2, price=1595, format="hobby box", packs=12)
    premium["chase_profile"] = {**premium["chase_profile"],
        "key_names": ["Rookie A", "Star B", "Legend C", "Star D"],
        "headline_chases": [{"tier": "JACKPOT", "card": f"Star auto {i}", "odds": "okända"} for i in range(4)],
        "format_hits": [{"format": "hobby box", "family": "autografer", "count": 2, "basis": "average", "quality": "premium"}]}
    assert rank_resale([lone, premium], "jackpot")[0]["id"] == 2


def test_one_off_parallel_roster_does_not_count_as_deep_chase():
    base = resale_item()["chase_profile"]
    unique = {**base, "key_names": [f"Star {n}" for n in range(6)],
              "headline_chases": [{"tier": "JACKPOT", "card": f"Star {n} 1/1",
                                   "odds": "1/1; packodds ej publicerat"} for n in range(5)]}
    deep = {**base, "key_names": [f"Star {n}" for n in range(6)],
            "headline_chases": [{"tier": "MONSTER", "card": f"Star {n} auto /99",
                                 "odds": "packodds ej publicerat"} for n in range(5)]}
    rare = resale_rank(resale_item(chase_profile=unique), "jackpot")
    broad = resale_rank(resale_item(chase_profile=deep), "jackpot")
    assert broad["ranking_factors"]["breadth"] > rare["ranking_factors"]["breadth"]
    assert broad["resale_score_precise"] > rare["resale_score_precise"]


def test_format_hits_do_not_leak_to_loose_pack():
    profile = resale_item()["chase_profile"]
    profile["headline_chases"] = [{"tier": "MONSTER", "card": "Star auto", "odds": "okänt"}]
    profile["format_hits"] = [{"format": "hobby box", "family": "autografer", "count": 2, "basis": "average", "quality": "premium"}]
    hobby = resale_rank(resale_item(format="hobby box", packs=12, chase_profile=profile))
    loose = resale_rank(resale_item(format="single pack", packs=1, chase_profile=profile))
    assert hobby["evidence_grade"].startswith("B")
    assert hobby["format_hits"][0]["basis"] == "average"
    assert loose["evidence_grade"].startswith("C")
    assert loose["format_hits"] == []
    assert hobby["resale_score"] > loose["resale_score"]


def test_guaranteed_base_card_is_not_treated_as_guaranteed_autograph():
    common = resale_item(format="hobby box", packs=10)
    rare = resale_item(**{**common, "id": 1, "chase_profile": {**common["chase_profile"],
        "format_hits": [{"format": "hobby box", "family": "rare", "count": 2, "basis": "guaranteed", "quality": "base"}]}})
    auto = resale_item(**{**common, "id": 2, "chase_profile": {**common["chase_profile"],
        "format_hits": [{"format": "hobby box", "family": "autografer", "count": 2, "basis": "guaranteed", "quality": "premium"}]}})
    assert rank_resale([rare, auto], "frequent")[0]["id"] == 2


def test_more_packs_help_sublinearly_without_becoming_hit_odds():
    single = resale_rank(resale_item(price=1000, packs=1, format="booster box"))
    display = resale_rank(resale_item(price=1000, packs=24, format="booster box"))
    assert display["ranking_factors"]["access"] > single["ranking_factors"]["access"]
    assert display["resale_score_precise"] > single["resale_score_precise"]
    assert display["has_market_ev"] is False


def test_jackpot_odds_do_not_certify_frequent_hits():
    item = resale_item(format="single pack", packs=1)
    item["chase_profile"]["tiers"]["everyday"]["score"] = 96
    item["chase_profile"]["tiers"]["good"]["score"] = 94
    ranked = resale_rank(item, "frequent")
    assert ranked["opening_profile"]["repeatable"] == 74
    assert ranked["frequency_basis"] == "Bedömd checklista; odds för bra träffar saknas"
    assert not any("Många dokumenterade chanser" in reason for reason in ranked["resale_reasons"])


def test_published_common_family_odds_support_repeatability():
    item = resale_item(format="hobby box", packs=12)
    item["chase_profile"]["tiers"]["everyday"] = {"score": 90, "items": ["Young Guns 1:4 hobby-pack"]}
    ranked = resale_rank(item, "frequent")
    assert ranked["opening_profile"]["repeatable"] > 74
    assert ranked["frequency_basis"].startswith("Publicerade familjeodds")


def test_format_guarantee_is_not_carried_over_to_loose_pack_frequency():
    profile = resale_item()["chase_profile"]
    profile["tiers"]["everyday"]["score"] = 95
    profile["tiers"]["good"]["score"] = 90
    profile["format_hits"] = [{"format": "hobby box", "family": "autografer", "count": 2,
                               "basis": "guaranteed", "quality": "premium"}]
    box = resale_rank(resale_item(format="hobby box", packs=10, chase_profile=profile), "frequent")
    pack = resale_rank(resale_item(format="single pack", packs=1, chase_profile=profile), "frequent")
    assert box["opening_profile"]["repeatable"] > 74
    assert pack["opening_profile"]["repeatable"] == 74
    assert box["resale_score"] > pack["resale_score"]


def test_more_packs_cannot_claim_measured_frequency():
    one = resale_rank(resale_item(format="booster box", packs=1), "frequent")
    many = resale_rank(resale_item(format="booster box", packs=36), "frequent")
    assert many["opening_profile"]["repeatable"] == one["opening_profile"]["repeatable"]
    assert many["ranking_factors"]["access"] > one["ranking_factors"]["access"]


def test_jackpot_price_does_not_outweigh_much_better_ceiling():
    cheap = resale_item(id=1, price=49, format="single pack", packs=1)
    expensive = resale_item(id=2, price=2200, format="hobby box", packs=10)
    cheap["chase_profile"] = {**cheap["chase_profile"], "tiers": {"everyday": {"score": 75}, "good": {"score": 80}, "big": {"score": 60}, "jackpot": {"score": 65}}}
    assert rank_resale([cheap, expensive], "jackpot")[0]["id"] == 2


def test_curated_format_facts_match_chase_profiles():
    from app.seed import CHASE_PROFILES, FORMAT_HITS
    from app.services.chase_content import format_hits
    assert FORMAT_HITS
    for slug, facts in FORMAT_HITS.items():
        assert slug in CHASE_PROFILES
        assert len(format_hits(CHASE_PROFILES[slug], facts[0][0])) == len(facts)


def test_primed_ranking_filters_without_requerying_database(monkeypatch):
    from datetime import datetime, timezone
    from app.routers import rankings
    monkeypatch.setattr(rankings, "_resale_cache", {"until": 0, "ranked": None, "refreshing": False})
    items = [resale_item(id=1, price=80, category="Magic", source_kind="verified_snapshot"),
             resale_item(id=2, price=500, category="Hockey", source_kind="verified_snapshot"),
             resale_item(id=3, price=50, category="Magic", source_kind="demo")]
    for item in items:
        item["observed_at"] = datetime.now(timezone.utc).isoformat()
    monkeypatch.setattr(rankings, "_items", lambda db, category, max_price: items)
    rankings.prime_resale_rankings(None)
    assert [x["id"] for x in rankings._resale_items(None, "balanced", "Magic", 100)] == [1]
    assert len(rankings._resale_items(None, "frequent", None, None)) == 2
