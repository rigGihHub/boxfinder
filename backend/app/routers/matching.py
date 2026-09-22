from fastapi import APIRouter
from ..schemas import MatchRequest, MatchResult
from ..services.matching import match_score, classify_match, normalize_title

router = APIRouter(prefix="/matching", tags=["matching"])

@router.post("/preview", response_model=MatchResult)
def preview_match(payload: MatchRequest):
    score = match_score(payload.source_title, payload.canonical_name, payload.expected_format)
    return MatchResult(score=score, status=classify_match(score))

@router.get("/normalize")
def normalize(title: str):
    x = normalize_title(title)
    return {"text":x.text,"year_season":x.year_season,"format":x.format,"language":x.language}
