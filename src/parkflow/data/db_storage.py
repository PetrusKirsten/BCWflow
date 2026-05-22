from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from parkflow.config import PARK_ID
from parkflow.data.queue_times import flatten_queue_times
from parkflow.data.storage import QueueSnapshotSaveResult


def get_database_url() -> str | None:
    """Return the configured database URL, if available."""

    return os.getenv("DATABASE_URL")


def normalize_database_url(database_url: str) -> str:
    """Normalize database URLs for the database driver."""

    if database_url.startswith("postgres://"):
        return "postgresql://" + database_url.removeprefix("postgres://")
    return database_url


def build_snapshot_id(*, park_id: int, ingested_at_utc: datetime) -> str:
    """Build a deterministic snapshot id from park id and ingestion timestamp."""

    timestamp = ingested_at_utc.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"park-{park_id}-{timestamp}"


@dataclass(frozen=True)
class DatabaseConfig:
    """Database connection settings."""

    database_url: str

    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        database_url = get_database_url()
        if not database_url:
            raise ValueError("DATABASE_URL is required for database storage")
        return cls(database_url=normalize_database_url(database_url))


class DatabaseQueueSnapshotStorage:
    """Persist queue-time snapshots to a PostgreSQL-compatible database."""

    def __init__(self, config: DatabaseConfig | None = None) -> None:
        self.config = config or DatabaseConfig.from_env()

    def ensure_schema(self, conn: Any) -> None:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS queue_time_snapshots (
                    snapshot_id TEXT PRIMARY KEY,
                    park_id INTEGER NOT NULL,
                    source TEXT NOT NULL,
                    ingested_at_utc TIMESTAMPTZ NOT NULL,
                    raw_payload JSONB NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS queue_time_observations (
                    snapshot_id TEXT NOT NULL REFERENCES queue_time_snapshots(snapshot_id) ON DELETE CASCADE,
                    park_id INTEGER NOT NULL,
                    land_id INTEGER,
                    land_name TEXT,
                    ride_id INTEGER,
                    ride_name TEXT,
                    is_open BOOLEAN,
                    wait_time INTEGER,
                    last_updated_utc TIMESTAMPTZ,
                    source TEXT NOT NULL,
                    ingested_at_utc TIMESTAMPTZ NOT NULL,
                    PRIMARY KEY (snapshot_id, ride_id)
                )
                """
            )
            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_queue_time_observations_ride_time
                ON queue_time_observations (ride_id, ingested_at_utc)
                """
            )

    def save_queue_snapshot(
        self,
        payload: dict[str, Any],
        *,
        park_id: int = PARK_ID,
        rebuild_processed: bool = False,
    ) -> QueueSnapshotSaveResult:
        import psycopg

        ingested_at_utc = datetime.now(timezone.utc)
        snapshot_id = build_snapshot_id(park_id=park_id, ingested_at_utc=ingested_at_utc)
        df = flatten_queue_times(payload, park_id=park_id)

        with psycopg.connect(self.config.database_url) as conn:
            self.ensure_schema(conn)
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO queue_time_snapshots (
                        snapshot_id, park_id, source, ingested_at_utc, raw_payload
                    )
                    VALUES (%s, %s, %s, %s, %s::jsonb)
                    ON CONFLICT (snapshot_id) DO NOTHING
                    """,
                    (
                        snapshot_id,
                        park_id,
                        "queue-times.com",
                        ingested_at_utc,
                        json.dumps(payload, ensure_ascii=False),
                    ),
                )

                for row in df.to_dict(orient="records"):
                    last_updated = row.get("last_updated_utc")
                    if hasattr(last_updated, "to_pydatetime"):
                        last_updated = last_updated.to_pydatetime()

                    cur.execute(
                        """
                        INSERT INTO queue_time_observations (
                            snapshot_id, park_id, land_id, land_name, ride_id, ride_name,
                            is_open, wait_time, last_updated_utc, source, ingested_at_utc
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (snapshot_id, ride_id) DO NOTHING
                        """,
                        (
                            snapshot_id,
                            row.get("park_id"),
                            row.get("land_id"),
                            row.get("land_name"),
                            row.get("ride_id"),
                            row.get("ride_name"),
                            row.get("is_open"),
                            row.get("wait_time"),
                            last_updated,
                            "queue-times.com",
                            ingested_at_utc,
                        ),
                    )
            conn.commit()

        return QueueSnapshotSaveResult(
            raw_snapshot_path=f"db://queue_time_snapshots/{snapshot_id}",
            rows_collected=len(df),
            processed_dataset_path=None,
        )
