from urllib.parse import urlparse


def is_direct_purchase_url(url: str | None) -> bool:
    """Only treat article-level URLs as purchase links."""
    if not url:
        return False
    parsed = urlparse(url)
    path = (parsed.path or "").rstrip("/").lower()
    if parsed.scheme not in {"http", "https"} or not parsed.netloc or not path:
        return False
    return "/category/" not in path
