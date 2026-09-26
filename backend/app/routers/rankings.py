from datetime import datetime, timezone
from threading import Lock, Thread
from time import monotonic
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db, SessionLocal
from .products import list_products
from ..services.rankings import rank_items
from ..services.resale_rankings import STRATEGIES, rank_resale

router = APIRouter(prefix="/rankings", tags=["rankings"])
ALLOWED_MODES = {"value", "upside", "rookies", "hit_density", "balanced"}
_resale_lock = Lock()
_resale_cache: dict = {"until": 0, "ranked": None, "refreshing": False}


def _items(db: Session, category: str | None, max_price: float | None):
    return list_products(category=category, max_price=max_price, db=db, include_details=False)


def prime_resale_rankings(db: Session):
    """Warm sorted snapshot rankings once; individual requests only filter/slice.

    The two-minute expiry bounds stock/price staleness. Each offer still shows
    its actual observed_at timestamp; searched_at is the time the query ran.
    """
    with _resale_lock:
        items = [x for x in _items(db, None, None) if x.get("source_kind") != "demo"]
        _resale_cache["ranked"] = {mode: [x for x in rank_resale(items, mode)
                                           if x.get("resale_score") is not None]
                                   for mode in STRATEGIES}
        _resale_cache["until"] = monotonic() + 120


def _refresh_resale_rankings():
    try:
        with SessionLocal() as db:
            prime_resale_rankings(db)
    except Exception:
        # Retain the last successful snapshot; a later request retries refresh.
        _resale_cache["until"] = monotonic() + 30
    finally:
        with _resale_lock:
            _resale_cache["refreshing"] = False


def _resale_items(db: Session, strategy: str, category: str | None, max_price: float | None):
    if _resale_cache["ranked"] is None:
        prime_resale_rankings(db)
    elif monotonic() >= _resale_cache["until"]:
        with _resale_lock:
            if not _resale_cache["refreshing"]:
                _resale_cache["refreshing"] = True
                Thread(target=_refresh_resale_rankings, daemon=True).start()
    items = _resale_cache["ranked"][strategy]
    if category:
        items = [x for x in items if x["category"].lower() == category.lower()]
    if max_price is not None:
        items = [x for x in items if x["price"] <= max_price]
    return items


@router.get("")
def rankings(
    mode: str = Query("value"), category: str | None = None,
    max_price: float | None = Query(None, ge=0), limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    mode = mode.lower().strip()
    if mode not in ALLOWED_MODES:
        return {"error": "unknown_ranking_mode", "allowed_modes": sorted(ALLOWED_MODES)}
    items = _items(db, category, max_price)
    ranked = rank_items(items, mode)[:limit]
    return {"mode": mode, "category": category, "max_price": max_price, "count": len(ranked), "items": ranked, "searched_at": datetime.now(timezone.utc).isoformat()}


@router.get("/overview")
def ranking_overview(db: Session = Depends(get_db)):
    items = _items(db, None, None)
    return {
        "searched_at": datetime.now(timezone.utc).isoformat(),
        "value": rank_items(items, "value")[:10],
        "upside": rank_items(items, "upside")[:10],
        "balanced": rank_items(items, "balanced")[:10],
        "rookies": rank_items(items, "rookies")[:10],
        "hit_density": rank_items(items, "hit_density")[:10],
        "under_500": rank_items([x for x in items if x.get("price", 10**12) <= 500], "value")[:10],
        "under_1000": rank_items([x for x in items if x.get("price", 10**12) <= 1000], "value")[:10],
        "categories": {
            category: rank_items([x for x in items if x.get("category", "").lower() == category.lower()], "value")[:10]
            for category in sorted({x.get("category") for x in items if x.get("category")})
        },
    }


@router.get("/resale")
def resale_rankings(
    strategy: str = Query("balanced"),
    category: str | None = None,
    max_price: float | None = Query(None, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    strategy = strategy.lower().strip()
    if strategy not in STRATEGIES:
        return {"error": "unknown_strategy", "allowed_strategies": sorted(STRATEGIES)}
    ranked = _resale_items(db, strategy, category, max_price)
    return {
        "searched_at": datetime.now(timezone.utc).isoformat(),
        "strategy": strategy,
        "category": category,
        "max_price": max_price,
        "count": len(ranked),
        "items": ranked[:limit],
        "disclaimer": "Rankingen jämför öppningspotential mellan kategorier, inte förväntad vinst. Betyg A kräver verifierade marknadsvärden och användbara odds. B kan bygga på familjeodds eller formatträffar; inget av dem är odds för ett namngivet kort. C bygger på verifierad chase-profil utan tillräckliga odds.",
    }
