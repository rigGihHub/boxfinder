from __future__ import annotations
from dataclasses import dataclass
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..models import BoxAnalysis, Card, CardMarketValue, Checklist, Odds
from .market_values import preferred_value

BASIS_WEIGHT = {"official": 1.0, "derived": .85, "estimated": .55, "unknown": 0.0, "demo": 0.0}

@dataclass
class EVResult:
    ev_low: float | None
    ev_high: float | None
    cards_total: int
    cards_with_values: int
    cards_with_usable_odds: int
    cards_in_ev: int
    value_coverage_pct: int
    odds_coverage_pct: int
    ev_coverage_pct: int
    data_quality: int
    notes: list[str]


def _best_odds(items: list[Odds]) -> Odds | None:
    usable = [o for o in items if o.probability_per_box is not None and o.probability_per_box >= 0 and BASIS_WEIGHT.get(o.basis, 0) > 0]
    if not usable:
        return None
    return max(usable, key=lambda o: BASIS_WEIGHT.get(o.basis, 0) * (o.confidence / 100))


def calculate_variant_ev(db: Session, variant_id: int, condition_bucket: str = "raw") -> EVResult:
    cl = db.scalar(select(Checklist).where(Checklist.variant_id == variant_id))
    if not cl:
        return EVResult(None, None, 0, 0, 0, 0, 0, 0, 0, 0, ["Checklist saknas."])
    cards = db.scalars(select(Card).where(Card.checklist_id == cl.id)).all()
    if not cards:
        return EVResult(None, None, 0, 0, 0, 0, 0, 0, 0, 0, ["Checklistan saknar kort."])
    ids = [c.id for c in cards]
    market = db.scalars(select(CardMarketValue).where(CardMarketValue.card_id.in_(ids), CardMarketValue.condition_bucket == condition_bucket)).all()
    market_by_card = {m.card_id: m for m in market}
    odds = db.scalars(select(Odds).where(Odds.variant_id == variant_id, Odds.card_id.is_not(None))).all()
    odds_by_card: dict[int, list[Odds]] = {}
    for o in odds:
        odds_by_card.setdefault(o.card_id, []).append(o)

    low_sum = high_sum = 0.0
    with_value = with_odds = used = 0
    quality_parts = []
    for c in cards:
        mv = market_by_card.get(c.id)
        value = preferred_value(mv) if mv else None
        if value is not None and value > 0:
            with_value += 1
        best = _best_odds(odds_by_card.get(c.id, []))
        if best:
            with_odds += 1
        if not mv or value is None or value <= 0 or not best:
            continue
        p = min(max(best.probability_per_box or 0, 0), 1)
        # The interval deliberately uses observed 90d range where available, otherwise a conservative band around the preferred value.
        low_value = mv.low_90d_sek if mv.low_90d_sek and mv.sales_90d >= 3 else value * .85
        high_value = mv.high_90d_sek if mv.high_90d_sek and mv.sales_90d >= 3 else value * 1.15
        low_sum += p * max(0, low_value)
        high_sum += p * max(0, high_value)
        used += 1
        odds_quality = best.confidence * BASIS_WEIGHT.get(best.basis, 0)
        quality_parts.append((mv.data_quality + odds_quality) / 2)

    total = len(cards)
    value_cov = round(with_value / total * 100)
    odds_cov = round(with_odds / total * 100)
    ev_cov = round(used / total * 100)
    evidence_quality = round(sum(quality_parts) / len(quality_parts)) if quality_parts else 0
    data_quality = round(.55 * evidence_quality + .25 * ev_cov + .20 * min(cl.confidence, 100)) if used else 0
    notes = []
    if ev_cov < 25: notes.append("EV-täckningen är låg; intervallet ska inte tolkas som hela boxens ekonomiska värde.")
    if with_odds < total: notes.append("Kort utan verifierbar/härledd sannolikhet bidrar inte till EV.")
    if with_value < total: notes.append("Kort utan användbar försäljningsdata bidrar inte till EV.")
    if used: notes.append("EV bygger på faktiskt sålda kort och raw-värde som standard.")
    return EVResult(
        round(low_sum, 2) if used else None,
        round(high_sum, 2) if used else None,
        total, with_value, with_odds, used, value_cov, odds_cov, ev_cov, min(100, data_quality), notes,
    )


def update_box_analysis_ev(db: Session, variant_id: int, condition_bucket: str = "raw") -> tuple[BoxAnalysis, EVResult]:
    result = calculate_variant_ev(db, variant_id, condition_bucket)
    analysis = db.scalar(select(BoxAnalysis).where(BoxAnalysis.variant_id == variant_id))
    if not analysis:
        analysis = BoxAnalysis(variant_id=variant_id, data_quality=0)
        db.add(analysis)
    analysis.ev_low = result.ev_low
    analysis.ev_high = result.ev_high
    analysis.data_quality = result.data_quality
    analysis.probability_basis = "mixed_verified" if result.cards_in_ev else "unknown"
    db.flush()
    return analysis, result
