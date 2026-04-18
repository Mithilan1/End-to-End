# Assignment 6 Guide

This repository is an evolution of the Assignment 5 Shopping Price Advisor application deployed on Vercel.

- GitHub repo: `https://github.com/Mithilan1/End-to-End`
- Deployed app: `https://end-to-end-sv5h.vercel.app/index.html`

## What the App Does

The app helps a shopper decide whether to buy a tracked product now or wait.

Supported tasks:

- text search for a tracked item
- image upload for a small catalog match
- price recommendation generation using historical and seasonal signals
- viewing trend history, sale-window forecasts, and optional LLM summaries

Out of scope:

- open-web shopping search across arbitrary retailers
- broad catalog coverage beyond the seeded tracked items
- guaranteed live prices when external source credentials are not configured
- fully autonomous purchasing or checkout actions

## Architecture Classification

I classify the system as `Hybrid`.

Why:

- the core recommendation path is deterministic and tool-like: ETL transforms raw records into bronze, silver, and gold outputs, and the app serves precomputed gold data
- optional OpenAI features add prompt-based summaries and vision-assisted image matching
- the deployed web flow also includes deterministic search, ranking, and forecast logic outside the model

Main alternative considered: `Prompt-first / long-context`.

Why I did not choose prompt-first as the main architecture:

- the app needs predictable numeric behavior for prices, trend windows, and sale forecasts
- deterministic transforms are easier to test and debug than asking a model to infer all calculations from raw history
- using gold-layer artifacts keeps inference cost and latency low
- storing transformed outputs creates a clearer operational boundary for CI, deployment, and troubleshooting

Required tradeoffs:

- amount of data / files: the catalog is small, so a full RAG stack would be overbuilt today
- context window: current product histories fit comfortably in structured files without pushing model context limits
- retrieval or storage needs: stored gold artifacts are still useful because they make the app fast and reproducible, even without RAG
- determinism: price recommendations, trend windows, and health endpoints benefit from predictable code paths
- cost: the default app can run without LLM calls, which keeps operating cost near zero
- operational overhead: ETL plus JSON artifacts is simpler than maintaining a vector index for this project size
- performance: loading precomputed JSON is faster than generating everything on demand
- ease of debugging: bronze, silver, and gold outputs make it easier to inspect where a problem started

## Important Capability Not Implemented

One important capability I did not implement is full `RAG`.

Would it help?

- yes, if the catalog grows to many products, many merchant pages, or richer textual evidence

What problem would it solve?

- retrieval could help surface relevant product notes, policy text, or merchant-specific evidence without placing everything directly into prompts

What complexity would it introduce?

- chunking strategy
- index management
- retrieval evaluation
- more deployment and debugging overhead

When I would adopt it:

- when the tracked catalog becomes materially larger
- when product descriptions, reviews, or merchant notes become important inputs
- when prompt size or manual context assembly becomes a bottleneck

## Pipeline and Data Flow

Raw inputs:

- `data/sample_price_history.csv`
- `data/camelcamelcamel_injection.csv`
- `data/shopbot_injection.csv`
- `data/track_items.csv`
- optional Amazon / OpenAI environment variables

Transform flow:

1. Bronze: `src/medallion.py` collects seeded and injected observations into `data/bronze/price_observations.json`
2. Silver: normalization and deduplication write `data/silver/normalized_prices.csv`
3. Gold: item-level features and recommendations write `data/gold/items.json` and `data/gold/recommendations.json`
4. Serving layer: `src/dashboard_service.py` shapes the gold data for the Flask API and frontend
5. UI layer: `src/web_app.py`, `public/index.html`, and `public/app.js` display the result

Source of truth at runtime:

- `data/gold/items.json`
- `data/gold/recommendations.json`

Useful internal information kept for debugging:

- transformed bronze, silver, and gold artifacts
- resolved item id and candidate scores from text search
- prediction fields such as best-price windows, forecast horizons, and sale-window forecasts
- optional image-match reason and confidence
- API status codes and structured JSON responses

Likely error points:

- malformed raw rows during ETL
- missing gold artifacts before app startup
- unsupported or ambiguous search terms
- weak filename-only image hints for unfamiliar uploads
- missing external credentials for optional LLM or Amazon integrations

## Evaluation Summary

Artifacts:

- fixtures: [../data/assignment6_cases.json](../data/assignment6_cases.json)
- runner: [../src/evaluate_assignment6.py](../src/evaluate_assignment6.py)
- results: [assignment6_evaluation_results.md](assignment6_evaluation_results.md)

The evaluation covers the 3 required areas:

1. Output quality
   The metric is exact match on the main recommendation action, `Buy now` vs `Wait`, with a non-empty explanation.
2. End-to-end task success
   The metric is exact API status and resolved item id for representative text and image tasks.
3. One upstream component
   The metric is top-1 exact item match accuracy for the text-search step before the final response is built.

Saved cases included:

- 5 representative cases
- 2 failure cases
- 1 lightweight baseline comparison against the original Assignment 5 text matcher

Latest results:

- output quality: 5/5 action-label accuracy
- upstream text-search baseline: 3/7
- upstream text-search improved system: 7/7
- end-to-end success: 7/7

Residual weakness:

- confidence calibration is weaker than action selection, scoring 3/5 on the saved output-quality cases

## Evidence-Based Improvement

Weak point found:

- Assignment 5 text search used a simple `SequenceMatcher` scorer, which misread shopper phrasing such as `alexa speaker` and `amazon streaming device`
- it also returned false positives for out-of-catalog generic searches

Evidence:

- baseline search accuracy on saved cases was `3/7`
- representative misses included `alexa speaker`, `wireless earbuds`, and `amazon streaming device`

Change made:

- added alias-aware matching in `src/data_store.py`
- combined token overlap with sequence similarity
- raised the acceptance threshold so unsupported searches return `404` instead of a bad catalog match
- added regression tests in `tests/test_data_store.py` and `tests/test_vercel_app.py`

What improved:

- upstream text-search accuracy improved from `3/7` to `7/7`
- end-to-end task success across saved search and image tasks reached `7/7`

What still remains weak:

- image recognition fallback is still lightweight
- confidence labels for recommendation quality remain less calibrated than the primary buy/wait action

## Video Walkthrough Checklist

Use this order to keep the demo under 12 minutes:

1. Show the deployed Vercel app and explain the user problem
2. Show the GitHub repo and say this is a continuation of Assignment 5
3. Classify the app as hybrid and explain why prompt-first was not chosen
4. Explain one capability not implemented yet: full RAG
5. Walk through raw inputs, bronze, silver, gold, API layer, and UI layer
6. Open `docs/assignment6_evaluation_results.md` and explain the three evaluation sections
7. Show the two failure cases and explain what they reveal
8. Explain the baseline comparison and the text-search improvement
9. Point out the remaining weakness around confidence calibration and lightweight image matching

## Repro Steps

```powershell
python -m unittest discover -s tests
python -m src.evaluate_assignment6
python index.py
```
