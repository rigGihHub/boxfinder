from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models import Product, ProductVariant, Checklist, Card
from app.services.discovery import box_quality_score, price_score, checklist_traits, goal_score, discover

def session():
    engine=create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()

def item(**overrides):
    x={
        "id":1,"name":"Test Box","category":"Hockey","manufacturer":"Test","format":"hobby box",
        "price":800,"market_median":1000,"discount_pct":20,"data_quality":80,
        "checklist_strength":80,"hit_density":75,"upside":90,"floor_score":60,
        "rookie_strength":85,"popularity":70,"box_value_score":78,
        "store":"A","source_kind":"manual","good_hits":[],
    }
    x.update(overrides)
    return x

def test_box_score_does_not_depend_on_price():
    a=box_quality_score(item(price=500,market_median=700))
    b=box_quality_score(item(price=1500,market_median=1700))
    assert a==b

def test_price_score_rewards_discount():
    assert price_score(item(price=750,market_median=1000)) > price_score(item(price=1000,market_median=1000))

def test_price_score_missing_without_market_reference():
    assert price_score(item(market_median=None)) is None

def test_checklist_traits_counts_autographs_and_rookies():
    db=session()
    p=Product(slug="d",canonical_name="Discovery",category="Hockey",manufacturer="Test")
    db.add(p); db.flush()
    v=ProductVariant(product_id=p.id,format="hobby box",language="English")
    db.add(v); db.flush()
    cl=Checklist(variant_id=v.id,source_name="test",source_type="manual",verification_status="verified",confidence=90)
    db.add(cl); db.flush()
    db.add_all([
        Card(checklist_id=cl.id,subject="A",is_autograph=True,is_rookie=True),
        Card(checklist_id=cl.id,subject="B",is_autograph=True),
    ]); db.flush()
    traits=checklist_traits(db,v.id)
    assert traits["autographs"]==2
    assert traits["rookies"]==1

def test_discovery_returns_unique_roles():
    db=session()
    items=[]
    for i in range(1,4):
        p=Product(slug=f"p{i}",canonical_name=f"Box {i}",category="Hockey",manufacturer="Test")
        db.add(p); db.flush()
        v=ProductVariant(product_id=p.id,format="hobby box",language="English")
        db.add(v); db.flush()
        x=item(id=v.id,name=f"Box {i}",upside=60+i*10,floor_score=90-i*10)
        items.append(x)
    db.flush()
    result=discover(db,items,"balanced")
    assert [x["recommendation_role"] for x in result["recommendations"]]==["Mitt val","Säkrare val","Jackpotval"]
    assert len({x["id"] for x in result["recommendations"]})==3
