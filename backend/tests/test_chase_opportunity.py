from app.services.chase_opportunity import parse_probability,probability_per_box,opportunity_for_links

def test_parse_only_explicit_numeric_odds():
    assert parse_probability("1:60 hobby packs")==1/60
    assert parse_probability("serial /25") is None
    assert parse_probability("Retail exact odds not asserted") is None

def test_box_probability_uses_pack_count():
    p=probability_per_box("1:60 packs",12)
    assert 0.18 < p < 0.19

def test_missing_odds_do_not_create_fake_opportunity_score():
    x=opportunity_for_links([{"tier":"JACKPOT","odds":"serial /10"}],12,1000)
    assert x["opportunity_score"] is None
    assert x["numeric_odds_routes"]==0

def test_explicit_odds_can_create_opportunity_score():
    x=opportunity_for_links([{"tier":"MYCKET BRA","odds":"1:60 packs"}],12,1000)
    assert x["opportunity_score"] is not None
    assert x["cards"][0]["probability_per_box"] is not None
