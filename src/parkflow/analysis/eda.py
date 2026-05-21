from __future__ import annotations

from dataclasses import dataclass
import unicodedata

import pandas as pd

from parkflow.config import (
    PARK_TIMEZONE,
    QUEUE_ANALYSIS_EXCLUDED_ATTRACTIONS,
    QUEUE_ANALYSIS_EXCLUDED_KEYWORDS,
)


@dataclass(frozen=True)
class EDAConfig:
    """Configuration used by exploratory analysis helpers."""

    timezone: str = PARK_TIMEZONE
    open_values: tuple[str, ...] = ("true", "1", "yes")
    scheduled_experience_keywords: tuple[str, ...] = (
        "show",
        "espetaculo",
        "espetáculo",
        "apresentacao",
        "apresentação",
        "teatro",
        "cinema",
        "circo",
        "circus",
        "parade",
        "desfile",
    )


def _normalize_text(value: object) -> str:
    """Normalize text for robust attraction-name matching."""

    if pd.isna(value):
        return ""
    text = str(value).strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(char for char in text if not unicodedata.combining(char))
    return text


_NORMALIZED_EXCLUDED_ATTRACTIONS = {_normalize_text(name) for name in QUEUE_ANALYSIS_EXCLUDED_ATTRACTIONS}
_NORMALIZED_EXCLUDED_KEYWORDS = tuple(_normalize_text(keyword) for keyword in QUEUE_ANALYSIS_EXCLUDED_KEYWORDS)


def _coerce_bool(series: pd.Series, true_values: tuple[str, ...] = ("true", "1", "yes")) -> pd.Series:
    """Convert mixed bool/string values to nullable booleans."""

    if series.dtype == "bool":
        return series.astype("boolean")

    lowered = series.astype("string").str.strip().str.lower()
    coerced = lowered.isin(true_values)
    return coerced.where(lowered.notna(), pd.NA).astype("boolean")


def _queue_pressure_exclusion_reason(name: object) -> str:
    """Explain whether a row should be excluded from queue-pressure charts."""

    normalized = _normalize_text(name)
    if not normalized:
        return "unknown_attraction_name"
    if normalized in _NORMALIZED_EXCLUDED_ATTRACTIONS:
        return "configured_non_queue_experience"
    if any(keyword and keyword in normalized for keyword in _NORMALIZED_EXCLUDED_KEYWORDS):
        return "keyword_non_queue_experience"
    return "included_by_default"


def _infer_attraction_mode_hint(name: object, keywords: tuple[str, ...]) -> str:
    """Return a conservative hint about whether an attraction may be scheduled/non-queue."""

    reason = _queue_pressure_exclusion_reason(name)
    if reason != "included_by_default":
        return "scheduled_or_non_queue_candidate"

    normalized = _normalize_text(name)
    normalized_keywords = tuple(_normalize_text(keyword) for keyword in keywords)
    if any(keyword and keyword in normalized for keyword in normalized_keywords):
        return "scheduled_experience_candidate"
    return "ride_or_queue_candidate"


def _classify_record_type(row: pd.Series) -> str:
    """Classify whether a row has a usable wait time or a missing/non-applicable wait time."""

    if bool(row.get("wait_time_reported", False)):
        if bool(row.get("queue_pressure_excluded_by_rule", False)):
            return "reported_wait_for_non_queue_candidate"
        if row.get("wait_time", 0) == 0:
            return "reported_zero_wait"
        return "reported_positive_wait"

    open_value = row.get("is_open_bool", pd.NA)
    if pd.isna(open_value):
        return "unknown_no_wait_time_reported"
    if bool(open_value):
        return "open_no_wait_time_reported"
    return "closed_no_wait_time_reported"


def prepare_queue_dataset(df: pd.DataFrame, config: EDAConfig | None = None) -> pd.DataFrame:
    """Normalize queue data for EDA and dashboard visualizations.

    Important modeling choice: missing wait times are kept as missing values.
    They are not converted to 0, because a missing value usually means the
    source did not report a queue time for that attraction/status.

    A second distinction is also important: a reported 0 is not always a useful
    queue-pressure signal. Some shows/photo spots/scheduled experiences may be
    represented by the source with wait_time = 0. Those records are kept in the
    dataset, but queue-pressure visuals can exclude them by default.
    """

    config = config or EDAConfig()
    if df.empty:
        return df.copy()

    out = df.copy()

    if "wait_time" in out.columns:
        out["wait_time"] = pd.to_numeric(out["wait_time"], errors="coerce")
    else:
        out["wait_time"] = pd.Series(pd.NA, index=out.index, dtype="Float64")

    out["wait_time_reported"] = out["wait_time"].notna()
    out["missing_wait_time"] = ~out["wait_time_reported"]

    if "is_open" in out.columns:
        out["is_open_bool"] = _coerce_bool(out["is_open"], true_values=config.open_values)
    else:
        out["is_open_bool"] = pd.Series(pd.NA, index=out.index, dtype="boolean")

    if "ride_name" in out.columns:
        out["queue_pressure_exclusion_reason"] = out["ride_name"].apply(_queue_pressure_exclusion_reason)
        out["queue_pressure_excluded_by_rule"] = out["queue_pressure_exclusion_reason"] != "included_by_default"
        out["attraction_mode_hint"] = out["ride_name"].apply(
            lambda value: _infer_attraction_mode_hint(value, config.scheduled_experience_keywords)
        )
    else:
        out["queue_pressure_exclusion_reason"] = "unknown_attraction_name"
        out["queue_pressure_excluded_by_rule"] = True
        out["attraction_mode_hint"] = "unknown"

    # Normalize timestamps. Prefer ingestion time for coverage and collection cadence;
    # prefer last_updated time for operational timing if present.
    for column in ["last_updated_utc", "ingested_at_utc"]:
        if column in out.columns:
            out[column] = pd.to_datetime(out[column], utc=True, errors="coerce")
            local_column = column.replace("_utc", "_local")
            out[local_column] = out[column].dt.tz_convert(config.timezone)

    if "last_updated_local" in out.columns:
        primary_ts = pd.to_datetime(out["last_updated_local"], errors="coerce")
    elif "ingested_at_local" in out.columns:
        primary_ts = pd.to_datetime(out["ingested_at_local"], errors="coerce")
    elif "last_updated_utc" in out.columns:
        primary_ts = pd.to_datetime(out["last_updated_utc"], utc=True, errors="coerce").dt.tz_convert(
            config.timezone
        )
    elif "ingested_at_utc" in out.columns:
        primary_ts = pd.to_datetime(out["ingested_at_utc"], utc=True, errors="coerce").dt.tz_convert(
            config.timezone
        )
    else:
        primary_ts = pd.Series(pd.NaT, index=out.index)

    out["analysis_timestamp_local"] = primary_ts

    if "hour" not in out.columns:
        out["hour"] = out["analysis_timestamp_local"].dt.hour
    if "date" not in out.columns:
        out["date"] = out["analysis_timestamp_local"].dt.date
    if "day_of_week" not in out.columns:
        out["day_of_week"] = out["analysis_timestamp_local"].dt.day_name()
    if "day_of_week_num" not in out.columns:
        out["day_of_week_num"] = out["analysis_timestamp_local"].dt.dayofweek
    if "is_weekend" not in out.columns:
        out["is_weekend"] = out["day_of_week_num"].isin([5, 6])

    if "time_period" not in out.columns:
        out["time_period"] = out["hour"].apply(_classify_time_period)

    out["has_positive_wait"] = out["wait_time_reported"] & out["wait_time"].gt(0)
    out["attraction_record_type"] = out.apply(_classify_record_type, axis=1)

    if "precipitation" in out.columns:
        out["precipitation"] = pd.to_numeric(out["precipitation"], errors="coerce")
        out["rain_flag"] = out["precipitation"].fillna(0) > 0

    if "temperature_2m" in out.columns:
        out["temperature_2m"] = pd.to_numeric(out["temperature_2m"], errors="coerce")

    return out


def _classify_time_period(hour: int | float | None) -> str:
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


def filter_queue_pressure_records(
    df: pd.DataFrame,
    rides: list[str] | None = None,
    only_open: bool = True,
    require_wait_time: bool = True,
    min_wait_time: int | float | None = 0,
    include_zero_only_attractions: bool = False,
    exclude_non_queue_candidates: bool = True,
) -> pd.DataFrame:
    """Return records suitable for queue-pressure charts.

    Defaults are intentionally conservative:
    - records without reported wait_time are removed;
    - known shows/photo spots/non-queue candidates are removed;
    - attractions that only show 0 min in the currently filtered data are hidden.

    The last rule is a visualization default, not a data deletion rule. It keeps
    early dashboards readable while the dataset is still tiny. Users can turn it
    off in Streamlit when they want to audit every reported 0.
    """

    if df.empty:
        return df.copy()

    out = prepare_queue_dataset(df)

    if rides:
        out = out[out["ride_name"].isin(rides)]
    if only_open and "is_open_bool" in out.columns:
        out = out[out["is_open_bool"].fillna(False)]
    if require_wait_time and "wait_time_reported" in out.columns:
        out = out[out["wait_time_reported"]]
    if exclude_non_queue_candidates and "queue_pressure_excluded_by_rule" in out.columns:
        out = out[~out["queue_pressure_excluded_by_rule"].fillna(False)]
    if min_wait_time is not None and "wait_time" in out.columns:
        out = out[out["wait_time"] >= min_wait_time]
    if not include_zero_only_attractions and not out.empty and {"ride_name", "wait_time"}.issubset(out.columns):
        max_wait_by_ride = out.groupby("ride_name")["wait_time"].max()
        keep_rides = max_wait_by_ride[max_wait_by_ride > 0].index
        out = out[out["ride_name"].isin(keep_rides)]

    return out


# Backward-compatible alias used by early notebooks/pages.
def filter_queue_data(
    df: pd.DataFrame,
    rides: list[str] | None = None,
    only_open: bool = True,
    min_wait_time: int | float | None = 0,
    require_wait_time: bool = True,
) -> pd.DataFrame:
    """Apply common dashboard/notebook filters."""

    return filter_queue_pressure_records(
        df,
        rides=rides,
        only_open=only_open,
        min_wait_time=min_wait_time,
        require_wait_time=require_wait_time,
        include_zero_only_attractions=True,
        exclude_non_queue_candidates=False,
    )


def build_wait_time_availability(df: pd.DataFrame) -> pd.DataFrame:
    """Return one row per attraction showing whether wait times are reported."""

    if df.empty or "ride_name" not in df.columns:
        return pd.DataFrame()

    data = prepare_queue_dataset(df)
    snapshot_col = "ingested_at_utc" if "ingested_at_utc" in data.columns else None

    aggregations: dict[str, tuple[str, str]] = {
        "records": ("ride_name", "size"),
        "wait_time_reported_records": ("wait_time_reported", "sum"),
        "missing_wait_time_records": ("missing_wait_time", "sum"),
        "wait_time_reported_rate": ("wait_time_reported", "mean"),
        "positive_wait_records": ("has_positive_wait", "sum"),
        "max_reported_wait": ("wait_time", "max"),
        "open_rate": ("is_open_bool", "mean"),
        "mode_hint": ("attraction_mode_hint", lambda s: s.dropna().mode().iloc[0] if not s.dropna().empty else "unknown"),
        "queue_pressure_exclusion_reason": (
            "queue_pressure_exclusion_reason",
            lambda s: s.dropna().mode().iloc[0] if not s.dropna().empty else "unknown_attraction_name",
        ),
    }
    if snapshot_col:
        aggregations["snapshots"] = (snapshot_col, "nunique")
    if "land_name" in data.columns:
        aggregations["land_name"] = ("land_name", lambda s: s.dropna().mode().iloc[0] if not s.dropna().empty else None)

    out = data.groupby("ride_name", as_index=False).agg(**aggregations)
    for column in ["wait_time_reported_rate", "open_rate"]:
        if column in out.columns:
            out[column] = out[column].round(3)
    if "max_reported_wait" in out.columns:
        out["max_reported_wait"] = out["max_reported_wait"].round(2)
    out["zero_only_reported_wait"] = (out["wait_time_reported_records"] > 0) & (out["positive_wait_records"] == 0)

    return out.sort_values(
        ["queue_pressure_exclusion_reason", "zero_only_reported_wait", "wait_time_reported_rate", "records"],
        ascending=[True, False, True, False],
    ).reset_index(drop=True)


def build_attraction_summary(
    df: pd.DataFrame,
    only_open: bool = True,
    require_wait_time: bool = True,
    include_zero_only_attractions: bool = False,
    exclude_non_queue_candidates: bool = True,
) -> pd.DataFrame:
    """Aggregate wait-time diagnostics by attraction.

    By default this returns queue-pressure candidates only. That keeps rankings
    from treating shows/photo spots or zero-only early records as operational
    queue pressure.
    """

    if df.empty or "ride_name" not in df.columns:
        return pd.DataFrame()

    data = filter_queue_pressure_records(
        df,
        only_open=only_open,
        require_wait_time=require_wait_time,
        include_zero_only_attractions=include_zero_only_attractions,
        exclude_non_queue_candidates=exclude_non_queue_candidates,
    )
    if data.empty:
        return pd.DataFrame()

    snapshot_col = "ingested_at_utc" if "ingested_at_utc" in data.columns else None
    aggregations: dict[str, tuple[str, str]] = {
        "observations": ("wait_time", "count"),
        "mean_wait": ("wait_time", "mean"),
        "median_wait": ("wait_time", "median"),
        "p90_wait": ("wait_time", lambda s: s.quantile(0.90)),
        "max_wait": ("wait_time", "max"),
        "positive_wait_rate": ("has_positive_wait", "mean"),
        "open_rate": ("is_open_bool", "mean"),
        "mode_hint": ("attraction_mode_hint", lambda s: s.dropna().mode().iloc[0] if not s.dropna().empty else "unknown"),
    }
    if snapshot_col:
        aggregations["snapshots"] = (snapshot_col, "nunique")
    if "date" in data.columns:
        aggregations["days_seen"] = ("date", "nunique")
    if "land_name" in data.columns:
        aggregations["land_name"] = ("land_name", lambda s: s.dropna().mode().iloc[0] if not s.dropna().empty else None)

    summary = data.groupby("ride_name", as_index=False).agg(**aggregations)
    for column in ["mean_wait", "median_wait", "p90_wait", "max_wait"]:
        if column in summary.columns:
            summary[column] = summary[column].round(2)
    for column in ["positive_wait_rate", "open_rate"]:
        if column in summary.columns:
            summary[column] = summary[column].round(3)

    return summary.sort_values(["p90_wait", "mean_wait", "observations"], ascending=False).reset_index(drop=True)


def build_hourly_summary(
    df: pd.DataFrame,
    only_open: bool = True,
    require_wait_time: bool = True,
    include_zero_only_attractions: bool = False,
    exclude_non_queue_candidates: bool = True,
) -> pd.DataFrame:
    """Aggregate wait-time diagnostics by local hour."""

    if df.empty:
        return pd.DataFrame()

    data = filter_queue_pressure_records(
        df,
        only_open=only_open,
        require_wait_time=require_wait_time,
        include_zero_only_attractions=include_zero_only_attractions,
        exclude_non_queue_candidates=exclude_non_queue_candidates,
    )
    if data.empty or "hour" not in data.columns:
        return pd.DataFrame()

    summary = (
        data.groupby("hour", as_index=False)
        .agg(
            observations=("wait_time", "count"),
            mean_wait=("wait_time", "mean"),
            median_wait=("wait_time", "median"),
            p90_wait=("wait_time", lambda s: s.quantile(0.90)),
            attractions=("ride_name", "nunique") if "ride_name" in data.columns else ("hour", "size"),
        )
        .sort_values("hour")
    )
    for column in ["mean_wait", "median_wait", "p90_wait"]:
        summary[column] = summary[column].round(2)
    return summary


def build_heatmap_matrix(
    df: pd.DataFrame,
    metric: str = "mean_wait",
    only_open: bool = True,
    require_wait_time: bool = True,
    include_zero_only_attractions: bool = False,
    exclude_non_queue_candidates: bool = True,
    top_n: int | None = None,
) -> pd.DataFrame:
    """Return ride × hour matrix for the operational heatmap."""

    if df.empty:
        return pd.DataFrame()

    data = filter_queue_pressure_records(
        df,
        only_open=only_open,
        require_wait_time=require_wait_time,
        include_zero_only_attractions=include_zero_only_attractions,
        exclude_non_queue_candidates=exclude_non_queue_candidates,
    )
    if data.empty or not {"ride_name", "hour", "wait_time"}.issubset(data.columns):
        return pd.DataFrame()

    aggfunc = {
        "mean_wait": "mean",
        "median_wait": "median",
        "p90_wait": lambda s: s.quantile(0.90),
        "max_wait": "max",
        "observations": "count",
    }.get(metric, "mean")

    matrix = data.pivot_table(index="ride_name", columns="hour", values="wait_time", aggfunc=aggfunc)

    # Sort attractions by overall pressure so the most operationally relevant rows rise to the top.
    ride_order = data.groupby("ride_name")["wait_time"].mean().sort_values(ascending=False).index
    if top_n:
        ride_order = ride_order[:top_n]
    matrix = matrix.reindex(ride_order)
    matrix = matrix.sort_index(axis=1)
    return matrix


def build_time_series_summary(
    df: pd.DataFrame,
    ride_name: str | None = None,
    only_open: bool = True,
    require_wait_time: bool = True,
    include_zero_only_attractions: bool = True,
    exclude_non_queue_candidates: bool = True,
) -> pd.DataFrame:
    """Create time-series data for a selected attraction or all attractions."""

    if df.empty:
        return pd.DataFrame()

    data = filter_queue_pressure_records(
        df,
        only_open=only_open,
        require_wait_time=require_wait_time,
        include_zero_only_attractions=include_zero_only_attractions,
        exclude_non_queue_candidates=exclude_non_queue_candidates,
    )
    if ride_name and "ride_name" in data.columns:
        data = data[data["ride_name"] == ride_name]
    if data.empty:
        return pd.DataFrame()

    time_col = "analysis_timestamp_local"
    if time_col not in data.columns:
        return pd.DataFrame()

    group_cols = [time_col]
    if not ride_name and "ride_name" in data.columns:
        group_cols.append("ride_name")

    ts = (
        data.groupby(group_cols, as_index=False)
        .agg(mean_wait=("wait_time", "mean"), max_wait=("wait_time", "max"), observations=("wait_time", "count"))
        .sort_values(group_cols)
    )
    ts["mean_wait"] = ts["mean_wait"].round(2)
    return ts


def build_weather_summary(
    df: pd.DataFrame,
    only_open: bool = True,
    require_wait_time: bool = True,
    include_zero_only_attractions: bool = False,
    exclude_non_queue_candidates: bool = True,
) -> pd.DataFrame:
    """Summarize exploratory queue patterns by simple weather buckets."""

    if df.empty:
        return pd.DataFrame()

    data = filter_queue_pressure_records(
        df,
        only_open=only_open,
        require_wait_time=require_wait_time,
        include_zero_only_attractions=include_zero_only_attractions,
        exclude_non_queue_candidates=exclude_non_queue_candidates,
    )
    if data.empty or "wait_time" not in data.columns:
        return pd.DataFrame()

    summaries = []

    if "rain_flag" in data.columns:
        rain = (
            data.groupby("rain_flag", as_index=False)
            .agg(
                observations=("wait_time", "count"),
                mean_wait=("wait_time", "mean"),
                p90_wait=("wait_time", lambda s: s.quantile(0.90)),
            )
            .rename(columns={"rain_flag": "bucket_value"})
        )
        rain["weather_dimension"] = "rain_flag"
        rain["bucket_value"] = rain["bucket_value"].map({True: "rain", False: "no_rain"})
        summaries.append(rain)

    if "temperature_2m" in data.columns and data["temperature_2m"].notna().sum() >= 3:
        temp = data.copy()
        try:
            temp["temperature_bucket"] = pd.qcut(
                temp["temperature_2m"], q=min(4, temp["temperature_2m"].nunique()), duplicates="drop"
            )
            temp_summary = (
                temp.groupby("temperature_bucket", as_index=False, observed=True)
                .agg(
                    observations=("wait_time", "count"),
                    mean_wait=("wait_time", "mean"),
                    p90_wait=("wait_time", lambda s: s.quantile(0.90)),
                )
                .rename(columns={"temperature_bucket": "bucket_value"})
            )
            temp_summary["weather_dimension"] = "temperature_bucket"
            temp_summary["bucket_value"] = temp_summary["bucket_value"].astype(str)
            summaries.append(temp_summary)
        except ValueError:
            pass

    if not summaries:
        return pd.DataFrame()

    out = pd.concat(summaries, ignore_index=True)
    for column in ["mean_wait", "p90_wait"]:
        out[column] = out[column].round(2)
    return out[["weather_dimension", "bucket_value", "observations", "mean_wait", "p90_wait"]]


def build_initial_insights(df: pd.DataFrame) -> list[str]:
    """Generate conservative, data-aware insight bullets for notebooks/dashboard."""

    if df.empty:
        return ["No processed data is available yet."]

    data = prepare_queue_dataset(df)
    summary = build_attraction_summary(data, only_open=True, require_wait_time=True)
    hourly = build_hourly_summary(data, only_open=True, require_wait_time=True)
    availability = build_wait_time_availability(data)
    insights: list[str] = []

    snapshot_count = data["ingested_at_utc"].nunique() if "ingested_at_utc" in data.columns else 0
    if snapshot_count < 10:
        insights.append(
            f"Current dataset has only {snapshot_count} snapshot(s); treat every pattern as a pipeline check, not a stable operational conclusion."
        )

    if not availability.empty:
        no_wait = availability[availability["wait_time_reported_rate"].fillna(0) == 0]
        zero_only = availability[
            (availability["zero_only_reported_wait"].fillna(False))
            & (availability["queue_pressure_exclusion_reason"] == "included_by_default")
        ]
        non_queue = availability[availability["queue_pressure_exclusion_reason"] != "included_by_default"]
        if not no_wait.empty:
            insights.append(
                f"{len(no_wait)} attraction(s) currently have no reported wait-time values. Keep them in data coverage, but exclude them from queue-pressure rankings unless a queue value appears later."
            )
        if not zero_only.empty:
            insights.append(
                f"{len(zero_only)} attraction(s) currently report only 0 min. They are hidden from pressure charts by default while the dataset is small, but can be audited from the filters."
            )
        if not non_queue.empty:
            insights.append(
                f"{len(non_queue)} attraction(s) are flagged as likely shows/photo/non-queue experiences and are excluded from pressure charts by default."
            )

    if not summary.empty:
        top = summary.iloc[0]
        insights.append(
            f"Highest current queue pressure by p90 is {top['ride_name']} with p90 ≈ {top['p90_wait']:.1f} min across {int(top['observations'])} reported observation(s)."
        )

    if not hourly.empty:
        peak = hourly.sort_values("mean_wait", ascending=False).iloc[0]
        insights.append(
            f"Highest average wait in the collected sample appears around {int(peak['hour']):02d}:00, with mean wait ≈ {peak['mean_wait']:.1f} min."
        )

    if "precipitation" in data.columns and data["precipitation"].notna().any():
        insights.append(
            "Weather variables are already linked to queue records, so the project is ready for exploratory weather comparisons as coverage grows."
        )

    return insights or ["Dataset loaded successfully; collect more snapshots to unlock stable patterns."]
