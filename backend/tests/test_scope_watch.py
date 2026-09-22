from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import Store, Product, ProductVariant, Offer, PriceSignal, ScopeWatchRule
from app.services.scope_watch import evaluate_scope_signal

def session():
    engine=create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()

def setup(db, category="Hockey", fmt="hobby box", price=450):
    store=Store(name="Scope Store",country="SE",collection_method="manual",policy_status="manual_allowed")
    product=Product(slug="scope-box",canonical_name="Scope Box",category=category,manufacturer="Test")
    db.add_all([store,product]); db.flush()
    variant=ProductVariant(product_id=product.id,format=fmt,language="English")
    db.add(variant); db.flush()
    offer=Offer(store_id=store.id,variant_id=variant.id,external_id="s1",source_title="Scope Box",
                price_sek=price,stock_status="in_stock",is_preorder=False,match_status="auto_matched")
    db.add(offer); db.flush()
    signal=PriceSignal(offer_id=offer.id,variant_id=variant.id,store_id=store.id,
                       signal_type="price_drop",old_price_sek=500,new_price_sek=price,
                       observed_at=datetime.utcnow())
    db.add(signal); db.flush()
    return variant,signal

def test_scope_rule_matches_category_format_and_price():
    db=session()
    v,s=setup(db)
    rule=ScopeWatchRule(category="Hockey",format="hobby box",max_price_sek=500,
                        trigger_type="matching_offer",active=True)
    db.add(rule); db.flush()
    events=evaluate_scope_signal(db,s)
    assert len(events)==1
    assert events[0].variant_id==v.id

def test_scope_rule_rejects_wrong_category():
    db=session()
    _,s=setup(db,category="Hockey")
    db.add(ScopeWatchRule(category="Fotboll",max_price_sek=500,trigger_type="matching_offer",active=True))
    db.flush()
    assert evaluate_scope_signal(db,s)==[]

def test_scope_rule_rejects_price_above_limit():
    db=session()
    _,s=setup(db,price=650)
    db.add(ScopeWatchRule(category="Hockey",max_price_sek=500,trigger_type="matching_offer",active=True))
    db.flush()
    assert evaluate_scope_signal(db,s)==[]

def test_trigger_specific_rule_only_matches_same_signal_type():
    db=session()
    _,s=setup(db)
    db.add(ScopeWatchRule(category="Hockey",trigger_type="new_90d_low",active=True))
    db.flush()
    assert evaluate_scope_signal(db,s)==[]

def test_scope_event_not_duplicated_for_same_signal():
    db=session()
    _,s=setup(db)
    db.add(ScopeWatchRule(category="Hockey",trigger_type="price_drop",active=True))
    db.flush()
    assert len(evaluate_scope_signal(db,s))==1
    db.flush()
    assert len(evaluate_scope_signal(db,s))==0
