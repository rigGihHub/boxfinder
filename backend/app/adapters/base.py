from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol

@dataclass
class RawOffer:
    external_id: str
    title: str
    url: str | None
    price: float
    currency: str = "SEK"
    stock_status: str = "unknown"
    is_preorder: bool = False
    observed_at: datetime = field(default_factory=datetime.utcnow)
    source_confidence: int = 80

class StoreAdapter(Protocol):
    key: str
    async def fetch_offers(self) -> list[RawOffer]: ...
