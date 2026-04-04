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
Mostly satisfied in-repo, but missing the GitHub Issue link

Repository artifact:
- [docs/prd.md](prd.md)

Still needed:
- create the parent PRD as a real GitHub Issue in the public repo
- add the issue URL here

## 3. `prd-to-issues`

Current evidence status:
Partially satisfied in-repo, but missing real GitHub Issues

Repository artifact:
- [docs/implementation_slices.md](implementation_slices.md)

Still needed:
- create GitHub Issues for the tracer-bullet slices
- link those issue URLs here

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
- preserved domain logic in the existing ETL and prediction modules
- a dedicated CamelCamelCamel API source adapter in [src/camelcamelcamel.py](src/camelcamelcamel.py)

Supporting artifacts:
- [src/medallion.py](../src/medallion.py)
- [src/camelcamelcamel.py](../src/camelcamelcamel.py)
- [src/dashboard_service.py](../src/dashboard_service.py)
- [docs/assignment5_compliance.md](assignment5_compliance.md)
