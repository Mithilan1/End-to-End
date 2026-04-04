from __future__ import annotations

import os
from pathlib import Path

from flask import Flask, jsonify, redirect, request

from src.dashboard_service import (
    DEFAULT_ITEMS_PATH,
    DEFAULT_RECOMMENDATIONS_PATH,
    load_dashboard_state,
    resolve_item_by_id,
    resolve_item_by_image,
    resolve_item_by_query,
)
from src.llm_client import generate_llm_summary

PROJECT_ROOT = Path(__file__).resolve().parent
PUBLIC_ROOT = PROJECT_ROOT / "public"

app = Flask(__name__, static_folder=str(PUBLIC_ROOT), static_url_path="")
app.config["MAX_CONTENT_LENGTH"] = 6 * 1024 * 1024


def _truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def _dashboard_state() -> tuple[dict, dict]:
    return load_dashboard_state(DEFAULT_ITEMS_PATH, DEFAULT_RECOMMENDATIONS_PATH)


def _json_error(message: str, status_code: int = 400, **extra):
    payload = {"ok": False, "message": message}
    payload.update(extra)
    return jsonify(payload), status_code


def _attach_summary(response_payload: dict, include_summary: bool) -> dict:
    if not include_summary:
        return response_payload

    result = response_payload.get("result")
    if not result:
        return response_payload

    summary = generate_llm_summary(result["item"], result["prediction"])
    result["llm_summary"] = summary
    return response_payload


@app.route("/")
def home():
    return app.send_static_file("index.html")


@app.route("/favicon.ico")
def favicon():
    if (PUBLIC_ROOT / "favicon.svg").exists():
        return redirect("/favicon.svg", code=307)
    return ("", 204)


@app.route("/api/health")
def health():
    try:
        items, _ = _dashboard_state()
    except FileNotFoundError as exc:
        return _json_error(str(exc), status_code=503)

    return jsonify(
        {
            "ok": True,
            "status": "ready",
            "catalog_size": len(items),
            "items_path": str(DEFAULT_ITEMS_PATH.relative_to(PROJECT_ROOT)),
            "recommendations_path": str(DEFAULT_RECOMMENDATIONS_PATH.relative_to(PROJECT_ROOT)),
        }
    )


@app.route("/api/catalog")
def catalog():
    try:
        items, _ = _dashboard_state()
    except FileNotFoundError as exc:
        return _json_error(str(exc), status_code=503)

    rows = [
        {
            "item_id": item["item_id"],
            "item_name": item["item_name"],
            "category": item.get("category", ""),
            "current_price": item.get("current_price", item.get("latest_price")),
        }
        for item in sorted(items.values(), key=lambda row: row["item_name"].lower())
    ]
    return jsonify({"ok": True, "items": rows})


@app.route("/api/items/<item_id>")
def get_item(item_id: str):
    include_summary = _truthy(request.args.get("summary"))
    try:
        items, recommendations = _dashboard_state()
    except FileNotFoundError as exc:
        return _json_error(str(exc), status_code=503)

    payload = resolve_item_by_id(item_id, items, recommendations)
    if payload is None:
        return _json_error("Item not found in the gold-layer catalog.", status_code=404, item_id=item_id)

    return jsonify(_attach_summary({"ok": True, **payload}, include_summary))


@app.route("/api/search")
def search():
    query = (request.args.get("q") or "").strip()
    include_summary = _truthy(request.args.get("summary"))
    if not query:
        return _json_error("Provide a non-empty `q` search query.", status_code=400)

    try:
        items, recommendations = _dashboard_state()
    except FileNotFoundError as exc:
        return _json_error(str(exc), status_code=503)

    payload = resolve_item_by_query(query, items, recommendations)
    payload = _attach_summary(payload, include_summary)
    status_code = 200 if payload["result"] else 404
    return jsonify({"ok": payload["result"] is not None, "query": query, **payload}), status_code


@app.route("/api/identify-image", methods=["POST"])
def identify_image():
    include_summary = _truthy(request.form.get("summary"))
    image = request.files.get("image")
    if image is None or not image.filename:
        return _json_error("Upload an image file using the `image` field.", status_code=400)

    try:
        items, recommendations = _dashboard_state()
    except FileNotFoundError as exc:
        return _json_error(str(exc), status_code=503)

    payload = resolve_item_by_image(image, items, recommendations)
    payload = _attach_summary(payload, include_summary)
    status_code = 200 if payload["result"] else 404
    return jsonify({"ok": payload["result"] is not None, **payload}), status_code


@app.errorhandler(413)
def file_too_large(_error):
    return _json_error("Image upload is too large. Keep uploads under 6 MB.", status_code=413)


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    debug_mode = _truthy(os.getenv("FLASK_DEBUG"))
    app.run(host="0.0.0.0", port=port, debug=debug_mode)
