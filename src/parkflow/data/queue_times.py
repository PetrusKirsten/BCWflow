from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import requests

from parkflow.config import PARK_ID, QUEUE_TIMES_BASE_URL, RAW_DIR


def fetch_live_queue_times(park_id: int = PARK_ID, timeout: int = 30) -> dict[str, Any]:
    """Fetch current queue times for a park from Queue-Times public API."""
    url = f"{QUEUE_TIMES_BASE_URL}/parks/{park_id}/queue_times.json"
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    return response.json()


def save_raw_queue_snapshot(payload: dict[str, Any], park_id: int = PARK_ID) -> Path:
    """Save a raw Queue-Times JSON snapshot with an ingestion timestamp."""
    now_utc = datetime.now(timezone.utc)
    out_dir = RAW_DIR / "queue_times" / f"park_id={park_id}" / now_utc.strftime("%Y-%m-%d")
    out_dir.mkdir(parents=True, exist_ok=True)

    out_path = out_dir / f"queue_times_{now_utc.strftime('%Y%m%dT%H%M%SZ')}.json"
    record = {
        "ingested_at_utc": now_utc.isoformat(),
        "park_id": park_id,
        "source": "queue-times.com",
        "payload": payload,
    }
    out_path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path


def flatten_queue_times(payload: dict[str, Any], park_id: int = PARK_ID) -> pd.DataFrame:
    """Flatten Queue-Times API payload into one row per ride."""
    rows: list[dict[str, Any]] = []

    for land in payload.get("lands", []):
        land_id = land.get("id")
        land_name = land.get("name")
        for ride in land.get("rides", []):
            rows.append(
                {
                    "park_id": park_id,
                    "land_id": land_id,
                    "land_name": land_name,
                    "ride_id": ride.get("id"),
                    "ride_name": ride.get("name"),
                    "is_open": ride.get("is_open"),
                    "wait_time": ride.get("wait_time"),
                    "last_updated_utc": ride.get("last_updated"),
                }
            )

    # Some parks may return rides outside lands.
    for ride in payload.get("rides", []):
        rows.append(
            {
                "park_id": park_id,
                "land_id": None,
                "land_name": None,
                "ride_id": ride.get("id"),
                "ride_name": ride.get("name"),
                "is_open": ride.get("is_open"),
                "wait_time": ride.get("wait_time"),
                "last_updated_utc": ride.get("last_updated"),
            }
        )

    df = pd.DataFrame(rows)
    if not df.empty:
        df["last_updated_utc"] = pd.to_datetime(df["last_updated_utc"], utc=True, errors="coerce")
    return df


def load_raw_snapshot(path: str | Path) -> dict[str, Any]:
    """Load a raw snapshot saved by save_raw_queue_snapshot."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return data


def flatten_raw_snapshot(path: str | Path) -> pd.DataFrame:
    """Flatten a raw snapshot file and preserve ingestion metadata."""
    record = load_raw_snapshot(path)
    df = flatten_queue_times(record["payload"], park_id=record["park_id"])
    if df.empty:
        return df
    df["ingested_at_utc"] = pd.to_datetime(record["ingested_at_utc"], utc=True)
    df["source"] = record.get("source", "queue-times.com")
    df["raw_file"] = str(path)
    return df
