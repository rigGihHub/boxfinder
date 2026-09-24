from app.services.purchase_links import is_direct_purchase_url


def test_purchase_link_rejects_homepage_and_category_pages():
    assert not is_direct_purchase_url("https://www.coolcard.se/")
    assert not is_direct_purchase_url("https://www.coolcard.se/category/boxar-nhl-2025-26")


def test_purchase_link_accepts_article_pages():
    assert is_direct_purchase_url("https://www.coolcard.se/product/example")
    assert is_direct_purchase_url("https://www.cardland.se/fotboll/example")
