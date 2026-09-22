from __future__ import annotations
from collections import defaultdict
from datetime import datetime, timedelta
from statistics import median
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..models import Card, CardMarketValue, Checklist, Odds, Offer, PriceHistory, ProductVariant
from .checklists import classify_outcome
from .market_values import preferred_value

USABLE_BASIS = {"official", "derived", "estimated"}


def _best_odds(odds: list[Odds]) -> Odds | None:
    usable = [o for o in odds if o.basis in USABLE_BASIS and o.probability_per_box is not None]
    if not usable:
        return None
    basis_rank = {"official": 3, "derived": 2, "estimated": 1}
    return max(usable, key=lambda o: (basis_rank.get(o.basis, 0), o.confidence))


def price_history_summary(db: Session, variant: ProductVariant, now: datetime | None = None) -> dict:
    now = now or datetime.utcnow()
    offer_ids = [o.id for o in variant.offers]
    if not offer_ids:
        return {"points": [], "windows": {}}
    rows = db.scalars(select(PriceHistory).where(PriceHistory.offer_id.in_(offer_ids)).order_by(PriceHistory.observed_at)).all()
    points = [{"date": r.observed_at.date().isoformat(), "price_sek": round(r.price_sek, 2), "stock_status": r.stock_status} for r in rows]
    windows = {}
    for days, key in [(30, "30d"), (90, "90d"), (365, "1y")]:
        vals = [r.price_sek for r in rows if r.observed_at >= now - timedelta(days=days) and r.price_sek > 0]
        windows[key] = {
            "observations": len(vals),
            "low": round(min(vals), 2) if vals else None,
            "high": round(max(vals), 2) if vals else None,
            "median": round(median(vals), 2) if vals else None,
        }
    return {"points": points[-120:], "windows": windows}


def chase_cards(db: Session, variant_id: int, limit: int = 25) -> tuple[list[dict], dict]:
    cl = db.scalar(select(Checklist).where(Checklist.variant_id == variant_id))
    if not cl:
        return [], {"status": "missing", "confidence": 0, "verification_status": None, "card_count": 0}
    cards = db.scalars(select(Card).where(Card.checklist_id == cl.id)).all()
    if not cards:
        return [], {"status": "empty", "confidence": cl.confidence, "verification_status": cl.verification_status, "card_count": 0}
    ids = [c.id for c in cards]
    values = db.scalars(select(CardMarketValue).where(CardMarketValue.card_id.in_(ids), CardMarketValue.condition_bucket == "raw")).all()
    value_by = {v.card_id: v for v in values}
    odds_rows = db.scalars(select(Odds).where(Odds.variant_id == variant_id, Odds.card_id.is_not(None))).all()
    odds_by: dict[int, list[Odds]] = defaultdict(list)
    for o in odds_rows:
        odds_by[o.card_id].append(o)

    items = []
    for c in cards:
        mv = value_by.get(c.id)
        value = preferred_value(mv) if mv else None
        odds = _best_odds(odds_by.get(c.id, []))
        outcome = classify_outcome(c)
        items.append({
            "card_id": c.id,
            "subject": c.subject,
            "card_number": c.card_number,
            "subset": c.subset,
            "parallel": c.parallel,
            "team_franchise": c.team_franchise,
            "serial_numbered_to": c.serial_numbered_to,
            "is_rookie": c.is_rookie,
            "is_autograph": c.is_autograph,
            "is_memorabilia": c.is_memorabilia,
            "is_case_hit": c.is_case_hit,
            "outcome": outcome,
            "raw_value_sek": round(value, 2) if value is not None else None,
            "market_data_quality": mv.data_quality if mv else 0,
            "sales_90d": mv.sales_90d if mv else 0,
            "probability_per_box": odds.probability_per_box if odds else None,
            "odds_basis": odds.basis if odds else "unknown",
            "odds_confidence": odds.confidence if odds else 0,
        })
    outcome_rank = {"jackpot": 4, "big_hit": 3, "good_hit": 2, "common": 1}
    items.sort(key=lambda x: (x["raw_value_sek"] is not None, x["raw_value_sek"] or 0, outcome_rank[x["outcome"]]), reverse=True)
    return items[:limit], {
        "status": "available",
        "confidence": cl.confidence,
        "verification_status": cl.verification_status,
        "source_name": cl.source_name,
        "source_type": cl.source_type,
        "card_count": len(cards),
    }


def outcome_groups(cards: list[dict]) -> dict:
    labels = {"common": "Vanligt", "good_hit": "Bra träff", "big_hit": "Stor hit", "jackpot": "Jackpot"}
    grouped = {}
    for key in ["common", "good_hit", "big_hit", "jackpot"]:
        subset = [c for c in cards if c["outcome"] == key]
        grouped[key] = {
            "label": labels[key],
            "count_in_top_list": len(subset),
            "examples": subset[:5],
        }
    return grouped


def make_summary(detail: dict) -> str:
    name = detail["name"]
    price = detail["price"]
    score = detail.get("box_value_score")
    a = detail.get("analysis") or {}
    parts = [f"{name} kostar just nu cirka {round(price)} kr hos billigaste observerade butik."]
    if score is not None:
        parts.append(f"Box Value Score är {score}/100.")
    if detail.get("discount_pct") is not None:
        d = detail["discount_pct"]
        if d >= 10:
            parts.append(f"Priset ligger ungefär {d}% under medianen för samtidiga erbjudanden.")
    if a.get("ev_low") is not None and a.get("ev_high") is not None:
        parts.append(f"Det beräknade EV-intervallet är {round(a['ev_low'])}–{round(a['ev_high'])} kr, men ska läsas tillsammans med datakvaliteten på {a.get('data_quality', 0)}/100.")
    if a.get("rookie_strength") is not None and a["rookie_strength"] >= 80:
        parts.append("Rookieprofilen är en tydlig styrka.")
    if a.get("hit_density") is not None and a["hit_density"] >= 80:
        parts.append("Produkten har hög hit density jämfört med övriga analyserade produkter.")
    if a.get("risk") and a["risk"] != "Okänd":
        parts.append(f"Risknivån är {a['risk'].lower()}.")
    if detail.get("source_kind") == "demo":
        parts.append("Underlaget innehåller demo-data och ska inte användas som köpbeslut innan priser, checklista och odds är verifierade.")
    return " ".join(parts)
