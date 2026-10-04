from datetime import datetime, timezone
from threading import Lock, Thread
from time import monotonic
from typing import Literal
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db, SessionLocal
from .products import list_products
from ..services.rankings import rank_items
from ..services.resale_rankings import STRATEGIES, rank_resale
from ..services.offer_freshness import is_recent_observation, MAX_OFFER_AGE_DAYS

router = APIRouter(prefix="/rankings", tags=["rankings"])
ALLOWED_MODES = {"value", "upside", "rookies", "hit_density", "balanced"}
_resale_lock = Lock()
_resale_cache: dict = {"until": 0, "ranked": None, "refreshing": False}


def _items(db: Session, category: str | None, max_price: float | None):
    return list_products(category=category, max_price=max_price, db=db, include_details=False, current_offers_only=True)


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


def _resale_items(db: Session, strategy: str, category: str | None, max_price: float | None, store_id: int | None = None, cost_basis: str = "item", store_name: str | None = None):
    if _resale_cache["ranked"] is None:
        prime_resale_rankings(db)
    elif monotonic() >= _resale_cache["until"]:
        with _resale_lock:
            if not _resale_cache["refreshing"]:
                _resale_cache["refreshing"] = True
                Thread(target=_refresh_resale_rankings, daemon=True).start()
    items = _resale_cache["ranked"][strategy]
    if store_id is not None or store_name is not None or cost_basis == "total":
        # Select the store offer BEFORE price filtering and scoring. A product
        # must not disappear just because a different store is cheaper.
        selected = []
        for item in items:
            offers = [offer for offer in item.get("store_offers", [])
                      if (store_id is None or offer["store_id"] == store_id)
                      and (store_name is None or offer["store"].casefold() == store_name.strip().casefold())
                      and is_recent_observation(offer.get("observed_at"))
                      and (cost_basis != "total" or (offer.get("total_price_sek") is not None
                           and is_recent_observation(offer.get("shipping_checked_at"))))]
            if offers:
                key = "total_price_sek" if cost_basis == "total" else "price"
                offer = min(offers, key=lambda o: o[key])
                selected.append({**item, **offer, "cost_basis": cost_basis,
                                 "ranking_price": offer[key]})
        items = rank_resale(selected, strategy)
    items = [x for x in items if is_recent_observation(x.get("observed_at"))]
    if category:
        items = [x for x in items if x["category"].lower() == category.lower()]
    if max_price is not None:
        items = [x for x in items if x.get("ranking_price", x["price"]) <= max_price]
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
    strategy: str = Query("value"),
    category: str | None = None,
    max_price: float | None = Query(None, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    store_id: int | None = Query(None, ge=1),
    cost_basis: Literal["item", "total"] = "item",
    store_name: str | None = None,
):
    strategy = strategy.lower().strip()
    if strategy not in STRATEGIES:
        return {"error": "unknown_strategy", "allowed_strategies": sorted(STRATEGIES)}
    # Temporarily compare item prices only, including legacy links requesting total.
    cost_basis = "item"
    ranked = _resale_items(db, strategy, category, max_price, store_id, cost_basis, store_name)
    # Coverage describes the whole rankable catalogue, independently of filters
    # and pagination. Count a shared product once globally and once per store.
    stores = {}
    products = set()
    shipping_stores = {}
    for item in _resale_cache["ranked"][strategy]:
        for offer in item.get("store_offers", []):
            if not is_recent_observation(offer.get("observed_at")):
                continue
            store = stores.setdefault(offer["store_id"], {
                "id": offer["store_id"], "name": offer["store"],
                "products": set(), "offers": set(),
            })
            products.add(item["id"])
            store["products"].add(item["id"])
            store["offers"].add((item["id"], offer["url"]))
            if offer.get("total_price_sek") is not None and is_recent_observation(offer.get("shipping_checked_at")):
                shipping_stores[offer["store_id"]] = offer["store"]
    store_coverage = [{"id": store["id"], "name": store["name"],
                       "product_count": len(store["products"]),
                       "offer_count": len(store["offers"])}
                      for store in sorted(stores.values(), key=lambda s: s["name"].casefold())]
    return {
        "searched_at": datetime.now(timezone.utc).isoformat(),
        "strategy": strategy,
        "store_id": store_id,
        "store_name": store_name,
        "cost_basis": cost_basis,
        "available_stores": store_coverage,
        "catalog_coverage": {"rankable_products": len(products),
                             "current_store_offers": sum(s["offer_count"] for s in store_coverage),
                             "stores": len(store_coverage)},
        "shipping_coverage": {"stores": len(shipping_stores),
                              "store_names": sorted(shipping_stores.values(), key=str.casefold)},
        "category": category,
        "max_price": max_price,
        "count": len(ranked),
        "items": ranked[:limit],
        "max_offer_age_days": MAX_OFFER_AGE_DAYS,
        "disclaimer": "Priser, budget och ranking är exklusive frakt. Betyget jämför bedömt innehåll med inköpspriset, inte förväntad vinst. Familjeodds och uppgifter om förpackningens innehåll är inte odds för ett namngivet kort.",
    }
