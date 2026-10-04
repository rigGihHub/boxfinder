from copy import deepcopy
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from app.services.offer_freshness import is_current_real_offer, is_recent_observation
from app.services.resale_rankings import rank_resale, resale_rank
from test_rankings import resale_item


def test_cheaper_identical_product_wins_even_below_old_price_floor():
    cheap = resale_item(id=1, price=50, packs=1)
    dear = resale_item(id=2, price=100, packs=1)
    assert rank_resale([dear, cheap], 'value')[0]['id'] == 1
    assert resale_rank(cheap, 'value')['resale_score_precise'] > resale_rank(dear, 'value')['resale_score_precise']


def test_top_card_ceiling_contributes_at_most_five_points():
    low = resale_item(price=500)
    high = deepcopy(low)
    for key in ['big', 'jackpot']:
        low['chase_profile']['tiers'][key]['score'] = 0
        high['chase_profile']['tiers'][key]['score'] = 100
    delta = resale_rank(high, 'value')['resale_score_precise'] - resale_rank(low, 'value')['resale_score_precise']
    assert 0 <= delta <= 5


def test_many_packs_do_not_invent_frequency_or_multiply_value():
    one = resale_rank(resale_item(packs=1), 'value')
    many = resale_rank(resale_item(packs=36), 'value')
    assert one['opening_profile']['repeatable'] == many['opening_profile']['repeatable'] == 50
    assert many['resale_score_precise'] == one['resale_score_precise']


def test_documented_box_can_beat_cheap_weak_loose_pack():
    cheap = resale_item(id=1, price=49, packs=1, format='single pack')
    for tier in cheap['chase_profile']['tiers'].values():
        tier['score'] = 25
    box = resale_item(id=2, price=899, packs=12, format='hobby box')
    box['chase_profile']['format_hits'] = [dict(format='hobby box', family='autografer', count=2, basis='guaranteed', quality='premium')]
    assert rank_resale([cheap, box], 'value')[0]['id'] == 2


def test_family_odds_and_cached_ev_cannot_become_verified_return():
    value = resale_rank(resale_item(ev_low=5000, ev_high=6000, data_quality=100), 'value')
    assert not value['has_market_ev']
    assert 'bedömning' in value['evidence_grade']
    assert 'inte förväntad vinst' in value['resale_warning']
    assert 'utan frakt' in value['resale_warning']


def test_value_mode_is_public_api_default():
    from app.routers.rankings import resale_rankings
    assert resale_rankings.__defaults__[0].default == 'value'


def test_observations_require_known_recent_utc_time():
    now = datetime.now(timezone.utc)
    assert is_recent_observation(now.isoformat(), now)
    assert is_recent_observation(now.replace(tzinfo=None), now)
    assert is_recent_observation(now - timedelta(days=14), now)
    for value in [None, 'bad', now + timedelta(seconds=1), now - timedelta(days=14, seconds=1)]:
        assert not is_recent_observation(value, now)


def test_expired_or_untrusted_offers_are_not_current():
    now = datetime.now(timezone.utc)
    offer = SimpleNamespace(source_kind='verified_snapshot', match_status='manual_matched', stock_status='in_stock', is_preorder=False, price_sek=300, observed_at=now)
    assert is_current_real_offer(offer, now)
    for name, value in [('stock_status','unknown'), ('match_status','review_required'), ('is_preorder',True), ('source_kind','demo'), ('price_sek',0), ('observed_at',now-timedelta(days=15))]:
        changed = SimpleNamespace(**{**vars(offer),name:value})
        assert not is_current_real_offer(changed, now)


def test_cached_ranking_cannot_extend_expired_price():
    from app.routers import rankings
    from time import monotonic
    from unittest.mock import patch
    now = datetime.now(timezone.utc)
    cache = dict(until=monotonic()+60, refreshing=False, ranked={'value':[
        dict(id=1,observed_at=(now-timedelta(days=15)).isoformat()),
        dict(id=2,observed_at=now.isoformat())]})
    with patch.object(rankings,'_resale_cache',cache):
        assert [x['id'] for x in rankings._resale_items(None,'value',None,None)] == [2]


def test_extra_packs_cannot_outweigh_materially_lower_entry_cost():
    cheap = resale_item(id=1, price=250, packs=1)
    many = resale_item(id=2, price=500, packs=36)
    assert rank_resale([many, cheap], 'value')[0]['id'] == 1
