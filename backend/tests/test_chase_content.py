import json
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models import Product,ProductVariant,ChaseProfile
from app.services.chase_content import get_profile,content_score,content_summary,chase_ladder,chase_coverage,pull_profile,has_actionable_odds

def test_content_score_rewards_depth_without_claiming_ev():
    p={"key_names":["A","B","C"],"tiers":{"everyday":{"score":80},"good":{"score":80},"big":{"score":90},"jackpot":{"score":95}}}
    s=content_score(p)
    assert 80 <= s <= 100

def test_missing_profile_has_no_fake_score():
    assert content_score(None) is None
    assert content_summary(None)["score"] is None

def test_profile_roundtrip():
    e=create_engine("sqlite:///:memory:");Base.metadata.create_all(e);S=sessionmaker(bind=e);db=S()
    p=Product(slug="x",canonical_name="X",category="Hockey",manufacturer="UD");db.add(p);db.flush()
    v=ProductVariant(product_id=p.id,format="hobby");db.add(v);db.flush()
    db.add(ChaseProfile(variant_id=v.id,content_json=json.dumps({"key_names":["Star"],"tiers":{"good":{"score":80}}}),source_name="Verified",source_url="https://example.test",verified_at=datetime.utcnow(),confidence=95));db.commit()
    x=get_profile(db,v.id)
    assert x["key_names"]==["Star"]
    assert x["confidence"]==95

def test_content_summary_has_opening_style():
    p={"key_names":[],"tiers":{"everyday":{"score":90,"items":["A"]},"good":{"score":80},"big":{"score":70},"jackpot":{"score":60}}}
    x=content_summary(p)
    assert x["style"]=="Hit-koncentrerad"

def test_no_key_names_can_still_score_well_from_verified_content():
    p={"key_names":[],"tiers":{"everyday":{"score":88,"items":["A","B"]},"good":{"score":92},"big":{"score":82},"jackpot":{"score":72}}}
    assert content_score(p)>=80

def test_exact_chase_ladder_orders_by_pull_tier():
    p={"headline_chases":[
        {"card":"One","tier":"JACKPOT","odds":"1/1"},
        {"card":"Two","tier":"BRA","odds":"1:2"},
        {"card":"Three","tier":"MONSTER","odds":"/25"},
    ]}
    ladder=chase_ladder(p)
    assert [x["tier"] for x in ladder]==["BRA","MONSTER","JACKPOT"]
    assert chase_coverage(p)["status"]=="card_level"
    assert chase_coverage(p)["has_odds"] is True

def test_product_level_profile_is_not_mislabeled_card_level():
    p={"tiers":{"good":{"score":80}}}
    assert chase_coverage(p)["status"]=="product_level"

def test_serial_number_is_not_mislabeled_as_pull_odds():
    serial_only={"headline_chases":[
        {"card":"Unique card","tier":"JACKPOT","odds":"1/1; individuellt packodds ej publicerat"},
        {"card":"Low numbered card","tier":"MONSTER","odds":"serial /25"},
    ]}
    assert has_actionable_odds(serial_only) is False
    assert chase_coverage(serial_only)["has_odds"] is False

def test_ratio_or_explicit_guarantee_counts_as_actionable_odds():
    ratio={"headline_chases":[{"card":"Insert","tier":"BRA","odds":"1:60 hobby-pack"}]}
    guarantee={"headline_chases":[{"card":"Auto family","tier":"BRA","odds":"1 autograph guaranteed per box"}]}
    assert has_actionable_odds(ratio) is True
    assert has_actionable_odds(guarantee) is True

def test_negated_guarantee_does_not_count_as_actionable_odds():
    profiles=(
        {"headline_chases":[{"card":"Auto","tier":"MONSTER","odds":"Autograf finns men är inte garanterad"}]},
        {"headline_chases":[{"card":"Auto","tier":"MONSTER","odds":"Specific player not guaranteed"}]},
        {"headline_chases":[{"card":"Auto","tier":"MONSTER","odds":"Löst pack saknar garanti"}]},
    )
    assert all(has_actionable_odds(profile) is False for profile in profiles)

def test_pull_profile_separates_repeatable_fun_and_ceiling():
    p={"tiers":{"everyday":{"score":90},"good":{"score":85},"big":{"score":70},"jackpot":{"score":60}}}
    x=pull_profile(p)
    assert x["repeatable"]>x["ceiling"]
    assert 0<=x["variance"]<=100

def test_missing_pull_profile_does_not_invent_scores():
    x=pull_profile(None)
    assert x["repeatable"] is None
    assert x["ceiling"] is None
