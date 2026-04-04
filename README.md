# Shopping Price Advisor POC

This repository is a proof of concept for a self-service shopping dashboard that answers one question: should I buy this item now or wait?

The project combines:

- a medallion-style ETL pipeline
- a Streamlit dashboard for text and image lookup
- a simple seasonality-aware recommendation engine
- a Shopbot source seam for current-price snapshots
- optional OpenAI summaries and image-based catalog matching
- GitHub Actions automation for scheduled ETL refreshes

## What The POC Demonstrates

- `bronze` data collection from seeded sample rows and CamelCamelCamel-style injections
- `bronze` data collection from seeded sample rows, CamelCamelCamel injections, and Shopbot current-price injections
- `silver` normalization and deduplication of price observations
- `gold` item-level features and precomputed buy/wait recommendations
- a dashboard that lets a user type an item name or upload a product photo
- a recommendation engine that combines current price, trailing best-price windows, average price, best buy months, 30/60/90-day forecasts, and upcoming sale windows

## Repository Layout

- `app.py`: Streamlit dashboard
- `src/medallion.py`: deep ETL module that owns bronze, silver, and gold publishing
- `src/etl.py`: CLI entrypoint for the ETL
- `src/predict.py`: public recommendation interface
- `src/llm_client.py`: OpenAI summary and vision helpers
- `src/image_search.py`: image lookup with LLM-first and heuristic fallback behavior
- `src/data_store.py`: gold-layer loading and fuzzy search helpers
- `src/camelcamelcamel.py`: CamelCamelCamel injection loader plus optional experimental scraper
- `src/shopbot.py`: Shopbot current-price adapter with configurable API seam and optional HTML fallback
- `data/sample_price_history.csv`: seeded sample history
- `data/camelcamelcamel_injection.csv`: injected CamelCamelCamel-style history for the POC
- `data/shopbot_injection.csv`: injected Shopbot-style current-price history for the POC
- `docs/prd.md`: project PRD artifact
- `docs/implementation_slices.md`: thin-slice follow-up backlog

## Medallion Flow

Running `python -m src.etl` creates:

- `data/bronze/price_observations.json`
- `data/silver/normalized_prices.csv`
- `data/gold/items.json`
- `data/gold/recommendations.json`

For compatibility with the original prototype, the ETL also writes `data/processed/items.json`.

## Getting Started

1. Create a virtual environment.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies.

```powershell
python -m pip install -r requirements.txt
```

3. Copy the environment template.

```powershell
copy .env.example .env
```

4. Run the ETL locally.

```powershell
python -m src.etl
```

5. Start the dashboard.

```powershell
streamlit run app.py
```

## OpenAI Support

Set `OPENAI_API_KEY` in `.env` to enable:

- LLM recommendation summaries
- LLM-assisted image-to-item matching

Optional model overrides:

- `OPENAI_SUMMARY_MODEL`
- `OPENAI_VISION_MODEL`

## Shopbot Support

The repo now supports a Shopbot source seam for current-price snapshots.

- `data/shopbot_injection.csv` is the default proof-of-concept path.
- `SHOPBOT_API_URL` and `SHOPBOT_API_KEY` can be used to point the app at a JSON API endpoint if you have one.
- `ENABLE_EXPERIMENTAL_SHOPBOT_FETCH=true` enables a best-effort HTML fetch fallback against Shopbot pages when no API endpoint is configured.

The dashboard uses Shopbot-derived current prices when they are available, then compares them with:

- best observed price in trailing 30, 60, and 90 days
- predicted price in 30, 60, and 90 days
- predicted prices for upcoming sale windows
- 6-month and 1-year trend charts

## CamelCamelCamel Notes

This POC treats CamelCamelCamel primarily as a reference and injection source.

- `data/camelcamelcamel_injection.csv` is the safest POC path because it keeps the ETL repeatable.
- `src/camelcamelcamel.py` still contains an experimental HTML scraping helper, but it is disabled by default.
- Set `ENABLE_EXPERIMENTAL_CAMEL_SCRAPE=true` only if you intentionally want to try live page extraction.

## GitHub Actions

The workflow in `.github/workflows/etl.yml` now:

- runs unit tests
- runs the ETL on pushes to `main`, pull requests, manual dispatch, and a daily schedule
- verifies that medallion outputs were produced
- uploads the medallion outputs as artifacts

The CI workflow installs `requirements-ci.txt` so scheduled ETL runs are not blocked by optional app dependencies, while local installs can still use `requirements.txt`.

## Design Constraints

- This is a proof of concept, not a scaled production system.
- The image lookup is intentionally lightweight and designed for a small tracked catalog.
- The recommendation engine is rule-based and explainable; it is not a trained forecasting model.
- The sample Shopbot rows are normalized to the dashboard currency for the POC. A production version would need explicit FX normalization before merging multi-country sources.
- The source adapter seam is kept explicit so a future official Amazon source can replace or augment the current reference-based flow.
