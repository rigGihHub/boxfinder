from __future__ import annotations
import re
from collections import defaultdict
from dataclasses import dataclass
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload
from ..models import CatalogCandidate, ProductVariant
from .matching import normalize_title, match_score, token_similarity

STORE_NOISE = {
    "köp","buy","online","sverige","sweden","lager","i","nu","preorder","pre-order",
    "förbeställ","kort","cards","trading","sealed","produkt","product",
}
FORMAT_WORDS = {
    "case","master","hobby","retail","mega","blaster","booster","bundle","elite",
    "trainer","etb","box","display","collection","tin","hanger","pack","single",
}
LANG_WORDS = {"english","engelsk","japanese","japansk","swedish","svensk","svenska","jp","jpn","en"}

@dataclass
class Identity:
    fingerprint: str
    core_tokens: tuple[str, ...]
    year_season: str | None
    format: str | None
    language: str | None
    category_hint: str | None

def product_identity(title: str) -> Identity:
    n = normalize_title(title)
    tokens = []
    for token in re.findall(r"[a-z0-9åäöéü]+", n.text):
        if token in STORE_NOISE or token in FORMAT_WORDS or token in LANG_WORDS:
            continue
        # season/year is represented as a hard field, not a fuzzy token.
        if re.fullmatch(r"20\d{2}", token) or re.fullmatch(r"\d{2}", token):
            continue
        if len(token) <= 1:
            continue
        tokens.append(token)
    unique = tuple(sorted(set(tokens)))
    hard = [
        n.category_hint or "?",
        n.year_season or "?",
        n.format or "?",
        n.language or "?",
    ]
    fingerprint = "|".join(hard + [" ".join(unique)])
    return Identity(
        fingerprint=fingerprint,
        core_tokens=unique,
        year_season=n.year_season,
        format=n.format,
        language=n.language,
        category_hint=n.category_hint,
    )

def _hard_compatible(a: Identity, b: Identity) -> bool:
    for left, right in [
        (a.format, b.format),
        (a.year_season, b.year_season),
        (a.language, b.language),
        (a.category_hint, b.category_hint),
    ]:
        if left and right and left != right:
            return False
    return True

def candidate_variant_score(candidate: CatalogCandidate, variant: ProductVariant) -> float:
    candidate_id = product_identity(candidate.source_title)
    canonical = f"{variant.product.canonical_name} {variant.format} {variant.language or ''}"
    variant_id = product_identity(canonical)
    if not _hard_compatible(candidate_id, variant_id):
        return 0.0
    score = match_score(candidate.source_title, canonical, variant.format)
    # Reward near-identical core identity but never override hard conflicts.
    a, b = set(candidate_id.core_tokens), set(variant_id.core_tokens)
    if a and b:
        overlap = len(a & b) / len(a | b)
        score = max(score, min(1.0, overlap * .82 + .15))
    return round(score, 3)

def variant_suggestions(db: Session, candidate: CatalogCandidate, limit: int = 5) -> list[dict]:
    variants = db.execute(
        select(ProductVariant).options(joinedload(ProductVariant.product))
    ).unique().scalars().all()
    scored = []
    for v in variants:
        score = candidate_variant_score(candidate, v)
        if score < .55:
            continue
        scored.append({
            "variant_id": v.id,
            "product_id": v.product_id,
            "canonical_name": v.product.canonical_name,
            "format": v.format,
            "language": v.language,
            "year_season": v.product.year_season,
            "category": v.product.category,
            "score": score,
            "recommendation": "auto_safe" if score >= .92 else ("review" if score >= .72 else "weak"),
        })
    return sorted(scored, key=lambda x: x["score"], reverse=True)[:limit]

def candidate_clusters(db: Session, status: str = "new") -> list[dict]:
    candidates = db.scalars(
        select(CatalogCandidate)
        .where(CatalogCandidate.review_status == status)
        .where(CatalogCandidate.sealed_candidate.is_(True))
        .order_by(CatalogCandidate.last_seen_at.desc())
    ).all()

    # First pass: exact semantic identity.
    groups: dict[str, list[CatalogCandidate]] = defaultdict(list)
    for c in candidates:
        groups[product_identity(c.source_title).fingerprint].append(c)

    result = []
    for fingerprint, rows in groups.items():
        ident = product_identity(rows[0].source_title)
        stores = sorted({r.store_id for r in rows})
        prices = [r.price_sek for r in rows if r.price_sek and r.price_sek > 0]
        result.append({
            "fingerprint": fingerprint,
            "candidate_count": len(rows),
            "store_count": len(stores),
            "candidate_ids": [r.id for r in rows],
            "titles": sorted({r.source_title for r in rows}),
            "format": ident.format,
            "year_season": ident.year_season,
            "language": ident.language,
            "category_hint": ident.category_hint,
            "min_price_sek": min(prices) if prices else None,
            "max_price_sek": max(prices) if prices else None,
            "multi_store": len(stores) >= 2,
        })
    return sorted(result, key=lambda x: (x["multi_store"], x["store_count"], x["candidate_count"]), reverse=True)
