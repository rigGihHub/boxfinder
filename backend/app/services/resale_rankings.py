from __future__ import annotations

import math

from .chase_content import content_score, has_actionable_odds, pull_profile


STRATEGIES = {"balanced", "jackpot", "frequent"}


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(value, high))


def _price_access(price: float | None) -> float:
    """A gentle price penalty; cheap packs must not automatically beat full boxes."""
    if price is None or price <= 0:
        return 0
    return clamp(100 - 18 * math.log2(max(price, 125) / 500))


def _tier_rank(tier: str | None) -> int:
    return {"BRA": 1, "MYCKET BRA": 2, "MONSTER": 3, "JACKPOT": 4}.get(tier or "", 0)


def resale_rank(item: dict, strategy: str = "balanced") -> dict:
    """Rank cross-category resale opportunity without presenting unverified profit as EV."""
    strategy = strategy if strategy in STRATEGIES else "balanced"
    profile = item.get("chase_profile")
    if not profile:
        return {
            **item,
            "resale_score": None,
            "resale_confidence": 0,
            "evidence_grade": "Ej rankbar",
            "ranking_basis": "Saknar verifierad chase-profil",
            "sellable_chases": [],
            "resale_reasons": [],
            "resale_warning": "Produkten rankas inte förrän innehåll och chase-kort har verifierats.",
        }

    pull = pull_profile(profile)
    repeatable = float(pull.get("repeatable") or 0)
    ceiling = float(pull.get("ceiling") or 0)
    richness = float(content_score(profile) or 0)
    price_access = _price_access(item.get("price"))
    data_quality = float(item.get("data_quality") or 0)
    ev_low = item.get("ev_low")
    ev_high = item.get("ev_high")
    price = item.get("price")

    cards = sorted(
        profile.get("headline_chases", []),
        key=lambda x: (_tier_rank(x.get("tier")), bool(x.get("odds"))),
        reverse=True,
    )
    has_exact = bool(cards)
    has_odds = has_actionable_odds(profile)
    profile_confidence = float(profile.get("confidence") or 0)

    if strategy == "jackpot":
        score = ceiling * .52 + richness * .20 + repeatable * .08 + price_access * .20
    elif strategy == "frequent":
        score = repeatable * .52 + richness * .20 + ceiling * .08 + price_access * .20
    else:
        score = ceiling * .32 + repeatable * .30 + richness * .18 + price_access * .20

    has_market_ev = ev_low is not None and ev_high is not None and price and price > 0
    if has_market_ev:
        ev_ratio = ((float(ev_low) + float(ev_high)) / 2) / float(price)
        ev_signal = clamp(ev_ratio / 1.25 * 100)
        score = score * .55 + ev_signal * .35 + data_quality * .10

    confidence = profile_confidence * .70 + (15 if has_exact else 0) + (15 if has_odds else 0)
    if has_market_ev:
        confidence = confidence * .75 + data_quality * .25
    confidence = round(clamp(confidence))

    if has_market_ev and confidence >= 75:
        grade = "A · EV + chase"
        basis = "Marknadsvärden, odds, pris och verifierad chase-profil"
    elif has_exact and has_odds and confidence >= 70:
        grade = "B · chase + odds"
        basis = "Verifierade chase-kort, produktodds och pris; fullständigt marknads-EV saknas"
    else:
        grade = "C · chaseprofil"
        basis = "Verifierat innehåll och pris; fullständiga odds eller försäljningsvärden saknas"

    reasons = []
    if repeatable >= 78:
        reasons.append("Många dokumenterade chanser till attraktiva träffar")
    if ceiling >= 85:
        reasons.append("Mycket högt tak med namngivna toppkort")
    if has_odds:
        reasons.append("Publicerade eller härledda odds visas vid chase-korten")
    if has_market_ev:
        reasons.append("Marknads-EV kan jämföras med inköpspriset")
    if price_access >= 82:
        reasons.append("Relativt låg insats för den kartlagda chasen")

    warning = (
        "EV bygger på verifierade marknadsvärden och odds, men en enskild öppning kan ge stor förlust."
        if has_market_ev
        else "Säljpotential, inte förväntad vinst: fullständiga sålda priser och kortspecifika odds saknas."
    )
    return {
        **item,
        "resale_score": round(clamp(score)),
        "resale_confidence": confidence,
        "evidence_grade": grade,
        "ranking_basis": basis,
        "sellable_chases": cards[:5],
        "resale_reasons": reasons[:4],
        "resale_warning": warning,
        "has_market_ev": bool(has_market_ev),
        "opening_profile": pull,
        "strategy": strategy,
    }


def rank_resale(items: list[dict], strategy: str = "balanced") -> list[dict]:
    ranked = [resale_rank(item, strategy) for item in items]
    return sorted(
        ranked,
        key=lambda x: (
            x.get("resale_score") is not None,
            x.get("resale_score") or -1,
            x.get("resale_confidence") or 0,
        ),
        reverse=True,
    )
