from app.services.rankings import rank_item, rank_items


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
