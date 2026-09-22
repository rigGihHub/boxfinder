import csv
import io
import json
from datetime import datetime
from urllib.parse import urljoin
import httpx
from .base import RawOffer

USER_AGENT = "BoxFinder/0.16 (+catalog-feed; contact-source-owner-before-enabling)"

def _bool(value) -> bool:
    return str(value or "").strip().lower() in {"1","true","yes","ja","y"}

def _price(value) -> float:
    text = str(value or "").strip().replace("\xa0","").replace(" ","").replace(",",".")
    price = float(text)
    if price <= 0:
        raise ValueError("price must be > 0")
    return price

def _stock(value) -> str:
    raw = str(value or "").strip().lower()
    if raw in {"in_stock","instock","in stock","i lager","lager","available","true","1"}:
        return "in_stock"
    if raw in {"out_of_stock","outofstock","out of stock","slut i lager","sold out","false","0"}:
        return "out_of_stock"
    return "unknown"

def _offer(row: dict, base_url: str | None = None) -> RawOffer:
    external_id = str(row.get("external_id") or row.get("id") or row.get("sku") or "").strip()
    title = str(row.get("title") or row.get("name") or "").strip()
    if not external_id or not title:
        raise ValueError("feed row must contain external_id/id/sku and title/name")
    raw_url = str(row.get("url") or row.get("link") or "").strip() or None
    url = urljoin(base_url, raw_url) if raw_url and base_url else raw_url
    return RawOffer(
        external_id=external_id,
        title=title,
        url=url,
        price=_price(row.get("price_sek") if row.get("price_sek") is not None else row.get("price")),
        currency=str(row.get("currency") or "SEK").upper(),
        stock_status=_stock(row.get("stock_status") if row.get("stock_status") is not None else row.get("availability")),
        is_preorder=_bool(row.get("is_preorder") if row.get("is_preorder") is not None else row.get("preorder")),
        observed_at=datetime.utcnow(),
        source_confidence=95,
    )

def parse_csv_feed(text: str, base_url: str | None = None) -> list[RawOffer]:
    reader = csv.DictReader(io.StringIO(text.lstrip("\ufeff")))
    offers = []
    for row in reader:
        try:
            offers.append(_offer(row, base_url))
        except (ValueError, TypeError):
            continue
    return offers

def _json_rows(data):
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("products","offers","items","data"):
            if isinstance(data.get(key), list):
                return data[key]
    raise ValueError("JSON feed must be a list or contain products/offers/items/data list")

def parse_json_feed(text: str, base_url: str | None = None) -> list[RawOffer]:
    data = json.loads(text)
    offers = []
    for row in _json_rows(data):
        if not isinstance(row, dict):
            continue
        try:
            offers.append(_offer(row, base_url))
        except (ValueError, TypeError):
            continue
    return offers

class GenericCsvFeedAdapter:
    key = "generic_csv_feed"
    def __init__(self, source_url: str):
        self.source_url = source_url
    async def fetch_offers(self) -> list[RawOffer]:
        async with httpx.AsyncClient(timeout=25, follow_redirects=True, headers={"User-Agent":USER_AGENT}) as client:
            r = await client.get(self.source_url)
            r.raise_for_status()
        return parse_csv_feed(r.text, str(r.url))

class GenericJsonFeedAdapter:
    key = "generic_json_feed"
    def __init__(self, source_url: str):
        self.source_url = source_url
    async def fetch_offers(self) -> list[RawOffer]:
        async with httpx.AsyncClient(timeout=25, follow_redirects=True, headers={"User-Agent":USER_AGENT}) as client:
            r = await client.get(self.source_url)
            r.raise_for_status()
        return parse_json_feed(r.text, str(r.url))
