import csv
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import requests

from .camelcamelcamel import normalize_price, parse_date

DEFAULT_TIMEOUT_SECONDS = 20
DEFAULT_SHOPBOT_SEARCH_URL = "https://www.shopbot.ca/"


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _truthy(value: str | None) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _safe_text(value: Any) -> str:
    return str(value or "").strip()


def load_injected_snapshots(path: Path) -> list[dict]:
    if not path.exists():
        return []

    rows = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            item_id = _safe_text(row.get("item_id"))
            date = _safe_text(row.get("date"))
            price = _safe_text(row.get("price"))
            if not item_id or not date or not price:
                continue

            rows.append(
                {
                    "item_id": item_id,
                    "item_name": _safe_text(row.get("item_name")),
                    "category": _safe_text(row.get("category")),
                    "shopbot_url": _safe_text(row.get("shopbot_url")),
                    "merchant": _safe_text(row.get("merchant")),
                    "date": parse_date(date),
                    "price": normalize_price(price),
                    "currency": _safe_text(row.get("currency")) or "CAD",
                }
            )
    return rows


def _extract_price_from_value(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = _safe_text(value)
    if not text:
        return None
    try:
        return normalize_price(text)
    except ValueError:
        return None


def _extract_first_price(payload: Any) -> float | None:
    if isinstance(payload, dict):
        for key in ("current_price", "price", "best_price", "amount", "offer_price", "min_price"):
            price = _extract_price_from_value(payload.get(key))
            if price is not None:
                return price
        for key in ("offer", "result", "product"):
            if key in payload:
                price = _extract_first_price(payload[key])
                if price is not None:
                    return price
        for key in ("results", "items", "offers", "products"):
            values = payload.get(key)
            if isinstance(values, list):
                for item in values:
                    price = _extract_first_price(item)
                    if price is not None:
                        return price
    elif isinstance(payload, list):
        for item in payload:
            price = _extract_first_price(item)
            if price is not None:
                return price
    return None


def _extract_first_text(payload: Any, keys: tuple[str, ...]) -> str:
    if isinstance(payload, dict):
        for key in keys:
            value = _safe_text(payload.get(key))
            if value:
                return value
        for nested_key in ("result", "product", "offer"):
            if nested_key in payload:
                text = _extract_first_text(payload[nested_key], keys)
                if text:
                    return text
        for list_key in ("results", "items", "offers", "products"):
            values = payload.get(list_key)
            if isinstance(values, list):
                for item in values:
                    text = _extract_first_text(item, keys)
                    if text:
                        return text
    elif isinstance(payload, list):
        for item in payload:
            text = _extract_first_text(item, keys)
            if text:
                return text
    return ""


def fetch_current_snapshot_from_api(item_name: str, shopbot_url: str = "", shopbot_query: str = "") -> dict | None:
    api_url = os.getenv("SHOPBOT_API_URL")
    if not api_url:
        return None

    headers = {"Accept": "application/json"}
    api_key = os.getenv("SHOPBOT_API_KEY")
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    params = {
        "query": shopbot_query or item_name,
        "item_name": item_name,
    }
    if shopbot_url:
        params["url"] = shopbot_url

    response = requests.get(api_url, params=params, headers=headers, timeout=DEFAULT_TIMEOUT_SECONDS)
    response.raise_for_status()
    payload = response.json()
    price = _extract_first_price(payload)
    if price is None:
        return None

    return {
        "item_name": _extract_first_text(payload, ("item_name", "title", "name")) or item_name,
        "price": price,
        "merchant": _extract_first_text(payload, ("merchant", "store", "seller")),
        "shopbot_url": _extract_first_text(payload, ("shopbot_url", "url", "link")) or shopbot_url,
        "currency": _extract_first_text(payload, ("currency", "currency_code")) or "CAD",
        "captured_at": _extract_first_text(payload, ("captured_at", "updated_at", "timestamp")) or _utc_timestamp(),
    }


def _extract_price_from_html(html: str) -> float | None:
    patterns = [
        r'"price"\s*:\s*"?(?P<price>[0-9]+(?:\.[0-9]{2})?)"?',
        r"from\s+\$(?P<price>[0-9][0-9,]*\.[0-9]{2})",
        r"\$(?P<price>[0-9][0-9,]*\.[0-9]{2})",
    ]
    for pattern in patterns:
        match = re.search(pattern, html, flags=re.IGNORECASE)
        if match:
            return normalize_price(match.group("price"))
    return None


def _extract_title_from_html(html: str) -> str:
    match = re.search(r"<title>(?P<title>.*?)</title>", html, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return ""
    title = re.sub(r"\s+", " ", match.group("title"))
    return title.strip()


def fetch_current_snapshot_from_html(item_name: str, shopbot_url: str = "", shopbot_query: str = "") -> dict | None:
    target_url = shopbot_url.strip()
    if not target_url:
        query = shopbot_query or item_name
        target_url = f"{DEFAULT_SHOPBOT_SEARCH_URL}?{urlencode({'search': query})}"

    response = requests.get(
        target_url,
        headers={"User-Agent": "Mozilla/5.0", "Accept-Language": "en-CA,en;q=0.9"},
        timeout=DEFAULT_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    html = response.text
    price = _extract_price_from_html(html)
    if price is None:
        return None

    return {
        "item_name": _extract_title_from_html(html) or item_name,
        "price": price,
        "merchant": "",
        "shopbot_url": target_url,
        "currency": "CAD",
        "captured_at": _utc_timestamp(),
    }


def fetch_current_snapshot(item_name: str, shopbot_url: str = "", shopbot_query: str = "") -> dict | None:
    try:
        snapshot = fetch_current_snapshot_from_api(item_name, shopbot_url=shopbot_url, shopbot_query=shopbot_query)
        if snapshot:
            snapshot["capture_method"] = "shopbot_api"
            return snapshot
    except Exception:
        pass

    if not _truthy(os.getenv("ENABLE_EXPERIMENTAL_SHOPBOT_FETCH")):
        return None

    try:
        snapshot = fetch_current_snapshot_from_html(item_name, shopbot_url=shopbot_url, shopbot_query=shopbot_query)
        if snapshot:
            snapshot["capture_method"] = "shopbot_html"
            return snapshot
    except Exception:
        return None

    return None


def snapshot_to_json(snapshot: dict) -> str:
    return json.dumps(snapshot, indent=2)
