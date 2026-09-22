from __future__ import annotations
from datetime import datetime, timedelta
from collections import defaultdict
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import CatalogCandidate, Offer, ProductVariant, Store
from .source_hub import SOURCE_PROFILES

TRUSTED_MATCH = {"auto_matched", "manual_matched"}
FRESH_DAYS = 14

def _store_metrics(db: Session, store: Store, now: datetime) -> dict:
    offers = db.scalars(select(Offer).where(Offer.store_id == store.id)).all()
    candidates = db.scalars(select(CatalogCandidate).where(CatalogCandidate.store_id == store.id)).all()
    live = [o for o in offers if o.source_kind != "demo"]
    trusted = [o for o in live if o.match_status in TRUSTED_MATCH and o.variant_id is not None]
    fresh = [
        o for o in trusted
        if o.observed_at is not None
        and o.observed_at >= now - timedelta(days=FRESH_DAYS)
        and o.stock_status == "in_stock"
        and not o.is_preorder
    ]
    stale = [o for o in trusted if o.observed_at is None or o.observed_at < now - timedelta(days=FRESH_DAYS)]
    profile = SOURCE_PROFILES.get(store.name, {"priority": 3, "coverage": []})

    policy_ok = store.policy_status in {"approved","automatic_allowed","robots_checked","feed_allowed","api_allowed","manual_allowed"}
    automatic_ok = store.policy_status in {"approved","automatic_allowed","robots_checked","feed_allowed","api_allowed"}
    adapter_ready = bool(store.adapter_key) or store.collection_method in {"manual","csv","feed","api"}
    recent_success = bool(store.last_success_at and store.last_success_at >= now - timedelta(days=7))

    score = 0
    score += 25 if policy_ok else 0
    score += 20 if adapter_ready else 0
    score += 20 if recent_success else 0
    score += 20 if fresh else 0
    score += 10 if trusted else 0
    score += 5 if candidates else 0

    blockers=[]
    if not policy_ok: blockers.append("policy")
    if not adapter_ready: blockers.append("adapter/feed")
    if not store.last_success_at: blockers.append("aldrig lyckad körning")
    elif not recent_success: blockers.append("ingen lyckad körning senaste 7 dagarna")
    if not trusted: blockers.append("inga säkert matchade produkter")
    if trusted and not fresh: blockers.append("inga färska lagerförda erbjudanden")

    return {
        "store_id": store.id,
        "name": store.name,
        "priority": profile.get("priority",3),
        "expected_coverage": profile.get("coverage",[]),
        "policy_status": store.policy_status,
        "collection_method": store.collection_method,
        "adapter_key": store.adapter_key,
        "automatic_allowed": automatic_ok,
        "readiness_score": score,
        "offers_total": len(live),
        "trusted_offers": len(trusted),
        "fresh_in_stock_offers": len(fresh),
        "stale_trusted_offers": len(stale),
        "catalog_candidates": len(candidates),
        "last_success_at": store.last_success_at.isoformat() if store.last_success_at else None,
        "blockers": blockers,
    }

def _category_coverage(db: Session, stores: list[Store], now: datetime) -> list[dict]:
    expected=defaultdict(set)
    for s in stores:
        profile=SOURCE_PROFILES.get(s.name,{})
        for category in profile.get("coverage",[]):
            expected[category].add(s.name)

    fresh_offers = db.scalars(
        select(Offer)
        .where(Offer.variant_id.is_not(None))
        .where(Offer.match_status.in_(TRUSTED_MATCH))
        .where(Offer.source_kind != "demo")
        .where(Offer.observed_at.is_not(None))
        .where(Offer.observed_at >= now - timedelta(days=FRESH_DAYS))
        .where(Offer.stock_status == "in_stock")
        .where(Offer.is_preorder.is_(False))
    ).all()

    actual_variants=defaultdict(set)
    actual_stores=defaultdict(set)
    for offer in fresh_offers:
        v=db.get(ProductVariant,offer.variant_id)
        if not v: continue
        category=v.product.category
        actual_variants[category].add(v.id)
        store=db.get(Store,offer.store_id)
        if store: actual_stores[category].add(store.name)

    categories=sorted(set(expected)|set(actual_variants))
    rows=[]
    for c in categories:
        exp=len(expected[c])
        active=len(actual_stores[c])
        rows.append({
            "category":c,
            "expected_source_count":exp,
            "active_source_count":active,
            "fresh_variant_count":len(actual_variants[c]),
            "expected_sources":sorted(expected[c]),
            "active_sources":sorted(actual_stores[c]),
            "source_coverage_pct": round(active/exp*100) if exp else (100 if active else 0),
        })
    return sorted(rows,key=lambda x:(x["source_coverage_pct"],-x["expected_source_count"],x["category"]))

def coverage_report(db: Session, now: datetime | None=None) -> dict:
    now=now or datetime.utcnow()
    stores=db.scalars(select(Store).where(Store.collection_method != "demo").order_by(Store.name)).all()
    store_rows=[_store_metrics(db,s,now) for s in stores]
    categories=_category_coverage(db,stores,now)

    p1=[x for x in store_rows if x["priority"]==1]
    p1_ready=[x for x in p1 if x["readiness_score"]>=70 and x["fresh_in_stock_offers"]>0]
    total_fresh=sum(x["fresh_in_stock_offers"] for x in store_rows)
    total_trusted=sum(x["trusted_offers"] for x in store_rows)

    next_actions=[]
    for x in sorted(store_rows,key=lambda r:(r["priority"], r["readiness_score"], r["name"])):
        if len(next_actions)>=8: break
        if x["readiness_score"]>=85 and x["fresh_in_stock_offers"]>0:
            continue
        if "policy" in x["blockers"]:
            action="Granska policy/feed/API innan automatisk insamling"
        elif "adapter/feed" in x["blockers"]:
            action="Konfigurera feed/API/CSV-adapter"
        elif "aldrig lyckad körning" in x["blockers"]:
            action="Kör första verifierade importen"
        elif "inga säkert matchade produkter" in x["blockers"]:
            action="Matcha katalogkandidater mot kanoniska produkter"
        elif "inga färska lagerförda erbjudanden" in x["blockers"]:
            action="Uppdatera pris och lager"
        else:
            action="Öka katalogtäckningen"
        next_actions.append({
            "store_id":x["store_id"],"store":x["name"],"priority":x["priority"],
            "readiness_score":x["readiness_score"],"action":action,"blockers":x["blockers"],
        })

    weak_categories=[x for x in categories if x["expected_source_count"]>0 and x["source_coverage_pct"]<50]

    return {
        "generated_at":now.isoformat(),
        "freshness_days":FRESH_DAYS,
        "summary":{
            "stores":len(store_rows),
            "priority_1_stores":len(p1),
            "priority_1_ready":len(p1_ready),
            "trusted_offers":total_trusted,
            "fresh_in_stock_offers":total_fresh,
            "categories_with_expected_sources":sum(1 for x in categories if x["expected_source_count"]>0),
            "weak_categories":len(weak_categories),
        },
        "stores":store_rows,
        "categories":categories,
        "next_actions":next_actions,
    }
