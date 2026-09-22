from app.services.store_intake import inspect_sample, infer_mapping, validate_rows
from app.adapters.mapped_feed import parse_mapped_feed

CSV="""sku,name,pris,lager,link
ABC1,2025-26 Upper Deck Series 1 Hobby Box,899,i lager,/p/abc1
ABC2,Disney Lorcana Reign of Jafar Display,1478,i lager,/p/abc2
"""

def test_infers_swedish_and_common_feed_columns():
    result=inspect_sample(CSV,"csv")
    assert result["ready"] is True
    assert result["effective_mapping"]["external_id"]=="sku"
    assert result["effective_mapping"]["title"]=="name"
    assert result["effective_mapping"]["price_sek"]=="pris"
    assert result["valid_rows"]==2

def test_preview_classifies_sealed_formats_without_guessing():
    result=inspect_sample(CSV,"csv")
    formats=result["detected_formats"]
    assert formats["hobby box"]==1
    assert formats["display"]==1
    assert result["sealed_candidates"]==2

def test_missing_required_mapping_blocks_ready():
    text="name,price\nTest Hobby Box,100\n"
    result=inspect_sample(text,"csv")
    assert result["ready"] is False
    assert "external_id" in result["required_mapping_missing"]

def test_mapped_feed_uses_saved_mapping_and_base_url():
    mapping={
        "external_id":"sku","title":"name","price_sek":"pris",
        "stock_status":"lager","url":"link"
    }
    offers=parse_mapped_feed(CSV,feed_format="csv",mapping=mapping,base_url="https://shop.example")
    assert len(offers)==2
    assert offers[0].external_id=="ABC1"
    assert offers[0].price==899
    assert offers[0].stock_status=="in_stock"
    assert offers[0].url=="https://shop.example/p/abc1"

def test_json_wrapper_is_supported():
    text='{"products":[{"product_id":"1","product_name":"Test Hobby Box","sale_price":"499"}]}'
    result=inspect_sample(text,"json")
    assert result["ready"] is True
    assert result["valid_rows"]==1
