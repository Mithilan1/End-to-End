from __future__ import annotations

import json
from datetime import date
from io import BytesIO
from pathlib import Path

from PIL import Image

from src.data_store import load_processed_items, search_item_by_name, search_item_candidates, similarity
from src.predict import predict_purchase_timing
from src.web_app import create_app

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CASES_PATH = PROJECT_ROOT / "data" / "assignment6_cases.json"
RESULTS_JSON_PATH = PROJECT_ROOT / "docs" / "assignment6_evaluation_results.json"
RESULTS_MD_PATH = PROJECT_ROOT / "docs" / "assignment6_evaluation_results.md"
ITEMS_PATH = PROJECT_ROOT / "data" / "gold" / "items.json"


def load_cases() -> dict:
    with CASES_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def legacy_search_item_by_name(query: str, items: dict) -> tuple[dict | None, float]:
    ranked = []
    for item in items.values():
        candidates = [item["item_name"], item["item_id"], item.get("category", "")]
        score = max(similarity(query, candidate) for candidate in candidates if candidate)
        if query.lower() in item["item_name"].lower():
            score += 0.2
        ranked.append((item, min(score, 1.0)))

    ranked.sort(key=lambda pair: pair[1], reverse=True)
    if not ranked:
        return None, 0.0
    match, score = ranked[0]
    return (match, score) if score >= 0.4 else (None, 0.0)


def evaluate_output_quality(cases: list[dict]) -> dict:
    rows = []
    passes = 0
    confidence_matches = 0
    for case in cases:
        prediction = predict_purchase_timing(
            case["item"],
            as_of=date.fromisoformat(case["as_of"]),
        )
        confidence_match = prediction["confidence"] == case["expected_confidence"]
        passed = prediction["recommendation"] == case["expected_recommendation"] and bool(prediction["reason"])
        passes += int(passed)
        confidence_matches += int(confidence_match)
        rows.append(
            {
                "case_id": case["case_id"],
                "description": case["description"],
                "expected_recommendation": case["expected_recommendation"],
                "actual_recommendation": prediction["recommendation"],
                "expected_confidence": case["expected_confidence"],
                "actual_confidence": prediction["confidence"],
                "confidence_match": confidence_match,
                "passed": passed,
            }
        )
    return {
        "metric": "Exact match on the buy-now vs wait recommendation; explanation must be non-empty.",
        "secondary_metric": "Confidence-label exact match is tracked separately as a calibration signal.",
        "passed_cases": passes,
        "total_cases": len(cases),
        "accuracy": round(passes / len(cases), 3) if cases else 0.0,
        "confidence_matches": confidence_matches,
        "confidence_accuracy": round(confidence_matches / len(cases), 3) if cases else 0.0,
        "cases": rows,
    }


def evaluate_search(items: dict, cases: list[dict]) -> dict:
    rows = []
    improved_passes = 0
    baseline_passes = 0
    for case in cases:
        improved_match, improved_score = search_item_by_name(case["query"], items)
        baseline_match, baseline_score = legacy_search_item_by_name(case["query"], items)
        improved_item_id = improved_match["item_id"] if improved_match else None
        baseline_item_id = baseline_match["item_id"] if baseline_match else None
        improved_passed = improved_item_id == case["expected_item_id"]
        baseline_passed = baseline_item_id == case["expected_item_id"]
        improved_passes += int(improved_passed)
        baseline_passes += int(baseline_passed)
        top_candidates = search_item_candidates(case["query"], items, limit=3)
        rows.append(
            {
                "case_id": case["case_id"],
                "query": case["query"],
                "kind": case["kind"],
                "expected_item_id": case["expected_item_id"],
                "baseline_item_id": baseline_item_id,
                "baseline_score": round(baseline_score, 3),
                "improved_item_id": improved_item_id,
                "improved_score": round(improved_score, 3),
                "baseline_passed": baseline_passed,
                "improved_passed": improved_passed,
                "top_candidates": [
                    {"item_id": item["item_id"], "score": round(score, 3)} for item, score in top_candidates
                ],
            }
        )
    return {
        "metric": "Top-1 exact item match accuracy on saved shopper queries, including unsupported-query rejection.",
        "baseline_name": "Legacy SequenceMatcher-only scorer from Assignment 5",
        "improved_name": "Alias-aware token scorer plus higher acceptance threshold",
        "baseline_passed_cases": baseline_passes,
        "improved_passed_cases": improved_passes,
        "total_cases": len(cases),
        "baseline_accuracy": round(baseline_passes / len(cases), 3) if cases else 0.0,
        "improved_accuracy": round(improved_passes / len(cases), 3) if cases else 0.0,
        "cases": rows,
    }


def _blank_png_bytes(size: tuple[int, int] = (120, 120)) -> BytesIO:
    image = Image.new("RGB", size, color=(240, 240, 240))
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


def evaluate_end_to_end(cases: list[dict]) -> dict:
    app = create_app(serve_local_static=False)
    client = app.test_client()
    rows = []
    passes = 0

    for case in cases:
        if case["mode"] == "search":
            response = client.get(f"/api/search?q={case['query']}")
        else:
            buffer = _blank_png_bytes()
            response = client.post(
                "/api/identify-image",
                data={"image": (buffer, case["filename"])},
                content_type="multipart/form-data",
            )

        payload = response.get_json()
        result_payload = payload.get("result") if isinstance(payload, dict) else None
        actual_item_id = result_payload.get("item", {}).get("item_id") if isinstance(result_payload, dict) else None
        passed = response.status_code == case["expected_status"] and actual_item_id == case["expected_item_id"]
        passes += int(passed)
        rows.append(
            {
                "case_id": case["case_id"],
                "mode": case["mode"],
                "kind": case["kind"],
                "expected_status": case["expected_status"],
                "actual_status": response.status_code,
                "expected_item_id": case["expected_item_id"],
                "actual_item_id": actual_item_id,
                "passed": passed,
            }
        )

    return {
        "metric": "HTTP status plus exact resolved item id for representative text and image tasks.",
        "passed_cases": passes,
        "total_cases": len(cases),
        "success_rate": round(passes / len(cases), 3) if cases else 0.0,
        "cases": rows,
    }


def build_markdown_report(results: dict) -> str:
    output_quality = results["output_quality"]
    search_eval = results["search_eval"]
    end_to_end = results["end_to_end"]

    lines = [
        "# Assignment 6 Evaluation Results",
        "",
        "## Summary",
        "",
        f"- Output quality accuracy: {output_quality['passed_cases']}/{output_quality['total_cases']} ({output_quality['accuracy']:.1%})",
        f"- Upstream text-search accuracy, baseline: {search_eval['baseline_passed_cases']}/{search_eval['total_cases']} ({search_eval['baseline_accuracy']:.1%})",
        f"- Upstream text-search accuracy, improved: {search_eval['improved_passed_cases']}/{search_eval['total_cases']} ({search_eval['improved_accuracy']:.1%})",
        f"- End-to-end task success: {end_to_end['passed_cases']}/{end_to_end['total_cases']} ({end_to_end['success_rate']:.1%})",
        "",
        "## Output Quality",
        "",
        f"Metric: {output_quality['metric']}",
        f"Secondary metric: confidence exact match = {output_quality['confidence_matches']}/{output_quality['total_cases']} ({output_quality['confidence_accuracy']:.1%})",
        "",
    ]

    for row in output_quality["cases"]:
        status = "PASS" if row["passed"] else "FAIL"
        lines.append(
            f"- `{row['case_id']}`: {status}. Expected `{row['expected_recommendation']}`, got `{row['actual_recommendation']}`. "
            f"Confidence expected `{row['expected_confidence']}`, got `{row['actual_confidence']}` "
            f"(match={row['confidence_match']})."
        )

    lines.extend(
        [
            "",
            "## Upstream Component: Text Search",
            "",
            f"Metric: {search_eval['metric']}",
            f"Baseline: {search_eval['baseline_name']}",
            f"Improved system: {search_eval['improved_name']}",
            "",
        ]
    )

    for row in search_eval["cases"]:
        lines.append(
            f"- `{row['case_id']}` ({row['kind']}): expected `{row['expected_item_id']}`, "
            f"baseline returned `{row['baseline_item_id']}` at {row['baseline_score']}, "
            f"improved returned `{row['improved_item_id']}` at {row['improved_score']}. "
            f"Baseline pass={row['baseline_passed']}, improved pass={row['improved_passed']}."
        )

    lines.extend(
        [
            "",
            "## End-to-End Tasks",
            "",
            f"Metric: {end_to_end['metric']}",
            "",
        ]
    )

    for row in end_to_end["cases"]:
        status = "PASS" if row["passed"] else "FAIL"
        lines.append(
            f"- `{row['case_id']}` ({row['kind']}): {status}. Expected status `{row['expected_status']}` "
            f"and item `{row['expected_item_id']}`, got status `{row['actual_status']}` and item `{row['actual_item_id']}`."
        )

    return "\n".join(lines) + "\n"


def main() -> None:
    cases = load_cases()
    items = load_processed_items(ITEMS_PATH)

    results = {
        "output_quality": evaluate_output_quality(cases["output_quality_cases"]),
        "search_eval": evaluate_search(items, cases["search_cases"]),
        "end_to_end": evaluate_end_to_end(cases["end_to_end_cases"]),
    }

    RESULTS_JSON_PATH.write_text(json.dumps(results, indent=2), encoding="utf-8")
    RESULTS_MD_PATH.write_text(build_markdown_report(results), encoding="utf-8")

    print(f"Wrote {RESULTS_JSON_PATH}")
    print(f"Wrote {RESULTS_MD_PATH}")


if __name__ == "__main__":
    main()
