# GitHub Issues Quick Post Pack

This file gives you copy-paste issue text for the Assignment 5 repo.

Repo:
- `https://github.com/Mithilan1/End-to-End`

Created issues:

- Parent PRD: https://github.com/Mithilan1/End-to-End/issues/1
- Slice 1: https://github.com/Mithilan1/End-to-End/issues/2
- Slice 2: https://github.com/Mithilan1/End-to-End/issues/3
- Slice 3: https://github.com/Mithilan1/End-to-End/issues/4
- Slice 4: https://github.com/Mithilan1/End-to-End/issues/5
- Slice 5: https://github.com/Mithilan1/End-to-End/issues/6
- Slice 6: https://github.com/Mithilan1/End-to-End/issues/7

Recommended posting order:

1. Parent PRD issue
2. Slice 1
3. Slice 2
4. Slice 3
5. Slice 4
6. Slice 5
7. Slice 6

After you post them:

1. Edit each child issue and replace the `#PARENT_PRD` placeholder with the real parent issue number
2. Replace blocker placeholders with real issue numbers
3. Because the work is already mostly done, you can close completed issues and link the relevant commits or PRs

## Parent PRD Issue

### Title

Assignment 5 PRD: Shopping Price Advisor end-to-end AI application

### Body

```md
## Problem statement

Build a focused proof-of-concept shopping advisory dashboard that helps a user decide whether to buy an item now or wait.

The application must:

- ingest realistic source data
- run a repeatable ETL flow
- store staged outputs in bronze, silver, and gold layers
- include an AI or reasoning layer
- expose the result through a deployed user-facing application

## Supported use case

The app supports a narrow shopping advisory workflow:

- search for a tracked product
- inspect current price versus historical context
- see a buy-now-or-wait recommendation
- view trailing best-price windows, forecast windows, and seasonal patterns
- optionally view LLM-generated explanations

## Architecture direction

- ingestion from realistic source files and configurable source seams
- medallion ETL pipeline with bronze, silver, and gold outputs
- curated gold-layer files as the application source of truth
- recommendation engine plus optional LLM explanation layer
- Vercel-deployable Flask web surface
- GitHub Actions automation for ETL validation

## Out of scope

- large-scale production infrastructure
- real-time streaming updates
- checkout or purchasing integrations
- broad marketplace coverage
- multi-user auth

## Required workflow evidence

This parent issue supports the Assignment 5 workflow:

- grill-me
- write-a-prd
- prd-to-issues
- tdd
- improve-codebase-architecture

## Notes

Child issues will represent thin vertical slices of implementation and evidence work.
```

## Slice 1

### Title

Establish medallion ETL contract for shopping price data

### Body

```md
## Parent PRD

#PARENT_PRD

## What to build

Create the end-to-end medallion ETL shape for the project so raw price observations can move into normalized silver data and curated gold outputs used by the dashboard.

This slice should produce a demoable ETL path through:

- input data ingestion
- transformation into bronze, silver, and gold layers
- output files that the app can read
- tests that validate the ETL behavior

## Acceptance criteria

- [ ] The ETL writes bronze, silver, and gold outputs
- [ ] The ETL can be run through a single public entrypoint
- [ ] The output format is stable enough for the app to consume
- [ ] Tests verify at least one meaningful ETL behavior

## Blocked by

None - can start immediately

## User stories addressed

- User story 7
- User story 8
- User story 10
- User story 11
- User story 12
```

## Slice 2

### Title

Add source seams for historical and current price ingestion

### Body

```md
## Parent PRD

#PARENT_PRD

## What to build

Add configurable source seams for realistic historical and current-price ingestion so the ETL can work with injected reference data and future live adapters without changing the downstream pipeline contract.

This slice should be demoable through:

- injected historical data
- injected or configurable current-price data
- explicit source metadata preserved into the pipeline
- a clean adapter boundary that supports future official APIs

## Acceptance criteria

- [ ] Historical reference data can be ingested through a documented source seam
- [ ] Current-price data can be ingested through a documented source seam
- [ ] Source metadata flows into the ETL outputs
- [ ] The adapter boundary remains isolated from downstream recommendation logic

## Blocked by

- Blocked by #ISSUE_1

## User stories addressed

- User story 7
- User story 12
- User story 13
- User story 14
- User story 17
```

## Slice 3

### Title

Publish gold recommendations and forecast windows

### Body

```md
## Parent PRD

#PARENT_PRD

## What to build

Build the recommendation layer that turns curated item data into buy-now-or-wait outputs, including target price, buy window, trailing best-price windows, and forecast windows for upcoming sale periods.

This slice should be demoable through:

- a gold recommendation output
- clear recommendation reasoning
- forecast windows users can inspect
- tests tied to recommendation behavior

## Acceptance criteria

- [ ] Gold recommendation outputs are generated from curated item data
- [ ] Recommendations include buy-now-or-wait behavior and target price information
- [ ] Forecast windows include 30, 60, and 90-day views or equivalent future windows
- [ ] Tests cover meaningful recommendation scenarios

## Blocked by

- Blocked by #ISSUE_1

## User stories addressed

- User story 1
- User story 3
- User story 4
- User story 5
- User story 8
- User story 9
- User story 10
- User story 11
- User story 15
```

## Slice 4

### Title

Build deployment-facing dashboard flow for search and trends

### Body

```md
## Parent PRD

#PARENT_PRD

## What to build

Create the deployment-facing dashboard experience that allows a user to search for an item and view current price, recommendation output, trend charts, and seasonal profile information from the gold layer.

This slice should be demoable through:

- text search
- result rendering
- current-price and recommendation cards
- trend and seasonal visual sections

## Acceptance criteria

- [ ] A user can search for a tracked item through the deployed-style app
- [ ] The app renders recommendation output from curated gold files
- [ ] Trend and seasonal views are displayed for a successful result
- [ ] Tests cover key deployment-facing API or UI behavior

## Blocked by

- Blocked by #ISSUE_3

## User stories addressed

- User story 1
- User story 3
- User story 4
- User story 5
- User story 7
- User story 8
- User story 9
- User story 10
- User story 11
```

## Slice 5

### Title

Add optional LLM explanation and image-assisted lookup

### Body

```md
## Parent PRD

#PARENT_PRD

## What to build

Add optional AI-enabled features that improve the user experience without becoming the entire application: an LLM explanation of the recommendation and image-assisted item lookup for a small tracked catalog.

This slice should be demoable through:

- optional LLM summary output
- image-assisted lookup
- graceful fallback behavior when the API key is missing

## Acceptance criteria

- [ ] The app can optionally generate a concise LLM explanation
- [ ] The app supports image-assisted lookup for tracked items
- [ ] Missing API configuration fails gracefully instead of breaking the app
- [ ] The feature remains optional and does not block the core experience

## Blocked by

- Blocked by #ISSUE_4

## User stories addressed

- User story 2
- User story 6
```

## Slice 6

### Title

Document deployment, testing, and assignment evidence

### Body

```md
## Parent PRD

#PARENT_PRD

## What to build

Document the final proof-of-concept boundaries and evidence required by the assignment, including deployment notes, testing notes, architecture notes, and the workflow evidence that maps the build back to the required skills.

This slice should be demoable through:

- clear README guidance
- deployment notes
- testing evidence
- architecture and compliance notes

## Acceptance criteria

- [ ] The README explains the project scope and usage clearly
- [ ] Deployment notes exist for the Vercel surface
- [ ] Testing evidence includes meaningful tests and Playwright MCP notes
- [ ] Architecture and assignment-compliance notes are present in the repo

## Blocked by

- Blocked by #ISSUE_1
- Blocked by #ISSUE_2
- Blocked by #ISSUE_3
- Blocked by #ISSUE_4
- Blocked by #ISSUE_5

## User stories addressed

- User story 14
- User story 17
```

## Quick Web UI Posting Order

Create these in this exact order:

1. Parent PRD
2. Slice 1
3. Slice 2
4. Slice 3
5. Slice 4
6. Slice 5
7. Slice 6

Then edit the blockers with real issue numbers.

## Suggested Close-Out Note After Posting

After the issues are created, you can add a short comment like this on each one:

```md
This issue was created retroactively to document the Assignment 5 PRD-to-issues workflow. The implementation and evidence now live in the repository history, tests, docs, and workflow artifacts.
```
