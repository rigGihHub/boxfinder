from app.models import CatalogCandidate, Product, ProductVariant, Store
from app.services.dedup import product_identity, candidate_variant_score, candidate_clusters

def test_identity_same_product_small_title_variation():
    a = product_identity("2025-26 Upper Deck Series 1 Hobby Box")
    b = product_identity("Upper Deck Series 1 2025/26 Hobby Box")
    assert a.format == "hobby box"
    assert b.format == "hobby box"
    assert a.year_season == b.year_season
    assert set(a.core_tokens) == set(b.core_tokens)

def test_identity_keeps_case_and_box_separate():
    a = product_identity("2025-26 Upper Deck Series 1 Hobby Box")
    b = product_identity("2025-26 Upper Deck Series 1 Sealed Case")
    assert a.format != b.format
    assert a.fingerprint != b.fingerprint

def test_candidate_variant_hard_format_conflict_scores_zero():
    product = Product(id=1, slug="ud-series-1", canonical_name="2025-26 Upper Deck Series 1", category="Hockey", manufacturer="Upper Deck", year_season="2025-26")
    variant = ProductVariant(id=2, product_id=1, format="hobby box", language="English", region="Global")
    variant.product = product
    c = CatalogCandidate(store_id=1, external_id="x", source_title="2025-26 Upper Deck Series 1 Sealed Case", sealed_candidate=True)
    assert candidate_variant_score(c, variant) == 0.0

def test_clusters_merge_same_identity_across_stores():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.database import Base
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        s1=Store(name="Store A", country="SE", collection_method="manual", policy_status="manual_allowed")
        s2=Store(name="Store B", country="SE", collection_method="manual", policy_status="manual_allowed")
        db.add_all([s1,s2]); db.flush()
        db.add_all([
            CatalogCandidate(store_id=s1.id, external_id="a", source_title="2025-26 Upper Deck Series 1 Hobby Box", price_sek=899, sealed_candidate=True, review_status="new"),
            CatalogCandidate(store_id=s2.id, external_id="b", source_title="Upper Deck Series 1 2025/26 Hobby Box", price_sek=949, sealed_candidate=True, review_status="new"),
        ])
        db.commit()
        rows=candidate_clusters(db)
        assert any(x["multi_store"] and x["store_count"] == 2 for x in rows)
    finally:
        db.close()
