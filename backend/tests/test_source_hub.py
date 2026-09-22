from types import SimpleNamespace
from app.services.source_hub import source_hub_row

def test_source_hub_blocks_unreviewed_automation():
    store=SimpleNamespace(id=1,name="Coolcard",country="SE",homepage_url="https://www.coolcard.se/",
        source_url="https://www.coolcard.se/",active=True,collection_method="public_html",
        adapter_key="public_html_catalog",policy_status="review_required",
        last_attempt_at=None,last_success_at=None,last_error=None)
    row=source_hub_row(store)
    assert row["priority"] == 1
    assert "Hockey" in row["coverage"]
    assert row["automation_status"] == "blocked_pending_review"

def test_source_hub_allows_explicitly_approved_source():
    store=SimpleNamespace(id=2,name="Coolcard",country="SE",homepage_url=None,source_url=None,active=True,
        collection_method="public_html",adapter_key="public_html_catalog",policy_status="approved",
        last_attempt_at=None,last_success_at=None,last_error=None)
    assert source_hub_row(store)["automation_status"] == "allowed"
