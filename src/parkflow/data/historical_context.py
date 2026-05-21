from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
import requests

from parkflow.config import PARK_ID, PROCESSED_DIR, QUEUE_TIMES_BASE_URL, RAW_DIR

USER_AGENT = "ParkFlowAnalytics/0.1 (+portfolio research; respectful public data use)"


def _slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_") or "table"


def fetch_public_html(path: str, timeout: int = 30) -> str:
    """Fetch a public Queue-Times HTML page for aggregated context.

    This should be used only for low-frequency, transparent collection of public aggregate pages.
    Do not use it for aggressive crawling.
    """
    url = f"{QUEUE_TIMES_BASE_URL}{path}"
    response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=timeout)
    response.raise_for_status()
    return response.text


def extract_html_tables(html: str) -> list[pd.DataFrame]:
    """Extract all HTML tables from a page using pandas.read_html."""
    try:
        return pd.read_html(html)
    except ValueError:
        return []


def save_public_context_tables(page_name: str, html: str) -> list[Path]:
    """Save raw HTML and parsed tables from a public aggregated context page."""
    raw_dir = RAW_DIR / "historical_context"
    processed_dir = PROCESSED_DIR / "historical_context"
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    raw_path = raw_dir / f"{_slugify(page_name)}.html"
    raw_path.write_text(html, encoding="utf-8")

    paths: list[Path] = []
    for i, table in enumerate(extract_html_tables(html), start=1):
        out_path = processed_dir / f"{_slugify(page_name)}_table_{i:02d}.csv"
        table.to_csv(out_path, index=False)
        paths.append(out_path)
    return paths


def collect_queue_times_stats(park_id: int = PARK_ID) -> list[Path]:
    """Collect public aggregate statistics tables for the park."""
    html = fetch_public_html(f"/parks/{park_id}/stats")
    return save_public_context_tables("queue_times_stats", html)


def collect_attendance_history(park_id: int = PARK_ID) -> list[Path]:
    """Collect public yearly attendance table for the park."""
    html = fetch_public_html(f"/parks/{park_id}/attendances")
    return save_public_context_tables("attendance_history", html)


def main() -> None:
    outputs = []
    outputs.extend(collect_queue_times_stats())
    outputs.extend(collect_attendance_history())

    if not outputs:
        print("No tables found. Check page structure or collection permissions.")
        return

    print("Saved context tables:")
    for path in outputs:
        print(f"- {path}")


if __name__ == "__main__":
    main()
