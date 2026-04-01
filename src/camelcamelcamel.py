import csv
import re
from datetime import datetime
from pathlib import Path
from typing import List

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0.0.0 Safari/537.36"
)


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
            parsed = {
                "date": parse_date(cells[0]),
                "price": normalize_price(cells[1]),
            }
        except ValueError:
            continue
        rows.append(parsed)
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

    response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=20)
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


def fetch_price_history(url: str) -> List[dict]:
    return scrape_price_history(url)
