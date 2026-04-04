# Vercel Deployment Guide

This repository now includes a Vercel-friendly deployment surface:

- [src/vercel_app.py](../src/vercel_app.py) exposes the deployed Flask application
- [pyproject.toml](../pyproject.toml) tells Vercel which Flask app to boot
- `public/**` contains the browser UI assets
- `data/gold/items.json` and `data/gold/recommendations.json` act as the runtime source of truth

## Local Dry Run

From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m unittest discover -s tests
python -m src.etl
python index.py
```

Open:

`http://127.0.0.1:8000`

## Vercel Setup

1. Import the GitHub repository into Vercel
2. Leave the framework detection on the Python default path
3. If you want LLM summaries or image-assisted catalog matching, set:
   - `OPENAI_API_KEY`
   - optional `OPENAI_SUMMARY_MODEL`
   - optional `OPENAI_VISION_MODEL`
4. Deploy

## Post-Deploy Checks

- load the home page
- confirm it redirects to `/index.html` instead of returning a 404 from Flask
- search for `Echo Dot`
- confirm the recommendation cards render
- confirm the 6-month and 1-year charts load
- optionally enable LLM summaries if the OpenAI key is configured

## Notes

- The deployed Vercel surface is separate from the local Streamlit prototype in [app.py](../app.py).
- The deployed Flask function should not use Flask static-file serving on Vercel. Static assets come from `public/**`.
- The ETL should still be run through GitHub Actions or locally before deploying if you change source data.
- The simplest assignment-friendly workflow is:
  - commit code and curated data
  - let GitHub Actions validate ETL and tests
  - deploy the repo to Vercel
