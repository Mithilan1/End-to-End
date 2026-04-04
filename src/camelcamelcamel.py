import csv
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, List, Tuple

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0.0.0 Safari/537.36"
)
DEFAULT_TIMEOUT_SECONDS = 20


def _truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _safe_text(value: Any) -> str:
    return str(value or "").strip()


def normalize_price(price_text: str) -> float:
    cleaned = price_text.replace("$", "").replace(",", "").strip()
    cleaned = re.sub(r"[^0-9\.]+", "", cleaned)
    return float(cleaned)


def parse_date(date_text: str) -> str:
    for fmt in ["%Y-%m-%d", "%b %d, %Y", "%d %b %Y", "%m/%d/%Y"]:
        try:
            return datetime.strptime(date_text.strip(), fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    raise ValueError(f"Cannot parse date: {date_text}")


def load_injected_history(path: Path) -> List[dict]:
    if not path.exists():
        return []

    rows = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            item_id = (row.get("item_id") or "").strip()
            date = (row.get("date") or "").strip()
            price = (row.get("price") or "").strip()
            if not item_id or not date or not price:
                continue

            rows.append(
                {
                    "item_id": item_id,
                    "item_name": (row.get("item_name") or "").strip(),
                    "category": (row.get("category") or "").strip(),
                    "camel_url": (row.get("camel_url") or "").strip(),
                    "date": parse_date(date),
                    "price": normalize_price(price),
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


def _extract_first_text(payload: Any, keys: tuple[str, ...]) -> str:
    if isinstance(payload, dict):
        for key in keys:
            text = _safe_text(payload.get(key))
            if text:
                return text
        for value in payload.values():
            nested = _extract_first_text(value, keys)
            if nested:
                return nested
    elif isinstance(payload, list):
        for item in payload:
            nested = _extract_first_text(item, keys)
            if nested:
                return nested
    return ""


def _extract_price_history_payload(payload: Any) -> List[dict]:
    rows: List[dict] = []
    if payload is None:
        return rows

    if isinstance(payload, dict):
        for key in ("history", "price_history", "records", "prices", "results", "items", "data"):
            if key in payload:
                rows.extend(_extract_price_history_payload(payload[key]))
        if "date" in payload and "price" in payload:
            try:
                rows.append({"date": parse_date(payload["date"]), "price": normalize_price(payload["price"])})
            except ValueError:
                pass
        return rows

    if isinstance(payload, list):
        for item in payload:
            rows.extend(_extract_price_history_payload(item))
        return rows

    return rows


def find_price_history_table(soup):
    for table in soup.find_all("table"):
        headers = [th.get_text(strip=True).lower() for th in table.find_all("th")]
        if "date" in headers and "price" in headers:
            return table
    return None


def parse_table_history(table) -> List[dict]:
    rows = []
    for row in table.find_all("tr"):
        cells = [cell.get_text(strip=True) for cell in row.find_all(["td", "th"])]
        if len(cells) < 2:
            continue
        if cells[0].lower() == "date" and cells[1].lower() == "price":
            continue
        try:
            rows.append({"date": parse_date(cells[0]), "price": normalize_price(cells[1])})
        except ValueError:
            continue
    return rows


def parse_script_history(html: str) -> List[dict]:
    rows = []
    date_price_pattern = re.compile(r"\['?(\d{4}-\d{2}-\d{2})'?,\s*\$?([0-9]+\.[0-9]{2})\]")
    for match in date_price_pattern.finditer(html):
        rows.append({"date": match.group(1), "price": float(match.group(2))})
    return rows


def scrape_price_history(url: str) -> List[dict]:
    import requests
    from bs4 import BeautifulSoup

    response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=DEFAULT_TIMEOUT_SECONDS)
    response.raise_for_status()
    html = response.text

    soup = BeautifulSoup(html, "html.parser")
    table = find_price_history_table(soup)
    if table is not None:
        history = parse_table_history(table)
        if history:
            return history

    history = parse_script_history(html)
    if history:
        return history

    raise ValueError("Unable to extract CamelCamelCamel price history from the page.")


def fetch_price_history_from_api(camel_url: str, item_name: str = "", item_id: str = "") -> List[dict]:
    api_url = os.getenv("CAMEL_API_URL", "").strip()
    if not api_url:
        return []

    headers = {"Accept": "application/json"}
    api_key = os.getenv("CAMEL_API_KEY", "").strip()
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    api_secret = os.getenv("CAMEL_API_SECRET", "").strip()
    if api_secret:
        headers["X-Api-Secret"] = api_secret

    partner_tag = os.getenv("CAMEL_API_PARTNER_TAG", "").strip()
    if partner_tag:
        headers["X-Partner-Tag"] = partner_tag

    params = {"url": camel_url}
    if item_name:
        params["query"] = item_name
    if item_id:
        params["item_id"] = item_id
    partner_type = os.getenv("CAMEL_API_PARTNER_TYPE", "").strip()
    if partner_type:
        params["partner_type"] = partner_type

    import requests

    response = requests.get(api_url, params=params, headers=headers, timeout=DEFAULT_TIMEOUT_SECONDS)
    response.raise_for_status()
    payload = response.json()
    history = _extract_price_history_payload(payload)
    return sorted(history, key=lambda entry: entry["date"]) if history else []


def fetch_price_history(camel_url: str, item_name: str = "", item_id: str = "") -> Tuple[List[dict], str]:
    if os.getenv("CAMEL_API_URL"):
        try:
            history = fetch_price_history_from_api(camel_url, item_name=item_name, item_id=item_id)
            if history:
                return history, "camelcamelcamel_api"
        except Exception as exc:
            print(f"Warning: CamelCamelCamel API request failed for {camel_url}: {exc}")

    if _truthy(os.getenv("ENABLE_EXPERIMENTAL_CAMEL_SCRAPE")):
        try:
            history = scrape_price_history(camel_url)
            return history, "camelcamelcamel_scrape"
        except Exception as exc:
            print(f"Warning: experimental CamelCamelCamel scrape failed for {camel_url}: {exc}")

    return [], "camelcamelcamel_api" if os.getenv("CAMEL_API_URL") else "camelcamelcamel_scrape"
