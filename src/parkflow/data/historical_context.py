from __future__ import annotations

import argparse
import re
import time
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta
from io import StringIO
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

    This function is intentionally used only for low-frequency context collection.
    It returns HTML because the historical/context pages are webpages, not JSON APIs.
    The HTML is parsed and saved; it should not be printed to the terminal.
    """

    url = f"{QUEUE_TIMES_BASE_URL}{path}"
    response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=timeout)
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        raise RuntimeError(f"HTTP {response.status_code} while fetching {url}") from exc

    content_type = response.headers.get("content-type", "")
    if "html" not in content_type.lower() and content_type:
        print(f"Warning: unexpected content type for {url}: {content_type}")

    return response.text


def extract_html_tables(html: str) -> list[pd.DataFrame]:
    """Extract all HTML tables from a page using pandas.read_html.

    Pandas 2.x warns when literal HTML is passed directly. Wrapping in StringIO keeps
    the terminal clean and avoids accidentally echoing large HTML payloads.
    """

    try:
        return pd.read_html(StringIO(html))
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
    tables = extract_html_tables(html)
    for i, table in enumerate(tables, start=1):
        out_path = processed_dir / f"{_slugify(page_name)}_table_{i:02d}.csv"
        table.to_csv(out_path, index=False)
        paths.append(out_path)

    if paths:
        print(f"Saved {len(paths)} parsed table(s) for {page_name}.")
    else:
        print(
            f"No HTML tables found for {page_name}. "
            f"Raw page saved for inspection at: {raw_path}"
        )
    return paths


def collect_queue_times_stats(park_id: int = PARK_ID, year: int | None = None) -> list[Path]:
    """Collect public aggregate statistics tables for the park.

    When year is provided, Queue-Times exposes a year-specific stats page, e.g.
    /parks/319/stats/2026. These tables are historical aggregate context, not
    row-level wait-time observations.
    """

    suffix = f"/{year}" if year else ""
    label = f"queue_times_stats_{year}" if year else "queue_times_stats_all_time"
    print(f"Fetching aggregate stats page: {label}")
    html = fetch_public_html(f"/parks/{park_id}/stats{suffix}")
    return save_public_context_tables(label, html)


def collect_attendance_history(park_id: int = PARK_ID) -> list[Path]:
    """Collect public yearly attendance table for the park."""

    print("Fetching attendance history page.")
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
    sleep_seconds: float = 1.0,
    save_raw_html: bool = False,
) -> Path:
    """Collect day-level public crowd-calendar records for a date range.

    This produces historical day-level context: crowd level and operating hours.
    It is intentionally not treated as row-level queue-time history.
    """

    today = date.today()
    start_date = start_date or date(today.year, 1, 1)
    end_date = end_date or today

    if end_date < start_date:
        raise ValueError("end_date must be greater than or equal to start_date")

    raw_dir = RAW_DIR / "historical_context" / "crowd_calendar"
    processed_dir = PROCESSED_DIR / "historical_context"
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    print(
        "Fetching day-level crowd calendar "
        f"from {start_date.isoformat()} to {end_date.isoformat()} "
        f"with {sleep_seconds:.2f}s delay between requests."
    )

    records: list[CalendarDayRecord] = []
    failures: list[tuple[str, str]] = []
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
            failures.append((day.isoformat(), str(exc)))
            print(f"Failed calendar day {day.isoformat()}: {exc}")
        time.sleep(max(sleep_seconds, 0))

    df = pd.DataFrame([asdict(record) for record in records])
    out_path = processed_dir / f"crowd_calendar_{start_date.isoformat()}_{end_date.isoformat()}.csv"
    df.to_csv(out_path, index=False)

    if failures:
        failures_path = processed_dir / f"crowd_calendar_failures_{start_date.isoformat()}_{end_date.isoformat()}.csv"
        pd.DataFrame(failures, columns=["date", "error"]).to_csv(failures_path, index=False)
        print(f"Saved {len(failures)} calendar failure(s) at: {failures_path}")

    print(f"Saved {len(df)} calendar record(s) at: {out_path}")
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
    parser.add_argument(
        "--calendar-only",
        action="store_true",
        help="Collect only the day-level calendar. Implies --collect-calendar and skips stats/attendance.",
    )
    parser.add_argument("--skip-stats", action="store_true", help="Skip all-time and yearly stats pages.")
    parser.add_argument("--skip-attendance", action="store_true", help="Skip yearly attendance history page.")
    parser.add_argument("--start-date", type=str, default=None, help="Calendar start date: YYYY-MM-DD.")
    parser.add_argument("--end-date", type=str, default=None, help="Calendar end date: YYYY-MM-DD.")
    parser.add_argument(
        "--sleep-seconds",
        type=float,
        default=1.0,
        help="Polite delay between calendar requests. Default is intentionally conservative.",
    )
    parser.add_argument(
        "--save-raw-calendar-html",
        action="store_true",
        help="Also save each daily calendar HTML page. Usually unnecessary.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.calendar_only:
        args.collect_calendar = True
        args.skip_stats = True
        args.skip_attendance = True

    outputs: list[Path] = []

    if not args.skip_stats:
        outputs.extend(collect_queue_times_stats(park_id=args.park_id))
        outputs.extend(collect_queue_times_stats(park_id=args.park_id, year=args.year))

    if not args.skip_attendance:
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
        print("No files saved. Check selected options or collection permissions.")
        return

    print("\nSaved historical/context files:")
    for path in outputs:
        print(f"- {path}")


if __name__ == "__main__":
    main()
