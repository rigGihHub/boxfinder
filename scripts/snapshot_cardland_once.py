"""One-time, review-only inventory capture from Cardland's public category pages.

Run manually; do not schedule or use it to publish buyable offers. Category
listings cannot prove exact variant, release status, or current stock.
"""

import json
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup


BASE = "https://www.cardland.se"
CATEGORIES = {
    "NFL": "/amerikansk-fotboll",
    "Baseboll": "/baseball",
    "Basket": "/basket",
    "Fotboll": "/fotboll",
    "Hockey": "/hockeykort",
    "Övrig sport": "/ovriga-sporter",
    "Disney": "/disney",
    "Marvel": "/marvel",
    "Pokémon": "/pokemon",
    "Star Wars": "/star-wars",
    "Övriga boxar": "/ovriga-boxar",
}


def category_rows(entry):
    category, path = entry
    html = subprocess.check_output(
        ["curl", "-fsSL", "--max-time", "35", BASE + path], text=True
    )
    soup = BeautifulSoup(html, "html.parser")
    rows = []
    for card in soup.select("div.product"):
        link = card.select_one("h3 a.productlist-title")
        price = card.select_one("span.product-price")
        if not link or not price or not link.get("href"):
            continue
        url = urljoin(BASE, link["href"])
        if urlparse(url).netloc != "www.cardland.se":
            continue
        amount = re.sub(r"[^\d]", "", price.get_text())
        if not amount:
            continue
        rows.append({"id": urlparse(url).path.strip("/"), "title": link.get_text(" ", strip=True),
                     "url": url, "category": category, "price_sek": int(amount),
                     "listing_available": "Köpbar produkt!" in card.get_text(" ", strip=True)})
    if not rows:
        raise ValueError(f"No product cards found at {path}")
    return rows


def main():
    with ThreadPoolExecutor(max_workers=2) as pool:
        groups = list(pool.map(category_rows, CATEGORIES.items()))
    unique = {row["id"]: row for group in groups for row in group}
    snapshot = {"observed_at": datetime.now(timezone.utc).isoformat(),
                "sources": [BASE + path for path in CATEGORIES.values()],
                "products": list(unique.values())}
    destination = Path(__file__).resolve().parents[1] / "backend/app/snapshots/cardland_2026_10_02.json"
    destination.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n")
    print(len(unique), "distinct listings,", sum(row["listing_available"] for row in unique.values()),
          "marked buyable on category pages; review snapshot:", destination)


if __name__ == "__main__":
    main()
