from pydantic import BaseModel, ConfigDict

class MatchRequest(BaseModel):
    source_title: str
    canonical_name: str
    expected_format: str | None = None

class MatchResult(BaseModel):
    score: float
    status: str

class OfferOut(BaseModel):
    store: str
    price_sek: float
    stock_status: str
    source_kind: str
    observed_at: str

class ProductCardOut(BaseModel):
    id: int
    slug: str
    name: str
    category: str
    manufacturer: str
    format: str
    price: float
    market_median: float | None
    store: str
    packs: int | None
    cards_per_pack: int | None
    total_cards: int | None
    ev_low: float | None
    ev_high: float | None
    box_value_score: int | None
    data_quality: int
    risk: str
    source_kind: str
    discount_pct: int | None
    match_status: str
    model_config = ConfigDict(from_attributes=True)
