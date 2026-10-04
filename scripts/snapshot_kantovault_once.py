"""Fetch the complete public catalogue for a one-time, separately reviewed import.

Usage: python scripts/snapshot_kantovault_once.py /tmp/kantovault-raw.json
The output is evidence, not an automatic promotion into the ranking.
"""
import argparse
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen

from bs4 import BeautifulSoup

ROOT = "https://kantovault.se"
CARD_TAGS = {"Booster Pack", "Booster Box", "Booster Bundle", "Box & Deck",
             "Blisters", "Elite Trainer Box"}


def fetch_json(url):
    with urlopen(url, timeout=40) as response:
        return json.load(response)


def product_evidence(product):
    url = ROOT + "/products/" + product["handle"]
    with urlopen(url, timeout=40) as response:
        soup = BeautifulSoup(response.read(), "html.parser")
    pills = soup.select(".product-pills")
    notice = " ".join(pill.get_text(" ", strip=True) for pill in pills)
    for element in soup(["script", "style", "nav", "footer", "header"]):
        element.decompose()
    text = soup.get_text(" ", strip=True)
    content = text.split("Produktinnehåll", 1)[1].split("Frakt & retur", 1)[0] if "Produktinnehåll" in text else ""
    return product["id"], {"url": url, "content": content, "notice": notice,
                           "observed_at": datetime.now(timezone.utc).isoformat()}


def collect():
    products, pages = [], []
    for page in range(1, 100):
        rows = fetch_json(f"{ROOT}/products.json?limit=250&page={page}")["products"]
        pages.append(len(rows))
        products.extend(rows)
        if not rows:
            break
    else:
        raise RuntimeError("Catalogue pagination did not finish")
    if len({p["id"] for p in products}) != len(products):
        raise RuntimeError("Duplicate products across pages; retry the snapshot")
    observed_at = datetime.now(timezone.utc).isoformat()
    # Availability can include a preorder. Read product-local notices as well.
    eligible = [p for p in products if CARD_TAGS.intersection(p["tags"])
                and any(v["available"] for v in p["variants"])]
    with ThreadPoolExecutor(max_workers=4) as pool:
        evidence = dict(pool.map(product_evidence, eligible))
    return {"observed_at": observed_at, "source": ROOT + "/products.json?limit=250",
            "page_counts": pages, "pagination_complete": True,
            "products": products, "product_pages": evidence}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.write_text(json.dumps(collect(), ensure_ascii=False, indent=2))
