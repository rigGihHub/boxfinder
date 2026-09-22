import hashlib
import json
import re
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
import httpx
from bs4 import BeautifulSoup
from .base import RawOffer

USER_AGENT = "BoxFinder/0.3 (+price-comparison; respectful-crawler)"
PRICE_RE = re.compile(r"(\d{1,3}(?:[ .]\d{3})*|\d+)(?:[,.](\d{1,2}))?\s*(?:kr|sek)", re.I)
CARD_TERMS = ("upper deck", "topps", "panini", "pokemon", "pokémon", "magic", "lorcana", "marvel", "hobby", "blaster", "booster", "trading card", "samlarkort")

def _price(text: str) -> float | None:
    m = PRICE_RE.search(text.replace("\xa0", " "))
    if not m:
        return None
    whole = re.sub(r"[ .]", "", m.group(1))
    decimal = m.group(2) or "0"
    return float(f"{whole}.{decimal}")

def _looks_relevant(title: str) -> bool:
    low = title.lower()
    return any(x in low for x in CARD_TERMS)

def _id(url: str | None, title: str) -> str:
    return hashlib.sha1((url or title).encode("utf-8")).hexdigest()[:24]

async def robots_allows(url: str, robots_url: str | None = None) -> bool:
    parsed = urlparse(url)
    robots_url = robots_url or f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    async with httpx.AsyncClient(timeout=12, follow_redirects=True, headers={"User-Agent": USER_AGENT}) as client:
        r = await client.get(robots_url)
        if r.status_code >= 400:
            return False
    rp = RobotFileParser()
    rp.set_url(robots_url)
    rp.parse(r.text.splitlines())
    return rp.can_fetch(USER_AGENT, url)

class PublicHtmlCatalogAdapter:
    key = "public_html_catalog"
    def __init__(self, source_url: str, robots_url: str | None = None):
        self.source_url = source_url
        self.robots_url = robots_url

    async def fetch_offers(self) -> list[RawOffer]:
        if not await robots_allows(self.source_url, self.robots_url):
            raise PermissionError("robots.txt does not allow this BoxFinder fetch or could not be verified")
        async with httpx.AsyncClient(timeout=20, follow_redirects=True, headers={"User-Agent": USER_AGENT}) as client:
            r = await client.get(self.source_url)
            r.raise_for_status()
        return parse_catalog_html(r.text, str(r.url))

def parse_catalog_html(html: str, base_url: str) -> list[RawOffer]:
    soup = BeautifulSoup(html, "html.parser")
    items: dict[str, RawOffer] = {}

    # Prefer explicit schema.org Product data when available.
    for node in soup.select('script[type="application/ld+json"]'):
        try:
            data = json.loads(node.get_text(strip=True) or "null")
        except Exception:
            continue
        stack = data if isinstance(data, list) else [data]
        for obj in stack:
            if not isinstance(obj, dict):
                continue
            if obj.get("@type") == "ItemList":
                stack.extend([x.get("item") for x in obj.get("itemListElement", []) if isinstance(x, dict) and x.get("item")])
                continue
            if obj.get("@type") != "Product":
                continue
            title = str(obj.get("name") or "").strip()
            offers = obj.get("offers") or {}
            if isinstance(offers, list):
                offers = offers[0] if offers else {}
            price = offers.get("price") if isinstance(offers, dict) else None
            try: price = float(str(price).replace(",", "."))
            except Exception: price = None
            if not title or price is None or not _looks_relevant(title):
                continue
            url = urljoin(base_url, obj.get("url") or offers.get("url") or "")
            availability = str(offers.get("availability", "")).lower()
            stock = "in_stock" if "instock" in availability else ("out_of_stock" if "outofstock" in availability else "unknown")
            items[_id(url, title)] = RawOffer(_id(url, title), title, url, price, stock_status=stock, source_confidence=95)

    # Conservative fallback for catalog cards/links. Requires title + SEK price in same card.
    for card in soup.select("article, li, .product, .product-card, .card, [data-product-id]"):
        text = " ".join(card.stripped_strings)
        price = _price(text)
        link = card.find("a", href=True)
        title = (link.get("title") if link else None) or (link.get_text(" ", strip=True) if link else "")
        title = re.sub(r"\s+", " ", title).strip()
        if price is None or len(title) < 6 or not _looks_relevant(title):
            continue
        url = urljoin(base_url, link["href"]) if link else None
        low = text.lower()
        stock = "out_of_stock" if any(x in low for x in ["slut i lager", "sold out", "out of stock"]) else "in_stock"
        preorder = any(x in low for x in ["förbeställ", "pre-order", "preorder"])
        key = _id(url, title)
        items.setdefault(key, RawOffer(key, title, url, price, stock_status=stock, is_preorder=preorder, source_confidence=75))
    return list(items.values())
