import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import pandas as pd

from .camelcamelcamel import load_injected_history, scrape_price_history
from .predict import predict_purchase_timing
from .shopbot import fetch_current_snapshot, load_injected_snapshots

ROOT = Path(__file__).resolve().parent.parent
DATA_ROOT = ROOT / "data"
DEFAULT_SAMPLE_PATH = DATA_ROOT / "sample_price_history.csv"
DEFAULT_TRACK_PATH = DATA_ROOT / "track_items.csv"
DEFAULT_INJECTION_PATH = DATA_ROOT / "camelcamelcamel_injection.csv"
DEFAULT_SHOPBOT_INJECTION_PATH = DATA_ROOT / "shopbot_injection.csv"


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _truthy(value: str | None) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _load_tracking_manifest(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}

    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    manifest = {}
    for row in rows:
        item_id = (row.get("item_id") or "").strip()
        if not item_id:
            continue
        manifest[item_id] = {
            "item_id": item_id,
            "item_name": (row.get("item_name") or item_id).strip(),
            "category": (row.get("category") or "unknown").strip(),
            "camel_url": (row.get("camel_url") or "").strip(),
            "shopbot_query": (row.get("shopbot_query") or row.get("item_name") or item_id).strip(),
            "shopbot_url": (row.get("shopbot_url") or "").strip(),
        }
    return manifest


def _build_observation(
    item_id: str,
    item_name: str,
    category: str,
    date: str,
    price: float,
    source: str,
    source_ref: str,
    camel_url: str = "",
    shopbot_url: str = "",
    merchant: str = "",
    currency: str = "USD",
) -> dict:
    return {
        "item_id": item_id,
        "item_name": item_name,
        "category": category,
        "date": date,
        "price": float(price),
        "currency": currency,
        "source": source,
        "source_ref": source_ref,
        "camel_url": camel_url,
        "shopbot_url": shopbot_url,
        "merchant": merchant,
        "ingested_at": _utc_timestamp(),
    }


def _extract_sample_records(path: Path) -> list[dict]:
    if not path.exists():
        return []

    df = pd.read_csv(path, parse_dates=["date"])
    records = []
    for row in df.itertuples():
        records.append(
            _build_observation(
                item_id=row.item_id,
                item_name=row.item_name,
                category=row.category,
                date=row.date.strftime("%Y-%m-%d"),
                price=float(row.price),
                source="sample_seed",
                source_ref=path.name,
                currency="USD",
            )
        )
    return records


def _extract_injected_records(path: Path, manifest: dict[str, dict]) -> list[dict]:
    rows = load_injected_history(path)
    records = []
    for row in rows:
        manifest_row = manifest.get(row["item_id"], {})
        records.append(
            _build_observation(
                item_id=row["item_id"],
                item_name=row.get("item_name") or manifest_row.get("item_name", row["item_id"]),
                category=row.get("category") or manifest_row.get("category", "unknown"),
                date=row["date"],
                price=float(row["price"]),
                source="camelcamelcamel_injection",
                source_ref=row.get("camel_url") or path.name,
                camel_url=row.get("camel_url") or manifest_row.get("camel_url", ""),
                currency="USD",
            )
        )
    return records


def _extract_shopbot_injected_records(path: Path, manifest: dict[str, dict]) -> list[dict]:
    rows = load_injected_snapshots(path)
    records = []
    for row in rows:
        manifest_row = manifest.get(row["item_id"], {})
        records.append(
            _build_observation(
                item_id=row["item_id"],
                item_name=row.get("item_name") or manifest_row.get("item_name", row["item_id"]),
                category=row.get("category") or manifest_row.get("category", "unknown"),
                date=row["date"],
                price=float(row["price"]),
                source="shopbot_injection",
                source_ref=row.get("shopbot_url") or path.name,
                shopbot_url=row.get("shopbot_url") or manifest_row.get("shopbot_url", ""),
                merchant=row.get("merchant", ""),
                currency=row.get("currency") or "CAD",
            )
        )
    return records


def _extract_scraped_records(manifest: dict[str, dict], enable_camel_scrape: bool) -> list[dict]:
    if not enable_camel_scrape:
        return []

    records = []
    for row in manifest.values():
        camel_url = row.get("camel_url", "").strip()
        if not camel_url:
            continue

        try:
            history = scrape_price_history(camel_url)
        except Exception as exc:
            print(f"Warning: failed to scrape {row['item_id']} from {camel_url}: {exc}")
            continue

        for entry in history:
            records.append(
                _build_observation(
                    item_id=row["item_id"],
                    item_name=row["item_name"],
                    category=row["category"],
                    date=entry["date"],
                    price=float(entry["price"]),
                    source="camelcamelcamel_scrape",
                    source_ref=camel_url,
                    camel_url=camel_url,
                    currency="USD",
                )
            )
    return records


def _extract_shopbot_live_records(manifest: dict[str, dict]) -> list[dict]:
    records = []
    for row in manifest.values():
        try:
            snapshot = fetch_current_snapshot(
                row["item_name"],
                shopbot_url=row.get("shopbot_url", ""),
                shopbot_query=row.get("shopbot_query", ""),
            )
        except Exception as exc:
            print(f"Warning: failed to fetch Shopbot snapshot for {row['item_id']}: {exc}")
            continue

        if not snapshot:
            continue

        captured_at = snapshot.get("captured_at", _utc_timestamp())[:10]
        records.append(
            _build_observation(
                item_id=row["item_id"],
                item_name=row["item_name"],
                category=row["category"],
                date=captured_at,
                price=float(snapshot["price"]),
                source=snapshot.get("capture_method", "shopbot_live"),
                source_ref=snapshot.get("shopbot_url") or row.get("shopbot_url", "") or row.get("shopbot_query", ""),
                shopbot_url=snapshot.get("shopbot_url") or row.get("shopbot_url", ""),
                merchant=snapshot.get("merchant", ""),
                currency=snapshot.get("currency") or "CAD",
            )
        )
    return records


def extract_bronze_records(
    manifest_path: Path | None = None,
    sample_path: Path | None = None,
    injection_path: Path | None = None,
    shopbot_injection_path: Path | None = None,
    enable_camel_scrape: bool | None = None,
) -> list[dict]:
    manifest_path = manifest_path or DEFAULT_TRACK_PATH
    sample_path = sample_path or DEFAULT_SAMPLE_PATH
    injection_path = injection_path or DEFAULT_INJECTION_PATH
    shopbot_injection_path = shopbot_injection_path or DEFAULT_SHOPBOT_INJECTION_PATH

    manifest = _load_tracking_manifest(manifest_path)
    records = []
    records.extend(_extract_sample_records(sample_path))
    records.extend(_extract_injected_records(injection_path, manifest))
    records.extend(_extract_shopbot_injected_records(shopbot_injection_path, manifest))

    scrape_enabled = _truthy(os.getenv("ENABLE_EXPERIMENTAL_CAMEL_SCRAPE")) if enable_camel_scrape is None else enable_camel_scrape
    records.extend(_extract_scraped_records(manifest, scrape_enabled))
    records.extend(_extract_shopbot_live_records(manifest))

    if not records:
        raise RuntimeError("No bronze observations were extracted. Add sample data or a CamelCamelCamel injection file.")

    return sorted(records, key=lambda row: (row["item_id"], row["date"], row["price"], row["source"]))


def write_bronze_layer(records: Iterable[dict], target_path: Path) -> Path:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    serializable = list(records)
    with target_path.open("w", encoding="utf-8") as handle:
        json.dump(serializable, handle, indent=2)
    return target_path


def build_silver_dataset(records: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(records)
    if df.empty:
        raise RuntimeError("Cannot build silver layer from empty bronze records.")

    for column, default in {
        "source_ref": "",
        "camel_url": "",
        "shopbot_url": "",
        "merchant": "",
        "currency": "USD",
    }.items():
        if column not in df.columns:
            df[column] = default

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df = df.dropna(subset=["item_id", "item_name", "category", "date", "price"])
    df["source_ref"] = df["source_ref"].fillna("").astype(str)
    df["camel_url"] = df["camel_url"].fillna("").astype(str)
    df["shopbot_url"] = df["shopbot_url"].fillna("").astype(str)
    df["merchant"] = df["merchant"].fillna("").astype(str)
    df["currency"] = df["currency"].fillna("").astype(str)

    silver = (
        df.sort_values(["item_id", "date", "price"])
        .groupby(["item_id", "date"], as_index=False)
        .agg(
            item_name=("item_name", "last"),
            category=("category", "last"),
            price=("price", "min"),
            currency=("currency", "last"),
            camel_url=("camel_url", "last"),
            shopbot_url=("shopbot_url", "last"),
            merchant=("merchant", lambda values: "|".join(sorted(set(filter(None, values))))),
            source=("source", lambda values: "|".join(sorted(set(values)))),
            source_ref=("source_ref", lambda values: "|".join(sorted(set(filter(None, values))))),
        )
        .sort_values(["item_id", "date"])
        .reset_index(drop=True)
    )

    silver["price"] = silver["price"].round(2)
    return silver


def write_silver_layer(df: pd.DataFrame, target_path: Path) -> Path:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    export_df = df.copy()
    export_df["date"] = export_df["date"].dt.strftime("%Y-%m-%d")
    export_df.to_csv(target_path, index=False)
    return target_path


def build_gold_items(df: pd.DataFrame) -> dict[str, dict]:
    items = {}
    for item_id, group in df.groupby("item_id"):
        group = group.sort_values("date").copy()
        monthly_profile = (
            group.assign(month=group["date"].dt.month)
            .groupby("month")["price"]
            .mean()
            .round(2)
            .to_dict()
        )
        best_buy_months = [int(month) for month, _ in sorted(monthly_profile.items(), key=lambda item: (item[1], item[0]))[:3]]
        prices = [
            {
                "date": row.date.strftime("%Y-%m-%d"),
                "price": float(row.price),
                "source": row.source.split("|"),
                "merchant": row.merchant.split("|") if row.merchant else [],
            }
            for row in group.itertuples()
        ]
        sources = sorted({source for row in group["source"] for source in row.split("|")})
        last_camel_url = next((value for value in reversed(group["camel_url"].tolist()) if value), "")
        last_shopbot_url = next((value for value in reversed(group["shopbot_url"].tolist()) if value), "")
        latest_row = group.iloc[-1]
        shopbot_rows = group[group["source"].str.contains("shopbot", case=False, regex=False)]
        current_row = shopbot_rows.iloc[-1] if not shopbot_rows.empty else latest_row

        items[item_id] = {
            "item_id": item_id,
            "item_name": group["item_name"].iloc[-1],
            "category": group["category"].iloc[-1],
            "latest_price": float(group["price"].iloc[-1]),
            "current_price": float(current_row["price"]),
            "current_price_date": current_row["date"].strftime("%Y-%m-%d"),
            "current_price_source": current_row["source"],
            "current_price_currency": current_row["currency"],
            "current_price_merchant": current_row["merchant"] or None,
            "avg_price": float(round(group["price"].mean(), 2)),
            "low_price": float(round(group["price"].min(), 2)),
            "high_price": float(round(group["price"].max(), 2)),
            "price_points": int(len(group)),
            "best_buy_months": best_buy_months,
            "seasonal_months": sorted(int(month) for month in monthly_profile.keys()),
            "monthly_price_profile": {str(month): float(price) for month, price in monthly_profile.items()},
            "available_sources": sources,
            "prices": prices,
            "camel_url": last_camel_url or None,
            "shopbot_url": last_shopbot_url or None,
            "last_updated": _utc_timestamp(),
        }
    return items


def build_gold_recommendations(items: dict[str, dict]) -> dict[str, dict]:
    return {item_id: predict_purchase_timing(item) for item_id, item in items.items()}


def write_gold_layers(
    items: dict[str, dict],
    recommendations: dict[str, dict],
    gold_dir: Path,
    data_root: Path | None = None,
) -> dict[str, Path]:
    gold_dir.mkdir(parents=True, exist_ok=True)
    items_path = gold_dir / "items.json"
    recommendations_path = gold_dir / "recommendations.json"

    with items_path.open("w", encoding="utf-8") as handle:
        json.dump(items, handle, indent=2)

    with recommendations_path.open("w", encoding="utf-8") as handle:
        json.dump(recommendations, handle, indent=2)

    outputs = {
        "gold_items": items_path,
        "gold_recommendations": recommendations_path,
    }

    if data_root is not None and data_root.resolve() == DATA_ROOT.resolve():
        processed_dir = data_root / "processed"
        processed_dir.mkdir(parents=True, exist_ok=True)
        legacy_path = processed_dir / "items.json"
        with legacy_path.open("w", encoding="utf-8") as handle:
            json.dump(items, handle, indent=2)
        outputs["legacy_processed_items"] = legacy_path

    return outputs


def run_medallion_pipeline(
    manifest_path: Path | None = None,
    sample_path: Path | None = None,
    injection_path: Path | None = None,
    shopbot_injection_path: Path | None = None,
    output_root: Path | None = None,
    enable_camel_scrape: bool | None = None,
) -> dict[str, Path]:
    output_root = output_root or DATA_ROOT
    bronze_dir = output_root / "bronze"
    silver_dir = output_root / "silver"
    gold_dir = output_root / "gold"

    bronze_records = extract_bronze_records(
        manifest_path=manifest_path,
        sample_path=sample_path,
        injection_path=injection_path,
        shopbot_injection_path=shopbot_injection_path,
        enable_camel_scrape=enable_camel_scrape,
    )
    bronze_path = write_bronze_layer(bronze_records, bronze_dir / "price_observations.json")

    silver_df = build_silver_dataset(bronze_records)
    silver_path = write_silver_layer(silver_df, silver_dir / "normalized_prices.csv")

    gold_items = build_gold_items(silver_df)
    gold_recommendations = build_gold_recommendations(gold_items)
    gold_paths = write_gold_layers(gold_items, gold_recommendations, gold_dir, data_root=output_root)

    outputs = {
        "bronze": bronze_path,
        "silver": silver_path,
    }
    outputs.update(gold_paths)
    return outputs
