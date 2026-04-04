# Assignment 5 Compliance Review

Reviewed against the assignment handout at:
`https://github.com/bipin-a/aidi-2001/blob/main/Assignments/assignment5/assignment5.md`

Review date:
April 2, 2026

## Satisfied In This Repository

- End-to-end application flow across ingestion, ETL, storage, reasoning, and UI
- Medallion-style storage layers with `bronze`, `silver`, and `gold` outputs
- Repeatable ETL entrypoint in [src/etl.py](../src/etl.py)
- GitHub Actions automation in [.github/workflows/etl.yml](../.github/workflows/etl.yml)
- User-facing application for text search and image-assisted lookup
- LLM-enabled layer through [src/llm_client.py](../src/llm_client.py)
- Meaningful tests for core behavior and pipeline outputs in [tests/test_predict.py](../tests/test_predict.py), [tests/test_medallion.py](../tests/test_medallion.py), and [tests/test_vercel_app.py](../tests/test_vercel_app.py)
- Vercel-ready deployment shape using [index.py](../index.py) and `public/**`
- Clear README and architecture/process notes

## Partially Satisfied Or Still Manual

- `write-a-prd` evidence exists in [docs/prd.md](prd.md), but the assignment still expects a parent GitHub Issue link
- `prd-to-issues` planning exists in [docs/implementation_slices.md](implementation_slices.md), but those slices still need to exist as actual GitHub Issues in the public repo
- `grill-me` still needs a saved excerpt, screenshot, or explicit notes from the original session
- Playwright MCP evidence is now documented in-repo, but the final video still needs to show it
- A real deployed Vercel URL must still be created and submitted
- The required 10-minute video with screen share, audio, and webcam is still a submission-time task

## Assignment-Alignment Notes

- The handout recommends object storage, but it does not require production infrastructure. This repo uses curated JSON and CSV files plus GitHub Actions artifacts to keep the POC simple and explainable.
- The repo now contains two UI surfaces:
  - [app.py](../app.py) for local Streamlit exploration
  - [index.py](../index.py) plus `public/**` for Vercel deployment
- The Vercel surface is the one intended for the assignment deployment requirement.

## Before Submission

- Create and link the parent PRD GitHub Issue
- Create and link the smaller GitHub Issues created from the PRD
- Add the saved `grill-me` evidence if it is not already captured elsewhere
- Deploy the repo to Vercel and test the live URL
- Record the required 10-minute video
