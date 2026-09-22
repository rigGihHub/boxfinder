from app.adapters.http_catalog import parse_catalog_html

def test_parses_json_ld_product():
    html = '''<script type="application/ld+json">{"@type":"Product","name":"2025-26 Upper Deck Series 1 Hobby Box","url":"/p/ud","offers":{"price":"899","availability":"https://schema.org/InStock"}}</script>'''
    items = parse_catalog_html(html, "https://example.se/cards")
    assert len(items) == 1
    assert items[0].price == 899
    assert items[0].stock_status == "in_stock"
    assert items[0].source_confidence == 95

def test_ignores_irrelevant_non_card_product():
    html = '''<script type="application/ld+json">{"@type":"Product","name":"Blue Baseball Cap","offers":{"price":"299"}}</script>'''
    assert parse_catalog_html(html, "https://example.se") == []
