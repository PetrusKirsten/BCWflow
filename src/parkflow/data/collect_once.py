from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

from parkflow.config import PARK_ID
from parkflow.data.db_storage import DatabaseQueueSnapshotStorage, get_database_url
from parkflow.data.operating_hours import OperatingHoursPolicy, is_within_nominal_operating_hours, now_local
from parkflow.data.queue_times import fetch_live_queue_times
from parkflow.data.storage import LocalQueueSnapshotStorage


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


def build_storage(storage_backend: str):
    """Build the requested storage backend."""

    if storage_backend == "local":
        return LocalQueueSnapshotStorage()
    if storage_backend == "database":
        return DatabaseQueueSnapshotStorage()
    if storage_backend == "auto":
        if get_database_url():
            return DatabaseQueueSnapshotStorage()
        return LocalQueueSnapshotStorage()
    raise ValueError(f"Unsupported storage backend: {storage_backend}")


def collect_queue_times_once(
    *,
    park_id: int = PARK_ID,
    timeout: int = 30,
    force_outside_hours: bool = False,
    rebuild_processed: bool = False,
    storage_backend: str = "auto",
) -> Path | str | None:
    """Collect exactly one Queue-Times snapshot and exit.

    This is the preferred entry point for cloud schedulers such as GitHub
    Actions, Railway Cron, Render Cron or system cron. Long-running loops are
    useful for local development, but cloud jobs should collect once and exit.

    Returns the saved snapshot location when a snapshot is collected. Returns
    None when the job intentionally skips collection outside nominal operating
    hours.
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
    storage = build_storage(storage_backend)
    result = storage.save_queue_snapshot(
        payload,
        park_id=park_id,
        rebuild_processed=rebuild_processed,
    )

    finished_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"[{finished_at}] saved queue snapshot: {result.raw_snapshot_path}")
    print(f"[{finished_at}] rides collected: {result.rows_collected}")

    if result.processed_dataset_path is not None:
        print(f"[{finished_at}] rebuilt processed queue dataset: {result.processed_dataset_path}")

    return result.raw_snapshot_path


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
    parser.add_argument(
        "--storage-backend",
        choices=["auto", "local", "database"],
        default="auto",
        help="Where to persist the snapshot. 'auto' uses DATABASE_URL when available.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    collect_queue_times_once(
        park_id=args.park_id,
        timeout=args.timeout,
        force_outside_hours=args.force_outside_hours,
        rebuild_processed=args.rebuild_processed,
        storage_backend=args.storage_backend,
    )


if __name__ == "__main__":
    main()
