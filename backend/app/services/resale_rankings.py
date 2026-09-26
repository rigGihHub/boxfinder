from __future__ import annotations

import math

from .chase_content import format_hits, has_actionable_odds, pull_profile


STRATEGIES = {"balanced", "jackpot", "frequent"}


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(value, high))


def _price_access(price: float | None) -> float:
    """Diminishing price signal, not a proxy for expected monetary return."""
    if price is None or price <= 0:
        return 0
    return clamp(100 - 14 * math.log2(max(price, 125) / 250))


def _opportunities(packs: int | None) -> float:
    # More packs mean more attempts, but never multiply a single-card jackpot's odds.
    if not isinstance(packs, (int, float)) or packs < 1:
        return 42
    return clamp(42 + 11 * math.log2(packs), 42, 80)


def _breadth(profile: dict) -> tuple[float, bool]:
    """Count distinct named routes, not the size of a serial-numbered print run."""
    names = {str(name).strip().casefold() for name in profile.get("key_names", []) if str(name).strip()}
    high = [c for c in profile.get("headline_chases", []) if _tier_rank(c.get("tier")) >= 3]
    distinct = {str(c.get("card", "")).strip().casefold() for c in high if c.get("card")}
    non_unique = [c for c in high if not ("1/1" in str(c.get("card", "")) or "1/1" in str(c.get("odds", "")))]
    breadth = clamp(36 + min(6, len(names)) * 6 + min(5, len(distinct)) * 4)
    # A list consisting mostly of unique 1/1s is a high ceiling, not a deep hit pool.
    concentrated = len(high) >= 1 and len(non_unique) <= 1 and len(high) - len(non_unique) >= 1
    return breadth, concentrated


WEIGHTS = {
    "balanced": {"ceiling": .30, "breadth": .18, "repeatable": .22, "format": .12, "access": .10, "evidence": .08},
    "jackpot": {"ceiling": .50, "breadth": .20, "repeatable": .08, "format": .05, "access": .12, "evidence": .05},
    "frequent": {"ceiling": .05, "breadth": .10, "repeatable": .45, "format": .25, "access": .10, "evidence": .05},
}


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
    breadth, concentrated = _breadth(profile)
    price_access = _price_access(item.get("price"))
    access = price_access * .75 + _opportunities(item.get("packs")) * .25
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
    hits = format_hits(profile, item.get("format"))
    # An average is weaker than a guaranteed family hit; neither guarantees a named card.
    quality = {"premium": (86, 73), "collectible": (72, 65), "base": (58, 54)}
    format_strength = max((quality[h["quality"]][0 if h["basis"] == "guaranteed" else 1]
                           + min(2, h["count"] - 1) * 3) for h in hits) if hits else 55
    profile_confidence = float(profile.get("confidence") or 0)

    evidence = clamp(55 + profile_confidence * .30 + (10 if has_odds else 0) + (5 if hits else 0))
    signals = {"ceiling": ceiling, "breadth": breadth, "repeatable": repeatable,
               "format": format_strength, "access": access, "evidence": evidence}
    score = sum(signals[key] * weight for key, weight in WEIGHTS[strategy].items())
    if concentrated:
        score -= 4 if strategy == "jackpot" else 2
    loose_pack = item.get("format") == "single pack"
    if loose_pack:
        score -= {"balanced": 3, "jackpot": 2, "frequent": 5}[strategy]

    has_market_ev = ev_low is not None and ev_high is not None and price and price > 0 and has_odds
    if has_market_ev:
        ev_ratio = ((float(ev_low) + float(ev_high)) / 2) / float(price)
        ev_signal = clamp(ev_ratio / 1.25 * 100)
        score = score * .55 + ev_signal * .35 + data_quality * .10

    confidence = profile_confidence * .65 + (15 if has_exact else 0) + (15 if has_odds else 0) + (5 if hits else 0)
    if has_market_ev:
        confidence = confidence * .75 + data_quality * .25
    confidence = round(clamp(confidence))

    if has_market_ev and confidence >= 75:
        grade = "A · EV + chase"
        basis = "Marknadsvärden, odds, pris och verifierad chase-profil"
    elif has_exact and (has_odds or hits) and confidence >= 70:
        grade = "B · chase + formatdata" if hits and not has_odds else "B · chase + odds"
        basis = "Verifierade chase-kort, formatträffar och pris; kortspecifika odds/marknads-EV saknas" if hits and not has_odds else "Verifierade chase-kort, produktodds och pris; fullständigt marknads-EV saknas"
    else:
        grade = "C · chaseprofil"
        basis = "Verifierat innehåll och pris; fullständiga odds eller försäljningsvärden saknas"

    reasons = []
    if repeatable >= 78:
        reasons.append("Många dokumenterade chanser till attraktiva träffar")
    if ceiling >= 85:
        reasons.append("Mycket högt tak med namngivna toppkort")
    if has_odds:
        reasons.append("Publicerade familje- eller produktodds visas vid chase-korten")
    if hits:
        reasons.append("Verifierat formatinnehåll: " + ", ".join(f"{h['count']:g} {h['family']} per {h['format']}" + (" i snitt" if h["basis"] == "average" else "") for h in hits[:2]))
    if has_market_ev:
        reasons.append("Marknads-EV kan jämföras med inköpspriset")
    if price_access >= 82:
        reasons.append("Relativt låg insats för den kartlagda chasen")
    if loose_pack:
        reasons.append("Löst paket: inga boxträffar är garanterade")

    warning = (
        "EV bygger på verifierade marknadsvärden och odds, men en enskild öppning kan ge stor förlust."
        if has_market_ev
        else "Öppningspotential, inte förväntad vinst: fullständiga sålda priser och kortspecifika odds saknas."
    )
    return {
        **item,
        "resale_score": round(clamp(score)),
        "resale_score_precise": round(clamp(score), 3),
        "resale_confidence": confidence,
        "evidence_grade": grade,
        "ranking_basis": basis,
        "sellable_chases": cards[:5],
        "resale_reasons": reasons[:4],
        "resale_warning": warning,
        "has_market_ev": bool(has_market_ev),
        "opening_profile": pull,
        "ranking_factors": {key: round(value, 1) for key, value in signals.items()},
        "format_hits": hits,
        "strategy": strategy,
    }


def rank_resale(items: list[dict], strategy: str = "balanced") -> list[dict]:
    ranked = [resale_rank(item, strategy) for item in items]
    return sorted(
        ranked,
        key=lambda x: (
            x.get("resale_score") is not None,
            x.get("resale_score_precise") if x.get("resale_score_precise") is not None else -1,
            x.get("resale_confidence") or 0,
            -(x.get("id") or 0),
        ),
        reverse=True,
    )
