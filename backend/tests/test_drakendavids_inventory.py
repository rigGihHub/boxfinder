from sqlalchemy import select, func

from app import seed
from app.models import CatalogCandidate, Offer, Product, Store
from app.routers.discovery import real_catalog
from app.services.drakendavids_snapshot import RAW, classify
from test_real_snapshot import session_factory


def test_complete_catalog_has_unique_variants_and_no_breaks_in_offers():
    inventory, offers = seed.DRAKENDAVIDS_INVENTORY, seed.DRAKENDAVIDS_OFFERS
    assert RAW['pagination_complete'] and RAW['page_counts'] == [250, 250, 71, 0]
    assert len(RAW['products']) == len({p['id'] for p in RAW['products']}) == 571
    assert len(inventory['variants']) == len({r['id'] for r in inventory['variants']}) == 1784
    assert len(offers) == len({r['sku'] for r in offers})
    assert len(offers) > 300
    assert all('Boxbreak' not in r['name'] and '?variant=' in r['buy_url'] for r in offers)
    assert all(r['packs'] is None and r['cards'] is None for r in offers if r['sku'].startswith('DD-SHOPIFY-'))
    assert all(r['slug'] not in seed.CHASE_PROFILES for r in offers if r['sku'].startswith('DD-SHOPIFY-'))
    assert all(r['exclusion_reason'] for r in inventory['variants'] if not r['randomized_cards'])


def test_refresh_reuses_existing_identities_and_excludes_unavailable(monkeypatch):
    Session = session_factory()
    monkeypatch.setattr(seed, 'SessionLocal', Session)
    snapshot = seed.REAL_SNAPSHOT
    monkeypatch.setattr(seed, 'REAL_SNAPSHOT', seed.PRE_DRAKENDAVIDS_SNAPSHOT)
    seed.seed_verified_snapshot()
    with Session() as db:
        previous = {o.external_id: (o.id, o.variant_id) for o in db.scalars(select(Offer).join(Store).where(Store.name == 'DrakenDavids'))}
    monkeypatch.setattr(seed, 'REAL_SNAPSHOT', snapshot)
    seed.seed_verified_snapshot()
    seed.seed_drakendavids_inventory()
    seed.seed_verified_snapshot()
    seed.seed_drakendavids_inventory()
    with Session() as db:
        store = db.scalar(select(Store).where(Store.name == 'DrakenDavids'))
        offers = db.scalars(select(Offer).where(Offer.store_id == store.id)).all()
        assert len(offers) == len(seed.DRAKENDAVIDS_OFFERS)
        assert all((o.id, o.variant_id) == previous[o.external_id] for o in offers if o.external_id in previous)
        assert db.scalar(select(func.count()).select_from(CatalogCandidate).where(CatalogCandidate.store_id == store.id)) == 1784
        expected = {r['buy_url']: r for r in seed.DRAKENDAVIDS_OFFERS if r['stock'] == 'in_stock' and not r['preorder']}
        catalog = real_catalog(store_name='DrakenDavids', category=None, budget=None, format=None, limit=200, db=db)
        assert catalog['count'] == len(expected)
        assert {r['url'] for r in catalog['products']} == expected.keys()
        assert all(r['price'] == expected[r['url']]['price'] for r in catalog['products'])
        disney = next(r for r in catalog['products'] if r['slug'] == 'cc-2026-topps-disney-chrome-value')
        assert disney['price'] == 499
        candidate = db.scalar(select(CatalogCandidate).where(CatalogCandidate.store_id == store.id, CatalogCandidate.review_status == 'new'))
        candidate.review_status = 'rejected'
        cid = candidate.id
        db.commit()
    seed.seed_drakendavids_inventory()
    with Session() as db:
        assert db.get(CatalogCandidate, cid).review_status == 'rejected'


def test_single_cards_and_services_never_become_boxes():
    for title, kind in [
        ('Ricky Villa Auto 1/1 - Topps Argentina Team Set 2024', ''),
        ('Topps Chrome Premier League 25/26 - Value Box Insert - Monday Night Lights', ''),
        ('Boxbreak #1017 - 3 x Topps Merlin Chrome - Hobby Box', 'Boxbreak'),
        ('Ultra Pro - Toploader förvaringsbox', 'Toploader'),
    ]:
        assert classify(dict(title=title, product_type=kind, body_html='', tags=[]))[4]
    product = dict(title='Topps Example - Hobby Box', product_type='', tags=[], body_html='Detta är en förbokning')
    assert classify(product)[3]
