import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models import Store
from app.services.ingestion import ingest_store

def test_policy_blocks_unreviewed_source():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    s = Store(name="Blocked", country="SE", active=True, adapter_key="public_html_catalog", source_url="https://example.invalid", policy_status="review_required")
    db.add(s); db.commit(); db.refresh(s)
    run = asyncio.run(ingest_store(db, s))
    assert run.status == "blocked"
    assert "not approved" in run.error
