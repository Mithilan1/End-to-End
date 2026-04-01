from calendar import month_name
from pathlib import Path

import pandas as pd
import streamlit as st

from src.data_store import load_processed_items, load_recommendations, search_item_by_name, search_item_candidates
from src.image_search import identify_item_from_image
from src.llm_client import generate_llm_summary
from src.predict import predict_purchase_timing

st.set_page_config(page_title="Shopping Price Advisor", layout="wide")

ITEMS_PATH = Path("data/gold/items.json")
RECOMMENDATIONS_PATH = Path("data/gold/recommendations.json")


def _history_dataframe(item: dict) -> pd.DataFrame:
    history_df = pd.DataFrame(item["prices"])
    history_df["date"] = pd.to_datetime(history_df["date"])
    return history_df.sort_values("date")


def _build_trend_dataframe(item: dict, prediction: dict, trailing_days: int) -> pd.DataFrame:
    history_df = _history_dataframe(item)
    reference_date = pd.to_datetime(prediction["reference_date"])
    window_start = reference_date - pd.Timedelta(days=trailing_days)
    filtered_history = history_df.loc[history_df["date"] >= window_start, ["date", "price"]].copy()
    filtered_history["actual_price"] = filtered_history["price"]
    filtered_history["forecast_price"] = None
    filtered_history = filtered_history[["date", "actual_price", "forecast_price"]]

    forecast_rows = [
        {"date": pd.to_datetime(row["date"]), "actual_price": None, "forecast_price": row["price"]}
        for row in prediction["forecast_prices"].values()
    ]
    chart_df = pd.concat([filtered_history, pd.DataFrame(forecast_rows)], ignore_index=True)
    chart_df = chart_df.sort_values("date").set_index("date")
    return chart_df


def _format_window_metric(label: str, window: dict) -> str:
    price = window.get("price")
    if price is None:
        return f"{label}: n/a"
    when = window.get("date") or "unknown"
    return f"{label}: ${price:.2f} ({when})"


st.title("Shopping Price Advisor")
st.write("Search by name or upload a product image to compare the current price, recent best prices, forecasted future prices, and likely sale-window deals.")

if not ITEMS_PATH.exists() or not RECOMMENDATIONS_PATH.exists():
    st.error("Gold-layer data not found. Run `python -m src.etl` first.")
    st.stop()

items = load_processed_items(ITEMS_PATH)
recommendations = load_recommendations(RECOMMENDATIONS_PATH)

with st.sidebar:
    st.header("Find an item")
    item_name = st.text_input("Type an item name")
    image_file = st.file_uploader("Or upload an item image", type=["png", "jpg", "jpeg"])
    show_llm = st.checkbox("Show LLM summary", value=True)
    st.caption("The dashboard uses gold ETL outputs, Shopbot current-price seams, and optional LLM vision when an API key is configured.")

selected_item = None
selected_recommendation = None
source = None
candidates = []

if image_file is not None:
    image_match = identify_item_from_image(image_file, items)
    if image_match:
        selected_item = items.get(image_match["item_id"])
        selected_recommendation = recommendations.get(image_match["item_id"])
        source = (
            f"Image matched via {image_match['method']} "
            f"({image_match['confidence']:.2f} confidence). {image_match['reason']}"
        )
        st.image(image_file, caption="Uploaded item image", use_container_width=True)
    else:
        st.warning("Could not confidently identify the item from the image. Try typing the item name.")

if selected_item is None and item_name:
    candidates = search_item_candidates(item_name, items, limit=3)
    match, score = search_item_by_name(item_name, items)
    if match:
        selected_item = match
        selected_recommendation = recommendations.get(match["item_id"])
        source = f"Text search matched '{match['item_name']}' with score {score:.2f}."
    else:
        st.warning("No matching item found for that query.")

if selected_item:
    prediction = selected_recommendation or predict_purchase_timing(selected_item)
    monthly_profile = {
        int(month): value for month, value in selected_item.get("monthly_price_profile", {}).items()
    }
    best_windows = prediction["best_price_windows"]
    forecast_prices = prediction["forecast_prices"]

    st.subheader(selected_item["item_name"])
    if source:
        st.caption(source)
    st.caption(
        f"Current price source: {selected_item.get('current_price_source', 'unknown')} on "
        f"{selected_item.get('current_price_date', prediction['reference_date'])}"
    )

    top_metrics = st.columns(5)
    top_metrics[0].metric("Current price", f"${selected_item['current_price']:.2f}")
    top_metrics[1].metric("Action", prediction["recommendation"])
    top_metrics[2].metric("Target price", f"${prediction['target_price']:.2f}")
    top_metrics[3].metric("Buy window", prediction["buy_window"])
    top_metrics[4].metric("Confidence", prediction["confidence"])

    best_columns = st.columns(3)
    best_columns[0].metric("Best 30 days", f"${best_windows['30']['price']:.2f}" if best_windows["30"]["price"] is not None else "n/a")
    best_columns[1].metric("Best 60 days", f"${best_windows['60']['price']:.2f}" if best_windows["60"]["price"] is not None else "n/a")
    best_columns[2].metric("Best 90 days", f"${best_windows['90']['price']:.2f}" if best_windows["90"]["price"] is not None else "n/a")

    forecast_columns = st.columns(3)
    forecast_columns[0].metric("Predicted 30 days", f"${forecast_prices['30']['price']:.2f}")
    forecast_columns[1].metric("Predicted 60 days", f"${forecast_prices['60']['price']:.2f}")
    forecast_columns[2].metric("Predicted 90 days", f"${forecast_prices['90']['price']:.2f}")

    insight_columns = st.columns(2)
    with insight_columns[0]:
        st.write("### Recommendation")
        st.write(prediction["reason"])
        st.write(
            f"Current price is {prediction['price_vs_average_pct']:.1f}% versus average and "
            f"{prediction['price_vs_low_pct']:.1f}% above the historical low."
        )
        st.write(
            f"Next sale signal: {prediction['next_sale_name']} "
            f"({month_name[prediction['next_sale_month']]})"
        )
        if selected_item.get("best_buy_months"):
            best_month_names = ", ".join(month_name[int(month)] for month in selected_item["best_buy_months"])
            st.write(f"Best historical buy months: {best_month_names}")
        st.write(_format_window_metric("Best price in trailing 30 days", best_windows["30"]))
        st.write(_format_window_metric("Best price in trailing 60 days", best_windows["60"]))
        st.write(_format_window_metric("Best price in trailing 90 days", best_windows["90"]))
        st.write(f"Data sources: {', '.join(selected_item.get('available_sources', []))}")
        if selected_item.get("camel_url"):
            st.write(f"CamelCamelCamel reference: {selected_item['camel_url']}")
        if selected_item.get("shopbot_url"):
            st.write(f"Shopbot reference: {selected_item['shopbot_url']}")

    with insight_columns[1]:
        st.write("### Seasonal profile")
        if monthly_profile:
            seasonal_df = pd.DataFrame(
                [
                    {"month": month_name[month], "average_price": price}
                    for month, price in sorted(monthly_profile.items())
                ]
            )
            st.dataframe(seasonal_df, use_container_width=True, hide_index=True)
        else:
            st.info("Monthly seasonality profile is not available for this item yet.")

    trend_tabs = st.tabs(["6-Month Trend", "1-Year Trend", "Upcoming Sales"])
    with trend_tabs[0]:
        st.write("### 6-month price trend with 30/60/90-day forecast")
        st.line_chart(_build_trend_dataframe(selected_item, prediction, trailing_days=180))

    with trend_tabs[1]:
        st.write("### 1-year price trend with 30/60/90-day forecast")
        st.line_chart(_build_trend_dataframe(selected_item, prediction, trailing_days=365))

    with trend_tabs[2]:
        sale_df = pd.DataFrame(
            [
                {
                    "sale_window": row["sale_name"],
                    "month": month_name[row["sale_month"]],
                    "target_date": row["target_date"],
                    "predicted_price": row["predicted_price"],
                }
                for row in prediction["future_sale_forecasts"]
            ]
        )
        st.write("### Predicted price for upcoming sale windows")
        st.dataframe(sale_df, use_container_width=True, hide_index=True)

    if candidates:
        alternative_rows = [
            {"candidate": item["item_name"], "score": round(score, 2)}
            for item, score in candidates
            if item["item_id"] != selected_item["item_id"]
        ]
        if alternative_rows:
            st.write("### Alternate matches")
            st.dataframe(pd.DataFrame(alternative_rows), use_container_width=True, hide_index=True)

    if show_llm:
        st.write("### LLM summary")
        st.write(generate_llm_summary(selected_item, prediction))
else:
    st.info("Type an item name or upload a product image to begin.")
