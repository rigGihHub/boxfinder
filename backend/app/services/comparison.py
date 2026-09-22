from __future__ import annotations
from typing import Any

METRICS = {
    "price": {"label": "Pris", "higher_is_better": False, "field": "price", "min_quality": 0},
    "box_value": {"label": "Box Value", "higher_is_better": True, "field": "box_value_score", "min_quality": 35},
    "ev_ratio": {"label": "EV / pris", "higher_is_better": True, "field": "ev_ratio", "min_quality": 55},
    "rookies": {"label": "Rookies", "higher_is_better": True, "field": "rookie_strength", "min_quality": 35},
    "hits": {"label": "Hit density", "higher_is_better": True, "field": "hit_density", "min_quality": 35},
    "upside": {"label": "Upside", "higher_is_better": True, "field": "upside", "min_quality": 35},
    "floor": {"label": "Golv", "higher_is_better": True, "field": "floor_score", "min_quality": 35},
    "data_quality": {"label": "Datakvalitet", "higher_is_better": True, "field": "data_quality", "min_quality": 0},
}


def _ev_ratio(item: dict[str, Any]) -> float | None:
    lo, hi, price = item.get("ev_low"), item.get("ev_high"), item.get("price")
    if lo is None or hi is None or not price:
        return None
    return round(((lo + hi) / 2) / price, 3)


def _risk_rank(value: str | None) -> int | None:
    if not value:
        return None
    v = value.lower()
    if "låg" in v or "low" in v:
        return 3
    if "med" in v:
        return 2
    if "hög" in v or "high" in v:
        return 1
    return None


def compare_items(items: list[dict[str, Any]]) -> dict[str, Any]:
    enriched = []
    for item in items:
        row = dict(item)
        row["ev_ratio"] = _ev_ratio(row)
        row["risk_rank"] = _risk_rank(row.get("risk"))
        enriched.append(row)

    winners: dict[str, Any] = {}
    for key, cfg in METRICS.items():
        candidates = []
        for item in enriched:
            value = item.get(cfg["field"])
            if value is None:
                continue
            if item.get("data_quality", 0) < cfg["min_quality"]:
                continue
            candidates.append((item["id"], value))
        if not candidates:
            winners[key] = {"winner_ids": [], "reason": "insufficient_data"}
            continue
        best_value = (max if cfg["higher_is_better"] else min)(v for _, v in candidates)
        ids = [i for i, v in candidates if v == best_value]
        winners[key] = {"winner_ids": ids, "value": best_value, "reason": "tie" if len(ids) > 1 else "winner"}

    risk_candidates = [(x["id"], x.get("risk_rank")) for x in enriched if x.get("risk_rank") is not None]
    if risk_candidates:
        best = max(v for _, v in risk_candidates)
        ids = [i for i, v in risk_candidates if v == best]
        winners["risk"] = {"winner_ids": ids, "value": best, "reason": "tie" if len(ids) > 1 else "winner"}
    else:
        winners["risk"] = {"winner_ids": [], "reason": "insufficient_data"}

    totals = {x["id"]: 0 for x in enriched}
    for metric, result in winners.items():
        if result.get("reason") in {"winner", "tie"}:
            for product_id in result.get("winner_ids", []):
                totals[product_id] += 1

    overall_id = max(totals, key=totals.get) if totals and max(totals.values()) > 0 else None
    return {
        "products": enriched,
        "winners": winners,
        "overall_winner_id": overall_id,
        "category_wins": totals,
        "disclaimer": "En kategorivinnare utses bara när relevant data finns och når miniminivån för datakvalitet. Lägst pris betyder inte automatiskt bäst köp.",
    }
