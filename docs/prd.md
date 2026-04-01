## Problem Statement

The current repository demonstrates a basic buy-now-or-wait prototype, but it does not yet behave like a self-service dashboard with a clear medallion ETL design. Item search works only for a small static catalog, image lookup is mostly a filename heuristic, the ETL output is a single processed file, and the CamelCamelCamel path is tightly coupled to one scraping function.

The user wants a proof-of-concept shopping advisory dashboard that can:

- accept a typed item name or an uploaded image
- locate the most likely catalog item
- use price-history data inspired by CamelCamelCamel
- use Shopbot-derived current-price data
- predict whether the buyer should buy now or wait
- estimate the next better buying window based on seasonality and upcoming sale periods
- show best observed prices in trailing 30, 60, and 90 days
- show predicted prices in 30, 60, and 90 days
- show a 6-month and 1-year price trend view
- run ETL on GitHub Actions using a medallion architecture

## Solution

Build a proof-of-concept dashboard around a deeper data pipeline with explicit `bronze`, `silver`, and `gold` layers.

- `bronze` stores raw price observations from sample seed data, CamelCamelCamel injections, and optional experimental scraping.
- `bronze` also accepts Shopbot current-price injections and an optional Shopbot live adapter.
- `silver` normalizes, deduplicates, and standardizes those observations into a clean analytical table.
- `gold` publishes item-level features and precomputed recommendations for the dashboard.

The dashboard will use gold outputs to deliver a simple self-service experience. Name search will fuzzy-match against the catalog. Image lookup will first try an LLM vision match when configured, then fall back to deterministic heuristics. The recommendation engine will combine historical lows, relative price position, monthly seasonality, and upcoming retail sale windows to produce a buy/wait recommendation and a likely next buy month.

## User Stories

1. As a shopper, I want to type a product name, so that I can quickly see whether I should buy now or wait.
2. As a shopper, I want to upload an image of a product, so that the dashboard can identify the likely item without me knowing the exact title.
3. As a shopper, I want the dashboard to show the current price versus historical average and low, so that I can understand the recommendation.
4. As a shopper, I want to know the next likely sale window, so that I can plan a later purchase if needed.
5. As a shopper, I want to know the best months to buy an item category, so that I can understand seasonal behavior instead of seeing a black-box answer.
6. As a shopper, I want a concise LLM explanation, so that I can get a plain-language summary of the buy/wait recommendation.
7. As a shopper, I want to see the current Shopbot-style price snapshot, so that I can compare the freshest observed price against historical trends.
8. As a shopper, I want to see the best price observed in the last 30, 60, and 90 days, so that I can judge recent deal quality.
9. As a shopper, I want to see predicted prices in 30, 60, and 90 days, so that I can estimate the cost of waiting.
10. As a shopper, I want to see predicted prices for future sales like Prime Day or Black Friday, so that I can plan purchases around retail events.
11. As a shopper, I want 6-month and 1-year trend charts, so that I can see how the recommendation fits the longer price curve.
12. As a project reviewer, I want the ETL pipeline separated into medallion layers, so that the design reads as an intentional data engineering proof of concept.
13. As a project reviewer, I want the raw CamelCamelCamel-style data to be injectable, so that the POC does not depend entirely on live scraping.
14. As a developer, I want the ingestion source boundary isolated, so that a future Amazon Product Advertising or Creators API adapter can be swapped in later.
15. As a developer, I want the recommendation logic tested through public interfaces, so that refactors do not silently break user-facing behavior.
16. As a developer, I want GitHub Actions to run the ETL and publish artifacts, so that the dashboard data can be refreshed without manual local steps.
17. As an evaluator, I want the repository README to explain the POC limits, so that unsupported assumptions about scale, API guarantees, or legal scraping are avoided.

## Implementation Decisions

- The ETL is centered on a deep `run_medallion_pipeline` interface that owns extraction, normalization, aggregation, and publishing.
- CamelCamelCamel is treated as a reference and injection source for the POC. A documented manual injection file is supported, while HTML scraping remains optional and explicitly experimental.
- Shopbot is treated as the current-price seam for the POC. A documented injection file is supported, with a configurable API endpoint and optional HTML fallback for experimental live runs.
- Gold outputs are split into item metadata and recommendation payloads so the dashboard can stay lightweight.
- The recommendation engine uses current price, historical low proximity, price position inside the historical range, trailing best-price windows, monthly average price profile, 30/60/90-day forecasts, and retail sale windows.
- The dashboard reads precomputed gold outputs first and only recalculates recommendations as a fallback.
- Image search prefers LLM vision only when an API key is configured; otherwise it degrades gracefully to deterministic matching.
- The OpenAI client is updated to a modern request pattern compatible with current `openai>=1.0` style clients.
- Search remains fuzzy and local to keep the POC simple; external search APIs are out of scope.
- The sample Shopbot data is normalized to the dashboard currency for the POC to avoid mixing illustrative currencies inside one recommendation engine.

## Testing Decisions

- Tests should verify public behavior: recommendation outcomes, medallion output shape, and deduplication semantics.
- Recommendation logic is tested through `predict_purchase_timing`, not through internal helper functions.
- Pipeline behavior is tested through medallion layer builders and the top-level ETL interface, not through intermediate implementation details.
- The most important tests cover buy-now decisions near a historical low, wait decisions when a cheaper seasonal window is close, and silver-layer deduplication when multiple sources provide the same day.

## Out of Scope

- High-scale ingestion, distributed processing, or warehouse deployment
- Live marketplace checkout integrations
- A guaranteed official CamelCamelCamel API integration
- A production-grade visual search or product-recognition model
- Real-time streaming price updates
- Multi-user authentication or access control

## Further Notes

- This repository is intentionally a proof of concept. The design favors clarity and explainability over breadth.
- The seam between the source adapter and the medallion pipeline is left explicit so that a future official Amazon source can replace or augment the current reference-based flow.
