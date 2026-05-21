from __future__ import annotations

import pandas as pd

from parkflow.analysis.eda import (
    build_attraction_summary,
    build_heatmap_matrix,
    build_hourly_summary,
    build_wait_time_availability,
    prepare_queue_dataset,
)


def sample_queue_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "ride_name": ["Ride A", "Ride A", "Ride B", "Ride B", "Show C"],
            "is_open": [True, True, True, False, True],
            "wait_time": [10, 30, 5, 0, None],
            "last_updated_utc": [
                "2026-05-21T12:00:00Z",
                "2026-05-21T13:00:00Z",
                "2026-05-21T12:00:00Z",
                "2026-05-21T13:00:00Z",
                "2026-05-21T13:00:00Z",
            ],
            "ingested_at_utc": [
                "2026-05-21T12:01:00Z",
                "2026-05-21T13:01:00Z",
                "2026-05-21T12:01:00Z",
                "2026-05-21T13:01:00Z",
                "2026-05-21T13:01:00Z",
            ],
        }
    )


def test_prepare_queue_dataset_adds_analysis_columns() -> None:
    df = prepare_queue_dataset(sample_queue_df())

    assert "analysis_timestamp_local" in df.columns
    assert "hour" in df.columns
    assert "is_open_bool" in df.columns
    assert "wait_time_reported" in df.columns
    assert "attraction_record_type" in df.columns
    assert df["wait_time"].sum() == 45


def test_missing_wait_time_is_not_converted_to_zero() -> None:
    df = prepare_queue_dataset(sample_queue_df())
    show = df.loc[df["ride_name"] == "Show C"].iloc[0]

    assert pd.isna(show["wait_time"])
    assert show["wait_time_reported"] is False or not bool(show["wait_time_reported"])
    assert show["attraction_record_type"] == "open_no_wait_time_reported"


def test_build_wait_time_availability_flags_no_wait_attractions() -> None:
    availability = build_wait_time_availability(sample_queue_df())
    show = availability.loc[availability["ride_name"] == "Show C"].iloc[0]

    assert show["wait_time_reported_records"] == 0
    assert show["wait_time_reported_rate"] == 0
    assert show["mode_hint"] == "scheduled_experience_candidate"


def test_build_attraction_summary_uses_open_reported_records() -> None:
    summary = build_attraction_summary(sample_queue_df(), only_open=True)

    assert set(summary["ride_name"]) == {"Ride A", "Ride B"}
    ride_a = summary.loc[summary["ride_name"] == "Ride A"].iloc[0]
    assert ride_a["mean_wait"] == 20
    assert ride_a["observations"] == 2


def test_build_hourly_summary_returns_expected_hours() -> None:
    hourly = build_hourly_summary(sample_queue_df(), only_open=True)

    assert not hourly.empty
    assert set(hourly["hour"]) == {9, 10}  # UTC-3 for America/Sao_Paulo


def test_build_heatmap_matrix_returns_ride_by_hour_table() -> None:
    matrix = build_heatmap_matrix(sample_queue_df(), metric="mean_wait", only_open=True)

    assert not matrix.empty
    assert "Ride A" in matrix.index
    assert "Show C" not in matrix.index
    assert 9 in matrix.columns
