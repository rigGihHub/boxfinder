from datetime import datetime, timedelta, timezone
from time import monotonic

from app.models import ShippingPolicy, Store
from app.routers import rankings
from app.services.price_compare import shipping_for
from app.services.resale_rankings import rank_resale, resale_rank
from app.services import shipping_snapshot
from test_rankings import resale_item
from test_real_snapshot import session_factory


def install_offers(monkeypatch):
    now = datetime.now(timezone.utc).isoformat()
    def offer(store_id, price, shipping):
        return dict(store_id=store_id, store=f"Store {store_id}", price=price,
                    url=f"https://store{store_id}.test/item", observed_at=now,
                    shipping_sek=shipping, shipping_checked_at=now,
                    total_price_sek=None if shipping is None else price+shipping)
    items = [resale_item(id=1, **offer(1,49,79), store_offers=[offer(1,49,79), offer(2,69,0)]),
             resale_item(id=2, **offer(1,60,None), store_offers=[offer(1,60,None)]),
             resale_item(id=3, **offer(1,70,0), store_offers=[offer(1,70,0)])]
    monkeypatch.setattr(rankings, "_resale_cache", dict(until=monotonic()+60, refreshing=False,
        ranked={s:rank_resale(items,s) for s in rankings.STRATEGIES}))


def test_total_cost_selects_right_store_and_budget(monkeypatch):
    install_offers(monkeypatch)
    items=rankings._resale_items(None,"value",None,100,cost_basis="total")
    assert [x["id"] for x in items]==[1,3]
    assert items[0]["store_id"]==2
    assert items[0]["price"]==69
    assert items[0]["ranking_price"]==69
    assert "store2.test" in items[0]["url"]
    assert rankings._resale_items(None,"value",None,100,1,"total")[0]["id"]==3
    assert len(rankings._resale_items(None,"value",None,100))==3


def test_score_uses_total_while_retaining_item_price():
    item=resale_item(price=49,ranking_price=128,cost_basis="total")
    result=resale_rank(item,"value")
    assert result["price"]==49
    assert result["resale_score_precise"]==resale_rank(resale_item(price=128),"value")["resale_score_precise"]
    assert "utan frakt" not in result["resale_warning"]


def test_shipping_coverage_is_global_and_requires_current_rules(monkeypatch):
    install_offers(monkeypatch)
    result = rankings.resale_rankings(strategy="value", category=None, max_price=1,
        limit=1, db=None, store_id=None, cost_basis="total")
    assert result["items"] == []
    assert result["shipping_coverage"] == {"stores": 2, "store_names": ["Store 1", "Store 2"]}
    for item in rankings._resale_cache["ranked"]["value"]:
        for offer in item["store_offers"]:
            if offer["store_id"] == 2:
                offer["shipping_checked_at"] = (datetime.now(timezone.utc)-timedelta(days=15)).isoformat()
    result = rankings.resale_rankings(strategy="value", category=None, max_price=None,
        limit=1, db=None, store_id=None, cost_basis="item")
    assert result["shipping_coverage"] == {"stores": 1, "store_names": ["Store 1"]}


def test_duplicate_offers_produce_one_product_and_can_cross_free_shipping_threshold(monkeypatch):
    install_offers(monkeypatch)
    item=rankings._resale_cache["ranked"]["value"][0]
    assert item["id"]==1
    item["store_offers"][0].update(price=999,total_price_sek=1058,shipping_sek=59)
    item["store_offers"].append({**item["store_offers"][0],"price":1000,"total_price_sek":1000,"shipping_sek":0})
    selected=rankings._resale_items(None,"value",None,None,1,"total")
    product=next(x for x in selected if x["id"]==1)
    assert product["price"]==product["ranking_price"]==1000
    assert len([x for x in selected if x["id"]==1])==1


def test_cached_total_cannot_extend_shipping_verification(monkeypatch):
    install_offers(monkeypatch)
    for item in rankings._resale_cache["ranked"]["value"]:
        for offer in item["store_offers"]:
            offer["shipping_checked_at"]=(datetime.now(timezone.utc)-timedelta(days=15)).isoformat()
    assert rankings._resale_items(None,"value",None,None,cost_basis="total")==[]


def test_expired_shipping_rule_is_unknown():
    p=ShippingPolicy(base_shipping_sek=59,free_shipping_threshold_sek=1000,
                     verification_status="manual_verified",updated_at=datetime.now(timezone.utc)-timedelta(days=15))
    assert shipping_for(p,1500)==(None,"expired")


def test_shipping_snapshot_preserves_verification_date_and_newer_changes(monkeypatch):
    Session=session_factory()
    monkeypatch.setattr(shipping_snapshot,"SessionLocal",Session)
    with Session() as db:
        db.add(Store(name="AlphaSpel"));db.commit()
    shipping_snapshot.seed_shipping_policies()
    shipping_snapshot.seed_shipping_policies()
    with Session() as db:
        p=db.query(ShippingPolicy).one()
        assert p.updated_at==shipping_snapshot.CHECKED_AT
        assert shipping_for(p,999)[0]==59
        assert shipping_for(p,1000)[0]==0
        p.base_shipping_sek=89
        p.updated_at=shipping_snapshot.CHECKED_AT+timedelta(hours=1)
        db.commit()
    shipping_snapshot.seed_shipping_policies()
    with Session() as db:
        assert db.query(ShippingPolicy).one().base_shipping_sek==89


def test_seeded_total_ranking_is_connected_to_store_shipping(monkeypatch):
    from app import seed
    Session=session_factory()
    monkeypatch.setattr(seed,"SessionLocal",Session)
    monkeypatch.setattr(shipping_snapshot,"SessionLocal",Session)
    seed.seed_verified_snapshot();seed.seed_chase_profiles()
    shipping_snapshot.seed_shipping_policies()
    monkeypatch.setattr(rankings,"_resale_cache",dict(until=0,ranked=None,refreshing=False))
    with Session() as db:
        result=rankings.resale_rankings(strategy="value",category=None,max_price=None,limit=100,
                                       db=db,store_id=None,cost_basis="total")
        assert result["items"]
        assert all(x["store"]=="AlphaSpel" for x in result["items"])
        assert all(x["ranking_price"]==x["price"]+x["shipping_sek"] for x in result["items"])
        assert all(x["shipping_source_url"]=="https://alphaspel.se/kopvillkor/" for x in result["items"])
