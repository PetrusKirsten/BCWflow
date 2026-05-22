from __future__ import annotations

from datetime import datetime, timezone

from parkflow.data.db_storage import build_snapshot_id, normalize_database_url


def test_normalize_database_url_accepts_postgresql_scheme():
    url = "postgresql://user:password@example.com:5432/database"

    assert normalize_database_url(url) == url


def test_normalize_database_url_converts_legacy_postgres_scheme():
    url = "postgres://user:password@example.com:5432/database"

    assert normalize_database_url(url) == "postgresql://user:password@example.com:5432/database"


def test_build_snapshot_id_is_deterministic():
    ingested_at = datetime(2026, 5, 22, 15, 30, 45, tzinfo=timezone.utc)

    assert build_snapshot_id(park_id=319, ingested_at_utc=ingested_at) == "park-319-20260522T153045Z"
