from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models import Store
from app.services.intake_batch import batch_status, save_batch

def session():
    engine=create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()

def test_batch_status_marks_missing_profiles():
    db=session()
    db.add(Store(name="A",country="SE",collection_method="manual",policy_status="review_required"))
    db.commit()
    rows=batch_status(db)
    assert rows[0]["status"]=="missing"
    assert rows[0]["automation_ready"] is False

def test_batch_save_validates_multiple_store_samples():
    db=session()
    a=Store(name="A",country="SE",collection_method="manual",policy_status="feed_allowed")
    b=Store(name="B",country="SE",collection_method="manual",policy_status="review_required")
    db.add_all([a,b]); db.flush()
    sample="sku,name,price\n1,Test Hobby Box,499\n"
    result=save_batch(db,[
        {"store_id":a.id,"feed_format":"csv","sample_text":sample,"source_url":"https://a.test/feed.csv"},
        {"store_id":b.id,"feed_format":"csv","sample_text":sample,"source_url":"https://b.test/feed.csv"},
    ])
    assert result["processed"]==2
    assert result["validated"]==2
    rows={x["store_name"]:x for x in batch_status(db)}
    assert rows["A"]["automation_ready"] is True
    assert rows["B"]["automation_ready"] is False
    assert rows["B"]["activation_ready"] is True
