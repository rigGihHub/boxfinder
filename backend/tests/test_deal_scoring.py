from app.services.deal_scoring import robust_market_reference, deal_confidence, deal_score, cross_store_discount, history_low_position, deal_label, enhanced_deal_score


def test_market_reference_requires_history_depth():
    assert robust_market_reference([100, 101], [90, 100]) is None


def test_market_reference_blends_history_and_cross_store_prices():
    ref = robust_market_reference([100, 100, 100, 100], [80, 120])
    assert ref == 100


def test_extreme_discount_reduces_confidence():
    normal = deal_confidence(observations=12, store_count=4, data_quality=80, discount_pct=20)
    extreme = deal_confidence(observations=12, store_count=4, data_quality=80, discount_pct=70)
    assert extreme < normal


def test_deal_score_requires_box_value_score():
    assert deal_score(discount_pct=20, box_value_score=None, confidence=80) is None


def test_cross_store_discount_uses_peer_prices():
    pct = cross_store_discount(800, [800, 1000, 1000])
    assert round(pct) == 20

def test_history_low_position_flags_within_five_percent():
    x = history_low_position(104, [100, 120, 140, 130])
    assert x["near_90d_low"] is True
    assert x["low"] == 100

def test_deal_label_requires_multiple_signals_for_strong_fynd():
    assert deal_label(discount_pct=15, cross_store_pct=10, near_low=True, confidence=80) == "Starkt fynd"
    assert deal_label(discount_pct=3, cross_store_pct=2, near_low=False, confidence=80) == "Normalt pris"

def test_enhanced_deal_score_still_requires_box_value():
    assert enhanced_deal_score(discount_pct=20, cross_store_pct=10, near_low=True, box_value_score=None, confidence=80) is None
