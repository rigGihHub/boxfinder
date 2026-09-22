from __future__ import annotations

from dataclasses import dataclass
from math import log1p


def clamp(v: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(v, high))


@dataclass(frozen=True)
class BudgetLine:
    product_id: int
    name: str
    quantity: int
    unit_price: float


@dataclass(frozen=True)
class BudgetRecommendation:
    score: int
    goal: str
    total_price: float
    budget_left: float
    lines: list[BudgetLine]
    estimated_ev_low: float | None
    estimated_ev_high: float | None
    data_coverage: int
    reasons: list[str]


def _weighted_average(items: list[dict], qtys: list[int], key: str) -> float | None:
    vals = []
    weights = []
    for item, qty in zip(items, qtys):
        value = item.get(key)
        if value is not None:
            vals.append(float(value))
            weights.append(qty)
    if not vals:
        return None
    return sum(v*w for v, w in zip(vals, weights)) / sum(weights)


def _ev_sum(items: list[dict], qtys: list[int], key: str) -> float | None:
    vals = []
    for item, qty in zip(items, qtys):
        v = item.get(key)
        if v is None:
            return None
        vals.append(float(v) * qty)
    return sum(vals)


def _candidate_score(items: list[dict], qtys: list[int], budget: float, goal: str) -> BudgetRecommendation:
    total = sum(float(i['price']) * q for i, q in zip(items, qtys))
    utilization = clamp(total / budget * 100) if budget else 0
    data_quality = _weighted_average(items, qtys, 'data_quality') or 0
    hit = _weighted_average(items, qtys, 'hit_density')
    upside = _weighted_average(items, qtys, 'upside')
    floor = _weighted_average(items, qtys, 'floor_score')
    value = _weighted_average(items, qtys, 'box_value_score')
    rookie = _weighted_average(items, qtys, 'rookie_strength')

    total_packs = sum((i.get('packs') or 0) * q for i, q in zip(items, qtys))
    variety = len(items)
    opening = clamp(log1p(total_packs) * 20 + (variety - 1) * 8)

    ev_low = _ev_sum(items, qtys, 'ev_low')
    ev_high = _ev_sum(items, qtys, 'ev_high')
    ev_signal = None
    if ev_low is not None and ev_high is not None and total > 0:
        ev_signal = clamp((((ev_low + ev_high) / 2) / total) * 70)

    known_fields = [value, hit, upside, floor, rookie, ev_signal]
    coverage = round(sum(x is not None for x in known_fields) / len(known_fields) * 100)

    goal = goal.lower().strip()
    components: list[tuple[float, float]] = [(utilization, .12), (data_quality, .14)]
    reasons: list[str] = []

    def add(v: float | None, w: float, reason: str):
        if v is not None:
            components.append((v, w))
            reasons.append(reason)

    if goal == 'value':
        add(value, .34, 'Prioriterar Box Value Score.')
        add(ev_signal, .26, 'Väger uppskattat EV mot pris när underlaget räcker.')
        add(hit, .14, 'Belönar fler relevanta träffar.')
    elif goal == 'chase':
        add(upside, .40, 'Prioriterar stor träffpotential.')
        add(hit, .18, 'Väger också hur ofta boxen ger action.')
        add(value, .12, 'Boxvärde används som broms mot ren jackpotjakt.')
    elif goal == 'fun':
        add(opening, .32, 'Belönar fler packs och variation i öppningen.')
        add(hit, .25, 'Prioriterar hög hit density.')
        add(floor, .12, 'Ett bättre golv minskar risken för helt tom öppning.')
    else:  # balanced
        add(value, .24, 'Väger total prisvärdhet.')
        add(hit, .18, 'Väger träfffrekvens.')
        add(floor, .14, 'Väger golv.')
        add(upside, .12, 'Väger upside utan att dominera.')
        add(opening, .06, 'Tar hänsyn till öppningsupplevelsen.')

    denom = sum(w for _, w in components)
    raw = sum(v*w for v, w in components) / denom if denom else 0
    raw *= (0.75 + 0.25 * coverage / 100)

    lines = [BudgetLine(int(i['id']), i['name'], q, float(i['price'])) for i, q in zip(items, qtys)]
    return BudgetRecommendation(
        score=round(clamp(raw)), goal=goal, total_price=round(total, 2),
        budget_left=round(budget-total, 2), lines=lines,
        estimated_ev_low=round(ev_low, 2) if ev_low is not None else None,
        estimated_ev_high=round(ev_high, 2) if ev_high is not None else None,
        data_coverage=coverage,
        reasons=reasons[:3],
    )


def optimize_budget(products: list[dict], budget: float, goal: str = 'balanced', limit: int = 5) -> list[BudgetRecommendation]:
    if budget <= 0:
        return []
    eligible = [p for p in products if p.get('price') and 0 < float(p['price']) <= budget]
    # keep the search bounded and bias toward items with actual analysis data
    eligible = sorted(eligible, key=lambda p: (p.get('box_value_score') is not None, p.get('box_value_score') or 0, p.get('data_quality') or 0), reverse=True)[:14]
    candidates: list[BudgetRecommendation] = []

    # one-product stacks
    for p in eligible:
        max_q = min(int(budget // float(p['price'])), 12)
        for q in range(1, max_q + 1):
            candidates.append(_candidate_score([p], [q], budget, goal))

    # two-product mixes; enough for MVP without combinatorial explosion
    for idx, a in enumerate(eligible):
        for b in eligible[idx+1:]:
            max_a = min(int(budget // float(a['price'])), 6)
            for qa in range(1, max_a + 1):
                remaining = budget - qa * float(a['price'])
                if remaining < float(b['price']):
                    continue
                qb = min(int(remaining // float(b['price'])), 6)
                if qb >= 1:
                    candidates.append(_candidate_score([a, b], [qa, qb], budget, goal))

    # dedupe same basket, then rank
    unique: dict[tuple, BudgetRecommendation] = {}
    for c in candidates:
        key = tuple(sorted((line.product_id, line.quantity) for line in c.lines))
        prev = unique.get(key)
        if prev is None or c.score > prev.score:
            unique[key] = c
    ranked = sorted(unique.values(), key=lambda c: (c.score, -c.budget_left, c.data_coverage), reverse=True)
    return ranked[:limit]
