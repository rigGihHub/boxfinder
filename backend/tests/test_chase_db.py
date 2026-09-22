from sqlalchemy import create_engine,select,func
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models import ChaseCard,VariantChaseCard,ChaseProfile,Product,ProductVariant,Store,Offer
import app.seed as seedmod

def sf():
    e=create_engine("sqlite:///:memory:");Base.metadata.create_all(e);return sessionmaker(bind=e)

def test_same_canonical_card_can_link_multiple_box_formats(monkeypatch):
    S=sf();monkeypatch.setattr(seedmod,"SessionLocal",S)
    seedmod.seed_verified_snapshot();seedmod.seed_chase_card_db()
    db=S()
    c=db.scalar(select(ChaseCard).where(ChaseCard.canonical_key=="hockey:2025-26:ud-s2:451:matthew-schaefer:young-guns"))
    links=db.scalars(select(VariantChaseCard).where(VariantChaseCard.chase_card_id==c.id)).all()
    assert len(links)>=2
    db.close()

def test_chase_seed_is_idempotent(monkeypatch):
    S=sf();monkeypatch.setattr(seedmod,"SessionLocal",S)
    seedmod.seed_verified_snapshot();seedmod.seed_chase_card_db();seedmod.seed_chase_card_db()
    db=S()
    assert db.scalar(select(func.count()).select_from(ChaseCard)) < len(seedmod.CHASE_CARD_DB)
    db.close()

def test_chase_profiles_seed_without_startup_name_error(monkeypatch):
    S=sf();monkeypatch.setattr(seedmod,"SessionLocal",S)
    seedmod.seed_verified_snapshot();seedmod.seed_chase_profiles()
    db=S()
    profiles=db.scalars(select(ChaseProfile)).all()
    assert len(profiles) >= 1
    db.close()

def test_chase_cards_have_sources(monkeypatch):
    S=sf();monkeypatch.setattr(seedmod,"SessionLocal",S)
    seedmod.seed_verified_snapshot();seedmod.seed_chase_card_db()
    db=S()
    links=db.scalars(select(VariantChaseCard)).all()
    assert links and all(x.source_url.startswith("https://") and x.confidence>=90 for x in links)
    db.close()

def test_chase_db_has_deeper_series2_routes(monkeypatch):
    S=sf();monkeypatch.setattr(seedmod,"SessionLocal",S)
    seedmod.seed_verified_snapshot();seedmod.seed_chase_card_db()
    db=S()
    schaefer=db.scalars(select(ChaseCard).where(ChaseCard.player_name=="Matthew Schaefer")).all()
    assert len(schaefer)>=4
    assert any(x.card_name=="Incarnations INC-5" for x in schaefer)
    assert any(x.card_name=="UD Canvas Program of Excellence C-259" for x in schaefer)
    db.close()

def test_exact_rare_routes_keep_odds_text(monkeypatch):
    S=sf();monkeypatch.setattr(seedmod,"SessionLocal",S)
    seedmod.seed_verified_snapshot();seedmod.seed_chase_card_db()
    db=S()
    c=db.scalar(select(ChaseCard).where(ChaseCard.canonical_key=="hockey:2025-26:ud-s2:schaefer:inc-5"))
    link=db.scalar(select(VariantChaseCard).where(VariantChaseCard.chase_card_id==c.id))
    assert "1:1,920" in link.odds_text
    db.close()
