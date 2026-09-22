from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.services.player_scanner import scan_subject

def test_player_scanner_unknown_subject_is_empty():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    assert scan_subject(db, "Definitely Not In Demo Checklist") == []
