from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models import Card, Checklist, Odds, Product, ProductVariant, Sale
from app.services.market_values import rebuild_market_value
from app.services.ev import calculate_variant_ev


def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def make_card(db):
    p=Product(slug="x", canonical_name="Test", category="Hockey", manufacturer="UD")
    db.add(p); db.flush()
    v=ProductVariant(product_id=p.id, format="Hobby Box", packs=12, cards_per_pack=8)
    db.add(v); db.flush()
    cl=Checklist(variant_id=v.id, source_name="Official", verification_status="verified", confidence=100)
    db.add(cl); db.flush()
    c=Card(checklist_id=cl.id, subject="Player", subset="Base", source_confidence=100)
    db.add(c); db.flush()
    return v,c


def test_market_value_uses_recent_medians():
    db=db_session(); v,c=make_card(db); now=datetime.utcnow()
    for i,price in enumerate([100,120,140]):
        db.add(Sale(card_id=c.id, source_name="test", external_id=str(i), sold_price=price, price_sek=price, sold_at=now-timedelta(days=i), condition_bucket="raw", verified=True, source_confidence=100))
    db.flush(); mv=rebuild_market_value(db,c.id,"raw",now)
    assert mv.median_7d_sek == 120
    assert mv.sales_90d == 3
    assert mv.data_quality > 0


def test_ev_requires_both_value_and_probability():
    db=db_session(); v,c=make_card(db); now=datetime.utcnow()
    db.add(Sale(card_id=c.id, source_name="test", external_id="1", sold_price=100, price_sek=100, sold_at=now, condition_bucket="raw", verified=True, source_confidence=100)); db.flush()
    rebuild_market_value(db,c.id,"raw",now)
    no_odds=calculate_variant_ev(db,v.id)
    assert no_odds.ev_low is None
    db.add(Odds(card_id=c.id, variant_id=v.id, category_key="card", basis="official", confidence=100, probability_per_box=.5))
    db.flush(); result=calculate_variant_ev(db,v.id)
    assert result.ev_low == 42.5
    assert result.ev_high == 57.5
    assert result.ev_coverage_pct == 100


def test_estimated_odds_are_allowed_but_lower_quality():
    db=db_session(); v,c=make_card(db); now=datetime.utcnow()
    db.add(Sale(card_id=c.id, source_name="test", external_id="1", sold_price=200, price_sek=200, sold_at=now, condition_bucket="raw", verified=True, source_confidence=100)); db.flush()
    rebuild_market_value(db,c.id,"raw",now)
    db.add(Odds(card_id=c.id, variant_id=v.id, category_key="card", basis="estimated", confidence=80, probability_per_box=.25)); db.flush()
    result=calculate_variant_ev(db,v.id)
    assert result.ev_low == 42.5
    assert result.data_quality < 100
