from __future__ import annotations
import json
from statistics import median
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Offer, ProductFact, ProductVariant

TRUSTED_MATCH={"auto_matched","manual_matched"}

def _facts(db: Session, variant_id: int) -> list[str]:
    row=db.scalar(select(ProductFact).where(ProductFact.variant_id==variant_id))
    if not row:
        return []
    try:
        data=json.loads(row.facts_json or "[]")
        return [str(x) for x in data if x]
    except Exception:
        return []

def _appeal_reasons(v: ProductVariant, facts: list[str], price: float | None) -> list[str]:
    reasons=[]
    lower=" ".join(facts).lower()
    if "autograf" in lower or "autograph" in lower:
        reasons.append("Bra för dig som jagar autografer: verifierat innehåll nämner autografträffar.")
    if "young guns" in lower:
        reasons.append("Intressant för rookie-jakt: verifierat innehåll nämner Young Guns.")
    if "numrer" in lower or "numbered" in lower or "/25" in lower or "/10" in lower or "1/1" in lower:
        reasons.append("Har verifierad chans till numrerade eller extra sällsynta parallels.")
    if "promo" in lower:
        reasons.append("Ger extra samlarvärde direkt genom verifierade promo-kort.")
    if "insert" in lower or "dazzlers" in lower or "canvas" in lower:
        reasons.append("Bra öppningsvariation: verifierat innehåll innehåller inserts/parallels utöver basen.")
    if v.packs and v.packs>=18:
        reasons.append(f"Många öppningar i samma köp: {v.packs} pack i produkten.")
    elif v.packs and v.packs>=6:
        reasons.append(f"Ger {v.packs} pack, vilket ger mer öppning än enstaka premiumprodukter.")
    if v.cards_per_pack and v.packs:
        total=v.cards_per_pack*v.packs
        if total>=100:
            reasons.append(f"Hög kortmängd: cirka {total} kort totalt enligt verifierad förpackningsdata.")
    if price is not None and price<=400:
        reasons.append("Låg ingångskostnad jämfört med hobbyboxar i samma katalog.")
    if not reasons and facts:
        reasons.append("Produkten har verifierat förpackningsinnehåll och kan jämföras utan att BoxFinder behöver gissa.")
    return reasons[:4]

def explain_variant(db: Session, v: ProductVariant) -> dict:
    facts=_facts(db,v.id)
    eligible=[
        o for o in v.offers
        if o.stock_status=="in_stock" and not o.is_preorder
        and (o.match_status in TRUSTED_MATCH or o.source_kind=="verified_snapshot")
    ]
    prices=[float(o.price_sek) for o in eligible if o.price_sek and o.price_sek>0]
    best=min(prices) if prices else None
    market_median=median(prices) if len(prices)>=2 else None
    discount_pct=None
    if best is not None and market_median:
        discount_pct=round((market_median-best)/market_median*100)

    reasons=_appeal_reasons(v,facts,best)

    if market_median is None:
        deal={
            "status":"not_verified",
            "label":"Fyndstatus ej verifierad",
            "reason":"BoxFinder har ännu inte minst två jämförbara aktuella butikspriser för den här produkten.",
            "discount_pct":None,
        }
    elif discount_pct>=15:
        deal={
            "status":"strong",
            "label":"Starkt pris",
            "reason":f"Bästa priset ligger cirka {discount_pct}% under medianen för aktuella jämförbara erbjudanden.",
            "discount_pct":discount_pct,
        }
    elif discount_pct>=7:
        deal={
            "status":"interesting",
            "label":"Intressant pris",
            "reason":f"Bästa priset ligger cirka {discount_pct}% under medianen för aktuella jämförbara erbjudanden.",
            "discount_pct":discount_pct,
        }
    else:
        deal={
            "status":"normal",
            "label":"Normalt pris",
            "reason":"Priset avviker inte tillräckligt från aktuella jämförbara erbjudanden för att kallas fynd.",
            "discount_pct":discount_pct,
        }

    if facts:
        evidence="Verifierade produktfakta finns."
    else:
        evidence="Pris, lager och format kan vara verifierade, men detaljerat boxinnehåll saknas ännu."

    return {
        "why_good":reasons,
        "deal":deal,
        "facts":facts,
        "evidence_note":evidence,
        "price_per_pack_sek":round(best/v.packs,2) if best is not None and v.packs else None,
    }
