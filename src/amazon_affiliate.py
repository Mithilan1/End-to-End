import os
import re
from datetime import datetime, timezone
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import requests

from .camelcamelcamel import normalize_price

DEFAULT_TIMEOUT_SECONDS = 20
DEFAULT_MARKETPLACE = "www.amazon.ca"


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _safe_text(value: Any) -> str:
    return str(value or "").strip()


def extract_asin(value: str) -> str:
    text = _safe_text(value)
    if not text:
        return ""

    match = re.search(r"(?:/dp/|/gp/product/|/product/)?([A-Z0-9]{10})(?:[/?]|$)", text, flags=re.IGNORECASE)
    if not match:
        return ""
    return match.group(1).upper()


def _normalize_marketplace(value: str | None) -> str:
    marketplace = _safe_text(value) or DEFAULT_MARKETPLACE
    if marketplace.startswith("http://") or marketplace.startswith("https://"):
        parsed = urlparse(marketplace)
        return parsed.netloc or DEFAULT_MARKETPLACE
    return marketplace.lstrip("/").rstrip("/")


def build_affiliate_product_url(
    asin: str,
    amazon_url: str = "",
    marketplace: str = "",
    partner_tag: str = "",
) -> str:
    resolved_asin = extract_asin(asin) or extract_asin(amazon_url)
    if not resolved_asin and not amazon_url:
        return ""

    if amazon_url:
        parsed = urlparse(amazon_url)
        scheme = parsed.scheme or "https"
        netloc = parsed.netloc or _normalize_marketplace(marketplace)
        path = parsed.path or (f"/dp/{resolved_asin}" if resolved_asin else "")
        query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    else:
        scheme = "https"
        netloc = _normalize_marketplace(marketplace)
        path = f"/dp/{resolved_asin}"
        query = {}

    if partner_tag:
        query["tag"] = partner_tag

    return urlunparse((scheme, netloc, path, "", urlencode(query), ""))


def _extract_price_from_value(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, dict):
        for key in ("amount", "value", "displayAmount", "price", "current_price", "listingPrice", "buyingPrice"):
            if key in value:
                nested = _extract_price_from_value(value.get(key))
                if nested is not None:
                    return nested
        return None

    text = _safe_text(value)
    if not text:
        return None
    try:
        return normalize_price(text)
    except ValueError:
        return None


def _extract_first_price(payload: Any) -> float | None:
    if isinstance(payload, dict):
        for key in (
            "current_price",
            "price",
            "listing_price",
            "listingPrice",
            "offer_price",
            "offerPrice",
            "buybox_price",
            "buyBoxPrice",
            "amount",
            "value",
            "buyingPrice",
            "displayAmount",
            "lowestPrice",
        ):
            price = _extract_price_from_value(payload.get(key))
            if price is not None:
                return price
        for key in ("offers", "offersV2", "offer", "result", "product", "item", "items", "data"):
            if key in payload:
                price = _extract_first_price(payload[key])
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


def _resolve_access_token() -> str:
    access_token = _safe_text(os.getenv("AMAZON_CREATOR_ACCESS_TOKEN"))
    if access_token:
        return access_token

    token_url = _safe_text(os.getenv("AMAZON_CREATOR_TOKEN_URL"))
    client_id = _safe_text(os.getenv("AMAZON_CREATOR_CLIENT_ID"))
    client_secret = _safe_text(os.getenv("AMAZON_CREATOR_CLIENT_SECRET"))
    if not (token_url and client_id and client_secret):
        return ""

    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
    }
    scope = _safe_text(os.getenv("AMAZON_CREATOR_SCOPE"))
    if scope:
        data["scope"] = scope

    response = requests.post(
        token_url,
        data=data,
        headers={"Accept": "application/json"},
        timeout=DEFAULT_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    payload = response.json()
    token = _safe_text(payload.get("access_token"))
    if token:
        return token
    raise ValueError("Amazon Creators token response did not include an access_token.")


def fetch_current_snapshot_from_api(
    item_name: str,
    amazon_asin: str = "",
    amazon_url: str = "",
    amazon_query: str = "",
    amazon_marketplace: str = "",
) -> dict | None:
    api_url = _safe_text(os.getenv("AMAZON_CREATOR_API_URL") or os.getenv("AMAZON_API_URL"))
    if not api_url:
        return None

    resolved_asin = extract_asin(amazon_asin) or extract_asin(amazon_url)
    marketplace = _normalize_marketplace(amazon_marketplace or os.getenv("AMAZON_CREATOR_MARKETPLACE"))
    partner_tag = _safe_text(os.getenv("AMAZON_CREATOR_PARTNER_TAG"))

    request_payload = {
        "asin": resolved_asin,
        "query": _safe_text(amazon_query) or item_name,
        "marketplace": marketplace,
        "partner_tag": partner_tag,
    }
    if amazon_url:
        request_payload["url"] = amazon_url

    headers = {"Accept": "application/json"}
    api_key = _safe_text(os.getenv("AMAZON_CREATOR_API_KEY"))
    if api_key:
        headers["x-api-key"] = api_key

    access_token = _resolve_access_token()
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"

    method = _safe_text(os.getenv("AMAZON_CREATOR_API_METHOD")).upper() or "GET"
    if method == "POST":
        response = requests.post(api_url, json=request_payload, headers=headers, timeout=DEFAULT_TIMEOUT_SECONDS)
    else:
        response = requests.get(api_url, params=request_payload, headers=headers, timeout=DEFAULT_TIMEOUT_SECONDS)
    response.raise_for_status()

    payload = response.json()
    price = _extract_first_price(payload)
    if price is None:
        return None

    payload_asin = extract_asin(_extract_first_text(payload, ("asin", "ASIN")))
    payload_url = _extract_first_text(payload, ("detail_page_url", "detailPageURL", "detailPageUrl", "url", "link"))
    affiliate_url = build_affiliate_product_url(
        payload_asin or resolved_asin,
        amazon_url=payload_url or amazon_url,
        marketplace=marketplace,
        partner_tag=partner_tag,
    )

    return {
        "item_name": _extract_first_text(payload, ("item_name", "title", "name", "productTitle")) or item_name,
        "price": price,
        "merchant": _extract_first_text(payload, ("merchant", "seller", "store", "brand")) or "Amazon",
        "amazon_url": affiliate_url or payload_url or amazon_url,
        "amazon_asin": payload_asin or resolved_asin,
        "currency": _extract_first_text(payload, ("currency", "currency_code", "currencyCode")) or "CAD",
        "captured_at": _extract_first_text(payload, ("captured_at", "updated_at", "timestamp")) or _utc_timestamp(),
        "marketplace": marketplace,
    }


def fetch_current_snapshot(
    item_name: str,
    amazon_asin: str = "",
    amazon_url: str = "",
    amazon_query: str = "",
    amazon_marketplace: str = "",
) -> dict | None:
    snapshot = fetch_current_snapshot_from_api(
        item_name,
        amazon_asin=amazon_asin,
        amazon_url=amazon_url,
        amazon_query=amazon_query,
        amazon_marketplace=amazon_marketplace,
    )
    if snapshot:
        snapshot["capture_method"] = "amazon_creators_api"
    return snapshot
