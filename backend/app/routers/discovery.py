import json
from datetime import datetime, timezone
from typing import Annotated
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload
from ..database import get_db
from ..models import ChaseProfile, Offer, ProductFact, ProductVariant
from .products import list_products
from ..services.discovery import GOALS, discover
from ..services.product_explanation import explain_variant
from ..services.chase_content import profile_from_row, content_summary, chase_ladder, chase_coverage, pull_profile
from ..services.purchase_links import is_direct_purchase_url
from ..services.offer_freshness import is_current_real_offer, is_recent_observation, TRUSTED_MATCH_STATUSES
from ..services.product_format import total_sealed_cards

router=APIRouter(prefix="/discovery",tags=["discovery"])

@router.get("/recommendations")
def recommendations(
    category: str | None = None,
    budget: float | None = Query(None, ge=1),
    goal: str = Query("balanced"),
    format: str | None = None,
    store_name: str | None = None,
    db: Session = Depends(get_db),
):
    goal=goal.lower().strip()
    if goal not in GOALS:
        return {"error":"unknown_goal","allowed_goals":sorted(GOALS)}
    # Select the chosen store before applying the budget. The cheapest offer
    # at another shop must not determine a store-specific recommendation.
    items=list_products(category=category,max_price=None if store_name else budget,
                        db=db,current_offers_only=bool(store_name))
    if store_name:
        wanted_store=store_name.strip().casefold()
        selected=[]
        for item in items:
            offers=[offer for offer in item.get("store_offers", [])
                    if offer["store"].casefold()==wanted_store]
            if not offers:
                continue
            offer=min(offers,key=lambda x:x["price"])
            if budget is not None and offer["price"]>budget:
                continue
            median=item.get("market_median")
            discount=round((median-offer["price"])/median*100) if median else None
            selected.append({**item, **offer, "store_id":offer["store_id"],
                             "price":offer["price"], "store":offer["store"],
                             "url":offer["url"], "observed_at":offer["observed_at"],
                             "discount_pct":discount})
        items=selected
    if format:
        wanted=format.strip().lower()
        items=[x for x in items if wanted in (x.get("format") or "").lower()]
    result=discover(db,items,goal)
    result["category"]=category
    result["budget"]=budget
    result["format"]=format
    result["store_name"]=store_name
    result["searched_at"]=datetime.now(timezone.utc).isoformat()
    return result


@router.get("/real-catalog")
def real_catalog(
    category: str | None = None,
    budget: float | None = Query(None, ge=1),
    format: str | None = None,
    store_name: str | None = None,
    limit: int = Query(60, ge=1, le=200),
    db: Session = Depends(get_db),
    offset: Annotated[int, Query(ge=0)] = 0,
    q: Annotated[str, Query(max_length=160)] = "",
):
    statement = (
        select(ProductVariant)
        .options(
            joinedload(ProductVariant.product),
            joinedload(ProductVariant.offers).joinedload(Offer.store),
        )
    )
    variants=db.execute(statement).unique().scalars().all()
    variant_ids=[v.id for v in variants]
    fact_rows_by_variant={}
    profiles_by_variant={}
    if variant_ids:
        fact_rows_by_variant={f.variant_id:f for f in db.scalars(select(ProductFact).where(ProductFact.variant_id.in_(variant_ids))).all()}
        profiles_by_variant={p.variant_id:p for p in db.scalars(select(ChaseProfile).where(ChaseProfile.variant_id.in_(variant_ids))).all()}
    rows=[]
    now=datetime.now(timezone.utc)
    expired_count=0
    latest_observed_at=None
    terms=q.casefold().split()
    for v in variants:
        if category and v.product.category.casefold()!=category.casefold():
            continue
        if format and format.strip().lower() not in (v.format or "").lower():
            continue
        searchable=f"{v.product.canonical_name} {v.product.category} {v.format or ''}".casefold()
        if not all(term in searchable for term in terms):
            continue
        eligible=[
            o for o in v.offers
            if o.source_kind=="verified_snapshot"
            and o.match_status in TRUSTED_MATCH_STATUSES
            and o.stock_status=="in_stock" and not o.is_preorder
            and o.price_sek is not None and o.price_sek>0
            and is_direct_purchase_url(o.url)
            and (not store_name or o.store.name.casefold()==store_name.strip().casefold())
            and (budget is None or o.price_sek<=budget)
        ]
        for offer in eligible:
            observed=offer.observed_at
            if observed is not None:
                observed=observed.replace(tzinfo=timezone.utc) if observed.tzinfo is None else observed
                if observed<=now and (latest_observed_at is None or observed>latest_observed_at):
                    latest_observed_at=observed
        real=[o for o in eligible if is_current_real_offer(o, now)]
        if not real:
            if any(o.observed_at and not is_recent_observation(o.observed_at, now)
                   and (o.observed_at.replace(tzinfo=timezone.utc) if o.observed_at.tzinfo is None else o.observed_at)<=now
                   for o in eligible):
                expired_count+=1
            continue
        best=min(real,key=lambda o:o.price_sek)
        fact=fact_rows_by_variant.get(v.id)
        try: facts=[str(x) for x in json.loads(fact.facts_json or "[]") if x] if fact else []
        except Exception: facts=[]
        observed=best.observed_at.replace(tzinfo=timezone.utc) if best.observed_at.tzinfo is None else best.observed_at
        age_days=max(0,(now-observed).days)
        explanation=explain_variant(db,v,facts_override=facts,selected_price=best.price_sek)
        chase_profile=profile_from_row(profiles_by_variant.get(v.id))
        content_rating=content_summary(chase_profile)
        ladder=chase_ladder(chase_profile)
        coverage=chase_coverage(chase_profile)
        pull=pull_profile(chase_profile)
        rows.append({
            "id":v.id,
            "slug":v.product.slug,
            "name":v.product.canonical_name,
            "category":v.product.category,
            "manufacturer":v.product.manufacturer,
            "format":v.format,
            "price":best.price_sek,
            "store":best.store.name,
            "url":best.url,
            "packs":v.packs,
            "cards_per_pack":v.cards_per_pack,
            "total_cards":total_sealed_cards(v),
            "observed_at":best.observed_at.isoformat() if best.observed_at else None,
            "age_days":age_days,
            "freshness":"fresh" if age_days is not None and age_days<=14 else "stale",
            "source_kind":best.source_kind,
            "facts":facts,
            "explanation":explanation,
            "chase_profile":chase_profile,
            "content_rating":content_rating,
            "chase_ladder":ladder,
            "chase_coverage":coverage,
            "pull_profile":pull,
            "fact_source_url":fact.source_url if fact else None,
            "data_scope":"Verifierat butikserbjudande. Ingen Box Value/EV-poäng utan separat analysunderlag.",
        })
    rows.sort(key=lambda x:(0 if x["chase_coverage"]["status"]=="card_level" else 1 if x["chase_coverage"]["status"]=="product_level" else 2,-(x["content_rating"]["score"] or -1),x["price"],x["name"],x["id"]))
    return {
        "searched_at":datetime.now(timezone.utc).isoformat(),
        "count":len(rows),
        "offset":offset,
        "has_more":offset+limit<len(rows),
        "expired_count":expired_count,
        "latest_observed_at":latest_observed_at.isoformat() if latest_observed_at else None,
        "q":q,
        "category":category,
        "budget":budget,
        "format":format,
        "store_name":store_name,
        "products":rows[offset:offset+limit],
        "note":"Detta är verifierade svenska butikssnapshots, inte live-feed. Tidsstämpeln visas per produkt och uppdateras inte förrän källan verifieras igen.",
    }
