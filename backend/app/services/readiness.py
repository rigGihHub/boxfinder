from datetime import datetime, timedelta
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from ..models import Checklist, Card, CardMarketValue, Odds, Offer, PriceHistory, ProductVariant

def ranking_readiness(db: Session, variant: ProductVariant) -> dict:
    checklist = db.execute(select(Checklist).where(Checklist.variant_id == variant.id)).scalar_one_or_none()
    card_ids = []
    if checklist:
        card_ids = list(db.execute(select(Card.id).where(Card.checklist_id == checklist.id)).scalars())
    total_cards = len(card_ids)
    odds_count = 0
    values_count = 0
    if card_ids:
        odds_count = len(set(db.execute(select(Odds.card_id).where(
            Odds.card_id.in_(card_ids), Odds.probability_per_box.is_not(None), Odds.basis != "unknown"
        )).scalars()))
        values_count = len(set(db.execute(select(CardMarketValue.card_id).where(
            CardMarketValue.card_id.in_(card_ids), CardMarketValue.condition_bucket == "raw",
            CardMarketValue.median_90d_sek.is_not(None)
        )).scalars()))
    return _readiness(variant, checklist, total_cards, odds_count, values_count, datetime.utcnow())


def ranking_readiness_many(db: Session, variants: list[ProductVariant]) -> dict[int, dict]:
    """Catalogue readiness in four queries, without loading every card/odd row."""
    if not variants:
        return {}
    checklists = {c.variant_id: c for c in db.scalars(
        select(Checklist).where(Checklist.variant_id.in_([v.id for v in variants])))}
    ids = [c.id for c in checklists.values()]
    totals = odds = values = {}
    if ids:
        totals = dict(db.execute(select(Card.checklist_id, func.count(Card.id))
            .where(Card.checklist_id.in_(ids)).group_by(Card.checklist_id)).all())
        odds = dict(db.execute(select(Card.checklist_id, func.count(func.distinct(Card.id)))
            .join(Odds, Odds.card_id == Card.id)
            .where(Card.checklist_id.in_(ids), Odds.probability_per_box.is_not(None), Odds.basis != "unknown")
            .group_by(Card.checklist_id)).all())
        values = dict(db.execute(select(Card.checklist_id, func.count(func.distinct(Card.id)))
            .join(CardMarketValue, CardMarketValue.card_id == Card.id)
            .where(Card.checklist_id.in_(ids), CardMarketValue.condition_bucket == "raw",
                   CardMarketValue.median_90d_sek.is_not(None))
            .group_by(Card.checklist_id)).all())
    now = datetime.utcnow()
    result = {}
    for variant in variants:
        checklist = checklists.get(variant.id)
        cid = checklist.id if checklist else None
        result[variant.id] = _readiness(variant, checklist, totals.get(cid, 0),
                                      odds.get(cid, 0), values.get(cid, 0), now)
    return result


def _readiness(variant, checklist, total_cards, odds_count, values_count, now):
    active = [o for o in variant.offers if o.stock_status == "in_stock" and not o.is_preorder and o.match_status == "auto_matched"]
    fresh = [o for o in active if o.observed_at and o.observed_at >= now - timedelta(days=7)]
    stores = len({o.store_id for o in fresh})
    offer_score = 100 if stores >= 3 else 75 if stores == 2 else 45 if stores == 1 else 0
    checklist_score = 0
    if checklist:
        verified = checklist.verification_status in {"verified", "approved"}
        checklist_score = min(100, int(checklist.confidence * (1.0 if verified else .7)))
    odds_score = round(100 * odds_count / total_cards) if total_cards else 0
    values_score = round(100 * values_count / total_cards) if total_cards else 0

    analysis_score = variant.analysis.data_quality if variant.analysis else 0
    score = round(.22*offer_score + .23*checklist_score + .20*odds_score + .20*values_score + .15*analysis_score)

    blockers=[]
    if stores == 0: blockers.append("Inget färskt, säkert matchat butikserbjudande")
    if not checklist: blockers.append("Checklista saknas")
    elif checklist_score < 60: blockers.append("Checklistan är inte tillräckligt verifierad")
    if odds_score < 35: blockers.append("För låg oddstäckning")
    if values_score < 35: blockers.append("För låg täckning av raw-marknadsvärden")

    if score >= 75 and not blockers:
        status="ready"; label="Redo"
    elif score >= 45:
        status="almost_ready"; label="Nästan redo"
    else:
        status="insufficient"; label="För lite data"

    return {
        "status":status, "label":label, "score":score, "blockers":blockers,
        "components":{
            "store_coverage":offer_score, "fresh_stores":stores,
            "checklist":checklist_score, "odds_coverage":odds_score,
            "raw_value_coverage":values_score, "analysis_quality":analysis_score,
            "cards":total_cards
        }
    }
