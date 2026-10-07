"""Account for format-specific cards beyond the pack-count baseline."""

SEPARATE_BOX_CARDS = {
    # Topps: two six-card packs plus a separate encased autograph topper.
    "dd-2025-26-topps-chrome-black-basketball-hobby": 1,
    # Nine 14-card Play Boosters plus one 15-card Collector Booster.
    # The two promo cards and lands are described separately from booster cards.
    "ad-mtg-tmnt-pizza-bundle": 1,
}


def total_sealed_cards(variant):
    # Current mixed-pack evidence has no common cards_per_pack value.
    if (variant.product.slug == "ad-mtg-tmnt-pizza-bundle"
            and variant.packs == 10 and variant.cards_per_pack is None):
        return 141  # 9 × 14 Play + 1 × 15 Collector, excluding promos/lands.
    if variant.packs is None or variant.cards_per_pack is None:
        return None
    return variant.packs * variant.cards_per_pack + SEPARATE_BOX_CARDS.get(variant.product.slug, 0)
