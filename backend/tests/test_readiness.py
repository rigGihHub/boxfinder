from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models import Product, ProductVariant, Store, Offer
from app.services.readiness import ranking_readiness

def test_readiness_is_explainable():
    engine=create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session=sessionmaker(bind=engine)
    db=Session()
    p=Product(slug="x", canonical_name="Test", category="Hockey", manufacturer="Test")
    db.add(p); db.flush()
    v=ProductVariant(product_id=p.id, format="Hobby", language="English", region="Global", packs=12, cards_per_pack=8)
    s=Store(name="Store", country="SE", collection_method="manual", policy_status="approved")
    db.add_all([v,s]); db.flush()
    db.add(Offer(store_id=s.id, variant_id=v.id, external_id="1", source_title="Test Hobby", price_sek=500,
                 stock_status="in_stock", is_preorder=False, source_kind="manual", source_confidence=100,
                 observed_at=datetime.utcnow(), match_confidence=.99, match_status="auto_matched"))
    db.commit(); db.refresh(v)
    result=ranking_readiness(db,v)
    assert result["status"] in {"ready","almost_ready","insufficient"}
    assert 0 <= result["score"] <= 100
    assert result["components"]["fresh_stores"] == 1
    assert "Checklista saknas" in result["blockers"]


def test_bulk_readiness_preserves_scores_and_counts_each_card_once():
    from sqlalchemy import event
    from sqlalchemy.orm import joinedload
    from sqlalchemy import select
    from app.models import Checklist, Card, Odds, CardMarketValue
    from app.services.readiness import ranking_readiness_many

    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    with sessionmaker(bind=engine)() as db:
        product = Product(slug='bulk', canonical_name='Bulk', category='Hockey', manufacturer='Test')
        db.add(product)
        db.flush()
        variants = [ProductVariant(product_id=product.id, format=fmt, language='English', region='Global')
                    for fmt in ('hobby box', 'blaster', 'single pack')]
        db.add_all(variants)
        db.flush()
        checklist = Checklist(variant_id=variants[0].id, source_name='Test',
                              verification_status='verified', confidence=90)
        db.add(checklist)
        db.flush()
        cards = [Card(checklist_id=checklist.id, subject=name) for name in ('A', 'B')]
        db.add_all(cards)
        db.flush()
        db.add_all([
            Odds(card_id=cards[0].id, variant_id=variants[0].id, category_key='one',
                 basis='official', probability_per_box=.1),
            Odds(card_id=cards[0].id, variant_id=variants[0].id, category_key='two',
                 basis='derived', probability_per_box=.2),
            Odds(card_id=cards[1].id, variant_id=variants[0].id, category_key='unknown',
                 basis='unknown', probability_per_box=.5),
            CardMarketValue(card_id=cards[0].id, condition_bucket='raw', median_90d_sek=100),
            CardMarketValue(card_id=cards[1].id, condition_bucket='graded', median_90d_sek=200),
        ])
        db.commit()
        variants = db.scalars(select(ProductVariant).options(
            joinedload(ProductVariant.offers), joinedload(ProductVariant.analysis))).unique().all()
        expected = {v.id: ranking_readiness(db, v) for v in variants}
        queries = []
        def count(*args):
            queries.append(args[2])
        event.listen(engine, 'before_cursor_execute', count)
        try:
            actual = ranking_readiness_many(db, variants)
        finally:
            event.remove(engine, 'before_cursor_execute', count)
        assert actual == expected
        assert len(queries) == 4
        assert actual[variants[0].id]['components']['odds_coverage'] == 50
        assert actual[variants[0].id]['components']['raw_value_coverage'] == 50
