# Vercel Deployment Guide

This repository now includes a Vercel-friendly deployment surface:

- [index.py](../index.py) exposes the Flask application
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
2. Leave the framework detection on the Python/other default path
3. If you want LLM summaries or image-assisted catalog matching, set:
   - `OPENAI_API_KEY`
   - optional `OPENAI_SUMMARY_MODEL`
   - optional `OPENAI_VISION_MODEL`
4. Deploy

## Post-Deploy Checks

- load the home page
- search for `Echo Dot`
- confirm the recommendation cards render
- confirm the 6-month and 1-year charts load
- optionally enable LLM summaries if the OpenAI key is configured

## Notes

- The deployed Vercel surface is separate from the local Streamlit prototype in [app.py](../app.py).
- The ETL should still be run through GitHub Actions or locally before deploying if you change source data.
- The simplest assignment-friendly workflow is:
  - commit code and curated data
  - let GitHub Actions validate ETL and tests
  - deploy the repo to Vercel
