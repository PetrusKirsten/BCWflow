from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time
from zoneinfo import ZoneInfo

import pandas as pd

from parkflow.config import NOMINAL_CLOSE_HOUR, NOMINAL_OPEN_HOUR, PARK_TIMEZONE


@dataclass(frozen=True)
class OperatingHoursPolicy:
    """Conservative operating-hours policy used for collection and analysis.

    The public pages can expose specific hours for a given day, but the first
    project version uses a nominal window as a safety filter. Raw records are
    preserved; queue-pressure charts exclude records collected outside this
    window by default.
    """

    timezone: str = PARK_TIMEZONE
    open_hour: int = NOMINAL_OPEN_HOUR
    close_hour: int = NOMINAL_CLOSE_HOUR

    @property
    def label(self) -> str:
        return f"{self.open_hour:02d}:00-{self.close_hour:02d}:00"


def now_local(policy: OperatingHoursPolicy | None = None) -> datetime:
    """Return the current local datetime for the park."""

    policy = policy or OperatingHoursPolicy()
    return datetime.now(tz=ZoneInfo(policy.timezone))


def is_within_nominal_operating_hours(
    value: datetime | pd.Timestamp | None = None,
    policy: OperatingHoursPolicy | None = None,
) -> bool:
    """Return True when a timestamp is inside the nominal park operating window.

    The close hour is treated as exclusive. For a 10:00-20:00 window, 19:59 is
    inside and 20:00 is outside.
    """

    policy = policy or OperatingHoursPolicy()
    if value is None:
        value = now_local(policy)

    ts = pd.Timestamp(value)
    if ts.tzinfo is None:
        ts = ts.tz_localize(policy.timezone)
    else:
        ts = ts.tz_convert(policy.timezone)

    local_time = ts.time()
    return time(policy.open_hour, 0) <= local_time < time(policy.close_hour, 0)


def add_operating_hour_columns(
    df: pd.DataFrame,
    timestamp_col: str = "ingested_at_utc",
    policy: OperatingHoursPolicy | None = None,
) -> pd.DataFrame:
    """Add collection-hour columns used to separate in-hours and off-hours data."""

    if df.empty:
        return df.copy()

    policy = policy or OperatingHoursPolicy()
    out = df.copy()

    if timestamp_col not in out.columns:
        out["collection_timestamp_local"] = pd.NaT
        out["collection_hour_local"] = pd.NA
        out["is_within_nominal_operating_hours"] = pd.NA
        out["operating_hour_status"] = "unknown_collection_time"
        return out

    timestamps = pd.to_datetime(out[timestamp_col], utc=True, errors="coerce")
    local = timestamps.dt.tz_convert(policy.timezone)
    out["collection_timestamp_local"] = local
    out["collection_hour_local"] = local.dt.hour
    out["nominal_operating_hours"] = policy.label
    out["is_within_nominal_operating_hours"] = (
        (local.dt.hour >= policy.open_hour) & (local.dt.hour < policy.close_hour)
    ).where(local.notna(), pd.NA)
    out["operating_hour_status"] = out["is_within_nominal_operating_hours"].map(
        {True: "within_nominal_operating_hours", False: "outside_nominal_operating_hours"}
    )
    out.loc[out["is_within_nominal_operating_hours"].isna(), "operating_hour_status"] = "unknown_collection_time"
    return out
