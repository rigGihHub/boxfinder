from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models import Store, Product, ProductVariant, Offer, PriceHistory
from app.services.price_signals import detect_offer_signals, recent_signals, signal_summary

def session():
    engine=create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()

def setup_offer(db, price=900, stock="in_stock"):
    s=Store(name="A",country="SE",collection_method="manual",policy_status="manual_allowed")
    p=Product(slug="x",canonical_name="Test Box",category="Hockey",manufacturer="Test")
    db.add_all([s,p]); db.flush()
    v=ProductVariant(product_id=p.id,format="hobby box",language="English")
    db.add(v); db.flush()
    o=Offer(store_id=s.id,variant_id=v.id,external_id="1",source_title="Test Box Hobby Box",
            price_sek=price,stock_status=stock,match_status="auto_matched")
    db.add(o); db.flush()
    return s,v,o

def test_price_drop_signal():
    db=session()
    _,_,o=setup_offer(db,800)
    signals=detect_offer_signals(db,o,previous_price=1000,previous_stock="in_stock",now=datetime.utcnow())
    assert "price_drop" in [x.signal_type for x in signals]

def test_back_in_stock_signal():
    db=session()
    _,_,o=setup_offer(db,800,"in_stock")
    signals=detect_offer_signals(db,o,previous_price=800,previous_stock="out_of_stock",now=datetime.utcnow())
    assert "back_in_stock" in [x.signal_type for x in signals]

def test_new_90_day_low_signal():
    db=session()
    _,v,o=setup_offer(db,700)
    now=datetime.utcnow()
    db.add_all([
        PriceHistory(offer_id=o.id,price_sek=900,stock_status="in_stock",observed_at=now-timedelta(days=60)),
        PriceHistory(offer_id=o.id,price_sek=800,stock_status="in_stock",observed_at=now-timedelta(days=20)),
    ]); db.flush()
    signals=detect_offer_signals(db,o,previous_price=800,previous_stock="in_stock",now=now)
    kinds=[x.signal_type for x in signals]
    assert "new_90d_low" in kinds
    assert "new_30d_low" in kinds

def test_no_false_low_without_history():
    db=session()
    _,_,o=setup_offer(db,700)
    signals=detect_offer_signals(db,o,previous_price=None,previous_stock=None,now=datetime.utcnow())
    assert "new_90d_low" not in [x.signal_type for x in signals]


def test_recent_signals_are_enriched():
    db=session()
    s,v,o=setup_offer(db,800)
    now=datetime.utcnow()
    detect_offer_signals(db,o,previous_price=1000,previous_stock="in_stock",now=now)
    db.commit()
    rows=recent_signals(db,days=7,limit=10)
    assert rows
    assert rows[0]["store_name"] == "A"
    assert "Test Box" in rows[0]["product_name"]
    assert rows[0]["category"] == "Hockey"

def test_signal_summary_counts_events():
    db=session()
    _,_,o=setup_offer(db,800)
    now=datetime.utcnow()
    detect_offer_signals(db,o,previous_price=1000,previous_stock="out_of_stock",now=now)
    db.commit()
    summary=signal_summary(db,days=7)
    assert summary["price_drops"] == 1
    assert summary["back_in_stock"] == 1
    assert summary["total_signals"] >= 2
