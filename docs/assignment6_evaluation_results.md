# Assignment 6 Evaluation Results

## Summary

- Output quality accuracy: 5/5 (100.0%)
- Upstream text-search accuracy, baseline: 3/7 (42.9%)
- Upstream text-search accuracy, improved: 7/7 (100.0%)
- End-to-end task success: 7/7 (100.0%)

## Output Quality

Metric: Exact match on the buy-now vs wait recommendation; explanation must be non-empty.
Secondary metric: confidence exact match = 3/5 (60.0%)

- `buy_now_near_low`: PASS. Expected `Buy now`, got `Buy now`. Confidence expected `High`, got `High` (match=True).
- `wait_for_november_window`: PASS. Expected `Wait`, got `Wait`. Confidence expected `High`, got `High` (match=True).
- `buy_now_even_without_sale_hint`: PASS. Expected `Buy now`, got `Buy now`. Confidence expected `High`, got `High` (match=True).
- `wait_for_future_discount`: PASS. Expected `Wait`, got `Wait`. Confidence expected `High`, got `Medium` (match=False).
- `wait_with_medium_confidence`: PASS. Expected `Wait`, got `Wait`. Confidence expected `Medium`, got `High` (match=False).

## Upstream Component: Text Search

Metric: Top-1 exact item match accuracy on saved shopper queries, including unsupported-query rejection.
Baseline: Legacy SequenceMatcher-only scorer from Assignment 5
Improved system: Alias-aware token scorer plus higher acceptance threshold

- `search_echo_alias` (representative): expected `amazon_echo_dot`, baseline returned `kindle_paperwhite` at 0.476, improved returned `amazon_echo_dot` at 1.0. Baseline pass=False, improved pass=True.
- `search_airpods_semantic` (representative): expected `apple_airpods_pro`, baseline returned `None` at 0.0, improved returned `apple_airpods_pro` at 1.0. Baseline pass=False, improved pass=True.
- `search_fire_device` (representative): expected `fire_tv_stick`, baseline returned `kindle_paperwhite` at 0.553, improved returned `fire_tv_stick` at 0.941. Baseline pass=False, improved pass=True.
- `search_kindle_alias` (representative): expected `kindle_paperwhite`, baseline returned `kindle_paperwhite` at 0.571, improved returned `kindle_paperwhite` at 0.834. Baseline pass=True, improved pass=True.
- `search_precise_title` (representative): expected `amazon_echo_dot`, baseline returned `amazon_echo_dot` at 0.78, improved returned `amazon_echo_dot` at 1.0. Baseline pass=True, improved pass=True.
- `search_unsupported_brand` (failure): expected `None`, baseline returned `None` at 0.0, improved returned `None` at 0.0. Baseline pass=True, improved pass=True.
- `search_out_of_catalog_generic` (failure): expected `None`, baseline returned `kindle_paperwhite` at 0.4, improved returned `None` at 0.0. Baseline pass=False, improved pass=True.

## End-to-End Tasks

Metric: HTTP status plus exact resolved item id for representative text and image tasks.

- `e2e_text_alias` (representative): PASS. Expected status `200` and item `amazon_echo_dot`, got status `200` and item `amazon_echo_dot`.
- `e2e_text_semantic` (representative): PASS. Expected status `200` and item `apple_airpods_pro`, got status `200` and item `apple_airpods_pro`.
- `e2e_text_catalog_device` (representative): PASS. Expected status `200` and item `fire_tv_stick`, got status `200` and item `fire_tv_stick`.
- `e2e_image_filename_hint` (representative): PASS. Expected status `200` and item `amazon_echo_dot`, got status `200` and item `amazon_echo_dot`.
- `e2e_text_precise_title` (representative): PASS. Expected status `200` and item `kindle_paperwhite`, got status `200` and item `kindle_paperwhite`.
- `e2e_unsupported_brand` (failure): PASS. Expected status `404` and item `None`, got status `404` and item `None`.
- `e2e_unknown_generic` (failure): PASS. Expected status `404` and item `None`, got status `404` and item `None`.
