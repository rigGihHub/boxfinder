from __future__ import annotations
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..models import Card, Checklist, ProductVariant
from .product_detail import chase_cards

GOALS = {"balanced", "autographs", "rookies", "jackpot", "hits", "fun"}

def clamp(v, lo=0, hi=100):
    return max(lo, min(v, hi))

def n(v, fallback=0):
    return fallback if v is None else v

def ten(v):
    return round(clamp(n(v)) / 10, 1)

def checklist_traits(db: Session, variant_id: int) -> dict:
    checklist = db.scalar(select(Checklist).where(Checklist.variant_id == variant_id))
    if not checklist:
        return {"available": False, "card_count": 0, "autographs": 0, "rookies": 0, "case_hits": 0, "memorabilia": 0}
    cards = db.scalars(select(Card).where(Card.checklist_id == checklist.id)).all()
    return {
        "available": bool(cards),
        "card_count": len(cards),
        "autographs": sum(1 for c in cards if c.is_autograph),
        "rookies": sum(1 for c in cards if c.is_rookie),
        "case_hits": sum(1 for c in cards if c.is_case_hit),
        "memorabilia": sum(1 for c in cards if c.is_memorabilia),
        "confidence": checklist.confidence,
        "verification_status": checklist.verification_status,
    }

def box_quality_score(item: dict) -> int | None:
    metrics = [item.get(k) for k in ("checklist_strength","hit_density","upside","floor_score","rookie_strength")]
    present = [v for v in metrics if v is not None]
    if len(present) < 2:
        return None
    weights = {
        "checklist_strength": .22, "hit_density": .23, "upside": .20,
        "floor_score": .15, "rookie_strength": .12, "popularity": .08,
    }
    weighted = [(item.get(k), w) for k,w in weights.items() if item.get(k) is not None]
    return round(sum(v*w for v,w in weighted) / sum(w for _,w in weighted))

def price_score(item: dict) -> int | None:
    median = item.get("market_median")
    price = item.get("price")
    if not median or not price or median <= 0:
        return None
    discount = (median-price)/median*100
    # 0% discount = 50, 25% under median = 100, 25% over = 0.
    return round(clamp(50 + discount*2))

def autograph_score(traits: dict) -> int | None:
    if not traits.get("available"):
        return None
    count = traits.get("autographs",0)
    return 20 if count == 0 else round(clamp(55 + min(count,6)*7.5))

def goal_score(item: dict, traits: dict, goal: str) -> int | None:
    q=box_quality_score(item)
    p=price_score(item)
    data=n(item.get("data_quality"))
    auto=autograph_score(traits)
    components = {
        "balanced": [(q,.38),(p,.22),(item.get("hit_density"),.15),(item.get("floor_score"),.10),(data,.15)],
        "autographs": [(auto,.48),(item.get("hit_density"),.15),(item.get("upside"),.12),(p,.10),(data,.15)],
        "rookies": [(item.get("rookie_strength"),.46),(q,.18),(p,.14),(item.get("hit_density"),.10),(data,.12)],
        "jackpot": [(item.get("upside"),.48),(q,.15),(p,.12),(item.get("popularity"),.10),(data,.15)],
        "hits": [(item.get("hit_density"),.50),(item.get("floor_score"),.16),(q,.12),(p,.10),(data,.12)],
        "fun": [(item.get("hit_density"),.25),(item.get("checklist_strength"),.22),(item.get("popularity"),.18),(item.get("upside"),.15),(p,.08),(data,.12)],
    }[goal]
    usable=[(v,w) for v,w in components if v is not None]
    if len(usable)<2:
        return None
    return round(sum(v*w for v,w in usable)/sum(w for _,w in usable))

def confidence(item: dict, traits: dict) -> int:
    score=n(item.get("data_quality"))*.60
    if traits.get("available"): score += 20
    known=sum(item.get(k) is not None for k in ("hit_density","upside","floor_score","rookie_strength","checklist_strength"))
    score += min(20,known*4)
    return round(clamp(score))

def exciting_reasons(item: dict, traits: dict) -> list[str]:
    reasons=[]
    if item.get("rookie_strength") is not None and item["rookie_strength"]>=75:
        reasons.append("Stark rookieprofil i analysen")
    if item.get("hit_density") is not None and item["hit_density"]>=75:
        reasons.append("Hög hitfrekvens jämfört med andra analyserade boxar")
    if item.get("upside") is not None and item["upside"]>=80:
        reasons.append("Hög jackpotpotential")
    if traits.get("autographs",0)>0:
        reasons.append(f"{traits['autographs']} autografkort identifierade i checklistan")
    if traits.get("case_hits",0)>0:
        reasons.append(f"{traits['case_hits']} case-hit-kort identifierade")
    if traits.get("memorabilia",0)>0:
        reasons.append(f"{traits['memorabilia']} memorabilia-kort identifierade")
    if item.get("discount_pct") is not None and item["discount_pct"]>=10:
        reasons.append(f"{item['discount_pct']} % under samtidig butiksmedian")
    return reasons[:4]

def opening_profile(item: dict, traits: dict) -> dict:
    auto=autograph_score(traits)
    return {
        "jackpot": ten(item.get("upside")) if item.get("upside") is not None else None,
        "hit_frequency": ten(item.get("hit_density")) if item.get("hit_density") is not None else None,
        "rookies": ten(item.get("rookie_strength")) if item.get("rookie_strength") is not None else None,
        "variety": ten(item.get("checklist_strength")) if item.get("checklist_strength") is not None else None,
        "autographs": ten(auto) if auto is not None else None,
        "risk": round(clamp(100-n(item.get("floor_score"),50))/10,1) if item.get("floor_score") is not None else None,
    }

def decorate(db: Session, item: dict, goal: str) -> dict:
    traits=checklist_traits(db,item["id"])
    chases,_=chase_cards(db,item["id"],5)
    return {
        **item,
        "goal":goal,
        "discovery_score":goal_score(item,traits,goal),
        "box_score":box_quality_score(item),
        "price_score":price_score(item),
        "discovery_confidence":confidence(item,traits),
        "opening_profile":opening_profile(item,traits),
        "traits":traits,
        "why_exciting":exciting_reasons(item,traits),
        "chase_cards":[{
            "name":c.get("subject"),"parallel":c.get("parallel"),"outcome":c.get("outcome"),
            "market_value_raw":c.get("raw_value_sek"),"probability_per_box":c.get("probability_per_box"),
            "is_autograph":c.get("is_autograph"),"is_rookie":c.get("is_rookie"),"is_case_hit":c.get("is_case_hit"),
        } for c in chases if c.get("subject")],
    }

def role_score(x: dict, role: str) -> float:
    if role=="pick":
        return (x.get("discovery_score") or 0)*.78 + x.get("discovery_confidence",0)*.22
    if role=="safe":
        return n(x.get("floor_score"))*.35+n(x.get("hit_density"))*.25+n(x.get("price_score"))*.18+x.get("discovery_confidence",0)*.22
    return n(x.get("upside"))*.48+n(x.get("price_score"))*.12+n(x.get("popularity"))*.10+x.get("discovery_confidence",0)*.18+n(x.get("box_score"))*.12

def discover(db: Session, items: list[dict], goal: str) -> dict:
    goal=goal if goal in GOALS else "balanced"
    decorated=[decorate(db,x,goal) for x in items]
    viable=[x for x in decorated if x["discovery_score"] is not None]
    selected=[]
    roles=[("Mitt val","pick"),("Säkrare val","safe"),("Jackpotval","jackpot")]
    for label,role in roles:
        candidates=[x for x in viable if x["id"] not in {s["id"] for s in selected}]
        if not candidates: break
        best=max(candidates,key=lambda x:role_score(x,role))
        selected.append({**best,"recommendation_role":label})
    return {
        "goal":goal,
        "count":len(selected),
        "recommendations":selected,
        "considered":len(items),
        "rankable":len(viable),
        "note":"Rekommendationerna bygger bara på data BoxFinder faktiskt har. Saknade odds, checklistor eller marknadspriser visas som saknade och gissas inte.",
    }
