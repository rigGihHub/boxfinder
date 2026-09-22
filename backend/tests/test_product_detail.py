from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models import Card, CardMarketValue, Checklist, Odds, Offer, PriceHistory, Product, ProductVariant, Store
from app.services.product_detail import chase_cards, outcome_groups, price_history_summary


def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def fixture(db):
    s=Store(name="Store", policy_status="manual_allowed")
    p=Product(slug="detail", canonical_name="Detail Test", category="Hockey", manufacturer="UD")
    db.add_all([s,p]); db.flush()
    v=ProductVariant(product_id=p.id, format="Hobby Box", packs=12, cards_per_pack=8)
    db.add(v); db.flush()
    o=Offer(store_id=s.id, variant_id=v.id, external_id="x", source_title="Detail Test Hobby", price_sek=799, stock_status="in_stock", source_kind="manual", match_status="auto_matched")
    db.add(o); db.flush()
    now=datetime.utcnow()
    for i,price in enumerate([999,899,799]):
        db.add(PriceHistory(offer_id=o.id, price_sek=price, stock_status="in_stock", observed_at=now-timedelta(days=i*10)))
    cl=Checklist(variant_id=v.id, source_name="Official", source_type="official", verification_status="verified", confidence=100)
    db.add(cl); db.flush()
    common=Card(checklist_id=cl.id, subject="Base Player", subset="Base", source_confidence=100)
    jackpot=Card(checklist_id=cl.id, subject="Star Rookie", subset="Rookies", parallel="Gold", serial_numbered_to=10, is_rookie=True, source_confidence=100)
    db.add_all([common,jackpot]); db.flush()
    db.add(CardMarketValue(card_id=jackpot.id, condition_bucket="raw", median_30d_sek=2500, sales_90d=8, data_quality=90))
    db.add(Odds(card_id=jackpot.id, variant_id=v.id, category_key="gold10", basis="official", confidence=100, probability_per_box=.02))
    db.flush()
    return v, common, jackpot


def test_chase_cards_puts_valued_jackpot_first():
    db=db_session(); v,_,jackpot=fixture(db)
    cards,meta=chase_cards(db,v.id)
    assert cards[0]["card_id"] == jackpot.id
    assert cards[0]["outcome"] == "jackpot"
    assert cards[0]["raw_value_sek"] == 2500
    assert meta["verification_status"] == "verified"


def test_price_history_has_90_day_summary():
    db=db_session(); v,_,_=fixture(db)
    hist=price_history_summary(db,v)
    assert hist["windows"]["90d"]["observations"] == 3
    assert hist["windows"]["90d"]["low"] == 799
    assert hist["windows"]["90d"]["median"] == 899


def test_outcomes_group_keeps_unknown_value_cards_visible():
    db=db_session(); v,_,_=fixture(db)
    cards,_=chase_cards(db,v.id)
    groups=outcome_groups(cards)
    assert "Vanligt" == groups["common"]["label"]
    assert groups["jackpot"]["count_in_top_list"] == 1
