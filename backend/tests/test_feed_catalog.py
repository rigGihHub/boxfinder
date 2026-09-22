from app.adapters.feed_catalog import parse_csv_feed, parse_json_feed
from app.models import Store
from app.services.ingestion import _policy_allows_adapter

def test_csv_feed_parser_maps_common_fields():
    text = """external_id,title,price_sek,stock_status,url,currency,is_preorder
abc-1,Pokemon Journey Together Booster Box,1499,in_stock,https://shop.test/p/1,SEK,false
"""
    rows = parse_csv_feed(text)
    assert len(rows) == 1
    assert rows[0].external_id == "abc-1"
    assert rows[0].price == 1499
    assert rows[0].stock_status == "in_stock"

def test_json_feed_parser_accepts_products_wrapper():
    text = '{"products":[{"id":"x1","name":"One Piece Booster Box","price":"1299","availability":"i lager"}]}'
    rows = parse_json_feed(text)
    assert len(rows) == 1
    assert rows[0].external_id == "x1"
    assert rows[0].stock_status == "in_stock"

def test_feed_adapter_requires_feed_policy():
    store = Store(name="Test", adapter_key="generic_csv_feed", policy_status="manual_allowed")
    allowed, reason = _policy_allows_adapter(store)
    assert allowed is False
    assert "feed_allowed" in reason

def test_html_adapter_requires_robots_checked():
    store = Store(name="Test2", adapter_key="public_html_catalog", policy_status="feed_allowed")
    allowed, reason = _policy_allows_adapter(store)
    assert allowed is False
    assert "robots_checked" in reason
