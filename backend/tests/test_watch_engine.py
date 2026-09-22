from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import Store, Product, ProductVariant, Offer, PriceSignal, WatchRule
from app.services.watch_engine import evaluate_signal, check_current_price_rule, serialize_events

def session():
    engine=create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()

def setup(db, price=800, stock="in_stock"):
    store=Store(name="Watch Store",country="SE",collection_method="manual",policy_status="manual_allowed")
    product=Product(slug="watch-box",canonical_name="Watch Box",category="Hockey",manufacturer="Test")
    db.add_all([store,product]); db.flush()
    variant=ProductVariant(product_id=product.id,format="hobby box",language="English")
    db.add(variant); db.flush()
    offer=Offer(store_id=store.id,variant_id=variant.id,external_id="w1",source_title="Watch Box Hobby Box",
                price_sek=price,stock_status=stock,is_preorder=False,match_status="auto_matched")
    db.add(offer); db.flush()
    return store,variant,offer

def test_price_below_can_trigger_immediately():
    db=session()
    _,v,_=setup(db,price=750)
    rule=WatchRule(variant_id=v.id,trigger_type="price_below",threshold_sek=800,active=True)
    db.add(rule); db.flush()
    event=check_current_price_rule(db,rule)
    assert event is not None
    assert event.price_sek == 750

def test_price_below_does_not_trigger_above_threshold():
    db=session()
    _,v,_=setup(db,price=850)
    rule=WatchRule(variant_id=v.id,trigger_type="price_below",threshold_sek=800,active=True)
    db.add(rule); db.flush()
    assert check_current_price_rule(db,rule) is None

def test_back_in_stock_signal_matches_rule():
    db=session()
    s,v,o=setup(db)
    rule=WatchRule(variant_id=v.id,trigger_type="back_in_stock",active=True)
    db.add(rule); db.flush()
    signal=PriceSignal(offer_id=o.id,variant_id=v.id,store_id=s.id,signal_type="back_in_stock",
                       previous_stock_status="out_of_stock",current_stock_status="in_stock",
                       new_price_sek=800,observed_at=datetime.utcnow())
    db.add(signal); db.flush()
    events=evaluate_signal(db,signal)
    assert len(events)==1
    assert events[0].event_type=="back_in_stock"

def test_inactive_rule_never_triggers():
    db=session()
    s,v,o=setup(db)
    rule=WatchRule(variant_id=v.id,trigger_type="price_drop",active=False)
    db.add(rule); db.flush()
    signal=PriceSignal(offer_id=o.id,variant_id=v.id,store_id=s.id,signal_type="price_drop",
                       old_price_sek=900,new_price_sek=800,observed_at=datetime.utcnow())
    db.add(signal); db.flush()
    assert evaluate_signal(db,signal)==[]

def test_watch_event_is_not_duplicated_for_same_signal():
    db=session()
    s,v,o=setup(db)
    rule=WatchRule(variant_id=v.id,trigger_type="price_drop",active=True)
    db.add(rule); db.flush()
    signal=PriceSignal(offer_id=o.id,variant_id=v.id,store_id=s.id,signal_type="price_drop",
                       old_price_sek=900,new_price_sek=800,observed_at=datetime.utcnow())
    db.add(signal); db.flush()
    assert len(evaluate_signal(db,signal))==1
    db.flush()
    assert len(evaluate_signal(db,signal))==0
