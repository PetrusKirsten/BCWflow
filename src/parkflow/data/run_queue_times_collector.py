from __future__ import annotations

import argparse
import time
from datetime import datetime, timezone

from parkflow.config import PARK_ID, PROCESSED_DIR
from parkflow.data.build_queue_times_dataset import build_queue_times_dataset
from parkflow.data.queue_times import fetch_live_queue_times, flatten_queue_times, save_raw_queue_snapshot


def collect_once(park_id: int, timeout: int) -> int:
    """Collect and save one queue-time snapshot. Returns number of rides found."""

    payload = fetch_live_queue_times(park_id=park_id, timeout=timeout)
    out_path = save_raw_queue_snapshot(payload, park_id=park_id)
    df = flatten_queue_times(payload, park_id=park_id)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"[{now}] saved snapshot: {out_path}")
    print(f"[{now}] rides collected: {len(df)}")
    return len(df)


def rebuild_processed_dataset() -> None:
    df = build_queue_times_dataset()
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    out_path = PROCESSED_DIR / "queue_times.csv"
    df.to_csv(out_path, index=False)
    print(f"Updated processed queue dataset: {out_path} ({len(df)} rows)")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Collect Queue-Times snapshots repeatedly to build a local historical dataset."
    )
    parser.add_argument("--park-id", type=int, default=PARK_ID, help="Queue-Times park ID.")
    parser.add_argument(
        "--interval-minutes",
        type=float,
        default=30,
        help="Minutes between snapshots. Use a respectful interval; 15–30 min is recommended.",
    )
    parser.add_argument(
        "--max-runs",
        type=int,
        default=None,
        help="Stop after N successful attempts. Omit to keep running until Ctrl+C.",
    )
    parser.add_argument("--timeout", type=int, default=30, help="HTTP timeout in seconds.")
    parser.add_argument(
        "--rebuild-after-each-run",
        action="store_true",
        help="Rebuild data/processed/queue_times.csv after each successful snapshot.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    interval_seconds = max(args.interval_minutes * 60, 60)
    runs = 0

    print("Starting ParkFlow queue-time collector")
    print(f"Park ID: {args.park_id}")
    print(f"Interval: {args.interval_minutes} minutes")
    print("Press Ctrl+C to stop.\n")

    try:
        while True:
            try:
                collect_once(park_id=args.park_id, timeout=args.timeout)
                runs += 1
                if args.rebuild_after_each_run:
                    rebuild_processed_dataset()
            except Exception as exc:  # noqa: BLE001 - collector should keep running after transient failures
                now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
                print(f"[{now}] collection failed: {exc!r}")

            if args.max_runs is not None and runs >= args.max_runs:
                print(f"Reached max runs ({args.max_runs}). Stopping collector.")
                break

            next_run_seconds = int(interval_seconds)
            print(f"Sleeping for {next_run_seconds} seconds...\n")
            time.sleep(interval_seconds)
    except KeyboardInterrupt:
        print("\nCollector stopped by user.")
        if not args.rebuild_after_each_run:
            print("Tip: rebuild the processed dataset with:")
            print("python -m parkflow.data.build_queue_times_dataset")


if __name__ == "__main__":
    main()
