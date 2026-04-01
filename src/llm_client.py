import base64
import json
import mimetypes
import os
from typing import Any

from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SUMMARY_MODEL = os.getenv("OPENAI_SUMMARY_MODEL", "gpt-4.1-mini")
VISION_MODEL = os.getenv("OPENAI_VISION_MODEL", "gpt-4.1-mini")

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


def _client():
    if not OPENAI_API_KEY or OpenAI is None:
        return None
    return OpenAI(api_key=OPENAI_API_KEY)


def _clean_output_text(response: Any) -> str:
    text = getattr(response, "output_text", "") or ""
    return text.strip().strip("`").strip()


def generate_llm_summary(item: dict, prediction: dict) -> str:
    client = _client()
    if client is None:
        return "OpenAI is not configured. Set OPENAI_API_KEY to enable LLM summaries and vision-based item lookup."

    forecast_prices = prediction.get("forecast_prices", {})
    sale_forecasts = prediction.get("future_sale_forecasts", [])
    predicted_30 = forecast_prices.get("30", {}).get("price")
    predicted_60 = forecast_prices.get("60", {}).get("price")
    predicted_90 = forecast_prices.get("90", {}).get("price")
    next_sale_price = sale_forecasts[0]["predicted_price"] if sale_forecasts else None

    prompt = (
        "You are a concise shopping advisor. Explain the recommendation using plain language.\n"
        f"Item: {item['item_name']}\n"
        f"Category: {item['category']}\n"
        f"Current price: ${prediction['current_price']:.2f}\n"
        f"Average price: ${item['avg_price']:.2f}\n"
        f"Historical low: ${item['low_price']:.2f}\n"
        f"Recommendation: {prediction['recommendation']}\n"
        f"Target price: ${prediction['target_price']:.2f}\n"
        f"Suggested buy window: {prediction['buy_window']}\n"
        f"Next sale signal: {prediction['next_sale_name']}\n"
        f"Predicted price in 30 days: ${predicted_30:.2f}\n"
        f"Predicted price in 60 days: ${predicted_60:.2f}\n"
        f"Predicted price in 90 days: ${predicted_90:.2f}\n"
        f"Predicted next sale price: {'n/a' if next_sale_price is None else f'${next_sale_price:.2f}'}\n"
        "Keep it under 120 words."
    )

    try:
        response = client.responses.create(
            model=SUMMARY_MODEL,
            input=[{"role": "user", "content": [{"type": "input_text", "text": prompt}]}],
            max_output_tokens=180,
        )
        return _clean_output_text(response) or "LLM summary was empty."
    except Exception as exc:
        return f"LLM request failed: {exc}"


def identify_catalog_item_from_image(image_bytes: bytes, filename: str, catalog: list[dict]) -> dict | None:
    client = _client()
    if client is None or not image_bytes or not catalog:
        return None

    mime_type = mimetypes.guess_type(filename or "")[0] or "image/png"
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")
    catalog_payload = [
        {
            "item_id": item["item_id"],
            "item_name": item["item_name"],
            "category": item.get("category", ""),
        }
        for item in catalog
    ]
    prompt = (
        "Choose the closest matching catalog item for this product photo. "
        "Return strict JSON with keys item_id, confidence, and reason. "
        "If nothing matches, use null for item_id.\n"
        f"Catalog: {json.dumps(catalog_payload)}"
    )

    try:
        response = client.responses.create(
            model=VISION_MODEL,
            input=[
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": prompt},
                        {"type": "input_image", "image_url": f"data:{mime_type};base64,{image_b64}"},
                    ],
                }
            ],
            max_output_tokens=220,
        )
    except Exception:
        return None

    text = _clean_output_text(response)
    if not text:
        return None

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1:
            return None
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return None
