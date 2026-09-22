from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload
from ..adapters.registry import build_adapter
from ..models import CatalogCandidate, IngestionRun, Offer, PriceHistory, ProductVariant, Store
from .matching import classify_match, match_score, normalize_title
from .price_signals import detect_offer_signals
from .watch_engine import evaluate_signal
from .scope_watch import evaluate_scope_signal

POLICY_RUNNABLE = {"robots_checked", "feed_allowed", "api_allowed", "manual_allowed"}

def _policy_allows_adapter(store: Store) -> tuple[bool, str | None]:
    key = store.adapter_key or "manual"
    if key in {"generic_csv_feed", "generic_json_feed", "generic_mapped_feed"}:
        if store.policy_status not in {"feed_allowed", "api_allowed"}:
            return False, "Feed/API adapter requires policy_status feed_allowed or api_allowed"
    elif key == "public_html_catalog":
        if store.policy_status != "robots_checked":
            return False, "Public HTML adapter requires policy_status robots_checked"
    elif key == "manual":
        if store.policy_status not in {"manual_allowed", "feed_allowed", "api_allowed", "robots_checked"}:
            return False, "Manual adapter requires an approved collection policy"
    return True, None

def _best_variant(raw_title: str, variants: list[ProductVariant]):
    scored = []
    for v in variants:
        canonical = f"{v.product.canonical_name} {v.format}"
        score = match_score(raw_title, canonical, v.format)
        scored.append((score, v))
    return max(scored, key=lambda x: x[0]) if scored else (0.0, None)

async def ingest_store(db: Session, store: Store) -> IngestionRun:
    run = IngestionRun(store_id=store.id)
    db.add(run)
    store.last_attempt_at = datetime.utcnow()
    db.commit(); db.refresh(run)

    if not store.active:
        run.status = "blocked"; run.error = "Store is inactive"; run.finished_at = datetime.utcnow(); db.commit(); return run
    if store.policy_status not in POLICY_RUNNABLE:
        run.status = "blocked"; run.error = f"Policy status '{store.policy_status}' is not approved for collection"; run.finished_at = datetime.utcnow(); db.commit(); return run

    adapter_allowed, policy_error = _policy_allows_adapter(store)
    if not adapter_allowed:
        run.status = "blocked"; run.error = policy_error; run.finished_at = datetime.utcnow(); db.commit(); return run

    try:
        adapter = build_adapter(store, db)
        raw_offers = await adapter.fetch_offers()
        run.fetched_count = len(raw_offers)
        variants = db.execute(select(ProductVariant).options(joinedload(ProductVariant.product))).unique().scalars().all()

        for raw in raw_offers:
            offer = db.scalar(select(Offer).where(Offer.store_id == store.id, Offer.external_id == raw.external_id))
            created = offer is None
            if created:
                offer = Offer(store_id=store.id, external_id=raw.external_id, source_title=raw.title, price_sek=raw.price)
                db.add(offer); db.flush(); run.created_count += 1
            else:
                run.updated_count += 1

            previous_price = None if created else offer.price_sek
            previous_stock = None if created else offer.stock_status

            score, variant = _best_variant(raw.title, variants)
            status = classify_match(score)
            offer.source_title = raw.title
            offer.url = raw.url
            offer.price_sek = raw.price
            offer.currency = raw.currency
            offer.stock_status = raw.stock_status
            offer.is_preorder = raw.is_preorder
            offer.source_kind = store.collection_method
            offer.source_confidence = raw.source_confidence
            offer.observed_at = raw.observed_at
            offer.match_confidence = score
            offer.match_status = status
            offer.variant_id = variant.id if variant and status != "unmatched" else None
            # Detect changes before adding the current observation to history.
            if offer.variant_id and status == "auto_matched":
                new_signals = detect_offer_signals(
                    db, offer, previous_price=previous_price,
                    previous_stock=previous_stock, now=raw.observed_at,
                )
                if new_signals:
                    db.flush()
                    for signal in new_signals:
                        evaluate_signal(db, signal)
                        evaluate_scope_signal(db, signal)
            db.add(PriceHistory(offer_id=offer.id, price_sek=raw.price, stock_status=raw.stock_status, observed_at=raw.observed_at))
            if status == "auto_matched":
                run.matched_count += 1
            elif status == "review":
                run.review_count += 1
            else:
                run.unmatched_count += 1

            # Discovery queue: every non-auto-matched source item is classified so
            # BoxFinder can grow its sealed catalog without inventing canonical products.
            if status != "auto_matched":
                n = normalize_title(raw.title)
                candidate = db.scalar(select(CatalogCandidate).where(
                    CatalogCandidate.store_id == store.id,
                    CatalogCandidate.external_id == raw.external_id,
                ))
                if candidate is None:
                    candidate = CatalogCandidate(
                        store_id=store.id,
                        external_id=raw.external_id,
                        source_title=raw.title,
                        first_seen_at=raw.observed_at,
                    )
                    db.add(candidate)
                candidate.source_title = raw.title
                candidate.url = raw.url
                candidate.price_sek = raw.price
                candidate.stock_status = raw.stock_status
                candidate.detected_format = n.format
                candidate.category_hint = n.category_hint
                candidate.language_hint = n.language
                candidate.year_season_hint = n.year_season
                candidate.sealed_candidate = n.sealed_candidate
                candidate.randomized = n.randomized
                candidate.exclusion_reason = n.exclusion_reason
                candidate.last_seen_at = raw.observed_at

        store.last_success_at = datetime.utcnow()
        store.last_error = None
        run.status = "success"
        run.finished_at = datetime.utcnow()
        db.commit(); db.refresh(run)
        return run
    except Exception as exc:
        db.rollback()
        # Reload tracked records after rollback.
        store = db.get(Store, store.id)
        run = db.get(IngestionRun, run.id)
        store.last_error = str(exc)[:2000]
        run.status = "error"
        run.error = str(exc)[:2000]
        run.finished_at = datetime.utcnow()
        db.commit(); db.refresh(run)
        return run
