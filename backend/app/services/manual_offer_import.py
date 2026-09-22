import csv, io
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..models import CatalogCandidate, Offer, PriceHistory, ProductVariant, Store
from sqlalchemy.orm import joinedload
from .matching import classify_match, match_score, normalize_title

REQUIRED = {"external_id", "title", "price_sek"}

def import_offer_csv(db: Session, store: Store, text: str) -> dict:
    reader = csv.DictReader(io.StringIO(text))
    fields = set(reader.fieldnames or [])
    missing = REQUIRED - fields
    if missing:
        raise ValueError(f"Missing columns: {', '.join(sorted(missing))}")
    result = {"rows":0,"created":0,"updated":0,"matched":0,"review":0,"unmatched":0,"errors":[]}
    for n, row in enumerate(reader, start=2):
        result["rows"] += 1
        try:
            price = float(str(row["price_sek"]).replace(" ", "").replace(",", "."))
            if price <= 0: raise ValueError("price_sek must be > 0")
            external_id = row["external_id"].strip(); title = row["title"].strip()
            if not external_id or not title: raise ValueError("external_id/title cannot be blank")
            offer = db.scalar(select(Offer).where(Offer.store_id==store.id, Offer.external_id==external_id))
            variants = db.execute(select(ProductVariant).options(joinedload(ProductVariant.product))).unique().scalars().all()
            scored = [(match_score(title, f"{v.product.canonical_name} {v.format}", v.format), v) for v in variants]
            conf, best = max(scored, key=lambda x: x[0]) if scored else (0.0, None)
            status = classify_match(conf)
            variant_id = best.id if best and status != "unmatched" else None
            if offer:
                offer.source_title=title; offer.price_sek=price; offer.url=row.get("url") or offer.url
                offer.stock_status=(row.get("stock_status") or "unknown").strip().lower()
                offer.is_preorder=str(row.get("is_preorder") or "").strip().lower() in {"1","true","yes","ja"}
                offer.observed_at=datetime.utcnow(); offer.variant_id=variant_id; offer.match_confidence=conf; offer.match_status=status
                result["updated"] += 1
            else:
                offer=Offer(store_id=store.id, external_id=external_id, source_title=title, url=row.get("url") or None,
                    price_sek=price, currency=(row.get("currency") or "SEK").upper(), stock_status=(row.get("stock_status") or "unknown").lower(),
                    is_preorder=str(row.get("is_preorder") or "").strip().lower() in {"1","true","yes","ja"},
                    source_kind="manual_csv", source_confidence=85, observed_at=datetime.utcnow(), variant_id=variant_id,
                    match_confidence=conf, match_status=status)
                db.add(offer); db.flush(); result["created"] += 1
            db.add(PriceHistory(offer_id=offer.id, price_sek=price, stock_status=offer.stock_status))
            if status=="auto_matched":
                result["matched"] += 1
            elif status=="review":
                result["review"] += 1
            else:
                result["unmatched"] += 1

            if status != "auto_matched":
                nrm = normalize_title(title)
                candidate = db.scalar(select(CatalogCandidate).where(
                    CatalogCandidate.store_id == store.id,
                    CatalogCandidate.external_id == external_id,
                ))
                if candidate is None:
                    candidate = CatalogCandidate(
                        store_id=store.id,
                        external_id=external_id,
                        source_title=title,
                        first_seen_at=offer.observed_at,
                    )
                    db.add(candidate)
                candidate.source_title = title
                candidate.url = offer.url
                candidate.price_sek = price
                candidate.stock_status = offer.stock_status
                candidate.detected_format = nrm.format
                candidate.category_hint = nrm.category_hint
                candidate.language_hint = nrm.language
                candidate.year_season_hint = nrm.year_season
                candidate.sealed_candidate = nrm.sealed_candidate
                candidate.randomized = nrm.randomized
                candidate.exclusion_reason = nrm.exclusion_reason
                candidate.last_seen_at = offer.observed_at
        except Exception as e:
            result["errors"].append({"row":n,"error":str(e)})
    db.commit()
    return result
