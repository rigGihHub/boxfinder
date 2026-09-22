import json
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload
from ..database import get_db
from ..models import Offer, ProductFact, ProductVariant
from .products import list_products
from ..services.discovery import GOALS, discover
from ..services.product_explanation import explain_variant
from ..services.chase_content import get_profile, content_summary, chase_ladder, chase_coverage, pull_profile

router=APIRouter(prefix="/discovery",tags=["discovery"])

@router.get("/recommendations")
def recommendations(
    category: str | None = None,
    budget: float | None = Query(None, ge=1),
    goal: str = Query("balanced"),
    db: Session = Depends(get_db),
):
    goal=goal.lower().strip()
    if goal not in GOALS:
        return {"error":"unknown_goal","allowed_goals":sorted(GOALS)}
    items=list_products(category=category,max_price=budget,db=db)
    result=discover(db,items,goal)
    result["category"]=category
    result["budget"]=budget
    return result


@router.get("/real-catalog")
def real_catalog(
    category: str | None = None,
    budget: float | None = Query(None, ge=1),
    limit: int = Query(60, ge=1, le=200),
    db: Session = Depends(get_db),
):
    q = (
        select(ProductVariant)
        .options(
            joinedload(ProductVariant.product),
            joinedload(ProductVariant.offers).joinedload(Offer.store),
        )
    )
    variants=db.execute(q).unique().scalars().all()
    rows=[]
    now=datetime.utcnow()
    for v in variants:
        real=[
            o for o in v.offers
            if o.source_kind=="verified_snapshot"
            and o.stock_status=="in_stock"
            and not o.is_preorder
        ]
        if not real:
            continue
        best=min(real,key=lambda o:o.price_sek)
        if category and v.product.category.lower()!=category.lower():
            continue
        if budget is not None and best.price_sek>budget:
            continue
        fact=db.scalar(select(ProductFact).where(ProductFact.variant_id==v.id))
        facts=[]
        if fact:
            try: facts=json.loads(fact.facts_json or "[]")
            except Exception: facts=[]
        age_days=max(0,(now-best.observed_at).days) if best.observed_at else None
        explanation=explain_variant(db,v)
        chase_profile=get_profile(db,v.id)
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
            "total_cards":v.packs*v.cards_per_pack if v.packs and v.cards_per_pack else None,
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
    rows.sort(key=lambda x:(0 if x["chase_coverage"]["status"]=="card_level" else 1 if x["chase_coverage"]["status"]=="product_level" else 2,-(x["content_rating"]["score"] or -1),x["price"],x["name"]))
    return {
        "count":len(rows),
        "category":category,
        "budget":budget,
        "products":rows[:limit],
        "note":"Detta är verifierade svenska butikssnapshots, inte live-feed. Tidsstämpeln visas per produkt och uppdateras inte förrän källan verifieras igen.",
    }
