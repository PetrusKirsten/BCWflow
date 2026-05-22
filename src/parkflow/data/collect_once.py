from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

from parkflow.config import PARK_ID, PROCESSED_DIR
from parkflow.data.operating_hours import OperatingHoursPolicy, is_within_nominal_operating_hours, now_local
from parkflow.data.queue_times import fetch_live_queue_times, flatten_queue_times, save_raw_queue_snapshot


def should_collect_now(
    *,
    force_outside_hours: bool = False,
    policy: OperatingHoursPolicy | None = None,
) -> bool:
    """Return whether a cloud/job execution should collect a snapshot now.

    Scheduled jobs should exit successfully when they run outside the nominal
    operating window. That keeps cron-like systems healthy while avoiding
    after-hours zero-minute records being interpreted as true queue pressure.
    """

    if force_outside_hours:
        return True
    return is_within_nominal_operating_hours(now_local(policy), policy=policy)


def rebuild_processed_dataset() -> Path:
    """Rebuild the processed queue-time dataset after a successful collection."""

    from parkflow.data.build_queue_times_dataset import build_queue_times_dataset

    df = build_queue_times_dataset()
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    out_path = PROCESSED_DIR / "queue_times.csv"
    df.to_csv(out_path, index=False)
    return out_path


def collect_queue_times_once(
    *,
    park_id: int = PARK_ID,
    timeout: int = 30,
    force_outside_hours: bool = False,
    rebuild_processed: bool = False,
) -> Path | None:
    """Collect exactly one Queue-Times snapshot and exit.

    This is the preferred entry point for cloud schedulers such as GitHub
    Actions, Railway Cron, Render Cron or system cron. Long-running loops are
    useful for local development, but cloud jobs should collect once and exit.

    Returns the raw snapshot path when a snapshot is collected. Returns None
    when the job intentionally skips collection outside nominal operating hours.
    """

    policy = OperatingHoursPolicy()
    local_now = now_local(policy)

    if not should_collect_now(force_outside_hours=force_outside_hours, policy=policy):
        print(
            f"[{local_now:%Y-%m-%d %H:%M:%S %Z}] outside nominal operating hours "
            f"({policy.label}). Skipping snapshot."
        )
        return None

    started_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"[{started_at}] collecting one Queue-Times snapshot for park_id={park_id}...")

    payload = fetch_live_queue_times(park_id=park_id, timeout=timeout)
    out_path = save_raw_queue_snapshot(payload, park_id=park_id)
    df = flatten_queue_times(payload, park_id=park_id)

    finished_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"[{finished_at}] saved raw queue snapshot: {out_path}")
    print(f"[{finished_at}] rides collected: {len(df)}")

    if rebuild_processed:
        processed_path = rebuild_processed_dataset()
        print(f"[{finished_at}] rebuilt processed queue dataset: {processed_path}")

    return out_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Collect exactly one Queue-Times snapshot and exit. Suitable for cloud schedulers."
    )
    parser.add_argument("--park-id", type=int, default=PARK_ID, help="Queue-Times park ID.")
    parser.add_argument("--timeout", type=int, default=30, help="HTTP timeout in seconds.")
    parser.add_argument(
        "--force-outside-hours",
        "--collect-outside-hours",
        dest="force_outside_hours",
        action="store_true",
        help="Collect even when local park time is outside the nominal operating window.",
    )
    parser.add_argument(
        "--rebuild-processed",
        action="store_true",
        help="Rebuild data/processed/queue_times.csv after collecting the snapshot.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    collect_queue_times_once(
        park_id=args.park_id,
        timeout=args.timeout,
        force_outside_hours=args.force_outside_hours,
        rebuild_processed=args.rebuild_processed,
    )


if __name__ == "__main__":
    main()
