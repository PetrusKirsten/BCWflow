from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone

from parkflow.config import PARK_ID


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
