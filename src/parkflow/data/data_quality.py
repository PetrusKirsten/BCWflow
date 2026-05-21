from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from parkflow.config import PARK_TIMEZONE, PROCESSED_DIR


@dataclass(frozen=True)
class DataPaths:
    """Default processed data paths used by audit scripts and dashboard pages."""

    queue_times: Path = PROCESSED_DIR / "queue_times.csv"
    modeling_dataset: Path = PROCESSED_DIR / "modeling_dataset.csv"


def _read_existing_csv(path: Path, date_columns: list[str] | None = None) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, parse_dates=date_columns or [])


def load_best_available_dataset(paths: DataPaths | None = None) -> tuple[pd.DataFrame, Path | None]:
    """Load modeling_dataset.csv when available, otherwise queue_times.csv.

    Returns the dataframe and the path used. If neither file exists, returns an empty
    dataframe and None.
    """

    paths = paths or DataPaths()
    parse_dates = ["last_updated_utc", "ingested_at_utc"]

    if paths.modeling_dataset.exists():
        return _read_existing_csv(paths.modeling_dataset, date_columns=parse_dates), paths.modeling_dataset
    if paths.queue_times.exists():
        return _read_existing_csv(paths.queue_times, date_columns=parse_dates), paths.queue_times
    return pd.DataFrame(), None


def add_audit_time_columns(df: pd.DataFrame, timezone: str = PARK_TIMEZONE) -> pd.DataFrame:
    """Add normalized local timestamp columns used in coverage summaries."""

    if df.empty:
        return df.copy()

    result = df.copy()
    for column in ["last_updated_utc", "ingested_at_utc"]:
        if column in result.columns:
            result[column] = pd.to_datetime(result[column], utc=True, errors="coerce")
            local_column = column.replace("_utc", "_local")
            result[local_column] = result[column].dt.tz_convert(timezone)

    timestamp_col = "ingested_at_local" if "ingested_at_local" in result.columns else "last_updated_local"
    if timestamp_col in result.columns:
        result["audit_date_local"] = result[timestamp_col].dt.date
        result["audit_hour_local"] = result[timestamp_col].dt.hour

    return result


def _format_datetime(value: pd.Timestamp | None) -> str:
    if value is None or pd.isna(value):
        return "—"
    return pd.Timestamp(value).strftime("%Y-%m-%d %H:%M")


def build_coverage_summary(df: pd.DataFrame) -> dict[str, object]:
    """Build high-level coverage metrics for the processed queue dataset."""

    if df.empty:
        return {
            "rows": 0,
            "snapshots": 0,
            "attractions": 0,
            "first_snapshot_local": "—",
            "last_snapshot_local": "—",
            "days_covered": 0,
            "average_wait_min": None,
            "p90_wait_min": None,
            "open_rate": None,
            "positive_wait_rate": None,
        }

    audited = add_audit_time_columns(df)
    snapshot_col = "ingested_at_utc" if "ingested_at_utc" in audited.columns else "last_updated_utc"
    snapshot_local_col = "ingested_at_local" if "ingested_at_local" in audited.columns else "last_updated_local"

    wait = pd.to_numeric(audited.get("wait_time", pd.Series(dtype="float64")), errors="coerce")
    is_open = audited.get("is_open")
    if is_open is not None:
        open_rate = is_open.astype(str).str.lower().isin(["true", "1", "yes"]).mean()
    else:
        open_rate = None

    return {
        "rows": int(len(audited)),
        "snapshots": int(audited[snapshot_col].nunique()) if snapshot_col in audited else 0,
        "attractions": int(audited["ride_name"].nunique()) if "ride_name" in audited else 0,
        "first_snapshot_local": _format_datetime(audited[snapshot_local_col].min())
        if snapshot_local_col in audited
        else "—",
        "last_snapshot_local": _format_datetime(audited[snapshot_local_col].max())
        if snapshot_local_col in audited
        else "—",
        "days_covered": int(audited["audit_date_local"].nunique())
        if "audit_date_local" in audited
        else 0,
        "average_wait_min": float(wait.mean()) if not wait.dropna().empty else None,
        "p90_wait_min": float(wait.quantile(0.90)) if not wait.dropna().empty else None,
        "open_rate": float(open_rate) if open_rate is not None else None,
        "positive_wait_rate": float((wait > 0).mean()) if len(wait) else None,
    }


def ride_coverage_report(df: pd.DataFrame) -> pd.DataFrame:
    """Return one row per attraction with coverage and wait-time diagnostics."""

    if df.empty or "ride_name" not in df.columns:
        return pd.DataFrame()

    audited = add_audit_time_columns(df)
    wait = pd.to_numeric(audited["wait_time"], errors="coerce") if "wait_time" in audited else pd.Series()
    audited = audited.assign(wait_time_numeric=wait)

    snapshot_col = "ingested_at_utc" if "ingested_at_utc" in audited.columns else "last_updated_utc"
    aggregations: dict[str, tuple[str, str]] = {
        "rows": ("ride_name", "size"),
        "avg_wait_min": ("wait_time_numeric", "mean"),
        "median_wait_min": ("wait_time_numeric", "median"),
        "p90_wait_min": ("wait_time_numeric", lambda s: s.quantile(0.90)),
        "max_wait_min": ("wait_time_numeric", "max"),
    }

    if snapshot_col in audited.columns:
        aggregations["snapshots"] = (snapshot_col, "nunique")
    if "is_open" in audited.columns:
        audited["is_open_bool"] = audited["is_open"].astype(str).str.lower().isin(["true", "1", "yes"])
        aggregations["open_rate"] = ("is_open_bool", "mean")
    if "audit_date_local" in audited.columns:
        aggregations["days_seen"] = ("audit_date_local", "nunique")

    report = audited.groupby("ride_name", as_index=False).agg(**aggregations)
    sort_cols = [col for col in ["p90_wait_min", "avg_wait_min", "rows"] if col in report.columns]
    return report.sort_values(sort_cols, ascending=False).reset_index(drop=True)


def hourly_coverage_report(df: pd.DataFrame) -> pd.DataFrame:
    """Summarize number of rows/snapshots by local date and hour."""

    if df.empty:
        return pd.DataFrame()

    audited = add_audit_time_columns(df)
    required = {"audit_date_local", "audit_hour_local"}
    if not required.issubset(audited.columns):
        return pd.DataFrame()

    snapshot_col = "ingested_at_utc" if "ingested_at_utc" in audited.columns else "last_updated_utc"
    aggregations: dict[str, tuple[str, str]] = {"rows": ("audit_hour_local", "size")}
    if snapshot_col in audited.columns:
        aggregations["snapshots"] = (snapshot_col, "nunique")
    if "ride_name" in audited.columns:
        aggregations["attractions"] = ("ride_name", "nunique")
    if "wait_time" in audited.columns:
        audited["wait_time_numeric"] = pd.to_numeric(audited["wait_time"], errors="coerce")
        aggregations["avg_wait_min"] = ("wait_time_numeric", "mean")

    return (
        audited.groupby(["audit_date_local", "audit_hour_local"], as_index=False)
        .agg(**aggregations)
        .sort_values(["audit_date_local", "audit_hour_local"])
        .reset_index(drop=True)
    )


def missingness_report(df: pd.DataFrame) -> pd.DataFrame:
    """Return missing-value diagnostics by column."""

    if df.empty:
        return pd.DataFrame(columns=["column", "missing_count", "missing_pct", "dtype"])

    missing = df.isna().sum().reset_index()
    missing.columns = ["column", "missing_count"]
    missing["missing_pct"] = missing["missing_count"] / len(df)
    missing["dtype"] = missing["column"].map(lambda col: str(df[col].dtype))
    return missing.sort_values(["missing_pct", "missing_count"], ascending=False).reset_index(drop=True)


def print_coverage_summary(df: pd.DataFrame) -> None:
    """CLI-friendly coverage summary."""

    summary = build_coverage_summary(df)
    print("ParkFlow data coverage summary")
    print("-" * 34)
    for key, value in summary.items():
        if isinstance(value, float):
            print(f"{key}: {value:.3f}")
        else:
            print(f"{key}: {value}")
