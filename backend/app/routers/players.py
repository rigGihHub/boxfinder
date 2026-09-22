from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.player_scanner import scan_subject

router = APIRouter(prefix="/players", tags=["players"])

@router.get("/search")
def player_search(q: str = Query(..., min_length=2, max_length=120), db: Session = Depends(get_db)):
    return {"query": q, "results": scan_subject(db, q), "score_note": "Opportunity Score är relativt inom just denna sökning och bygger bara på produkter med användbara odds."}
