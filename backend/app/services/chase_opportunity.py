from __future__ import annotations
import re

TIER_WEIGHT={"BRA":1.0,"MYCKET BRA":2.0,"MONSTER":3.5,"JACKPOT":5.0}

def parse_probability(odds_text: str | None):
    """Only parse explicit numeric odds. Returns probability per pack/card event, or None."""
    if not odds_text: return None
    text=odds_text.replace(" ","")
    m=re.search(r"1:([\d,]+)",text)
    if m:
        n=int(m.group(1).replace(",",""))
        return 1/n if n>0 else None
    return None

def probability_per_box(odds_text: str | None, packs: int | None):
    p=parse_probability(odds_text)
    if p is None or not packs: return None
    # At least one occurrence across n independent packs. Approximation is explicitly labelled.
    return 1-(1-p)**packs

def opportunity_for_links(links: list[dict], packs: int | None, price: float | None):
    mapped=[]
    weighted=0.0
    probabilistic=0
    for x in links:
        pb=probability_per_box(x.get("odds"),packs)
        weight=TIER_WEIGHT.get(x.get("tier"),.5)
        if pb is not None:
            probabilistic+=1
            weighted += weight*pb
        mapped.append({**x,"probability_per_box":round(pb*100,3) if pb is not None else None})
    # Opportunity score only uses numeric, parseable odds. No fake probability for serial-only/checklist claims.
    score=None
    value_per_1000=None
    if probabilistic:
        score=round(min(100,weighted*100))
        if price and price>0:
            value_per_1000=round(weighted*1000/price*100,2)
    return {
        "cards":mapped,
        "opportunity_score":score,
        "opportunity_per_1000_sek":value_per_1000,
        "numeric_odds_routes":probabilistic,
        "mapped_routes":len(mapped),
        "basis":"Approximation from explicit per-pack numeric odds only; overlapping card families may not be independent.",
    }
