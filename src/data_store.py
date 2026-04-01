import json
from difflib import SequenceMatcher
from pathlib import Path


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_processed_items(path: Path) -> dict:
    return load_json(path)


def load_recommendations(path: Path) -> dict:
    return load_json(path)


def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def _score_query_against_item(query: str, item: dict) -> float:
    candidates = [item["item_name"], item["item_id"], item.get("category", "")]
    base_score = max(similarity(query, candidate) for candidate in candidates if candidate)
    if query.lower() in item["item_name"].lower():
        base_score += 0.2
    return min(base_score, 1.0)


def search_item_candidates(query: str, items: dict, limit: int = 3) -> list[tuple[dict, float]]:
    ranked = []
    for item in items.values():
        score = _score_query_against_item(query, item)
        ranked.append((item, score))
    ranked.sort(key=lambda pair: pair[1], reverse=True)
    return ranked[:limit]


def search_item_by_name(query: str, items: dict) -> tuple:
    candidates = search_item_candidates(query, items, limit=1)
    if not candidates:
        return None, 0.0
    match, score = candidates[0]
    return (match, score) if score >= 0.4 else (None, 0.0)
