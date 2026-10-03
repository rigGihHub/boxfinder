from datetime import datetime, timedelta, timezone

MAX_OFFER_AGE_DAYS = 14
TRUSTED_MATCH_STATUSES = {"auto_matched", "manual_matched"}


def is_recent_observation(value, now=None):
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return False
    if not isinstance(value, datetime):
        return False
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return now - timedelta(days=MAX_OFFER_AGE_DAYS) <= value <= now


def is_current_real_offer(offer, now=None):
    return (offer.source_kind != "demo" and offer.match_status in TRUSTED_MATCH_STATUSES
            and offer.stock_status == "in_stock" and not offer.is_preorder
            and offer.price_sek is not None and offer.price_sek > 0
            and is_recent_observation(offer.observed_at, now))
