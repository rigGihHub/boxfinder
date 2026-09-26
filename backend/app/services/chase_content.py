import json
import re
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..models import ChaseProfile, ProductVariant

WEIGHTS={"everyday":0.20,"good":0.28,"big":0.32,"jackpot":0.20}

def get_profile(db: Session, variant_id: int):
    row=db.scalar(select(ChaseProfile).where(ChaseProfile.variant_id==variant_id))
    return profile_from_row(row)

def profile_from_row(row: ChaseProfile | None):
    if not row: return None
    try: data=json.loads(row.content_json)
    except Exception: return None
    data["source_name"]=row.source_name
    data["source_url"]=row.source_url
    data["confidence"]=row.confidence
    data["verified_at"]=row.verified_at.isoformat()
    return data

def content_score(profile: dict | None):
    if not profile: return None
    tiers=profile.get("tiers",{})
    # Score measures richness/frequency of attractive content, not financial return.
    parts={}
    for key in WEIGHTS:
        tier=tiers.get(key,{})
        parts[key]=float(tier.get("score",0))
    score=sum(parts[k]*WEIGHTS[k] for k in WEIGHTS)
    depth=min(8,len(profile.get("key_names",[])))*0.75
    tiers=profile.get("tiers",{})
    repeatable=min(5,len(tiers.get("everyday",{}).get("items",[])))*0.8
    return round(min(100,score+depth+repeatable))

def content_summary(profile):
    if not profile: return {"score":None,"label":"Innehåll ej kartlagt","reasons":[]}
    score=content_score(profile)
    if score>=80: label="Exceptionellt chase-innehåll"
    elif score>=65: label="Starkt chase-innehåll"
    elif score>=50: label="Bra öppningsinnehåll"
    else: label="Smalare chase-profil"
    everyday=float(profile.get("tiers",{}).get("everyday",{}).get("score",0))
    jackpot=float(profile.get("tiers",{}).get("jackpot",{}).get("score",0))
    if everyday>=85: style="Hit-koncentrerad"
    elif jackpot>=90 and everyday<80: style="Jackpot-tung"
    elif everyday>=72 and jackpot>=70: style="Balanserad chase"
    else: style="Chase-beroende"
    return {"score":score,"label":label,"style":style,"reasons":profile.get("why_exciting",[])[:4]}


TIER_ORDER={"BRA":1,"MYCKET BRA":2,"MONSTER":3,"JACKPOT":4}

def has_actionable_odds(profile: dict | None) -> bool:
    """True only for a published ratio or explicit guarantee.

    Text that merely says odds are not published must never improve evidence grade.
    """
    if not profile:
        return False
    for card in profile.get("headline_chases",[]):
        odds=(card.get("odds") or "").lower()
        if not odds:
            continue
        negated_guarantee = any(phrase in odds for phrase in (
            "inte garanter", "ej garanter", "not guaranteed", "no guarantee", "saknar garanti",
        ))
        if not negated_guarantee and ("garanter" in odds or "guaranteed" in odds):
            return True
        # A serial number such as 1/1 or /25 describes card scarcity, not the
        # probability of pulling it. Only explicit ratio notation (1:120) is
        # actionable evidence for the ranking grade.
        if re.search(r"\b1\s*:\s*[\d ]+", odds):
            return True
    return False

def format_hits(profile: dict | None, product_format: str | None) -> list[dict]:
    """Return only source-checked, explicitly scoped format observations.

    An average box hit is not a card-specific probability or a pack guarantee.
    Legacy prose in headline cards is deliberately not parsed into guarantees.
    """
    if not profile or not product_format:
        return []
    return [fact for fact in profile.get("format_hits", [])
            if isinstance(fact, dict)
            and fact.get("format") == product_format
            and fact.get("basis") in {"guaranteed", "average"}
            and fact.get("quality") in {"premium", "collectible", "base"}
            and isinstance(fact.get("count"), (int, float))
            and not isinstance(fact.get("count"), bool)
            and fact["count"] > 0
            and fact.get("family")]

def chase_ladder(profile: dict | None):
    if not profile: return []
    cards=profile.get("headline_chases",[])
    return sorted(cards,key=lambda x:(TIER_ORDER.get(x.get("tier",""),99),x.get("card","")))

def chase_coverage(profile: dict | None):
    if not profile:
        return {"status":"unmapped","headline_cards":0,"has_odds":False}
    cards=profile.get("headline_chases",[])
    return {
        "status":"card_level" if cards else "product_level",
        "headline_cards":len(cards),
        "has_odds":has_actionable_odds(profile),
    }


def pull_profile(profile: dict | None):
    """Collector-facing shape: separates repeatable fun from ceiling. Not monetary EV."""
    if not profile:
        return {"repeatable":None,"ceiling":None,"variance":None,"label":"Ej kartlagt"}
    tiers=profile.get("tiers",{})
    everyday=float(tiers.get("everyday",{}).get("score",0))
    good=float(tiers.get("good",{}).get("score",0))
    big=float(tiers.get("big",{}).get("score",0))
    jackpot=float(tiers.get("jackpot",{}).get("score",0))
    repeatable=round(0.6*everyday+0.4*good)
    ceiling=round(0.45*big+0.55*jackpot)
    variance=max(0,min(100,round(50+(ceiling-repeatable)*1.35)))
    if repeatable>=82 and ceiling>=82: label="Mycket kul + högt tak"
    elif repeatable>=78: label="Många bra chanser"
    elif ceiling>=88: label="Jackpotjakt"
    elif repeatable>=65 and ceiling>=65: label="Balanserad öppning"
    else: label="Smalare chase"
    return {"repeatable":repeatable,"ceiling":ceiling,"variance":variance,"label":label}
