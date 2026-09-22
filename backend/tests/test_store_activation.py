from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models import Store, StoreIntakeProfile
from app.services.store_activation import activation_queue
def dbs():
 e=create_engine("sqlite:///:memory:");Base.metadata.create_all(e);return sessionmaker(bind=e)()
def test_policy_cannot_be_bypassed_by_high_priority():
 db=dbs();s=Store(name="Coolcard",country="SE",collection_method="feed",policy_status="review_required",source_url="https://x.test/feed");db.add(s);db.flush()
 db.add(StoreIntakeProfile(store_id=s.id,status="validated",feed_format="csv",field_mapping_json="{}"));db.commit()
 x=activation_queue(db)["queue"][0]
 assert x["status"]=="blocked"
 assert "feed/API-policy ej klar" in x["blockers"]
def test_validated_permitted_source_can_be_ready():
 db=dbs();s=Store(name="Coolcard",country="SE",collection_method="feed",policy_status="feed_allowed",source_url="https://x.test/feed",adapter_key="generic_mapped_feed");db.add(s);db.flush()
 db.add(StoreIntakeProfile(store_id=s.id,status="validated",feed_format="csv",field_mapping_json="{}"));db.commit()
 assert activation_queue(db)["queue"][0]["status"]=="ready"
