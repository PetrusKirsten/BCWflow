from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from parkflow.config import PARK_ID, PROCESSED_DIR
from parkflow.data.queue_times import flatten_queue_times, save_raw_queue_snapshot


@dataclass(frozen=True)
class QueueSnapshotSaveResult:
    """Metadata returned after saving a queue-time snapshot."""

    raw_snapshot_path: Path
    rows_collected: int
    processed_dataset_path: Path | None = None


class LocalQueueSnapshotStorage:
    """Persist queue-time snapshots using the current local file layout.

    The collector should depend on this storage layer instead of calling the
    file-writing functions directly. This keeps the project ready for future
    storage backends without changing the collector interface.
    """

    def save_queue_snapshot(
        self,
        payload: dict[str, Any],
        *,
        park_id: int = PARK_ID,
        rebuild_processed: bool = False,
    ) -> QueueSnapshotSaveResult:
        raw_snapshot_path = save_raw_queue_snapshot(payload, park_id=park_id)
        df = flatten_queue_times(payload, park_id=park_id)
        processed_dataset_path = None

        if rebuild_processed:
            processed_dataset_path = self.rebuild_processed_dataset()

        return QueueSnapshotSaveResult(
            raw_snapshot_path=raw_snapshot_path,
            rows_collected=len(df),
            processed_dataset_path=processed_dataset_path,
        )

    def rebuild_processed_dataset(self) -> Path:
        """Rebuild the processed queue-time dataset from local raw snapshots."""

        from parkflow.data.build_queue_times_dataset import build_queue_times_dataset

        df = build_queue_times_dataset()
        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        out_path = PROCESSED_DIR / "queue_times.csv"
        df.to_csv(out_path, index=False)
        return out_path
