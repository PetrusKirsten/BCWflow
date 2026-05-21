from __future__ import annotations

import pandas as pd

from parkflow.analysis.eda import (
    build_attraction_summary,
    build_heatmap_matrix,
    build_hourly_summary,
    prepare_queue_dataset,
)


def sample_queue_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "ride_name": ["Ride A", "Ride A", "Ride B", "Ride B"],
            "is_open": [True, True, True, False],
            "wait_time": [10, 30, 5, 0],
            "last_updated_utc": [
                "2026-05-21T12:00:00Z",
                "2026-05-21T13:00:00Z",
                "2026-05-21T12:00:00Z",
                "2026-05-21T13:00:00Z",
            ],
            "ingested_at_utc": [
                "2026-05-21T12:01:00Z",
                "2026-05-21T13:01:00Z",
                "2026-05-21T12:01:00Z",
                "2026-05-21T13:01:00Z",
            ],
        }
    )


def test_prepare_queue_dataset_adds_analysis_columns() -> None:
    df = prepare_queue_dataset(sample_queue_df())

    assert "analysis_timestamp_local" in df.columns
    assert "hour" in df.columns
    assert "is_open_bool" in df.columns
    assert df["wait_time"].sum() == 45


def test_build_attraction_summary_uses_open_records() -> None:
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
    assert 9 in matrix.columns
