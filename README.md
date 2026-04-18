# Shopping Price Advisor POC

This repository is a proof of concept for a self-service shopping dashboard that answers one question: should I buy this item now or wait?

The project combines:

- a medallion-style ETL pipeline
- a Vercel-friendly Flask plus static web dashboard for text and image lookup
- a Streamlit dashboard for local exploration
- a simple seasonality-aware recommendation engine
- an Amazon affiliate source seam for live current-price snapshots
- optional OpenAI summaries and image-based catalog matching
- GitHub Actions automation for scheduled ETL refreshes

## What The POC Demonstrates

- `bronze` data collection from seeded sample rows and CamelCamelCamel-style injections
- `bronze` data collection from seeded sample rows, CamelCamelCamel injections, Amazon affiliate-compatible current snapshots, and Shopbot fallback injections
- `silver` normalization and deduplication of price observations
- `gold` item-level features and precomputed buy/wait recommendations
- a dashboard that lets a user type an item name or upload a product photo
- a recommendation engine that combines current price, trailing best-price windows, average price, best buy months, 30/60/90-day forecasts, and upcoming sale windows

## Repository Layout

- `index.py`: Flask application entrypoint for both local preview and Vercel deployment
- `public/`: static frontend assets for the deployed web UI
- `streamlit_app.py`: Streamlit dashboard
- `src/medallion.py`: deep ETL module that owns bronze, silver, and gold publishing
- `src/etl.py`: CLI entrypoint for the ETL
- `src/predict.py`: public recommendation interface
- `src/dashboard_service.py`: shared dashboard data shaping for the web and local UI surfaces
- `src/amazon_affiliate.py`: Amazon affiliate or Creators API-compatible current-price adapter
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

You now have two ways to run the project:

- `python index.py` for the local Flask web app
- `streamlit run streamlit_app.py` for the original local Streamlit dashboard

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

5. Start the local Flask web app.

```powershell
python index.py
```

6. Or start the Streamlit dashboard.

```powershell
streamlit run streamlit_app.py
```

The Flask web app runs on:

- `http://127.0.0.1:8000`

The Streamlit app usually runs on:

- `http://localhost:8501`

## Amazon Affiliate API Support

The preferred live current-price source is now an Amazon affiliate or Creators API-compatible endpoint.

Set these values in `.env` when you have access:

- `AMAZON_CREATOR_API_URL`
- `AMAZON_CREATOR_API_METHOD`
- `AMAZON_CREATOR_TOKEN_URL`
- `AMAZON_CREATOR_CLIENT_ID`
- `AMAZON_CREATOR_CLIENT_SECRET`
- `AMAZON_CREATOR_ACCESS_TOKEN`
- `AMAZON_CREATOR_SCOPE`
- `AMAZON_CREATOR_API_KEY`
- `AMAZON_CREATOR_PARTNER_TAG`
- `AMAZON_CREATOR_MARKETPLACE`

The tracking manifest in `data/track_items.csv` now supports:

- `amazon_asin`
- `amazon_marketplace`
- `amazon_url`
- `amazon_query`

The ETL uses Amazon live price snapshots for the freshest current-price seam when configured, while continuing to use the existing sample and injected history files for longer-term trend analysis.

## OpenAI Support

Set `OPENAI_API_KEY` in `.env` to enable:

- LLM recommendation summaries
- LLM-assisted image-to-item matching

Optional model overrides:

- `OPENAI_SUMMARY_MODEL`
- `OPENAI_VISION_MODEL`

## CamelCamelCamel API Support

If you have access to a CamelCamelCamel Product Advertising API endpoint, configure the live source using environment variables in `.env`:

- `CAMEL_API_URL`
- `CAMEL_API_KEY`
- `CAMEL_API_SECRET`
- `CAMEL_API_PARTNER_TAG`
- `CAMEL_API_PARTNER_TYPE`

The ETL will prefer the API source when configured and only fall back to experimental page scraping if `ENABLE_EXPERIMENTAL_CAMEL_SCRAPE=true`.

> Do not commit actual secret values into Git. Put them in `.env` locally or GitHub Secrets for CI.

## Shopbot Support

The repo still supports a legacy Shopbot source seam for current-price snapshots.

- `data/shopbot_injection.csv` is the default proof-of-concept path.
- `SHOPBOT_API_URL` and `SHOPBOT_API_KEY` can be used to point the app at a JSON API endpoint if you have one.
- `ENABLE_EXPERIMENTAL_SHOPBOT_FETCH=true` enables a best-effort HTML fetch fallback against Shopbot pages when no API endpoint is configured.

When legacy Shopbot snapshots are available, the dashboard compares them with:

- best observed price in trailing 30, 60, and 90 days
- predicted price in 30, 60, and 90 days
- predicted prices for upcoming sale windows
- 6-month and 1-year trend charts

## CamelCamelCamel Notes

This POC treats CamelCamelCamel as a reference and as a swappable source seam:

- `data/camelcamelcamel_injection.csv` is the safest POC path because it keeps the ETL repeatable.
- `src/camelcamelcamel.py` still supports a configurable reference-data adapter through `CAMEL_API_URL` and `CAMEL_API_KEY`.
- The preferred live current-price source is the Amazon affiliate adapter in `src/amazon_affiliate.py`.
- Set `ENABLE_EXPERIMENTAL_CAMEL_SCRAPE=true` only if you intentionally want to run the experimental HTML page extraction fallback.

## GitHub Actions

The workflow in `.github/workflows/etl.yml` now:

- runs unit tests
- runs the ETL on pushes to `main`, pull requests, manual dispatch, and a daily schedule
- verifies that medallion outputs were produced
- uploads the medallion outputs as artifacts

The CI workflow installs `requirements-ci.txt` so scheduled ETL runs are not blocked by the optional OpenAI SDK dependency. Local and deployment installs can still use `requirements.txt` when you want LLM features enabled.

## Assignment 6 Evaluation

Assignment 6 artifacts are now included directly in the repo:

- `data/assignment6_cases.json`: saved representative cases, failure cases, and evaluation fixtures
- `src/evaluate_assignment6.py`: reproducible evaluation runner
- `docs/assignment6_evaluation_results.md`: reviewer-friendly summary of the latest evaluation run
- `docs/assignment6_evaluation_results.json`: structured evaluation output
- `docs/assignment6_guide.md`: architecture justification, pipeline walkthrough, improvement summary, and video prep notes

Run the evaluation locally with:

```powershell
python -m src.evaluate_assignment6
```

## Vercel Deployment

The repository is now structured to be deployable on Vercel with:

- [index.py](index.py) as the Flask entrypoint
- `public/**` as the browser UI
- `data/gold/items.json` and `data/gold/recommendations.json` as the deployed app's curated source of truth

Deployment notes live in:

- [docs/vercel_deployment.md](docs/vercel_deployment.md)

## Assignment Evidence

Reviewer-focused assignment notes live in:

- [docs/assignment6_guide.md](docs/assignment6_guide.md)
- [docs/assignment6_evaluation_results.md](docs/assignment6_evaluation_results.md)
- [docs/skill_evidence.md](docs/skill_evidence.md)
- [docs/playwright_mcp_evidence.md](docs/playwright_mcp_evidence.md)

## Design Constraints

- This is a proof of concept, not a scaled production system.
- The image lookup is intentionally lightweight and designed for a small tracked catalog.
- The recommendation engine is rule-based and explainable; it is not a trained forecasting model.
- The sample Shopbot rows are normalized to the dashboard currency for the POC. A production version would need explicit FX normalization before merging multi-country sources.
- The source adapter seam is kept explicit so a future official Amazon source can replace or augment the current reference-based flow.
