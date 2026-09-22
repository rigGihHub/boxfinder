from .manual import ManualAdapter
from .http_catalog import PublicHtmlCatalogAdapter
from .feed_catalog import GenericCsvFeedAdapter, GenericJsonFeedAdapter
from .mapped_feed import GenericMappedFeedAdapter

def build_adapter(store, db=None):
    if store.adapter_key == "manual" or not store.adapter_key:
        return ManualAdapter()
    if store.adapter_key == "public_html_catalog":
        if not store.source_url:
            raise ValueError("Store is missing source_url")
        return PublicHtmlCatalogAdapter(store.source_url, store.robots_url)
    if store.adapter_key == "generic_mapped_feed":
        if db is None:
            raise ValueError("generic_mapped_feed requires database session")
        from sqlalchemy import select
        from ..models import StoreIntakeProfile
        import json
        profile = db.scalar(select(StoreIntakeProfile).where(StoreIntakeProfile.store_id == store.id))
        if profile is None or profile.status != "validated":
            raise ValueError("Store has no validated intake profile")
        source_url = profile.source_url or store.source_url
        if not source_url:
            raise ValueError("Validated intake profile is missing source_url")
        return GenericMappedFeedAdapter(
            source_url,
            feed_format=profile.feed_format,
            mapping=json.loads(profile.field_mapping_json or "{}"),
            base_url=profile.base_url,
        )
    if store.adapter_key == "generic_csv_feed":
        if not store.source_url:
            raise ValueError("Store is missing source_url")
        return GenericCsvFeedAdapter(store.source_url)
    if store.adapter_key == "generic_json_feed":
        if not store.source_url:
            raise ValueError("Store is missing source_url")
        return GenericJsonFeedAdapter(store.source_url)
    raise ValueError(f"Unknown adapter_key: {store.adapter_key}")
