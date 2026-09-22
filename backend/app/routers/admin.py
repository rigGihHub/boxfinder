from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload
from ..database import get_db
from ..services.readiness import ranking_readiness
from ..models import Card, CardMarketValue, CatalogCandidate, Checklist, IngestionRun, Odds, Offer, Product, ProductVariant, Sale, ShippingPolicy, Store, StoreIntakeProfile
from ..services.ingestion import ingest_store
from ..services.matching import normalize_title
from ..services.dedup import candidate_clusters, variant_suggestions
from ..services.source_hub import source_hub_row
from ..services.update_manager import run_all_sources, status_payload
from ..services.catalog_coverage import coverage_report
from ..services.store_intake import inspect_sample, save_profile, serialize_profile
from ..services.intake_batch import batch_status, save_batch
from ..services.store_activation import activation_queue

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/data-quality")
def data_quality(db: Session = Depends(get_db)):
    return {
        "stores": db.scalar(select(func.count()).select_from(Store)),
        "products": db.scalar(select(func.count()).select_from(Product)),
        "variants": db.scalar(select(func.count()).select_from(ProductVariant)),
        "offers": db.scalar(select(func.count()).select_from(Offer)),
        "unmatched_offers": db.scalar(select(func.count()).select_from(Offer).where(Offer.match_status == "unmatched")),
        "review_offers": db.scalar(select(func.count()).select_from(Offer).where(Offer.match_status == "review")),
        "verified_live_offers": db.scalar(select(func.count()).select_from(Offer).where(Offer.source_kind != "demo", Offer.match_status == "auto_matched")),
        "demo_offers": db.scalar(select(func.count()).select_from(Offer).where(Offer.source_kind == "demo")),
        "checklists": db.scalar(select(func.count()).select_from(Checklist)),
        "verified_checklists": db.scalar(select(func.count()).select_from(Checklist).where(Checklist.verification_status == "verified")),
        "cards": db.scalar(select(func.count()).select_from(Card)),
        "odds_records": db.scalar(select(func.count()).select_from(Odds)),
        "official_odds_records": db.scalar(select(func.count()).select_from(Odds).where(Odds.basis == "official")),
        "sales": db.scalar(select(func.count()).select_from(Sale)),
        "verified_sales": db.scalar(select(func.count()).select_from(Sale).where(Sale.verified.is_(True))),
        "card_market_values": db.scalar(select(func.count()).select_from(CardMarketValue)),
        "raw_market_values": db.scalar(select(func.count()).select_from(CardMarketValue).where(CardMarketValue.condition_bucket == "raw")),
    }





class IntakeBatchItem(BaseModel):
    store_id: int
    feed_format: str = "csv"
    sample_text: str
    field_mapping: dict[str, str] | None = None
    source_url: str | None = None
    base_url: str | None = None

class IntakeBatchPayload(BaseModel):
    items: list[IntakeBatchItem]

@router.get("/stores/activation-queue")
def store_activation_queue(db: Session = Depends(get_db)):
    return activation_queue(db)

@router.get("/intake/batch-status")
def intake_batch_status(db: Session = Depends(get_db)):
    return batch_status(db)

@router.post("/intake/batch")
def intake_batch(payload: IntakeBatchPayload, db: Session = Depends(get_db)):
    if not payload.items:
        raise HTTPException(400, "At least one store item is required")
    return save_batch(db, [x.model_dump() for x in payload.items])

class IntakePreviewPayload(BaseModel):
    feed_format: str = "csv"
    sample_text: str
    field_mapping: dict[str, str] | None = None

class IntakeProfilePayload(BaseModel):
    feed_format: str = "csv"
    field_mapping: dict[str, str]
    source_url: str | None = None
    base_url: str | None = None
    sample_hash: str | None = None
    rows_seen: int = 0
    valid_rows: int = 0
    invalid_rows: int = 0
    ready: bool = False

@router.post("/stores/{store_id}/intake/preview")
def preview_store_intake(store_id: int, payload: IntakePreviewPayload, db: Session = Depends(get_db)):
    store=db.get(Store,store_id)
    if not store:
        raise HTTPException(404,"Store not found")
    try:
        return inspect_sample(payload.sample_text,payload.feed_format,payload.field_mapping)
    except Exception as exc:
        raise HTTPException(400,str(exc))

@router.put("/stores/{store_id}/intake/profile")
def upsert_store_intake_profile(store_id: int, payload: IntakeProfilePayload, db: Session = Depends(get_db)):
    store=db.get(Store,store_id)
    if not store:
        raise HTTPException(404,"Store not found")
    validation={
        "rows_seen":payload.rows_seen,
        "valid_rows":payload.valid_rows,
        "invalid_rows":payload.invalid_rows,
        "ready":payload.ready,
    }
    profile=save_profile(
        db,store,feed_format=payload.feed_format,mapping=payload.field_mapping,
        source_url=payload.source_url,base_url=payload.base_url,
        sample_hash=payload.sample_hash,validation=validation,
    )
    return serialize_profile(profile,store.name)

@router.get("/stores/{store_id}/intake/profile")
def get_store_intake_profile(store_id: int, db: Session = Depends(get_db)):
    store=db.get(Store,store_id)
    if not store:
        raise HTTPException(404,"Store not found")
    profile=db.scalar(select(StoreIntakeProfile).where(StoreIntakeProfile.store_id==store_id))
    return serialize_profile(profile,store.name) if profile else None

@router.post("/stores/{store_id}/intake/activate")
def activate_store_intake(store_id: int, db: Session = Depends(get_db)):
    store=db.get(Store,store_id)
    if not store:
        raise HTTPException(404,"Store not found")
    profile=db.scalar(select(StoreIntakeProfile).where(StoreIntakeProfile.store_id==store_id))
    if profile is None or profile.status!="validated":
        raise HTTPException(400,"A validated intake profile is required")
    if not (profile.source_url or store.source_url):
        raise HTTPException(400,"A source_url is required")
    store.adapter_key="generic_mapped_feed"
    store.collection_method="feed"
    # Policy status is deliberately NOT changed here.
    db.commit()
    return {
        "store_id":store.id,
        "adapter_key":store.adapter_key,
        "collection_method":store.collection_method,
        "policy_status":store.policy_status,
        "note":"Intake profile activated. Collection still obeys the store policy gate.",
    }

@router.get("/update-manager/status")
def update_manager_status():
    return status_payload()

@router.post("/update-manager/run")
async def update_manager_run():
    return await run_all_sources()

class ShippingPolicyPayload(BaseModel):
    base_shipping_sek: float | None = None
    free_shipping_threshold_sek: float | None = None
    source_url: str | None = None
    verification_status: str = "review_required"
    confidence: int = 0

@router.get("/shipping-policies")
def shipping_policies(db: Session = Depends(get_db)):
    rows = db.scalars(select(ShippingPolicy).order_by(ShippingPolicy.store_id)).all()
    stores = {s.id: s.name for s in db.scalars(select(Store)).all()}
    return [{"store_id":p.store_id,"store_name":stores.get(p.store_id),"base_shipping_sek":p.base_shipping_sek,
             "free_shipping_threshold_sek":p.free_shipping_threshold_sek,"source_url":p.source_url,
             "verification_status":p.verification_status,"confidence":p.confidence,"updated_at":p.updated_at.isoformat()} for p in rows]

@router.put("/stores/{store_id}/shipping-policy")
def upsert_shipping_policy(store_id: int, payload: ShippingPolicyPayload, db: Session = Depends(get_db)):
    store = db.get(Store, store_id)
    if not store: raise HTTPException(404, "Store not found")
    if payload.base_shipping_sek is not None and payload.base_shipping_sek < 0: raise HTTPException(400, "base_shipping_sek must be >= 0")
    if payload.free_shipping_threshold_sek is not None and payload.free_shipping_threshold_sek < 0: raise HTTPException(400, "free_shipping_threshold_sek must be >= 0")
    if not 0 <= payload.confidence <= 100: raise HTTPException(400, "confidence must be 0-100")
    allowed={"review_required","verified","manual_verified"}
    if payload.verification_status not in allowed: raise HTTPException(400, f"verification_status must be one of {sorted(allowed)}")
    policy=db.scalar(select(ShippingPolicy).where(ShippingPolicy.store_id==store_id))
    if policy is None:
        policy=ShippingPolicy(store_id=store_id); db.add(policy)
    policy.base_shipping_sek=payload.base_shipping_sek; policy.free_shipping_threshold_sek=payload.free_shipping_threshold_sek
    policy.source_url=payload.source_url; policy.verification_status=payload.verification_status; policy.confidence=payload.confidence
    from datetime import datetime
    policy.updated_at=datetime.utcnow(); db.commit()
    return {"store_id":store_id,"store_name":store.name,"base_shipping_sek":policy.base_shipping_sek,
            "free_shipping_threshold_sek":policy.free_shipping_threshold_sek,"verification_status":policy.verification_status,"confidence":policy.confidence}


@router.get("/catalog-coverage")
def catalog_coverage(db: Session = Depends(get_db)):
    return coverage_report(db)

@router.get("/source-hub")
def source_hub(db: Session = Depends(get_db)):
    rows = db.scalars(select(Store).order_by(Store.name)).all()
    return sorted([source_hub_row(s) for s in rows if s.collection_method != "demo"], key=lambda x: (x["priority"], x["name"]))

@router.get("/stores")
def stores(db: Session = Depends(get_db)):
    rows = db.scalars(select(Store).order_by(Store.name)).all()
    return [{
        "id": s.id, "name": s.name, "country": s.country, "homepage_url": s.homepage_url,
        "source_url": s.source_url, "adapter_key": s.adapter_key, "collection_method": s.collection_method,
        "policy_status": s.policy_status, "active": s.active,
        "last_attempt_at": s.last_attempt_at.isoformat() if s.last_attempt_at else None,
        "last_success_at": s.last_success_at.isoformat() if s.last_success_at else None,
        "last_error": s.last_error,
    } for s in rows]

@router.post("/stores/{store_id}/ingest")
async def run_ingestion(store_id: int, db: Session = Depends(get_db)):
    store = db.get(Store, store_id)
    if not store: raise HTTPException(404, "Store not found")
    run = await ingest_store(db, store)
    return {"run_id": run.id, "status": run.status, "fetched": run.fetched_count, "created": run.created_count, "updated": run.updated_count, "matched": run.matched_count, "review": run.review_count, "unmatched": run.unmatched_count, "error": run.error}

@router.get("/ingestion-runs")
def ingestion_runs(db: Session = Depends(get_db)):
    rows = db.scalars(select(IngestionRun).order_by(IngestionRun.started_at.desc()).limit(100)).all()
    return [{
        "id": r.id, "store_id": r.store_id, "status": r.status, "started_at": r.started_at.isoformat(),
        "finished_at": r.finished_at.isoformat() if r.finished_at else None, "fetched": r.fetched_count,
        "created": r.created_count, "updated": r.updated_count, "matched": r.matched_count,
        "review": r.review_count, "unmatched": r.unmatched_count, "error": r.error,
    } for r in rows]

from fastapi import Body
from ..services.manual_offer_import import import_offer_csv

@router.post("/stores/{store_id}/offers/import-csv")
def import_store_offers_csv(store_id: int, csv_text: str = Body(..., media_type="text/plain"), db: Session = Depends(get_db)):
    store = db.get(Store, store_id)
    if not store:
        raise HTTPException(404, "Store not found")
    try:
        return import_offer_csv(db, store, csv_text)
    except ValueError as exc:
        raise HTTPException(400, str(exc))



@router.get("/catalog-candidates")
def catalog_candidates(
    sealed_only: bool = True,
    status: str | None = None,
    limit: int = 250,
    db: Session = Depends(get_db),
):
    q = select(CatalogCandidate).order_by(CatalogCandidate.last_seen_at.desc())
    if sealed_only:
        q = q.where(CatalogCandidate.sealed_candidate.is_(True))
    if status:
        q = q.where(CatalogCandidate.review_status == status)
    rows = db.scalars(q.limit(min(max(limit, 1), 1000))).all()
    stores = {s.id: s.name for s in db.scalars(select(Store)).all()}
    return [{
        "id": c.id,
        "store_id": c.store_id,
        "store_name": stores.get(c.store_id),
        "external_id": c.external_id,
        "source_title": c.source_title,
        "url": c.url,
        "price_sek": c.price_sek,
        "stock_status": c.stock_status,
        "detected_format": c.detected_format,
        "category_hint": c.category_hint,
        "language_hint": c.language_hint,
        "year_season_hint": c.year_season_hint,
        "sealed_candidate": c.sealed_candidate,
        "randomized": c.randomized,
        "exclusion_reason": c.exclusion_reason,
        "review_status": c.review_status,
        "first_seen_at": c.first_seen_at.isoformat(),
        "last_seen_at": c.last_seen_at.isoformat(),
    } for c in rows]



@router.get("/catalog-clusters")
def catalog_clusters(status: str = "new", db: Session = Depends(get_db)):
    return candidate_clusters(db, status=status)

@router.get("/catalog-candidates/{candidate_id}/suggestions")
def catalog_candidate_suggestions(candidate_id: int, db: Session = Depends(get_db)):
    candidate = db.get(CatalogCandidate, candidate_id)
    if not candidate:
        raise HTTPException(404, "Catalog candidate not found")
    return {
        "candidate_id": candidate.id,
        "source_title": candidate.source_title,
        "suggestions": variant_suggestions(db, candidate),
    }

@router.post("/catalog-candidates/{candidate_id}/link/{variant_id}")
def link_catalog_candidate(candidate_id: int, variant_id: int, db: Session = Depends(get_db)):
    candidate = db.get(CatalogCandidate, candidate_id)
    if not candidate:
        raise HTTPException(404, "Catalog candidate not found")
    variant = db.get(ProductVariant, variant_id)
    if not variant:
        raise HTTPException(404, "Product variant not found")

    offer = db.scalar(select(Offer).where(
        Offer.store_id == candidate.store_id,
        Offer.external_id == candidate.external_id,
    ))
    if offer:
        offer.variant_id = variant.id
        offer.match_status = "manual_matched"
        offer.match_confidence = 1.0

    candidate.review_status = "linked"
    db.commit()
    return {
        "candidate_id": candidate.id,
        "variant_id": variant.id,
        "status": candidate.review_status,
        "offer_updated": bool(offer),
    }

@router.post("/catalog-candidates/{candidate_id}/reject")
def reject_catalog_candidate(candidate_id: int, db: Session = Depends(get_db)):
    candidate = db.get(CatalogCandidate, candidate_id)
    if not candidate:
        raise HTTPException(404, "Catalog candidate not found")
    candidate.review_status = "rejected"
    db.commit()
    return {"candidate_id": candidate.id, "status": candidate.review_status}

@router.post("/catalog-candidates/{candidate_id}/reopen")
def reopen_catalog_candidate(candidate_id: int, db: Session = Depends(get_db)):
    candidate = db.get(CatalogCandidate, candidate_id)
    if not candidate:
        raise HTTPException(404, "Catalog candidate not found")
    candidate.review_status = "new"
    db.commit()
    return {"candidate_id": candidate.id, "status": candidate.review_status}

@router.get("/catalog-candidates/stats")
def catalog_candidate_stats(db: Session = Depends(get_db)):
    total = db.scalar(select(func.count()).select_from(CatalogCandidate)) or 0
    sealed = db.scalar(select(func.count()).select_from(CatalogCandidate).where(CatalogCandidate.sealed_candidate.is_(True))) or 0
    randomized = db.scalar(select(func.count()).select_from(CatalogCandidate).where(CatalogCandidate.randomized.is_(True))) or 0
    accessories = db.scalar(select(func.count()).select_from(CatalogCandidate).where(CatalogCandidate.exclusion_reason.like("accessory:%"))) or 0
    new = db.scalar(select(func.count()).select_from(CatalogCandidate).where(CatalogCandidate.review_status == "new")) or 0
    return {"total": total, "sealed_candidates": sealed, "randomized": randomized, "accessories_excluded": accessories, "new_for_review": new}

@router.get("/catalog/normalize")
def catalog_normalize(title: str):
    n = normalize_title(title)
    return {
        "source_title": title,
        "normalized_text": n.text,
        "year_season": n.year_season,
        "format": n.format,
        "language": n.language,
        "category_hint": n.category_hint,
        "sealed_candidate": n.sealed_candidate,
        "randomized": n.randomized,
        "exclusion_reason": n.exclusion_reason,
    }

@router.get("/ranking-readiness")
def readiness_overview(db: Session = Depends(get_db)):
    variants = db.execute(
        select(ProductVariant).options(
            joinedload(ProductVariant.product),
            joinedload(ProductVariant.offers),
            joinedload(ProductVariant.analysis),
        )
    ).unique().scalars().all()
    rows = []
    for v in variants:
        r = ranking_readiness(db, v)
        rows.append({"variant_id": v.id, "name": f"{v.product.canonical_name} {v.format}", **r})
    return sorted(rows, key=lambda x: x["score"], reverse=True)
