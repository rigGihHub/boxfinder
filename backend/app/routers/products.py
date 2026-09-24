from statistics import median
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload
from ..database import get_db
from ..models import ChaseProfile, ProductVariant, Offer
from ..services.ev import calculate_variant_ev
from ..services.product_detail import chase_cards, make_summary, outcome_groups, price_history_summary
from ..services.scoring import calculate_box_value_score
from ..services.readiness import ranking_readiness
from ..services.price_compare import comparison_for_variant
from ..services.price_signals import recent_signals
from ..services.product_explanation import explain_variant
from ..services.chase_content import get_profile, profile_from_row, content_summary, chase_ladder, chase_coverage, pull_profile
from ..services.purchase_links import is_direct_purchase_url

router = APIRouter(prefix="/products", tags=["products"])

def serialize_variant(v: ProductVariant):
    offers = [
        o for o in v.offers
        if o.stock_status == "in_stock"
        and not o.is_preorder
        and is_direct_purchase_url(o.url)
    ]
    if not offers:
        return None
    best = min(offers, key=lambda o: o.price_sek)
    prices = [o.price_sek for o in offers]
    market_median = median(prices) if len(prices) >= 2 else None
    a = v.analysis
    score = calculate_box_value_score(
        price=best.price_sek, market_median=market_median,
        ev_low=a.ev_low if a else None, ev_high=a.ev_high if a else None,
        checklist_strength=a.checklist_strength if a else None,
        hit_density=a.hit_density if a else None, upside=a.upside if a else None,
        floor_score=a.floor_score if a else None, rookie_strength=a.rookie_strength if a else None,
        liquidity=a.liquidity if a else None, popularity=a.popularity if a else None,
        data_quality=a.data_quality if a else 0,
    )
    discount = round((market_median-best.price_sek)/market_median*100) if market_median else None
    return {
        "id": v.id, "slug": v.product.slug, "name": f"{v.product.canonical_name} {v.format}",
        "category": v.product.category, "manufacturer": v.product.manufacturer, "format": v.format,
        "price": best.price_sek, "market_median": market_median, "store": best.store.name,
        "url": best.url, "observed_at": best.observed_at.isoformat() if best.observed_at else None,
        "packs": v.packs, "cards_per_pack": v.cards_per_pack,
        "total_cards": v.packs*v.cards_per_pack if v.packs and v.cards_per_pack else None,
        "ev_low": a.ev_low if a else None, "ev_high": a.ev_high if a else None,
        "box_value_score": score, "data_quality": a.data_quality if a else 0,
        "checklist_strength": a.checklist_strength if a else None,
        "hit_density": a.hit_density if a else None, "upside": a.upside if a else None,
        "floor_score": a.floor_score if a else None, "rookie_strength": a.rookie_strength if a else None,
        "liquidity": a.liquidity if a else None, "popularity": a.popularity if a else None,
        "risk": a.risk if a else "Okänd", "source_kind": best.source_kind,
        "discount_pct": discount, "match_status": best.match_status,
        "offer_count": len(offers),
    }

@router.get("")
def list_products(category: str | None = None, max_price: float | None = Query(None, ge=0), db: Session = Depends(get_db), include_details: bool = True):
    q = select(ProductVariant).options(joinedload(ProductVariant.product), joinedload(ProductVariant.offers).joinedload(Offer.store), joinedload(ProductVariant.analysis))
    variants = db.execute(q).unique().scalars().all()
    items = []
    profiles_by_variant = {}
    if not include_details and variants:
        ids = [v.id for v in variants]
        profiles_by_variant = {
            row.variant_id: profile_from_row(row)
            for row in db.scalars(select(ChaseProfile).where(ChaseProfile.variant_id.in_(ids))).all()
        }
    for v in variants:
        x = serialize_variant(v)
        if x:
            if include_details:
                x["ranking_readiness"] = ranking_readiness(db, v)
                x["explanation"] = explain_variant(db, v)
                top_cards, _ = chase_cards(db, v.id, 3)
                profile = get_profile(db, v.id)
            else:
                top_cards = []
                profile = profiles_by_variant.get(v.id)
            x["chase_profile"] = profile
            x["chase_ladder"] = chase_ladder(profile)
            x["good_hits"] = [
                {
                    "name": c.get("subject"),
                    "card_number": c.get("card_number"),
                    "parallel": c.get("parallel"),
                    "market_value_raw": c.get("raw_value_sek"),
                    "outcome": c.get("outcome"),
                }
                for c in top_cards
                if c.get("subject") and c.get("outcome") in {"good_hit", "big_hit", "jackpot"}
            ]
            items.append(x)
    if category: items = [x for x in items if x["category"].lower() == category.lower()]
    if max_price is not None: items = [x for x in items if x["price"] <= max_price]
    return sorted(items, key=lambda x: (x["box_value_score"] is not None, x["box_value_score"] or -1), reverse=True)

@router.get("/{variant_id}/price-comparison")
def product_price_comparison(variant_id: int, db: Session = Depends(get_db)):
    q = select(ProductVariant).where(ProductVariant.id == variant_id).options(
        joinedload(ProductVariant.product),
        joinedload(ProductVariant.offers).joinedload(Offer.store),
    )
    v = db.execute(q).unique().scalar_one_or_none()
    if not v:
        raise HTTPException(404, "Product variant not found")
    return comparison_for_variant(db, v)

@router.get("/{variant_id}")
def product_detail(variant_id: int, db: Session = Depends(get_db)):
    q = select(ProductVariant).where(ProductVariant.id == variant_id).options(joinedload(ProductVariant.product), joinedload(ProductVariant.offers).joinedload(Offer.store), joinedload(ProductVariant.analysis))
    v = db.execute(q).unique().scalar_one_or_none()
    if not v: raise HTTPException(404, "Product variant not found")
    result = serialize_variant(v)
    if not result: raise HTTPException(404, "No active offers for product variant")
    result["offers"] = sorted([{"store":o.store.name,"price_sek":o.price_sek,"stock_status":o.stock_status,"is_preorder":o.is_preorder,"source_kind":o.source_kind,"source_confidence":o.source_confidence,"observed_at":o.observed_at.isoformat(),"url":o.url} for o in v.offers], key=lambda x:x["price_sek"])
    history = price_history_summary(db, v)
    top_cards, checklist_meta = chase_cards(db, variant_id, 25)
    ev = calculate_variant_ev(db, variant_id)
    a = v.analysis
    result["analysis"] = {
        "ev_low": a.ev_low if a else None, "ev_high": a.ev_high if a else None,
        "checklist_strength": a.checklist_strength if a else None, "hit_density": a.hit_density if a else None,
        "upside": a.upside if a else None, "floor_score": a.floor_score if a else None,
        "rookie_strength": a.rookie_strength if a else None, "liquidity": a.liquidity if a else None,
        "popularity": a.popularity if a else None, "data_quality": a.data_quality if a else 0,
        "risk": a.risk if a else "Okänd", "probability_basis": a.probability_basis if a else "unknown",
    }
    result["ev_coverage"] = {
        "cards_total": ev.cards_total, "with_values": ev.cards_with_values, "with_usable_odds": ev.cards_with_usable_odds,
        "in_ev": ev.cards_in_ev, "value_pct": ev.value_coverage_pct, "odds_pct": ev.odds_coverage_pct,
        "ev_pct": ev.ev_coverage_pct, "notes": ev.notes,
    }
    result["price_history"] = history
    result["price_comparison"] = comparison_for_variant(db, v)
    result["price_signals"] = recent_signals(db, days=30, limit=30, variant_id=v.id)
    result["explanation"] = explain_variant(db, v)
    result["chase_profile"] = get_profile(db, v.id)
    result["content_rating"] = content_summary(result["chase_profile"])
    result["chase_ladder"] = chase_ladder(result["chase_profile"])
    result["chase_coverage"] = chase_coverage(result["chase_profile"])
    result["pull_profile"] = pull_profile(result["chase_profile"])
    result["checklist"] = checklist_meta
    result["chase_cards"] = top_cards
    result["outcomes"] = outcome_groups(top_cards)
    result["summary"] = make_summary(result)
    return result
