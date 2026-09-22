from __future__ import annotations

from dataclasses import dataclass


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(value, high))


@dataclass(frozen=True)
class RankingResult:
    score: int | None
    reasons: list[str]


def _analysis(item: dict, key: str) -> float | None:
    value = item.get(key)
    return float(value) if value is not None else None


def rank_item(item: dict, mode: str) -> RankingResult:
    """Create profile-specific scores without inventing missing data.

    Missing inputs remain missing. Profiles that need unavailable fields return None
    instead of substituting arbitrary values.
    """
    mode = mode.lower().strip()
    value_score = _analysis(item, "box_value_score")
    data_quality = _analysis(item, "data_quality") or 0
    upside = _analysis(item, "upside")
    rookie = _analysis(item, "rookie_strength")
    hit_density = _analysis(item, "hit_density")
    floor = _analysis(item, "floor_score")
    price = _analysis(item, "price")
    ev_low = _analysis(item, "ev_low")
    ev_high = _analysis(item, "ev_high")

    if mode == "value":
        if value_score is None:
            return RankingResult(None, ["Saknar tillräckligt EV-underlag för Box Value Score."])
        reasons = ["Box Value Score väger EV/pris, innehåll, risk och datakvalitet."]
        return RankingResult(round(value_score), reasons)

    if mode == "upside":
        if upside is None or price is None or price <= 0:
            return RankingResult(None, ["Saknar verifierad upside eller prisdata."])
        ev_signal = None
        if ev_high is not None:
            ev_signal = clamp((ev_high / price) * 55)
        parts = [(upside, .62), (data_quality, .18)]
        if ev_signal is not None:
            parts.append((ev_signal, .20))
            denom = 1.0
        else:
            denom = .80
        score = sum(v * w for v, w in parts) / denom
        return RankingResult(round(clamp(score)), ["Prioriterar toppotential framför golv.", "Datakvalitet bromsar osäkra jackpot-signaler."])

    if mode == "rookies":
        if rookie is None:
            return RankingResult(None, ["Saknar bedömd rookie strength."])
        secondary = value_score if value_score is not None else data_quality
        score = rookie * .72 + secondary * .28
        return RankingResult(round(clamp(score)), ["Rookieklass väger tyngst.", "Boxvärde/datastöd används som sekundär signal."])

    if mode == "hit_density":
        if hit_density is None:
            return RankingResult(None, ["Saknar verifierad hit density."])
        secondary = value_score if value_score is not None else data_quality
        score = hit_density * .72 + secondary * .28
        return RankingResult(round(clamp(score)), ["Prioriterar hur ofta boxen ger inserts/parallels/hits."])

    if mode == "balanced":
        required = [value_score, upside, hit_density, floor]
        if any(x is None for x in required):
            return RankingResult(None, ["Saknar underlag för balanserad profil."])
        score = value_score * .42 + hit_density * .20 + floor * .18 + upside * .12 + data_quality * .08
        return RankingResult(round(clamp(score)), ["Väger värde, träfffrekvens, golv och upside."])

    raise ValueError(f"Unknown ranking mode: {mode}")


def rank_items(items: list[dict], mode: str) -> list[dict]:
    ranked: list[dict] = []
    for item in items:
        result = rank_item(item, mode)
        enriched = dict(item)
        enriched["ranking_mode"] = mode
        enriched["ranking_score"] = result.score
        enriched["ranking_reasons"] = result.reasons
        ranked.append(enriched)
    return sorted(
        ranked,
        key=lambda x: (x["ranking_score"] is not None, x["ranking_score"] or -1, x.get("data_quality") or 0),
        reverse=True,
    )
