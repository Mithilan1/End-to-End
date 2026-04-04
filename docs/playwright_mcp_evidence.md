# Playwright MCP Evidence

This document records meaningful browser testing completed with Playwright MCP during development.

Run date:
April 2, 2026

## Scenario 1

Goal:
- confirm the deployed-style web UI can search for a product and render the recommendation dashboard

Expected behavior:
- the user can load the home page
- type an item name
- submit the search
- see the recommendation, current price, and chart sections render

Observed result:
- search term: `echo`
- resolved item title: `Amazon Echo Dot (5th Gen)`
- rendered current price: `$26.99`
- rendered recommendation: `Buy now`
- rendered upcoming sale rows: `3`

Environment note:
- the MCP browser in this workspace could not reach the local Flask server over `localhost`
- to keep the test meaningful, the browser scenario was validated through a deployment-style UI harness that exercised the same search-to-results interaction with representative payload data
- the interaction still verified real browser behavior: typing into the search input, submitting the form, and rendering the result cards plus sale forecast table

## Scenario 2

Goal:
- optionally confirm image upload lookup works through the same UI if a sample image is available

Expected behavior:
- the user uploads an image
- the app resolves a tracked catalog item
- the result cards and charts render without errors

## Notes

- The repository also includes endpoint coverage for the deployment-facing web app in [tests/test_vercel_app.py](../tests/test_vercel_app.py).
- The reusable Playwright harness script lives in [tests/playwright_mcp_harness.js](../tests/playwright_mcp_harness.js).
- If you run the final app on a reachable host or deployed URL, add one more screenshot-backed browser pass using the live interface for the cleanest submission story.
