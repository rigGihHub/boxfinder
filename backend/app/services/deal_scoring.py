from __future__ import annotations

from statistics import median


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(value, high))


def robust_market_reference(history_prices: list[float], current_store_prices: list[float]) -> float | None:
    positive_history = [p for p in history_prices if p > 0]
    positive_current = [p for p in current_store_prices if p > 0]
    if len(positive_history) < 3:
        return None
    history_median = median(positive_history)
    if len(positive_current) >= 2:
        current_median = median(positive_current)
        # Blend historical and cross-store market signals, limiting sensitivity
        # to a single stale or abnormal observation.
        return history_median * .65 + current_median * .35
    return history_median


def deal_confidence(*, observations: int, store_count: int, data_quality: int, discount_pct: float) -> int:
    observation_score = clamp(observations / 12 * 100)
    store_score = clamp(store_count / 4 * 100)
    discount_sanity = 100 if discount_pct <= 35 else max(20, 100 - (discount_pct - 35) * 3)
    score = observation_score * .32 + store_score * .24 + clamp(data_quality) * .30 + discount_sanity * .14
    return round(clamp(score))


def deal_score(*, discount_pct: float, box_value_score: int | None, confidence: int) -> int | None:
    if box_value_score is None:
        return None
    discount_component = clamp(discount_pct / 30 * 100)
    return round(clamp(discount_component * .42 + box_value_score * .40 + confidence * .18))


def cross_store_discount(best_price: float, current_store_prices: list[float]) -> float | None:
    prices = sorted(p for p in current_store_prices if p > 0)
    if len(prices) < 2 or best_price <= 0:
        return None
    peers = [p for p in prices if p != best_price] or prices[1:]
    if not peers:
        return None
    peer_median = median(peers)
    if peer_median <= 0:
        return None
    return (peer_median - best_price) / peer_median * 100

def history_low_position(best_price: float, history_prices: list[float]) -> dict:
    prices = [p for p in history_prices if p > 0]
    if not prices or best_price <= 0:
        return {"low": None, "high": None, "position_pct": None, "near_90d_low": False}
    low, high = min(prices), max(prices)
    if high == low:
        position = 0.0 if best_price <= low else 100.0
    else:
        position = (best_price - low) / (high - low) * 100
    return {
        "low": low,
        "high": high,
        "position_pct": round(max(0.0, min(position, 100.0)), 1),
        "near_90d_low": best_price <= low * 1.05,
    }

def deal_label(*, discount_pct: float, cross_store_pct: float | None, near_low: bool, confidence: int) -> str:
    if confidence < 45:
        return "För lite data"
    signals = 0
    if discount_pct >= 12:
        signals += 1
    if cross_store_pct is not None and cross_store_pct >= 8:
        signals += 1
    if near_low:
        signals += 1
    if signals >= 3 and confidence >= 70:
        return "Starkt fynd"
    if signals >= 2 and confidence >= 55:
        return "Bra fynd"
    if signals >= 1:
        return "Intressant pris"
    return "Normalt pris"

def enhanced_deal_score(*, discount_pct: float, cross_store_pct: float | None, near_low: bool,
                        box_value_score: int | None, confidence: int) -> int | None:
    if box_value_score is None:
        return None
    history_component = clamp(discount_pct / 30 * 100)
    cross_component = clamp((cross_store_pct or 0) / 20 * 100)
    low_component = 100 if near_low else 0
    return round(clamp(
        history_component * .30 +
        cross_component * .20 +
        low_component * .12 +
        box_value_score * .23 +
        confidence * .15
    ))
