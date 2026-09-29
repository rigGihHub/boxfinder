"""Count sealed cards that are supplied outside the listed packs."""

SEPARATE_BOX_CARDS = {
    # Topps: two six-card packs plus a separate encased autograph topper.
    "dd-2025-26-topps-chrome-black-basketball-hobby": 1,
}


def total_sealed_cards(variant):
    if variant.packs is None or variant.cards_per_pack is None:
        return None
    return variant.packs * variant.cards_per_pack + SEPARATE_BOX_CARDS.get(variant.product.slug, 0)
