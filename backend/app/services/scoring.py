def clamp(value: float, low: float = 0, high: float = 100) -> float:
    return max(low, min(value, high))

def calculate_box_value_score(*, price: float, market_median: float | None, ev_low: float | None, ev_high: float | None,
                              checklist_strength: int | None, hit_density: int | None, upside: int | None,
                              floor_score: int | None, rookie_strength: int | None, liquidity: int | None,
                              popularity: int | None, data_quality: int) -> int | None:
    if price <= 0 or ev_low is None or ev_high is None:
        return None
    mid_ev = (ev_low + ev_high) / 2
    ev_ratio = clamp(min(mid_ev / price, 1.5) / 1.5 * 100)
    discount = 0.0
    if market_median and market_median > 0:
        discount = clamp(max(0, min((market_median - price) / market_median, 0.4)) / 0.4 * 100)
    rookie = rookie_strength if rookie_strength is not None else 65
    components = {
        "ev_ratio": (ev_ratio, .28), "discount": (discount, .14),
        "checklist": (checklist_strength or 0, .14), "hit_density": (hit_density or 0, .12),
        "upside": (upside or 0, .08), "floor": (floor_score or 0, .08),
        "rookie": (rookie, .05), "liquidity": (liquidity or 0, .04),
        "popularity": (popularity or 0, .03), "data_quality": (data_quality, .04),
    }
    return round(clamp(sum(v * w for v, w in components.values())))
