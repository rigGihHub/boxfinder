from datetime import datetime, timedelta, timezone
from time import monotonic

from app.routers import rankings
from app.services.resale_rankings import rank_resale
from test_rankings import resale_item


def install_cache(monkeypatch):
    now = datetime.now(timezone.utc).isoformat()
    def offer(store_id, price):
        return dict(store_id=store_id, store=f'Store {store_id}', price=price,
                    observed_at=now, url=f'https://shop{store_id}.test/product/{price}')
    items = [resale_item(id=1, **offer(1,50), store_offers=[offer(1,50),offer(2,1000)]),
             resale_item(id=2, **offer(1,100), store_offers=[offer(1,100),offer(2,200)]),
             resale_item(id=3, **offer(1,80), store_offers=[offer(1,80)])]
    monkeypatch.setattr(rankings, '_resale_cache', dict(until=monotonic()+60, refreshing=False,
        ranked={strategy:rank_resale(items,strategy) for strategy in rankings.STRATEGIES}))


def test_store_uses_own_offer_and_reranks_before_budget_filter(monkeypatch):
    install_cache(monkeypatch)
    all_items = rankings._resale_items(None,'value',None,None)
    assert all_items[0]['id'] == 1
    selected = rankings._resale_items(None,'value',None,None,2)
    assert [x['id'] for x in selected] == [2,1]
    assert [x['price'] for x in selected] == [200,1000]
    assert all(x['store_id']==2 and 'shop2.test' in x['url'] for x in selected)
    budget = rankings._resale_items(None,'value',None,500,2)
    assert [x['id'] for x in budget] == [2]
    assert rankings._resale_items(None,'value',None,None,999) == []
    assert rankings._resale_items(None,'value',None,None)[0]['price'] == 50


def test_expired_selected_offer_is_excluded_even_if_other_store_is_fresh(monkeypatch):
    install_cache(monkeypatch)
    for item in rankings._resale_cache['ranked']['value']:
        for offer in item['store_offers']:
            if offer['store_id']==2:
                offer['observed_at']=(datetime.now(timezone.utc)-timedelta(days=15)).isoformat()
    assert rankings._resale_items(None,'value',None,None,2) == []


def test_store_options_remain_available_when_budget_has_no_results(monkeypatch):
    install_cache(monkeypatch)
    result=rankings.resale_rankings(strategy='value',category=None,max_price=1,limit=20,db=None,store_id=2)
    assert result['items']==[]
    assert result['store_id']==2
    assert result['available_stores']==[{'id':1,'name':'Store 1'},{'id':2,'name':'Store 2'}]


def test_seeded_cardland_backup_is_selectable_even_when_not_cheapest(monkeypatch):
    from test_real_snapshot import session_factory
    from app import seed
    from app.routers.products import list_products
    Session=session_factory()
    monkeypatch.setattr(seed,'SessionLocal',Session)
    seed.seed_verified_snapshot()
    seed.seed_chase_profiles()
    monkeypatch.setattr(rankings,'_resale_cache',dict(until=0,ranked=None,refreshing=False))
    with Session() as db:
        items=list_products(None,None,db,False,True)
        cardland=[offer for item in items for offer in item['store_offers'] if offer['store']=='Cardland']
        assert len(cardland)>=5
        store_id=cardland[0]['store_id']
        result=rankings.resale_rankings(strategy='value',category=None,max_price=None,limit=100,db=db,store_id=store_id)
        assert len(result['items'])>=5
        assert all(x['store']=='Cardland' and 'cardland.se/' in x['url'] for x in result['items'])
        assert len({x['id'] for x in result['items']})==len(result['items'])
