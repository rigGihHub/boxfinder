from __future__ import annotations
import csv, io, json
from datetime import datetime
from urllib.parse import urljoin
import httpx

from .base import RawOffer
from .feed_catalog import _price, _stock, _bool, USER_AGENT

def _rows(text: str, feed_format: str) -> list[dict]:
    if feed_format == "csv":
        return [dict(r) for r in csv.DictReader(io.StringIO(text.lstrip("\ufeff")))]
    if feed_format == "json":
        data=json.loads(text)
        if isinstance(data,list):
            return [x for x in data if isinstance(x,dict)]
        if isinstance(data,dict):
            for key in ("products","offers","items","data"):
                if isinstance(data.get(key),list):
                    return [x for x in data[key] if isinstance(x,dict)]
        raise ValueError("JSON feed must be a list or contain products/offers/items/data")
    raise ValueError("Unsupported mapped feed_format")

def parse_mapped_feed(text: str, *, feed_format: str, mapping: dict, base_url: str|None=None) -> list[RawOffer]:
    required={"external_id","title","price_sek"}
    missing=required-set(mapping)
    if missing:
        raise ValueError(f"Mapped feed missing required mappings: {', '.join(sorted(missing))}")
    result=[]
    for row in _rows(text,feed_format):
        try:
            external_id=str(row.get(mapping["external_id"]) or "").strip()
            title=str(row.get(mapping["title"]) or "").strip()
            if not external_id or not title:
                continue
            raw_url=str(row.get(mapping.get("url")) or "").strip() if mapping.get("url") else ""
            url=urljoin(base_url,raw_url) if raw_url and base_url else (raw_url or None)
            currency=str(row.get(mapping.get("currency")) or "SEK").upper() if mapping.get("currency") else "SEK"
            stock=_stock(row.get(mapping.get("stock_status"))) if mapping.get("stock_status") else "unknown"
            preorder=_bool(row.get(mapping.get("is_preorder"))) if mapping.get("is_preorder") else False
            result.append(RawOffer(
                external_id=external_id,
                title=title,
                url=url,
                price=_price(row.get(mapping["price_sek"])),
                currency=currency,
                stock_status=stock,
                is_preorder=preorder,
                observed_at=datetime.utcnow(),
                source_confidence=95,
            ))
        except (ValueError,TypeError):
            continue
    return result

class GenericMappedFeedAdapter:
    key="generic_mapped_feed"
    def __init__(self, source_url: str, *, feed_format: str, mapping: dict, base_url: str|None=None):
        self.source_url=source_url
        self.feed_format=feed_format
        self.mapping=mapping
        self.base_url=base_url
    async def fetch_offers(self) -> list[RawOffer]:
        async with httpx.AsyncClient(timeout=25,follow_redirects=True,headers={"User-Agent":USER_AGENT}) as client:
            r=await client.get(self.source_url)
            r.raise_for_status()
        return parse_mapped_feed(
            r.text,feed_format=self.feed_format,mapping=self.mapping,
            base_url=self.base_url or str(r.url)
        )
