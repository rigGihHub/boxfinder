from .base import RawOffer

class ManualAdapter:
    key = "manual"
    async def fetch_offers(self) -> list[RawOffer]:
        return []
