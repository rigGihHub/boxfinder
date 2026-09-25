# BoxFinder v0.47.2

## v0.47.2 – CardSurfer catalog and UWCL odds

- Added verified CardSurfer offers for Prizm Basketball, Chrome UWCL, WWE, O-Pee-Chee and PWHL.
- Added format-safe chase profiles for the Prizm retail blaster and Chrome UWCL hobby box.
- Recorded official Topps UWCL checklist names and hobby-family odds without presenting family odds as player odds.
- Rejected unavailable NordicBreaks personals, inconsistent sold-out DrakenDavids listings and Marvel preorders.

## v0.47.1 – Magic/Marvel multi-store expansion
- Added four in-stock Dragon's Lair products: Marvel Super Heroes Play Booster and Bundle plus Spider-Man Play Booster and Display.
- Added Dragon's Lair as a second verified offer for the existing Marvel Super Heroes Play Booster Display.
- Added official Wizards slot odds and named Play Booster chases without leaking Collector Booster-exclusive headliners.
- Product fact provenance now names the actual store instead of always saying Coolcard.

## v0.47.0 – Format-safe catalog expansion
- Added verified Basket, NFL, Yu-Gi-Oh and Racing products with exact Swedish purchase links.
- Added format-specific chase profiles for hobby boxes, retail boxes, hangers and loose packs.
- Serial numbers such as `1/1` and negated guarantees no longer count as published pull odds.
- Replaced shared display/loose-pack profiles with explicit pack-safe variants.

## v0.39.1 – Release hardening
- Fixed clean-database startup failure in chase-profile seeding.
- Fixed frontend build blockers in Source Hub and Chase Finder.
- Added shared API helper for server-rendered chase search.
- Upgraded Next.js to 14.2.35.


## Nytt i v0.13.1
- Verifierad svensk källkartläggning utökad med Kortlagret som kandidat.
- Bulkimport av riktiga butikserbjudanden via CSV: `POST /admin/stores/{store_id}/offers/import-csv`.
- CSV-importen använder samma produktmatchningsmotor som crawlerflödet och skapar PriceHistory automatiskt.
- Stöd för lagerstatus, preorder, valuta, URL och externa produkt-ID:n i importen.
- Källpolicyn är fortsatt strikt: nya publika butiker ligger som `review_required` tills automatisk insamling uttryckligen är godkänd.
- Backend verifierad med 32/32 tester.

### CSV-format
Obligatoriskt: `external_id,title,price_sek`
Valfritt: `stock_status,url,currency,is_preorder`

Exempel:
```csv
external_id,title,price_sek,stock_status,url
SKU-123,2025-26 Upper Deck Series 1 Hobby Box,799,in_stock,https://butik.se/produkt
```

## Nytt
- Budget Builder: svarar på “Jag har X kr – vad ska jag köpa?”
- Kombinerar enskilda produkter och tvåprodukt-mixar inom budget.
- Fyra mål: `balanced`, `value`, `chase`, `fun`.
- Budget Fit Score 0–100 är en jämförelsesignal, inte avkastningsprognos.
- Saknad EV eller analysdata behandlas som saknad data, aldrig som noll.
- Returnerar totalpris, kvarvarande budget, EV-intervall när tillgängligt och datatäckning.
- Frontend har snabbval för 500, 1 000 och 2 000 kr.

## API
`GET /budget/recommendations?budget=1000&goal=balanced&limit=5`

Mål:
- `balanced`: värde + hit density + golv + upside + öppningsupplevelse
- `value`: Box Value + EV/pris
- `chase`: stor hitpotential med datakvalitet som broms
- `fun`: fler packs, variation och hit density

## Viktig princip
Budget Builder beskriver statistiskt samlarvärde och öppningsprofil. Den är inte en prognos om vinst och ska inte framställa boxöppning som investering.


## v0.10.0 – Box Battle
- Nytt `/compare?ids=1,2[,3,4]`-API för jämförelse av 2–4 produktvarianter.
- Vinnare per pris, Box Value, EV/pris, rookies, hit density, upside, golv, risk och datakvalitet.
- EV/pris kräver minst 55/100 datakvalitet innan en vinnare kan utses.
- Kategorier med otillräcklig data lämnas utan vinnare i stället för att gissas.
- Övergripande battle-vinnare baseras på antal kategorivinster, inte på en ny ogenomskinlig superscore.
- Frontend har en ny Box Battle-sektion i samma foil/samlarbox-identitet.


## v0.10.0 – Product Intelligence Page
- Complete product detail endpoint with offers, price history summaries, checklist metadata and EV coverage.
- Top 25 chase-card board using raw market values and best usable odds.
- “Vanligt / Bra träff / Stor hit / Jackpot” outcome groups without inventing missing cards or odds.
- Deterministic data-grounded product summary; demo data is explicitly warned against for purchase decisions.
- Dedicated premium collectible-box product page in the Next.js frontend.

## v0.13.1 – Ranking Readiness

Every product now gets an explainable readiness gate:
- **Redo**: enough verified/fresh data for ranking.
- **Nästan redo**: useful but incomplete.
- **För lite data**: should not be presented as equally trustworthy.

Components include fresh matched store coverage, checklist verification, odds coverage,
raw market-value coverage, and analysis data quality. The API exposes this on product
responses and at `GET /admin/ranking-readiness`.

## Start locally on Windows

Prerequisites: Python 3.12+ and Node.js LTS. PostgreSQL is optional for the first local
run because the default development database is SQLite.

Backend (PowerShell):
```
cd backend
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Frontend (a second PowerShell window):
```
cd frontend
npm install
$env:NEXT_PUBLIC_API_URL="http://localhost:8000"
npm run dev
```

Open `http://localhost:3000`. API documentation is at `http://localhost:8000/docs`.

For PostgreSQL later, set `DATABASE_URL` before starting the backend, for example:
```
$env:DATABASE_URL="postgresql+psycopg://boxfinder:PASSWORD@localhost:5432/boxfinder"
```


## v0.13.1 – Source Hub

New admin-facing Source Hub at `/admin/source-hub`:
- Prioritized Swedish store candidates.
- Category coverage and source strengths.
- Explicit automation status: allowed, manual only, or blocked pending review.
- Last attempt/success/error visibility.
- Clear recommendation for CSV/feed vs crawling.
- Curated MVP source set: Coolcard, Samlarhobby, Bangerpack, Kortlagret, Pardon My Kicks, MajkiPoké, TCGPoke, Hatstore.

Important: public storefront access is not treated as permission for automated crawling. CSV/feed/manual import remains the default until a source has been reviewed.


## v0.13.1 – clearer value at a glance
- Product cards now show up to three verified chase/good-hit cards from the imported checklist and raw market data.
- No chase names are fabricated; missing checklist/chase data is shown as missing.
- Budget Builder presets now include 100 kr and 250 kr.
- Dagens boxfynd now falls back to the current top three products when no deal passes the verified-deal threshold, clearly labelled as not verified bargains.


## v0.14.0 – Data Update Manager + expanded Swedish source map

- New Data Update Manager in Source Hub.
- Manual `Uppdatera data nu` action.
- Automatic scheduled source update every 6 hours while the backend is running.
- Explicit run status, last/next run, fetched/created/updated counters.
- Source policy remains a hard gate: unapproved sources are skipped rather than crawled.
- Swedish source catalog expanded to 26 store candidates across sports cards and TCG.
- The strategy is now broad sealed-product coverage first; advanced EV/ranking is added only when checklist, odds and market-value quality is sufficient.

## v0.15.0 – Swedish Sealed Catalog Engine

- Added a dedicated sealed-product normalization taxonomy.
- Distinguishes case, hobby box, retail box, mega box, blaster, booster box, booster bundle, ETB, collection box, tin, hanger, bundle, starter deck and single pack.
- Strong safety rule prevents cases from being matched as boxes.
- Accessories such as sleeves, albums, binders and deck boxes are excluded from the sealed candidate queue.
- New CatalogCandidate discovery queue captures non-matched store items rather than silently dropping them.
- Candidates get format, category, language, season, sealed/randomized flags and review status.
- New admin endpoints for candidate list, candidate stats and title normalization preview.
- Source map expanded with Terratide and TCG Deals Sverige; Hatstore promoted for sports-card coverage.

## v0.16.0 – Store Product Discoverer

- Added generic approved CSV and JSON feed adapters for complete store catalogs.
- Feed adapters are hard-gated: they only run with `feed_allowed` or `api_allowed`.
- Public HTML adapter is now separately gated behind `robots_checked`.
- Added admin discovery queue page at `/admin/catalog`.
- Added catalog candidate link/reject/reopen endpoints.
- Unknown store products can be captured and reviewed without affecting ranking.
- Added a documented standard store-feed schema.
- Source Hub links directly to the product discovery queue.

## v0.17.0 – Multi-store Product Dedup

- Added deterministic product identity fingerprints for sealed products.
- Same unknown product from several stores is grouped before canonical creation.
- Hard identity fields keep case/box/pack, season, language and category conflicts separate.
- Added candidate-to-existing-variant suggestions with explainable confidence.
- Added `/admin/catalog-clusters` and `/admin/catalog-candidates/{id}/suggestions`.
- Product Queue now highlights likely same-product groups across Swedish stores and shows the price span.
- Existing known variants continue to auto-match store offers, so one canonical product can carry prices from many stores.

## v0.18.0 – Trusted Swedish Price Comparison

- Added price comparison for one canonical product across multiple Swedish stores.
- Only fresh in-stock, non-preorder, trusted matches enter the safe comparison.
- Added separate best item price and best total price.
- Shipping is never silently assumed to be 0 SEK; total price appears only when shipping rules are verified.
- Added per-store ShippingPolicy as a new table, safe for existing SQLite databases via create_all.
- Added store median, price spread, shipping coverage and fresh observation timestamps.
- Added `/products/{variant_id}/price-comparison` plus admin shipping-policy endpoints.
- Product detail UI now separates trusted price comparison from raw observed store data.

## v0.19.0 – Evidence-based Dagens boxfynd

- Deal Scanner now combines three independent price signals: robust historical reference, current peer-store pricing and proximity to the historical low.
- Fresh current offers are limited to 14 days and must be in stock, non-preorder and trusted matched.
- Manual matches are accepted alongside auto matches; demo offers never create a real deal.
- Added explainable deal labels: Normalt pris, Intressant pris, Bra fynd and Starkt fynd.
- Each deal exposes the evidence behind the label instead of relying on one opaque score.
- Cross-store discount, history low/high, history position and signal list are returned by `/deals`.
- Frontend Dagens boxfynd now shows the evidence directly.

## v0.20.0 – Intelligent Price Watch

- Added persistent PriceSignal events.
- Ingestion detects meaningful price drops (>2%), new 30-day lows, new 90-day lows, back-in-stock events and a new store for an already-known box.
- Signals are generated only for auto-matched canonical products during automated ingestion.
- Historical-low detection compares against observations before the current update to avoid self-comparison.
- Added `GET /deals/signals/recent` for recent price intelligence.
- Signal events preserve old/new price, stock transition, timestamp and evidence.

## v0.21.0 – Price Radar / What Changed

- Added a user-facing Price Radar section: "Vad har hänt sedan sist?"
- Home page shows recent price drops, new 30-day lows, back-in-stock events and newly discovered stores.
- Price signal feed is enriched with product name, category and store name.
- Added `/deals/signals/summary` for compact 7/30/90-day signal summaries.
- Product detail now includes the latest 30-day price events for that exact sealed product.
- Empty states remain explicit; BoxFinder does not invent activity before real store updates exist.

## v0.22.0 – Personal Watch Engine

- Added persistent watch rules for exact sealed-product variants.
- Supported triggers: price below a chosen SEK threshold, back in stock, new 90-day low and next price drop.
- Price-threshold rules are checked immediately when created, so an already-good price is not missed.
- New price signals from ingestion automatically evaluate active watch rules.
- Added persistent WatchEvent inbox with read/unread state and audit history.
- Added `/watchlist/rules` and `/watchlist/events` API endpoints.
- Product detail now has direct watch controls.
- Added `/watchlist` UI showing active rules and triggered events.
- No external notification channel is claimed yet; this release creates the reliable in-app trigger/inbox layer first.

## v0.23.0 – Broad Collector Watches

- Added broad watch rules that can watch categories, formats, manufacturers and maximum price instead of only one exact box.
- Examples: all Hockey hobby boxes under 500 SEK, all Pokémon Elite Trainer Boxes under 600 SEK.
- Broad watch rules can react to any matching signal, price drops, new 90-day lows or back-in-stock events.
- Scope watches are evaluated automatically during ingestion alongside exact-product watches.
- Added persistent scope-watch events and API endpoints under `/watchlist/scope-*`.
- Watchlist UI now includes a simple broad-watch builder and recent matching products.
- Broad watch matching remains strict: no category/format guessing is introduced.

## v0.24.0 – Collector Discovery

- Added a new `/discover` purchase-discovery flow: category/sport → budget → collector goal → three differentiated recommendations.
- Collector goals: balanced, autographs, rookies, jackpot, many hits and fun-to-open.
- Recommendations are deliberately split into `Mitt val`, `Säkrare val` and `Jackpotval` rather than pretending one box fits everyone.
- Added separate `BOXEN` and `PRISET NU` scores. Product quality is not allowed to hide a bad current price, and a cheap price is not allowed to make a weak box look intrinsically strong.
- Added an Opening Profile with jackpot, hit frequency, rookies, variety, autographs and risk.
- Checklist traits count identified autographs, rookies, case hits and memorabilia without inventing guarantees.
- Top chase cards are shown only when checklist/market data exists.
- Discovery confidence is explicit; missing market/checklist/odds data remains missing.
- Added `GET /discovery/recommendations`.
- Homepage now has a direct “Jag vill öppna något” entry point.

## v0.25.0 – Catalog Coverage Control Tower

- Added a catalog-coverage engine focused on the current real bottleneck: Swedish store/product data.
- Source Hub now measures each store's readiness, trusted offers, fresh in-stock offers, stale offers, catalog candidates and blockers.
- Added category coverage showing expected Swedish sources vs sources with fresh trusted offers.
- Added prioritized next data actions, so the app can say whether the next task is policy review, feed/API/CSV setup, first verified import, product matching or price/stock refresh.
- Fresh live coverage requires trusted matching, in-stock, non-preorder and an observation timestamp no older than 14 days.
- Added `GET /admin/catalog-coverage`.
- Fixed taxonomy so generic `Display` is its own canonical sealed format instead of silently being treated as `booster box`.
- No crawling permission is inferred from public availability.

## v0.26.0 – Store Intake Pipeline

- Added a reusable store intake wizard for CSV and JSON product feeds.
- BoxFinder now auto-detects common Swedish and English fields for product ID, title, price, stock, URL, currency and preorder.
- New feed preview validates rows before activation and shows detected categories, sealed formats and representative products.
- Added persistent StoreIntakeProfile records with mapping, source URL, validation state and row-quality metrics.
- Added GenericMappedFeedAdapter so differently named retailer feeds can be connected without writing one custom adapter per store.
- Feed activation never changes collection policy. A mapped feed still requires `feed_allowed` or `api_allowed` before ingestion can run.
- Added `/admin/intake` UI and API endpoints for preview, save, retrieve and activate intake profiles.
- Existing normalization and discovery queue remain in the path after ingestion.

## v0.27.0 – Feed Onboarding Batch

- Added batch onboarding status for all configured Swedish store sources.
- Added `GET /admin/intake/batch-status` with profile, policy, adapter and automation readiness per store.
- Added `POST /admin/intake/batch` to validate/save several CSV/JSON feed samples in one request.
- Added `/admin/intake/batch` UI showing validated profiles, policy blockers and which stores are actually automation-ready.
- A validated feed profile and collection permission remain separate requirements; batch onboarding never overrides policy.

## v0.28.0 – Store Activation Queue
- Prioritizes Swedish sources by strategic sealed-card coverage and actual technical readiness.
- Separates strategic value from policy/feed readiness; priority can never bypass collection permission.
- Adds `/admin/activation` and `GET /admin/stores/activation-queue`.
- Queue exposes blockers and the next concrete onboarding action per store.

## v0.29.0 – Usable Test Catalog + Fresh Data Button
- Fixed an upgrade bug where older local databases could contain some products but miss the starter discovery catalog, leaving Collector Discovery empty.
- Starter/test products are now seeded idempotently per slug/variant rather than only when the entire product table is empty.
- Added a visible `Uppdatera data nu` control on the homepage and Collector Discovery.
- The refresh control runs the real Update Manager, reports checked/success/blocked/fetched counts, and reloads the UI after completion.
- Refresh never bypasses store collection policy; blocked sources remain blocked.
- Automatic source refresh remains every six hours while the backend is running.

## v0.30.0 – Self-healing Local Test Startup
- Detects frontend/backend version mismatch in DATASTATUS.
- Adds `/system/diagnostics` and idempotent `/system/repair`.
- `Uppdatera + kontrollera data` repairs missing starter catalog before running Update Manager.
- Local dev CORS includes ports 3000 and 3001.
- Collector Discovery marks starter recommendations as `TESTDATA · EJ BUTIKSPRIS`.
- Empty discovery now points to backend/version status instead of silently appearing empty.

## v0.31.0 – First Verified Swedish Market Snapshot

- Added a curated, source-verifiable Swedish sealed-card snapshot from Coolcard dated 2026-09-12.
- Adds 20+ real hockey boxes, blasters and packs with current observed SEK price, stock state, packs/cards and store source.
- Real snapshot offers are stored separately as `verified_snapshot`, confidence 100, manual matched; they are never presented as live feeds.
- Added verified product facts for products where the source page exposes box-break/content information (Series 1, Series 2, O-Pee-Chee and Clear Cut).
- Added `GET /discovery/real-catalog` and a new “Riktig svensk butiksdata” section in Collector Discovery.
- Real products do not receive invented Box Value, EV or chase scores when analysis inputs are missing.
- Update/data status now reports the number of verified snapshots and explicitly says when blocked sources were not refreshed.

## v0.32.0 – More real data + click-through + Why this box?

- Expanded the verified Swedish snapshot with current Coolcard football and Pokémon sealed products alongside hockey.
- Added verified football products such as Panini Prizm FIFA, Topps Chrome/Team Set/Premier League products, Futera and low-cost UCC/MLS formats.
- Added verified Pokémon collection boxes, booster boxes/displays and ETB data.
- Added a product-explanation engine that clearly separates “why this product is interesting” from “is this actually a deal?”.
- A product with only one current store observation is explicitly labelled `Fyndstatus ej verifierad`; BoxFinder will not call it a deal without comparison evidence.
- Main product cards, mini rankings, Box Battle, Deal Scanner, Collector Discovery and budget product lines now click through to the exact BoxFinder product.
- Product detail includes a dedicated `Varför är den intressant? / Bra box eller faktiskt fynd?` section.

## v0.33.0 – Chase & Content Engine
- Product quality is now content-first: what attractive cards can actually be pulled matters more than price.
- Added verified chase profiles for 2025-26 Upper Deck Series 1 Hobby, Series 2 Hobby and Clear Cut Hobby.
- Product pages show four pull tiers: common-interesting, good hit, big hit and monster hit.
- Added key chase names, verified odds/serial-number information, content caveats and source links.
- Collector Discovery now ranks verified catalog products with mapped chase content ahead of unmapped products and surfaces good-hit/jackpot examples.
- Content Score is deliberately not EV and does not imply profitability.
- Missing chase evidence yields no score rather than an invented one.

## v0.34.0 – Content-first expansion
- Expanded Chase & Content profiles beyond the initial three products.
- Added verified-content profiles for O-Pee-Chee Hobby, Series 2 Retail Blaster, Panini Prizm FIFA Choice, Topps Bayern Lineage, Pokémon Mega Zygarde Premium Collection and Paradox Rift 18-pack display.
- Profiles with incomplete checklists deliberately leave player names/odds blank instead of guessing.
- Content score now puts slightly more emphasis on repeatable interesting pulls and less on merely having famous names.
- Added opening-style labels such as Hit-koncentrerad, Jackpot-tung and Balanserad chase.
- Collector Discovery explicitly sorts mapped chase content before unmapped products.

## v0.35.0 – Exact Chase Card Ladder
- Added card-level chase intelligence instead of only product-level descriptions.
- Series 2 Hobby now maps exact Young Guns numbers for Matthew Schaefer #451, Michael Misa #487, Zeev Buium #486, Danila Yurov #452, Easton Cowan #462 and Alexander Nikishin #461.
- Series 2 maps verified Young Guns Outburst 1:60, Clear Cut 1:144, Deluxe /250, Exclusives /100, Outburst Red /25, High Gloss /10 and Outburst Gold 1/1.
- Added rare Schaefer paths including Celebration Variation and Program of Excellence Canvas.
- Clear Cut maps major signed names and premium /25, /10, 1/1, Gold Ink and SSP autograph paths.
- Product pages now show an exact BRA -> MYCKET BRA -> MONSTER -> JACKPOT card ladder with odds/serial information.
- Discovery prioritizes card-level mapped products over generic product-level profiles.

## v0.36.0 – Pull Profile + Series 1/O-Pee-Chee exact chase data
- Series 1 Hobby now has exact card-level chase paths including Ivan Demidov #205, Artyom Levshunov #201, Gabe Perreault #202 and verified Young Guns parallel odds/serials.
- O-Pee-Chee Hobby now maps high-series Marquee Rookies and verified Blue/Red/Retro Black /100/Purple /49/1-of-1 chase paths.
- Added Pull Profile: `Bra saker ofta`, `Hur högt är taket?`, and `Varians`.
- Pull Profile measures collector experience and chase structure, not financial EV.
- Missing evidence still yields no invented score.

## v0.37.0 – Chase Database + Chase Finder
- Introduced normalized `ChaseCard` and `VariantChaseCard` tables.
- The same canonical card can now be linked to multiple box formats without duplicating the card.
- Seeded exact named chase cards for Series 1, Series 2 and Clear Cut.
- Matthew Schaefer and Michael Misa Young Guns are linked to both Series 2 Hobby and Retail Blaster, while format-specific odds remain separate.
- Added `/chase/search` and `/chase/players`.
- Added `/chase` UI: search a player and see which verified boxes can contain their mapped chase cards, current verified price, tier and format-specific odds.
- Home page now leads with `Vilket kort vill du dra?`.
- Unknown checklist relationships are not inferred.

## v0.38.0 – Player-to-Box Intelligence
- Deepened the normalized chase database with exact Series 1/Series 2 inserts and rare chase routes.
- Added Matthew Schaefer Incarnations INC-5 (1:1,920), Population Count PC-37 and Program of Excellence Canvas C-259.
- Added Michael Misa and Zeev Buium Incarnations, plus additional Canvas/Population Count paths.
- Added more Ivan Demidov Series 1 chase cards.
- New `/chase/best-boxes` aggregates all verified chase routes for a player and ranks purchasable box formats.
- Chase Finder now answers `What should I buy if I want to pull this player?`, with budget filtering.
- Ranking is checklist/chase coverage, not financial EV, and explicitly says so.

## v0.39.0 – Evidence-aware Chase Opportunity
- Fixed a conceptual weakness: checklist coverage is no longer presented as if it were pull probability.
- Added an odds parser that only accepts explicit numeric odds such as 1:60; serial numbering and vague checklist claims do not create fake probabilities.
- Computes approximate per-box probability from explicit per-pack odds and known pack count.
- Best-box ranking now separates Coverage Score from Opportunity Score.
- Added opportunity per 1,000 SEK when numeric odds and verified price both exist.
- UI shows per-box approximations only for routes with numeric odds and says ODDS SAKNAS otherwise.
