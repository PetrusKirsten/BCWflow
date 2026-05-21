from __future__ import annotations

import argparse
import re
import time
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup

from parkflow.config import PARK_ID, PROCESSED_DIR, QUEUE_TIMES_BASE_URL, RAW_DIR

USER_AGENT = "ParkFlowAnalytics/0.2 (+portfolio research; respectful public data use)"


@dataclass(frozen=True)
class CalendarDayRecord:
    """One public crowd-calendar day from Queue-Times."""

    date: str
    park_id: int
    source_url: str
    crowd_level_pct: int | None
    crowd_label: str | None
    operating_hours: str | None
    open_time: str | None
    close_time: str | None
    fetched_at_utc: str


def _slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_") or "table"


def _date_range(start: date, end: date):
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def fetch_public_html(path: str, timeout: int = 30) -> str:
    """Fetch a public Queue-Times HTML page for aggregated context.

    Use only for low-frequency, transparent collection of public aggregate pages.
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


def collect_queue_times_stats(park_id: int = PARK_ID, year: int | None = None) -> list[Path]:
    """Collect public aggregate statistics tables for the park.

    When year is provided, Queue-Times exposes a year-specific stats page, e.g.
    /parks/319/stats/2026. These tables are historical aggregate context, not
    row-level wait-time observations.
    """

    suffix = f"/{year}" if year else ""
    html = fetch_public_html(f"/parks/{park_id}/stats{suffix}")
    name = f"queue_times_stats_{year}" if year else "queue_times_stats_all_time"
    return save_public_context_tables(name, html)


def collect_attendance_history(park_id: int = PARK_ID) -> list[Path]:
    """Collect public yearly attendance table for the park."""

    html = fetch_public_html(f"/parks/{park_id}/attendances")
    return save_public_context_tables("attendance_history", html)


def parse_crowd_calendar_day(html: str, day: date, park_id: int, source_url: str) -> CalendarDayRecord:
    """Parse one Queue-Times crowd-calendar day page into a compact record."""

    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True)

    crowd_level_match = re.search(r"Crowd level\s+(\d+)%", text, flags=re.IGNORECASE)
    crowd_level_pct = int(crowd_level_match.group(1)) if crowd_level_match else None

    label = None
    for candidate in ["Empty", "Quiet", "Busy", "Packed"]:
        if re.search(rf"Crowd level\s+{candidate}\b", text, flags=re.IGNORECASE):
            label = candidate
            break

    hours_match = re.search(r"\b(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})\b", text)
    open_time = hours_match.group(1) if hours_match else None
    close_time = hours_match.group(2) if hours_match else None
    operating_hours = f"{open_time}-{close_time}" if open_time and close_time else None

    return CalendarDayRecord(
        date=day.isoformat(),
        park_id=park_id,
        source_url=source_url,
        crowd_level_pct=crowd_level_pct,
        crowd_label=label,
        operating_hours=operating_hours,
        open_time=open_time,
        close_time=close_time,
        fetched_at_utc=datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
    )


def collect_crowd_calendar(
    park_id: int = PARK_ID,
    start_date: date | None = None,
    end_date: date | None = None,
    sleep_seconds: float = 0.25,
    save_raw_html: bool = False,
) -> Path:
    """Collect day-level public crowd-calendar records for a date range.

    This produces historical day-level context: crowd level and operating hours.
    It is intentionally not treated as row-level queue-time history.
    """

    today = date.today()
    start_date = start_date or date(today.year, 1, 1)
    end_date = end_date or today

    raw_dir = RAW_DIR / "historical_context" / "crowd_calendar"
    processed_dir = PROCESSED_DIR / "historical_context"
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    records: list[CalendarDayRecord] = []
    for day in _date_range(start_date, end_date):
        path = f"/parks/{park_id}/calendar/{day:%Y/%m/%d}"
        url = f"{QUEUE_TIMES_BASE_URL}{path}"
        try:
            html = fetch_public_html(path)
            if save_raw_html:
                raw_path = raw_dir / f"{day.isoformat()}.html"
                raw_path.write_text(html, encoding="utf-8")
            records.append(parse_crowd_calendar_day(html, day=day, park_id=park_id, source_url=url))
            print(f"Collected calendar day {day.isoformat()}")
        except Exception as exc:  # noqa: BLE001 - keep date-range collection resilient
            print(f"Failed calendar day {day.isoformat()}: {exc!r}")
        time.sleep(max(sleep_seconds, 0))

    df = pd.DataFrame([asdict(record) for record in records])
    out_path = processed_dir / f"crowd_calendar_{start_date.isoformat()}_{end_date.isoformat()}.csv"
    df.to_csv(out_path, index=False)
    return out_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect public historical context for ParkFlow.")
    parser.add_argument("--park-id", type=int, default=PARK_ID)
    parser.add_argument("--year", type=int, default=date.today().year)
    parser.add_argument(
        "--collect-calendar",
        action="store_true",
        help="Collect day-level crowd-calendar records for the selected date range.",
    )
    parser.add_argument("--start-date", type=str, default=None, help="Calendar start date: YYYY-MM-DD.")
    parser.add_argument("--end-date", type=str, default=None, help="Calendar end date: YYYY-MM-DD.")
    parser.add_argument("--sleep-seconds", type=float, default=0.25, help="Polite delay between calendar requests.")
    parser.add_argument("--save-raw-calendar-html", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    outputs: list[Path] = []

    outputs.extend(collect_queue_times_stats(park_id=args.park_id))
    outputs.extend(collect_queue_times_stats(park_id=args.park_id, year=args.year))
    outputs.extend(collect_attendance_history(park_id=args.park_id))

    if args.collect_calendar:
        start = datetime.strptime(args.start_date, "%Y-%m-%d").date() if args.start_date else date(args.year, 1, 1)
        end = datetime.strptime(args.end_date, "%Y-%m-%d").date() if args.end_date else date.today()
        outputs.append(
            collect_crowd_calendar(
                park_id=args.park_id,
                start_date=start,
                end_date=end,
                sleep_seconds=args.sleep_seconds,
                save_raw_html=args.save_raw_calendar_html,
            )
        )

    if not outputs:
        print("No files saved. Check page structure or collection permissions.")
        return

    print("Saved historical/context files:")
    for path in outputs:
        print(f"- {path}")


if __name__ == "__main__":
    main()
