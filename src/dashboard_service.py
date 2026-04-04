from __future__ import annotations

from calendar import month_name
from datetime import datetime
from pathlib import Path

from .data_store import (
    load_processed_items,
    load_recommendations,
    search_item_by_name,
    search_item_candidates,
)
from .image_search import identify_item_from_image
from .predict import predict_purchase_timing

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ITEMS_PATH = PROJECT_ROOT / "data" / "gold" / "items.json"
DEFAULT_RECOMMENDATIONS_PATH = PROJECT_ROOT / "data" / "gold" / "recommendations.json"


def load_dashboard_state(
    items_path: Path = DEFAULT_ITEMS_PATH,
    recommendations_path: Path = DEFAULT_RECOMMENDATIONS_PATH,
) -> tuple[dict, dict]:
    if not items_path.exists() or not recommendations_path.exists():
        raise FileNotFoundError(
            "Gold-layer data not found. Run `python -m src.etl` before starting the dashboard."
        )
    return load_processed_items(items_path), load_recommendations(recommendations_path)


def _history_rows(item: dict) -> list[dict]:
    rows = []
    for entry in item.get("prices", []):
        try:
            point_date = datetime.fromisoformat(entry["date"])
            point_price = float(entry["price"])
        except (KeyError, TypeError, ValueError):
            continue
        rows.append(
            {
                "date": point_date,
                "price": point_price,
                "source": entry.get("source", []),
                "merchant": entry.get("merchant", []),
            }
        )
    rows.sort(key=lambda row: row["date"])
    return rows


def build_trend_series(item: dict, prediction: dict, trailing_days: int) -> list[dict]:
    history_rows = _history_rows(item)
    reference_date = datetime.fromisoformat(prediction["reference_date"])
    window_start = reference_date.timestamp() - (trailing_days * 24 * 60 * 60)
    trend_rows = []

    for row in history_rows:
        if row["date"].timestamp() < window_start:
            continue
        trend_rows.append(
            {
                "date": row["date"].date().isoformat(),
                "actual_price": round(row["price"], 2),
                "forecast_price": None,
            }
        )

    for forecast in prediction.get("forecast_prices", {}).values():
        trend_rows.append(
            {
                "date": forecast["date"],
                "actual_price": None,
                "forecast_price": round(float(forecast["price"]), 2),
            }
        )

    trend_rows.sort(key=lambda row: row["date"])
    return trend_rows


def serialize_item_payload(item: dict, prediction: dict | None = None) -> dict:
    prediction = prediction or predict_purchase_timing(item)
    monthly_profile = {
        int(month): round(float(value), 2)
        for month, value in (item.get("monthly_price_profile") or {}).items()
    }

    history = [
        {
            "date": row["date"].date().isoformat(),
            "price": round(row["price"], 2),
            "source": row["source"],
            "merchant": row["merchant"],
        }
        for row in _history_rows(item)
    ]

    seasonal_profile = [
        {
            "month_number": month,
            "month_label": month_name[month],
            "average_price": value,
        }
        for month, value in sorted(monthly_profile.items())
    ]

    return {
        "item": item,
        "prediction": prediction,
        "history": history,
        "seasonal_profile": seasonal_profile,
        "trend_6m": build_trend_series(item, prediction, trailing_days=180),
        "trend_1y": build_trend_series(item, prediction, trailing_days=365),
    }


def _candidate_rows(candidates: list[tuple[dict, float]]) -> list[dict]:
    return [
        {
            "item_id": item["item_id"],
            "item_name": item["item_name"],
            "category": item.get("category", ""),
            "score": round(score, 2),
        }
        for item, score in candidates
    ]


def resolve_item_by_id(item_id: str, items: dict, recommendations: dict) -> dict | None:
    item = items.get(item_id)
    if not item:
        return None
    prediction = recommendations.get(item_id) or predict_purchase_timing(item)
    return {
        "source": f"Loaded '{item['item_name']}' from the gold-layer catalog.",
        "result": serialize_item_payload(item, prediction),
        "candidates": [],
    }


def resolve_item_by_query(query: str, items: dict, recommendations: dict) -> dict:
    candidates = search_item_candidates(query, items, limit=3)
    match, score = search_item_by_name(query, items)
    if not match:
        return {
            "source": "No high-confidence text match was found.",
            "result": None,
            "candidates": _candidate_rows(candidates),
        }

    prediction = recommendations.get(match["item_id"]) or predict_purchase_timing(match)
    return {
        "source": f"Text search matched '{match['item_name']}' with score {score:.2f}.",
        "result": serialize_item_payload(match, prediction),
        "candidates": _candidate_rows(
            [(item, item_score) for item, item_score in candidates if item["item_id"] != match["item_id"]]
        ),
    }


def resolve_item_by_image(image_file, items: dict, recommendations: dict) -> dict:
    image_match = identify_item_from_image(image_file, items)
    if not image_match:
        return {
            "source": "Could not confidently identify the item from the image.",
            "result": None,
            "candidates": [],
        }

    item_id = image_match["item_id"]
    item = items.get(item_id)
    if item is None:
        return {
            "source": "The image match did not map to a tracked catalog item.",
            "result": None,
            "candidates": [],
        }

    prediction = recommendations.get(item_id) or predict_purchase_timing(item)
    return {
        "source": (
            f"Image matched via {image_match['method']} "
            f"({image_match['confidence']:.2f} confidence). {image_match['reason']}"
        ),
        "result": serialize_item_payload(item, prediction),
        "candidates": [],
    }
