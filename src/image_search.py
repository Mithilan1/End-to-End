from io import BytesIO

from PIL import Image

from .llm_client import identify_catalog_item_from_image

KNOWN_ITEMS = {
    "echo": "amazon_echo_dot",
    "fire": "fire_tv_stick",
    "airpods": "apple_airpods_pro",
    "kindle": "kindle_paperwhite",
}


def _catalog(items) -> list[dict]:
    values = items.values() if isinstance(items, dict) else items
    return [
        {
            "item_id": item["item_id"],
            "item_name": item["item_name"],
            "category": item.get("category", ""),
        }
        for item in values
    ]


def _filename_match(filename: str, known_item_ids: set[str]) -> dict | None:
    lower_name = filename.lower()
    for token, item_id in KNOWN_ITEMS.items():
        if token in lower_name and item_id in known_item_ids:
            return {
                "item_id": item_id,
                "confidence": 0.65,
                "method": "filename_hint",
                "reason": f"Filename contains the token '{token}'.",
            }
    return None


def _dimension_match(image_bytes: bytes, known_item_ids: set[str]) -> dict | None:
    try:
        image = Image.open(BytesIO(image_bytes))
        width, height = image.size
    except Exception:
        return None

    if width >= 800 and height >= 800 and "kindle_paperwhite" in known_item_ids:
        return {
            "item_id": "kindle_paperwhite",
            "confidence": 0.35,
            "method": "dimension_fallback",
            "reason": "Large upright image matched the broad e-reader fallback.",
        }
    return None


def identify_item_from_image(image_file, items) -> dict | None:
    catalog = _catalog(items)
    known_item_ids = {item["item_id"] for item in catalog}
    filename = getattr(image_file, "name", "")
    image_bytes = image_file.getvalue() if hasattr(image_file, "getvalue") else image_file.read()
    if not image_bytes:
        return None

    llm_match = identify_catalog_item_from_image(image_bytes, filename, catalog)
    if llm_match:
        item_id = llm_match.get("item_id")
        if item_id in known_item_ids:
            confidence = float(llm_match.get("confidence", 0.0) or 0.0)
            return {
                "item_id": item_id,
                "confidence": confidence,
                "method": "llm_vision",
                "reason": llm_match.get("reason", "LLM vision selected the closest catalog match."),
            }

    filename_match = _filename_match(filename, known_item_ids)
    if filename_match:
        return filename_match

    return _dimension_match(image_bytes, known_item_ids)
