from __future__ import annotations

import pandas as pd

from parkflow.analysis.eda import (
    build_attraction_summary,
    build_heatmap_matrix,
    build_hourly_summary,
    build_wait_time_availability,
    filter_queue_pressure_records,
    prepare_queue_dataset,
)


def sample_queue_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "ride_name": ["Ride A", "Ride A", "Ride B", "Ride B", "Show C", "Fotos com Trolls", "Zero Ride"],
            "is_open": [True, True, True, False, True, True, True],
            "wait_time": [10, 30, 5, 0, None, 0, 0],
            "last_updated_utc": [
                "2026-05-21T12:00:00Z",
                "2026-05-21T13:00:00Z",
                "2026-05-21T12:00:00Z",
                "2026-05-21T13:00:00Z",
                "2026-05-21T13:00:00Z",
                "2026-05-21T13:00:00Z",
                "2026-05-21T13:00:00Z",
            ],
            "ingested_at_utc": [
                "2026-05-21T12:01:00Z",
                "2026-05-21T13:01:00Z",
                "2026-05-21T12:01:00Z",
                "2026-05-21T13:01:00Z",
                "2026-05-21T13:01:00Z",
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
    assert "queue_pressure_exclusion_reason" in df.columns
    assert "is_within_nominal_operating_hours" in df.columns
    assert df["wait_time"].sum() == 45


def test_missing_wait_time_is_not_converted_to_zero() -> None:
    df = prepare_queue_dataset(sample_queue_df())
    show = df.loc[df["ride_name"] == "Show C"].iloc[0]

    assert pd.isna(show["wait_time"])
    assert show["wait_time_reported"] is False or not bool(show["wait_time_reported"])
    assert show["attraction_record_type"] == "open_no_wait_time_reported"


def test_configured_non_queue_attraction_is_flagged_even_with_zero_wait() -> None:
    df = prepare_queue_dataset(sample_queue_df())
    photos = df.loc[df["ride_name"] == "Fotos com Trolls"].iloc[0]

    assert bool(photos["wait_time_reported"])
    assert photos["wait_time"] == 0
    assert bool(photos["queue_pressure_excluded_by_rule"])
    assert photos["queue_pressure_exclusion_reason"] in {
        "configured_non_queue_experience",
        "keyword_non_queue_experience",
    }


def test_build_wait_time_availability_flags_no_wait_and_zero_only_attractions() -> None:
    availability = build_wait_time_availability(sample_queue_df())
    show = availability.loc[availability["ride_name"] == "Show C"].iloc[0]
    zero = availability.loc[availability["ride_name"] == "Zero Ride"].iloc[0]

    assert show["wait_time_reported_records"] == 0
    assert show["wait_time_reported_rate"] == 0
    assert show["mode_hint"] == "scheduled_or_non_queue_candidate"
    assert bool(zero["zero_only_reported_wait"])


def test_filter_queue_pressure_records_excludes_zero_only_and_non_queue_by_default() -> None:
    filtered = filter_queue_pressure_records(sample_queue_df())

    assert set(filtered["ride_name"]) == {"Ride A"}
    assert "Fotos com Trolls" not in set(filtered["ride_name"])
    assert "Zero Ride" not in set(filtered["ride_name"])


def test_filter_queue_pressure_records_can_include_zero_only_when_requested() -> None:
    filtered = filter_queue_pressure_records(sample_queue_df(), include_zero_only_attractions=True)

    assert "Zero Ride" in set(filtered["ride_name"])
    assert "Fotos com Trolls" not in set(filtered["ride_name"])


def test_filter_queue_pressure_records_can_include_outside_hours_when_requested() -> None:
    filtered = filter_queue_pressure_records(sample_queue_df(), only_operating_hours=False)

    assert set(filtered["ride_name"]) == {"Ride A", "Ride B"}


def test_build_attraction_summary_uses_queue_pressure_records() -> None:
    summary = build_attraction_summary(sample_queue_df(), only_open=True)

    assert set(summary["ride_name"]) == {"Ride A"}
    ride_a = summary.loc[summary["ride_name"] == "Ride A"].iloc[0]
    assert ride_a["mean_wait"] == 30
    assert ride_a["observations"] == 1


def test_build_hourly_summary_returns_expected_hours() -> None:
    hourly = build_hourly_summary(sample_queue_df(), only_open=True)

    assert not hourly.empty
    assert set(hourly["hour"]) == {10}  # 09:00 local is outside the nominal 10:00-20:00 window


def test_build_heatmap_matrix_returns_ride_by_hour_table() -> None:
    matrix = build_heatmap_matrix(sample_queue_df(), metric="mean_wait", only_open=True)

    assert not matrix.empty
    assert "Ride A" in matrix.index
    assert "Show C" not in matrix.index
    assert "Fotos com Trolls" not in matrix.index
    assert "Zero Ride" not in matrix.index
    assert 10 in matrix.columns
    assert 9 not in matrix.columns
