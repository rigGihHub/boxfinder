from datetime import datetime, timezone

from app.routers import discovery


def test_store_recommendations_use_selected_offer_before_budget(monkeypatch):
    observed = datetime.now(timezone.utc).isoformat()
    item = {
        "id": 1, "category": "Hockey", "format": "hobby box",
        "price": 80, "store": "Other", "url": "https://other.test/item",
        "store_offers": [
            {"store_id": 1, "store": "Other", "price": 80, "url": "https://other.test/item", "observed_at": observed},
            {"store_id": 2, "store": "Selected", "price": 120, "url": "https://selected.test/item", "observed_at": observed},
        ],
    }
    seen = {}

    def products(**kwargs):
        seen["max_price"] = kwargs["max_price"]
        seen["current_only"] = kwargs["current_offers_only"]
        return [item]

    def discover(_db, items, _goal):
        seen["items"] = items
        return {"recommendations": [], "considered": len(items), "rankable": 0}

    monkeypatch.setattr(discovery, "list_products", products)
    monkeypatch.setattr(discovery, "discover", discover)
    result = discovery.recommendations(
        category=None, budget=150, goal="balanced", format=None, store_name=" selected ", db=None
    )
    assert seen["max_price"] is None and seen["current_only"] is True
    assert result["considered"] == 1
    assert seen["items"][0]["price"] == 120
    assert seen["items"][0]["url"] == "https://selected.test/item"

    result = discovery.recommendations(
        category=None, budget=100, goal="balanced", format=None, store_name="Selected", db=None
    )
    assert result["considered"] == 0
