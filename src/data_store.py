import json
import re
from difflib import SequenceMatcher
from pathlib import Path

CATALOG_ALIASES = {
    "amazon_echo_dot": [
        "echo dot",
        "alexa speaker",
        "amazon smart speaker",
        "smart speaker",
    ],
    "apple_airpods_pro": [
        "airpods",
        "airpods pro",
        "wireless earbuds",
        "apple earbuds",
        "noise cancelling earbuds",
    ],
    "fire_tv_stick": [
        "firestick",
        "streaming stick",
        "streaming device",
        "tv stick",
    ],
    "kindle_paperwhite": [
        "kindle",
        "paperwhite",
        "e-reader",
        "ereader",
        "ebook reader",
    ],
}

STOP_WORDS = {
    "a",
    "an",
    "and",
    "for",
    "gen",
    "generation",
    "the",
    "with",
}


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_processed_items(path: Path) -> dict:
    return load_json(path)


def load_recommendations(path: Path) -> dict:
    return load_json(path)


def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def _normalize_text(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()
    return " ".join(cleaned.split())


def _tokenize(value: str) -> set[str]:
    return {token for token in _normalize_text(value).split() if token and token not in STOP_WORDS}


def _token_overlap_score(query: str, candidate: str) -> float:
    query_tokens = _tokenize(query)
    candidate_tokens = _tokenize(candidate)
    if not query_tokens or not candidate_tokens:
        return 0.0
    overlap = len(query_tokens & candidate_tokens)
    if overlap == 0:
        return 0.0
    coverage = overlap / len(query_tokens)
    precision = overlap / len(candidate_tokens)
    return round((0.7 * coverage) + (0.3 * precision), 4)


def _candidate_names(item: dict) -> list[str]:
    candidates = [item["item_name"], item["item_id"], item.get("category", "")]
    candidates.extend(CATALOG_ALIASES.get(item["item_id"], []))
    return [candidate for candidate in candidates if candidate]


def _score_query_against_item(query: str, item: dict) -> float:
    normalized_query = _normalize_text(query)
    best_score = 0.0

    for candidate in _candidate_names(item):
        normalized_candidate = _normalize_text(candidate)
        sequence_score = similarity(normalized_query, normalized_candidate)
        overlap_score = _token_overlap_score(normalized_query, normalized_candidate)
        score = max(sequence_score, overlap_score)

        if normalized_query and normalized_query in normalized_candidate:
            score += 0.2
        elif overlap_score >= 0.6:
            score += 0.12

        best_score = max(best_score, score)

    return min(best_score, 1.0)


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
    return (match, score) if score >= 0.75 else (None, 0.0)
