from calendar import month_name
from datetime import date, datetime, timedelta, timezone

import numpy as np

MAJOR_SALE_WINDOWS = [
    ("Spring Sale", 3),
    ("Prime Day", 7),
    ("Back to School", 8),
    ("Black Friday / Cyber Monday", 11),
    ("Holiday Deals", 12),
]

CATEGORY_SALE_HINTS = {
    "smart_home": [7, 11, 12],
    "audio": [7, 11],
    "e-reader": [7, 11, 12],
}

FORECAST_HORIZONS = (30, 60, 90)


def _today(as_of: date | datetime | None = None) -> date:
    if as_of is None:
        return datetime.now(timezone.utc).date()
    if isinstance(as_of, datetime):
        return as_of.date()
    return as_of


def _month_gap(current_month: int, future_month: int) -> int:
    return (future_month - current_month) % 12


def find_next_sale_months(current_month: int, category: str | None = None) -> list[tuple[int, str, int]]:
    hints = set(CATEGORY_SALE_HINTS.get((category or "").lower(), []))
    sales = []
    for name, month in MAJOR_SALE_WINDOWS:
        weight = 0 if month in hints else 1
        sales.append((_month_gap(current_month, month), weight, name, month))
    sales.sort(key=lambda item: (item[0], item[1], item[3]))
    return [(gap, name, month) for gap, _, name, month in sales]


def _price_series(item: dict) -> list[tuple[date, float]]:
    rows = []
    for entry in item.get("prices", []):
        try:
            point_date = datetime.fromisoformat(entry["date"]).date()
            point_price = float(entry["price"])
        except (KeyError, TypeError, ValueError):
            continue
        rows.append((point_date, point_price))
    rows.sort(key=lambda row: row[0])
    return rows


def _reference_date(item: dict, as_of: date | datetime | None = None) -> date:
    if as_of is not None:
        return _today(as_of)
    series = _price_series(item)
    if series:
        return series[-1][0]
    return _today()


def _monthly_profile(item: dict) -> dict[int, float]:
    profile = item.get("monthly_price_profile") or {}
    normalized = {}
    for month, value in profile.items():
        normalized[int(month)] = float(value)
    if normalized:
        return normalized

    derived = {}
    for point_date, point_price in _price_series(item):
        derived.setdefault(point_date.month, []).append(point_price)
    return {month: round(sum(values) / len(values), 2) for month, values in derived.items()}


def _best_buy_months(item: dict) -> list[int]:
    explicit = item.get("best_buy_months")
    if explicit:
        return [int(month) for month in explicit]
    profile = _monthly_profile(item)
    return [month for month, _ in sorted(profile.items(), key=lambda row: (row[1], row[0]))[:3]]


def _choose_buy_month(current_month: int, best_buy_months: list[int]) -> int | None:
    if not best_buy_months:
        return None
    ranked = sorted(best_buy_months, key=lambda month: (_month_gap(current_month, month), month))
    return ranked[0]


def calculate_best_price_windows(item: dict, as_of: date | datetime | None = None, windows: tuple[int, ...] = FORECAST_HORIZONS) -> dict[str, dict]:
    reference_date = _reference_date(item, as_of)
    series = _price_series(item)
    result = {}
    for days in windows:
        window_start = reference_date - timedelta(days=days)
        candidates = [(point_date, point_price) for point_date, point_price in series if window_start <= point_date <= reference_date]
        if not candidates:
            result[str(days)] = {"price": None, "date": None}
            continue
        best_date, best_price = min(candidates, key=lambda row: (row[1], row[0]))
        result[str(days)] = {"price": round(best_price, 2), "date": best_date.isoformat()}
    return result


def _fit_trend(item: dict, reference_date: date) -> tuple[float, float]:
    series = _price_series(item)
    if not series:
        current_price = float(item.get("current_price", item["latest_price"]))
        return 0.0, current_price

    recent = series[-min(len(series), 12) :]
    x = np.array([(point_date - reference_date).days for point_date, _ in recent], dtype=float)
    y = np.array([point_price for _, point_price in recent], dtype=float)
    if len(np.unique(x)) < 2:
        return 0.0, float(y[-1])
    slope, intercept = np.polyfit(x, y, 1)
    return float(slope), float(intercept)


def forecast_price_for_date(item: dict, target_date: date, as_of: date | datetime | None = None) -> float:
    reference_date = _reference_date(item, as_of)
    slope, intercept = _fit_trend(item, reference_date)
    current_price = float(item.get("current_price", item["latest_price"]))
    avg_price = float(item["avg_price"])
    low_price = float(item["low_price"])
    high_price = float(item["high_price"])
    monthly_profile = _monthly_profile(item)

    target_x = (target_date - reference_date).days
    trend_price = (slope * target_x) + intercept
    seasonal_price = monthly_profile.get(target_date.month, avg_price)
    blended = (0.65 * trend_price) + (0.35 * seasonal_price)
    if np.isnan(blended):
        blended = current_price

    lower_bound = max(low_price * 0.85, 0.01)
    upper_bound = max(high_price * 1.15, lower_bound)
    bounded = min(max(blended, lower_bound), upper_bound)
    return round(float(bounded), 2)


def forecast_prices(item: dict, as_of: date | datetime | None = None, horizons: tuple[int, ...] = FORECAST_HORIZONS) -> dict[str, dict]:
    reference_date = _reference_date(item, as_of)
    forecasts = {}
    for days in horizons:
        target_date = reference_date + timedelta(days=days)
        forecasts[str(days)] = {
            "date": target_date.isoformat(),
            "price": forecast_price_for_date(item, target_date, as_of=reference_date),
        }
    return forecasts


def _sale_target_date(reference_date: date, sale_month: int) -> date:
    year = reference_date.year
    if sale_month < reference_date.month or (sale_month == reference_date.month and reference_date.day > 15):
        year += 1
    return date(year, sale_month, 15)


def predict_future_sale_prices(item: dict, as_of: date | datetime | None = None, limit: int = 4) -> list[dict]:
    reference_date = _reference_date(item, as_of)
    forecasts = []
    for _, sale_name, sale_month in find_next_sale_months(reference_date.month, item.get("category"))[:limit]:
        target_date = _sale_target_date(reference_date, sale_month)
        forecasts.append(
            {
                "sale_name": sale_name,
                "sale_month": sale_month,
                "target_date": target_date.isoformat(),
                "predicted_price": forecast_price_for_date(item, target_date, as_of=reference_date),
            }
        )
    return forecasts


def predict_purchase_timing(item: dict, as_of: date | datetime | None = None) -> dict:
    reference_date = _reference_date(item, as_of)
    current_month = reference_date.month
    latest = float(item.get("current_price", item["latest_price"]))
    avg_price = float(item["avg_price"])
    low_price = float(item["low_price"])
    high_price = float(item["high_price"])
    best_buy_months = _best_buy_months(item)
    buy_month = _choose_buy_month(current_month, best_buy_months)
    buy_gap = _month_gap(current_month, buy_month) if buy_month else None
    monthly_profile = _monthly_profile(item)
    seasonal_target = monthly_profile.get(buy_month, avg_price) if buy_month else avg_price

    next_sale = find_next_sale_months(current_month, item.get("category"))[0]
    next_sale_name = next_sale[1]
    next_sale_month = next_sale[2]

    best_price_windows = calculate_best_price_windows(item, as_of=reference_date)
    horizon_forecasts = forecast_prices(item, as_of=reference_date)
    sale_forecasts = predict_future_sale_prices(item, as_of=reference_date)
    future_prices = [row["price"] for row in horizon_forecasts.values()]
    future_prices.extend(row["predicted_price"] for row in sale_forecasts)
    best_future_price = min(future_prices) if future_prices else latest

    price_vs_average_pct = 0.0 if avg_price == 0 else round(((latest - avg_price) / avg_price) * 100, 1)
    price_vs_low_pct = 0.0 if low_price == 0 else round(((latest - low_price) / low_price) * 100, 1)
    price_position = 0.0 if high_price == low_price else (latest - low_price) / (high_price - low_price)
    close_to_low = price_vs_low_pct <= 5
    better_future_available = best_future_price <= latest * 0.94
    seasonal_discount_available_soon = buy_gap is not None and buy_gap <= 2 and latest > seasonal_target * 1.07

    if close_to_low or price_position <= 0.15 or latest <= best_future_price * 1.02:
        recommendation = "Buy now"
        confidence = "High" if close_to_low or price_position <= 0.15 else "Medium"
        reason = (
            f"The current price (${latest:.2f}) is already near the historical low (${low_price:.2f}) "
            f"and within 2% of the best near-term forecast."
        )
        buy_window = "Now"
    elif better_future_available or seasonal_discount_available_soon:
        recommendation = "Wait"
        confidence = "High"
        reason = (
            f"The current price (${latest:.2f}) is expected to improve to roughly ${best_future_price:.2f} "
            f"over the next forecast window or sale period."
        )
        buy_window = month_name[buy_month] if buy_month else month_name[next_sale_month]
    else:
        recommendation = "Wait"
        confidence = "Medium"
        reason = (
            f"The current price (${latest:.2f}) is not at the lowest observed range, "
            f"and the next retail sale signal is {next_sale_name}."
        )
        buy_window = month_name[buy_month] if buy_month else month_name[next_sale_month]

    target_price = round(min(low_price * 1.05, seasonal_target, avg_price * 0.97, best_future_price), 2)

    return {
        "recommendation": recommendation,
        "reason": reason,
        "latest_price": latest,
        "current_price": latest,
        "target_price": target_price,
        "next_sale_name": next_sale_name,
        "next_sale_month": next_sale_month,
        "buy_month": buy_month,
        "buy_window": buy_window,
        "confidence": confidence,
        "price_vs_average_pct": price_vs_average_pct,
        "price_vs_low_pct": price_vs_low_pct,
        "best_buy_months": best_buy_months,
        "best_price_windows": best_price_windows,
        "forecast_prices": horizon_forecasts,
        "future_sale_forecasts": sale_forecasts,
        "reference_date": reference_date.isoformat(),
    }
