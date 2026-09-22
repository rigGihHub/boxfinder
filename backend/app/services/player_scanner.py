from math import prod
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload
from ..models import Card, Checklist, Odds, Offer, ProductVariant


def _best_price(variant: ProductVariant):
    offers = [o for o in variant.offers if o.stock_status == "in_stock" and not o.is_preorder]
    offers = offers or [o for o in variant.offers if not o.is_preorder]
    return min((o.price_sek for o in offers), default=None)


def scan_subject(db: Session, query: str):
    q = query.strip()
    if len(q) < 2:
        return []
    cards = db.execute(
        select(Card)
        .where(Card.subject.ilike(f"%{q}%"))
        .options(joinedload(Card.odds), joinedload(Card.checklist))
    ).unique().scalars().all()

    grouped = {}
    for card in cards:
        vid = card.checklist.variant_id
        g = grouped.setdefault(vid, {"cards": [], "probabilities": []})
        g["cards"].append(card)
        for odd in card.odds:
            if odd.variant_id == vid and odd.probability_per_box is not None and odd.basis in {"official", "derived", "estimated", "demo"}:
                g["probabilities"].append(float(odd.probability_per_box))

    rows = []
    for vid, data in grouped.items():
        variant = db.execute(
            select(ProductVariant).where(ProductVariant.id == vid)
            .options(joinedload(ProductVariant.product), joinedload(ProductVariant.offers).joinedload(Offer.store))
        ).unique().scalar_one()
        price = _best_price(variant)
        probs = [max(0.0, min(1.0, p)) for p in data["probabilities"]]
        any_hit = (1 - prod(1 - p for p in probs)) if probs else None
        per_1000 = (any_hit * 1000 / price) if any_hit is not None and price else None
        rows.append({
            "variant_id": vid,
            "product": f"{variant.product.canonical_name} {variant.format}",
            "category": variant.product.category,
            "price_sek": price,
            "matching_cards": len(data["cards"]),
            "cards_with_odds": len(probs),
            "probability_any_matching_card": round(any_hit, 6) if any_hit is not None else None,
            "probability_per_1000_sek": round(per_1000, 6) if per_1000 is not None else None,
            "probability_basis": "mixed" if probs else "unknown",
            "subjects": sorted({c.subject for c in data["cards"]})[:8],
        })

    known = [r for r in rows if r["probability_per_1000_sek"] is not None]
    max_eff = max((r["probability_per_1000_sek"] for r in known), default=None)
    for r in rows:
        r["opportunity_score"] = round(100 * r["probability_per_1000_sek"] / max_eff) if max_eff and r["probability_per_1000_sek"] is not None else None
    return sorted(rows, key=lambda r: (r["opportunity_score"] is not None, r["opportunity_score"] or -1, r["matching_cards"]), reverse=True)
