from datetime import datetime
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base

class Store(Base):
    __tablename__ = "stores"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    country: Mapped[str] = mapped_column(String(2), default="SE")
    homepage_url: Mapped[str | None] = mapped_column(String(500))
    source_url: Mapped[str | None] = mapped_column(String(1000))
    robots_url: Mapped[str | None] = mapped_column(String(1000))
    terms_url: Mapped[str | None] = mapped_column(String(1000))
    adapter_key: Mapped[str | None] = mapped_column(String(120))
    collection_method: Mapped[str] = mapped_column(String(40), default="manual")
    policy_status: Mapped[str] = mapped_column(String(40), default="review_required", index=True)
    min_interval_seconds: Mapped[int] = mapped_column(Integer, default=60)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime)
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime)
    last_error: Mapped[str | None] = mapped_column(Text)
    offers: Mapped[list["Offer"]] = relationship(back_populates="store")
    ingestion_runs: Mapped[list["IngestionRun"]] = relationship(back_populates="store")

class ShippingPolicy(Base):
    __tablename__ = "shipping_policies"
    id: Mapped[int] = mapped_column(primary_key=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id"), unique=True, index=True)
    base_shipping_sek: Mapped[float | None] = mapped_column(Float)
    free_shipping_threshold_sek: Mapped[float | None] = mapped_column(Float)
    source_url: Mapped[str | None] = mapped_column(String(1000))
    verification_status: Mapped[str] = mapped_column(String(40), default="review_required", index=True)
    confidence: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Product(Base):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(220), unique=True, index=True)
    canonical_name: Mapped[str] = mapped_column(String(300), index=True)
    category: Mapped[str] = mapped_column(String(80), index=True)
    manufacturer: Mapped[str] = mapped_column(String(120), index=True)
    year_season: Mapped[str | None] = mapped_column(String(40), index=True)
    series: Mapped[str | None] = mapped_column(String(160), index=True)
    variants: Mapped[list["ProductVariant"]] = relationship(back_populates="product")

class ProductVariant(Base):
    __tablename__ = "product_variants"
    __table_args__ = (UniqueConstraint("product_id", "format", "language", "region", name="uq_variant_identity"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    format: Mapped[str] = mapped_column(String(80), index=True)
    language: Mapped[str] = mapped_column(String(40), default="English")
    region: Mapped[str] = mapped_column(String(40), default="Global")
    packs: Mapped[int | None] = mapped_column(Integer)
    cards_per_pack: Mapped[int | None] = mapped_column(Integer)
    ean_upc: Mapped[str | None] = mapped_column(String(80), index=True)
    product: Mapped[Product] = relationship(back_populates="variants")
    offers: Mapped[list["Offer"]] = relationship(back_populates="variant")
    analysis: Mapped["BoxAnalysis | None"] = relationship(back_populates="variant", uselist=False)

class Offer(Base):
    __tablename__ = "offers"
    __table_args__ = (UniqueConstraint("store_id", "external_id", name="uq_store_external_offer"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id"), index=True)
    variant_id: Mapped[int | None] = mapped_column(ForeignKey("product_variants.id"), index=True)
    external_id: Mapped[str] = mapped_column(String(220))
    source_title: Mapped[str] = mapped_column(String(500))
    url: Mapped[str | None] = mapped_column(String(1000))
    price_sek: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(3), default="SEK")
    stock_status: Mapped[str] = mapped_column(String(30), default="unknown", index=True)
    is_preorder: Mapped[bool] = mapped_column(Boolean, default=False)
    source_kind: Mapped[str] = mapped_column(String(30), default="manual")
    source_confidence: Mapped[int] = mapped_column(Integer, default=50)
    observed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    match_confidence: Mapped[float | None] = mapped_column(Float)
    match_status: Mapped[str] = mapped_column(String(30), default="unmatched", index=True)
    store: Mapped[Store] = relationship(back_populates="offers")
    variant: Mapped[ProductVariant | None] = relationship(back_populates="offers")
    history: Mapped[list["PriceHistory"]] = relationship(back_populates="offer", cascade="all, delete-orphan")

class PriceHistory(Base):
    __tablename__ = "price_history"
    id: Mapped[int] = mapped_column(primary_key=True)
    offer_id: Mapped[int] = mapped_column(ForeignKey("offers.id"), index=True)
    price_sek: Mapped[float] = mapped_column(Float)
    stock_status: Mapped[str] = mapped_column(String(30))
    observed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    offer: Mapped[Offer] = relationship(back_populates="history")

class IngestionRun(Base):
    __tablename__ = "ingestion_runs"
    id: Mapped[int] = mapped_column(primary_key=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id"), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String(30), default="running", index=True)
    fetched_count: Mapped[int] = mapped_column(Integer, default=0)
    created_count: Mapped[int] = mapped_column(Integer, default=0)
    updated_count: Mapped[int] = mapped_column(Integer, default=0)
    matched_count: Mapped[int] = mapped_column(Integer, default=0)
    review_count: Mapped[int] = mapped_column(Integer, default=0)
    unmatched_count: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(Text)
    store: Mapped[Store] = relationship(back_populates="ingestion_runs")

class BoxAnalysis(Base):
    __tablename__ = "box_analyses"
    id: Mapped[int] = mapped_column(primary_key=True)
    variant_id: Mapped[int] = mapped_column(ForeignKey("product_variants.id"), unique=True, index=True)
    ev_low: Mapped[float | None] = mapped_column(Float)
    ev_high: Mapped[float | None] = mapped_column(Float)
    checklist_strength: Mapped[int | None] = mapped_column(Integer)
    hit_density: Mapped[int | None] = mapped_column(Integer)
    upside: Mapped[int | None] = mapped_column(Integer)
    floor_score: Mapped[int | None] = mapped_column(Integer)
    rookie_strength: Mapped[int | None] = mapped_column(Integer)
    liquidity: Mapped[int | None] = mapped_column(Integer)
    popularity: Mapped[int | None] = mapped_column(Integer)
    data_quality: Mapped[int] = mapped_column(Integer, default=0)
    risk: Mapped[str] = mapped_column(String(30), default="Okänd")
    probability_basis: Mapped[str] = mapped_column(String(30), default="unknown")
    reasons_json: Mapped[str] = mapped_column(Text, default="[]")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    variant: Mapped[ProductVariant] = relationship(back_populates="analysis")

class Checklist(Base):
    __tablename__ = "checklists"
    id: Mapped[int] = mapped_column(primary_key=True)
    variant_id: Mapped[int] = mapped_column(ForeignKey("product_variants.id"), unique=True, index=True)
    source_name: Mapped[str] = mapped_column(String(240))
    source_url: Mapped[str | None] = mapped_column(String(1000))
    source_type: Mapped[str] = mapped_column(String(40), default="official")
    verification_status: Mapped[str] = mapped_column(String(40), default="review_required", index=True)
    confidence: Mapped[int] = mapped_column(Integer, default=0)
    imported_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    notes: Mapped[str | None] = mapped_column(Text)
    cards: Mapped[list["Card"]] = relationship(back_populates="checklist", cascade="all, delete-orphan")

class Card(Base):
    __tablename__ = "cards"
    id: Mapped[int] = mapped_column(primary_key=True)
    checklist_id: Mapped[int] = mapped_column(ForeignKey("checklists.id"), index=True)
    card_number: Mapped[str | None] = mapped_column(String(80), index=True)
    subject: Mapped[str] = mapped_column(String(240), index=True)
    team_franchise: Mapped[str | None] = mapped_column(String(180), index=True)
    subset: Mapped[str] = mapped_column(String(180), default="Base", index=True)
    parallel: Mapped[str | None] = mapped_column(String(180), index=True)
    serial_numbered_to: Mapped[int | None] = mapped_column(Integer)
    is_rookie: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_autograph: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_memorabilia: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_case_hit: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    rarity_label: Mapped[str | None] = mapped_column(String(120))
    source_confidence: Mapped[int] = mapped_column(Integer, default=0)
    checklist: Mapped[Checklist] = relationship(back_populates="cards")
    odds: Mapped[list["Odds"]] = relationship(back_populates="card", cascade="all, delete-orphan")

class Odds(Base):
    __tablename__ = "odds"
    id: Mapped[int] = mapped_column(primary_key=True)
    card_id: Mapped[int | None] = mapped_column(ForeignKey("cards.id"), index=True)
    variant_id: Mapped[int] = mapped_column(ForeignKey("product_variants.id"), index=True)
    category_key: Mapped[str] = mapped_column(String(180), index=True)
    basis: Mapped[str] = mapped_column(String(30), default="unknown", index=True)
    source_name: Mapped[str | None] = mapped_column(String(240))
    source_url: Mapped[str | None] = mapped_column(String(1000))
    confidence: Mapped[int] = mapped_column(Integer, default=0)
    one_in_packs: Mapped[float | None] = mapped_column(Float)
    hits_per_box: Mapped[float | None] = mapped_column(Float)
    probability_per_box: Mapped[float | None] = mapped_column(Float)
    notes: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    card: Mapped[Card | None] = relationship(back_populates="odds")

class Sale(Base):
    __tablename__ = "sales"
    __table_args__ = (UniqueConstraint("source_name", "external_id", name="uq_sale_source_external"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    card_id: Mapped[int] = mapped_column(ForeignKey("cards.id"), index=True)
    source_name: Mapped[str] = mapped_column(String(120), index=True)
    external_id: Mapped[str] = mapped_column(String(220))
    source_url: Mapped[str | None] = mapped_column(String(1000))
    sold_price: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(3), default="SEK")
    price_sek: Mapped[float] = mapped_column(Float, index=True)
    condition_bucket: Mapped[str] = mapped_column(String(30), default="raw", index=True)
    grade_company: Mapped[str | None] = mapped_column(String(30), index=True)
    grade_value: Mapped[str | None] = mapped_column(String(20), index=True)
    sold_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    source_confidence: Mapped[int] = mapped_column(Integer, default=0)
    verified: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class CardMarketValue(Base):
    __tablename__ = "card_market_values"
    __table_args__ = (UniqueConstraint("card_id", "condition_bucket", name="uq_card_market_value_condition"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    card_id: Mapped[int] = mapped_column(ForeignKey("cards.id"), index=True)
    condition_bucket: Mapped[str] = mapped_column(String(30), default="raw", index=True)
    latest_price_sek: Mapped[float | None] = mapped_column(Float)
    median_7d_sek: Mapped[float | None] = mapped_column(Float)
    median_30d_sek: Mapped[float | None] = mapped_column(Float)
    median_90d_sek: Mapped[float | None] = mapped_column(Float)
    low_90d_sek: Mapped[float | None] = mapped_column(Float)
    high_90d_sek: Mapped[float | None] = mapped_column(Float)
    sales_7d: Mapped[int] = mapped_column(Integer, default=0)
    sales_30d: Mapped[int] = mapped_column(Integer, default=0)
    sales_90d: Mapped[int] = mapped_column(Integer, default=0)
    data_quality: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class CatalogCandidate(Base):
    __tablename__ = "catalog_candidates"
    __table_args__ = (UniqueConstraint("store_id", "external_id", name="uq_catalog_candidate_store_external"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id"), index=True)
    external_id: Mapped[str] = mapped_column(String(220))
    source_title: Mapped[str] = mapped_column(String(500), index=True)
    url: Mapped[str | None] = mapped_column(String(1000))
    price_sek: Mapped[float | None] = mapped_column(Float)
    stock_status: Mapped[str] = mapped_column(String(30), default="unknown", index=True)
    detected_format: Mapped[str | None] = mapped_column(String(80), index=True)
    category_hint: Mapped[str | None] = mapped_column(String(80), index=True)
    language_hint: Mapped[str | None] = mapped_column(String(40))
    year_season_hint: Mapped[str | None] = mapped_column(String(40))
    sealed_candidate: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    randomized: Mapped[bool] = mapped_column(Boolean, default=False)
    exclusion_reason: Mapped[str | None] = mapped_column(String(200))
    review_status: Mapped[str] = mapped_column(String(30), default="new", index=True)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class PriceSignal(Base):
    __tablename__ = "price_signals"
    __table_args__ = (
        UniqueConstraint("offer_id", "signal_type", "observed_at", name="uq_price_signal_offer_type_time"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    offer_id: Mapped[int] = mapped_column(ForeignKey("offers.id"), index=True)
    variant_id: Mapped[int] = mapped_column(ForeignKey("product_variants.id"), index=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id"), index=True)
    signal_type: Mapped[str] = mapped_column(String(40), index=True)
    old_price_sek: Mapped[float | None] = mapped_column(Float)
    new_price_sek: Mapped[float | None] = mapped_column(Float)
    change_pct: Mapped[float | None] = mapped_column(Float)
    previous_stock_status: Mapped[str | None] = mapped_column(String(30))
    current_stock_status: Mapped[str | None] = mapped_column(String(30))
    evidence: Mapped[str | None] = mapped_column(Text)
    observed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class WatchRule(Base):
    __tablename__ = "watch_rules"
    id: Mapped[int] = mapped_column(primary_key=True)
    variant_id: Mapped[int] = mapped_column(ForeignKey("product_variants.id"), index=True)
    trigger_type: Mapped[str] = mapped_column(String(40), index=True)
    threshold_sek: Mapped[float | None] = mapped_column(Float)
    active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    label: Mapped[str | None] = mapped_column(String(240))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_triggered_at: Mapped[datetime | None] = mapped_column(DateTime)

class WatchEvent(Base):
    __tablename__ = "watch_events"
    __table_args__ = (
        UniqueConstraint("watch_rule_id", "price_signal_id", name="uq_watch_event_rule_signal"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    watch_rule_id: Mapped[int] = mapped_column(ForeignKey("watch_rules.id"), index=True)
    variant_id: Mapped[int] = mapped_column(ForeignKey("product_variants.id"), index=True)
    price_signal_id: Mapped[int | None] = mapped_column(ForeignKey("price_signals.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(40), index=True)
    message: Mapped[str] = mapped_column(String(500))
    price_sek: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    read_at: Mapped[datetime | None] = mapped_column(DateTime)


class ScopeWatchRule(Base):
    __tablename__ = "scope_watch_rules"
    id: Mapped[int] = mapped_column(primary_key=True)
    category: Mapped[str | None] = mapped_column(String(80), index=True)
    format: Mapped[str | None] = mapped_column(String(80), index=True)
    manufacturer: Mapped[str | None] = mapped_column(String(120), index=True)
    max_price_sek: Mapped[float | None] = mapped_column(Float)
    trigger_type: Mapped[str] = mapped_column(String(40), default="matching_offer", index=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    label: Mapped[str | None] = mapped_column(String(240))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_triggered_at: Mapped[datetime | None] = mapped_column(DateTime)

class ScopeWatchEvent(Base):
    __tablename__ = "scope_watch_events"
    __table_args__ = (
        UniqueConstraint("scope_watch_rule_id", "price_signal_id", name="uq_scope_watch_event_rule_signal"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    scope_watch_rule_id: Mapped[int] = mapped_column(ForeignKey("scope_watch_rules.id"), index=True)
    variant_id: Mapped[int] = mapped_column(ForeignKey("product_variants.id"), index=True)
    price_signal_id: Mapped[int | None] = mapped_column(ForeignKey("price_signals.id"), index=True)
    message: Mapped[str] = mapped_column(String(500))
    price_sek: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    read_at: Mapped[datetime | None] = mapped_column(DateTime)


class StoreIntakeProfile(Base):
    __tablename__ = "store_intake_profiles"
    id: Mapped[int] = mapped_column(primary_key=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id"), unique=True, index=True)
    feed_format: Mapped[str] = mapped_column(String(20), default="csv", index=True)
    field_mapping_json: Mapped[str] = mapped_column(Text, default="{}")
    base_url: Mapped[str | None] = mapped_column(String(1000))
    source_url: Mapped[str | None] = mapped_column(String(1000))
    sample_hash: Mapped[str | None] = mapped_column(String(80), index=True)
    status: Mapped[str] = mapped_column(String(30), default="draft", index=True)
    rows_seen: Mapped[int] = mapped_column(Integer, default=0)
    valid_rows: Mapped[int] = mapped_column(Integer, default=0)
    invalid_rows: Mapped[int] = mapped_column(Integer, default=0)
    last_validated_at: Mapped[datetime | None] = mapped_column(DateTime)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ProductFact(Base):
    __tablename__ = "product_facts"
    id: Mapped[int] = mapped_column(primary_key=True)
    variant_id: Mapped[int] = mapped_column(ForeignKey("product_variants.id"), unique=True, index=True)
    facts_json: Mapped[str] = mapped_column(Text, default="[]")
    source_name: Mapped[str] = mapped_column(String(160))
    source_url: Mapped[str] = mapped_column(String(1000))
    verified_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    confidence: Mapped[int] = mapped_column(Integer, default=100)


class ChaseProfile(Base):
    __tablename__ = "chase_profiles"
    id: Mapped[int] = mapped_column(primary_key=True)
    variant_id: Mapped[int] = mapped_column(ForeignKey("product_variants.id"), unique=True, index=True)
    content_json: Mapped[str] = mapped_column(Text, default="{}")
    source_name: Mapped[str] = mapped_column(String(200))
    source_url: Mapped[str] = mapped_column(String(1000))
    verified_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    confidence: Mapped[int] = mapped_column(Integer, default=100)


class ChaseCard(Base):
    __tablename__ = "chase_cards"
    id: Mapped[int] = mapped_column(primary_key=True)
    canonical_key: Mapped[str] = mapped_column(String(300), unique=True, index=True)
    player_name: Mapped[str] = mapped_column(String(200), index=True)
    card_name: Mapped[str] = mapped_column(String(400), index=True)
    card_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    category: Mapped[str] = mapped_column(String(80), index=True)
    rookie: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

class VariantChaseCard(Base):
    __tablename__ = "variant_chase_cards"
    id: Mapped[int] = mapped_column(primary_key=True)
    variant_id: Mapped[int] = mapped_column(ForeignKey("product_variants.id"), index=True)
    chase_card_id: Mapped[int] = mapped_column(ForeignKey("chase_cards.id"), index=True)
    tier: Mapped[str] = mapped_column(String(40), index=True)
    odds_text: Mapped[str | None] = mapped_column(String(300), nullable=True)
    serial_to: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_url: Mapped[str] = mapped_column(String(1000))
    confidence: Mapped[int] = mapped_column(Integer, default=95)
