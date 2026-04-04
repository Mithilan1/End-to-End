# Required Skill Evidence

This file maps the assignment's required skills to the repository artifacts that show the workflow.

## 1. `grill-me`

Current evidence status:
Partial

What is present:
- The final scope is narrow, POC-sized, and intentionally bounded
- The solution favors curated files, a focused dashboard, and explainable heuristics instead of overbuilt infrastructure

What still needs to be added for full assignment evidence:
- a saved chat excerpt, screenshot, or notes from the actual `grill-me` interaction
- a short note describing what changed because of the grilling

Suggested addition:
- paste the excerpt into this file or add a screenshot under `docs/images/`

## 2. `write-a-prd`

Current evidence status:
Satisfied

Repository artifact:
- [docs/prd.md](prd.md)

GitHub issue:
- Parent PRD issue: https://github.com/Mithilan1/End-to-End/issues/1

## 3. `prd-to-issues`

Current evidence status:
Satisfied

Repository artifact:
- [docs/implementation_slices.md](implementation_slices.md)

GitHub issues:
- https://github.com/Mithilan1/End-to-End/issues/2
- https://github.com/Mithilan1/End-to-End/issues/3
- https://github.com/Mithilan1/End-to-End/issues/4
- https://github.com/Mithilan1/End-to-End/issues/5
- https://github.com/Mithilan1/End-to-End/issues/6
- https://github.com/Mithilan1/End-to-End/issues/7

## 4. `tdd`

Current evidence status:
Satisfied

Repository artifacts:
- [tests/test_predict.py](../tests/test_predict.py)
- [tests/test_medallion.py](../tests/test_medallion.py)
- [tests/test_vercel_app.py](../tests/test_vercel_app.py)

What the tests cover:
- buy-now behavior near historical lows
- wait behavior when a better seasonal window is close
- silver-layer deduplication of overlapping same-day records
- top-level medallion output generation
- deployment-facing API behavior for health, search, and image lookup

## 5. `improve-codebase-architecture`

Current evidence status:
Satisfied

Before:
- one processed file driving the dashboard
- UI-specific logic mixed closely with the surface layer
- source adapters and medallion concepts not clearly separated

After:
- explicit `bronze`, `silver`, and `gold` outputs in the ETL
- shared dashboard shaping logic in [src/dashboard_service.py](../src/dashboard_service.py)
- deployment-facing Flask entrypoint in [index.py](../index.py)
- Streamlit prototype isolated in [streamlit_app.py](../streamlit_app.py)
- preserved domain logic in the existing ETL and prediction modules
- a dedicated CamelCamelCamel API source adapter in [src/camelcamelcamel.py](src/camelcamelcamel.py)

Supporting artifacts:
- [src/medallion.py](../src/medallion.py)
- [src/camelcamelcamel.py](../src/camelcamelcamel.py)
- [src/dashboard_service.py](../src/dashboard_service.py)
- [docs/assignment5_compliance.md](assignment5_compliance.md)
