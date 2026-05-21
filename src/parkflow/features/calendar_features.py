from __future__ import annotations

import pandas as pd


def classify_time_period(hour: int | float) -> str:
    if pd.isna(hour):
        return "unknown"
    hour = int(hour)
    if 5 <= hour < 12:
        return "morning"
    if 12 <= hour < 18:
        return "afternoon"
    if 18 <= hour < 22:
        return "evening"
    return "night"


def add_time_features(
    df: pd.DataFrame,
    timestamp_col: str,
    timezone: str = "America/Sao_Paulo",
) -> pd.DataFrame:
    """Add local calendar/time features from a timestamp column."""
    out = df.copy()
    local_col = timestamp_col.replace("_utc", "") + "_local"

    ts = pd.to_datetime(out[timestamp_col], utc=True, errors="coerce")
    out[local_col] = ts.dt.tz_convert(timezone)

    out["date"] = out[local_col].dt.date
    out["hour"] = out[local_col].dt.hour
    out["day_of_week"] = out[local_col].dt.day_name()
    out["day_of_week_num"] = out[local_col].dt.dayofweek
    out["month"] = out[local_col].dt.month
    out["year"] = out[local_col].dt.year
    out["is_weekend"] = out["day_of_week_num"].isin([5, 6])
    out["time_period"] = out["hour"].apply(classify_time_period)
    return out
