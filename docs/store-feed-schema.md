# BoxFinder store feed schema

Preferred machine-readable source for a store is an explicit CSV/JSON feed supplied or approved by the store.

Required semantic fields:
- external_id / id / sku
- title / name
- price_sek / price

Recommended:
- url / link
- stock_status / availability
- currency
- is_preorder / preorder

Example CSV:

```csv
external_id,title,price_sek,stock_status,url,currency,is_preorder
123,2025-26 Upper Deck Series 1 Hobby Box,899,in_stock,https://example.se/p/123,SEK,false
```

Example JSON:

```json
{
  "products": [
    {
      "id": "123",
      "name": "2025-26 Upper Deck Series 1 Hobby Box",
      "price": 899,
      "availability": "in_stock",
      "url": "https://example.se/p/123",
      "currency": "SEK",
      "preorder": false
    }
  ]
}
```

A feed adapter must not run unless the store is explicitly marked `feed_allowed` or `api_allowed`.
Public HTML collection requires `robots_checked` and remains separate from feed permission.
