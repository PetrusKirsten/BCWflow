from __future__ import annotations

from pathlib import Path

import streamlit as st

from parkflow.analysis.eda import (
    build_attraction_summary,
    build_initial_insights,
    build_wait_time_availability,
    filter_queue_pressure_records,
    prepare_queue_dataset,
)
from parkflow.data.data_quality import load_best_available_dataset
from parkflow.visualization.plots import (
    plot_attraction_time_series,
    plot_p90_wait_by_ride,
    plot_wait_distribution,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]

st.set_page_config(page_title="Attraction Explorer | ParkFlow", page_icon="🎡", layout="wide")

st.title("🎡 Attraction Explorer")
st.caption("Compare attraction-level wait-time pressure, distributions and time-series behavior.")
st.info("Powered by Queue-Times.com. Independent portfolio project; not affiliated with the park.")

df, path = load_best_available_dataset()
if path is None or df.empty:
    st.warning("No processed data found yet.")
    st.code("python -m parkflow.data.build_queue_times_dataset", language="bash")
    st.stop()

st.caption(f"Using dataset: `{path.relative_to(PROJECT_ROOT)}`")
df = prepare_queue_dataset(df)

rides = sorted(df["ride_name"].dropna().unique().tolist()) if "ride_name" in df.columns else []

with st.sidebar:
    st.header("Filters")
    selected_rides = st.multiselect(
        "Attractions",
        rides,
        default=[],
        help="Leave empty to include all attractions before the queue-pressure filters are applied.",
    )
    only_open = st.checkbox("Only open attraction records", value=True)
    only_operating_hours = st.checkbox(
        "Only nominal operating hours",
        value=True,
        help="Recommended. Excludes snapshots collected outside the nominal 10:00-20:00 park window from queue-pressure charts.",
    )
    require_wait_time = st.checkbox(
        "Only records with reported wait time",
        value=True,
        help="Recommended for queue-pressure analysis. Turn off only when auditing missing/non-applicable values.",
    )
    exclude_non_queue_candidates = st.checkbox(
        "Hide likely shows/photo/non-queue experiences",
        value=True,
        help="Uses a conservative configured list plus keywords such as show/fotos/circo.",
    )
    include_zero_only_attractions = st.checkbox(
        "Include zero-only attractions",
        value=False,
        help="Off by default to avoid clutter while the dataset is still small. Turn on to audit attractions that only report 0 min so far.",
    )
    min_wait = st.slider("Minimum wait time", min_value=0, max_value=120, value=0, step=5)
    top_n = st.slider("Top attractions shown", min_value=5, max_value=30, value=15, step=1)

base = df.copy()
if selected_rides:
    base = base[base["ride_name"].isin(selected_rides)]
if only_open:
    base = base[base["is_open_bool"].fillna(False)]
if only_operating_hours and "is_within_nominal_operating_hours" in base.columns:
    base = base[base["is_within_nominal_operating_hours"].astype("boolean").fillna(False)]

records_before_wait_filter = len(base)
if require_wait_time:
    base = base[base["wait_time_reported"]]
base = base[base["wait_time"] >= min_wait]

pressure_df = filter_queue_pressure_records(
    base,
    only_open=False,
    require_wait_time=False,
    min_wait_time=None,
    include_zero_only_attractions=include_zero_only_attractions,
    exclude_non_queue_candidates=exclude_non_queue_candidates,
    only_operating_hours=False,
)
summary = build_attraction_summary(
    pressure_df,
    only_open=False,
    require_wait_time=False,
    include_zero_only_attractions=True,
    exclude_non_queue_candidates=False,
    only_operating_hours=False,
)
availability = build_wait_time_availability(df)
no_wait_current = availability[availability["wait_time_reported_rate"].fillna(0) == 0] if not availability.empty else availability
zero_only_current = availability[availability["zero_only_reported_wait"].fillna(False)] if not availability.empty else availability
non_queue_current = availability[availability["queue_pressure_exclusion_reason"] != "included_by_default"] if not availability.empty else availability

col1, col2, col3, col4 = st.columns(4)
col1.metric("Filtered rows", f"{len(base):,}")
col2.metric("Queue-pressure rows", f"{len(pressure_df):,}")
col3.metric("Queue attractions", f"{pressure_df['ride_name'].nunique() if 'ride_name' in pressure_df else 0:,}")
col4.metric("Mean wait", "—" if pressure_df.empty else f"{pressure_df['wait_time'].mean():.1f} min")

if require_wait_time and records_before_wait_filter > len(base):
    st.caption(
        f"Excluded {records_before_wait_filter - len(base):,} record(s) without reported wait time from queue-pressure charts."
    )

st.caption(
    "By default, this page focuses on queue-pressure candidates: reported wait-time records, excluding likely non-queue experiences and attractions that only show 0 min in the current sample."
)

with st.expander("Audit: why some attractions are hidden from pressure charts"):
    st.write(
        "Hidden attractions are not removed from the dataset. They are separated because a reported 0 can mean either a real empty queue or a non-queue/scheduled experience. With few snapshots, hiding zero-only attractions keeps the charts readable."
    )
    if no_wait_current is not None and not no_wait_current.empty:
        st.write("**No reported wait-time values yet**")
        st.dataframe(no_wait_current, width="stretch", hide_index=True)
    if zero_only_current is not None and not zero_only_current.empty:
        st.write("**Only 0-minute wait values observed so far**")
        cols = [
            col
            for col in [
                "ride_name",
                "records",
                "wait_time_reported_records",
                "positive_wait_records",
                "max_reported_wait",
                "open_rate",
                "queue_pressure_exclusion_reason",
            ]
            if col in zero_only_current.columns
        ]
        st.dataframe(zero_only_current[cols], width="stretch", hide_index=True)
    if non_queue_current is not None and not non_queue_current.empty:
        st.write("**Configured/keyword non-queue candidates**")
        cols = [
            col
            for col in ["ride_name", "records", "queue_pressure_exclusion_reason", "mode_hint", "max_reported_wait"]
            if col in non_queue_current.columns
        ]
        st.dataframe(non_queue_current[cols], width="stretch", hide_index=True)

if len(df) < 100:
    st.warning(
        "The dataset is still very small. Use this page to validate the analytical structure; stronger conclusions need more snapshots."
    )

st.subheader("Initial read")
for insight in build_initial_insights(df):
    st.write(f"- {insight}")

st.subheader("Attraction ranking")
left, right = st.columns([1.2, 1])
with left:
    st.plotly_chart(
        plot_p90_wait_by_ride(
            pressure_df,
            top_n=top_n,
            include_zero_only_attractions=True,
            exclude_non_queue_candidates=False,
            only_operating_hours=False,
        ),
        width="stretch",
    )
with right:
    display_cols = [
        col
        for col in [
            "ride_name",
            "observations",
            "mean_wait",
            "median_wait",
            "p90_wait",
            "max_wait",
            "positive_wait_rate",
            "mode_hint",
        ]
        if col in summary.columns
    ]
    if summary.empty:
        st.info("No queue-pressure records in the current filter.")
    else:
        st.dataframe(summary[display_cols], width="stretch", hide_index=True)

st.subheader("Distribution")
st.plotly_chart(
    plot_wait_distribution(
        pressure_df,
        rides=selected_rides or None,
        include_zero_only_attractions=True,
        exclude_non_queue_candidates=False,
        only_operating_hours=False,
    ),
    width="stretch",
)

st.subheader("Time series")
ride_options = sorted(pressure_df["ride_name"].dropna().unique().tolist()) if "ride_name" in pressure_df else []
ride_for_ts = st.selectbox(
    "Select one attraction", options=[None] + ride_options, format_func=lambda x: "All queue-pressure attractions" if x is None else x
)
st.plotly_chart(
    plot_attraction_time_series(
        pressure_df,
        ride_name=ride_for_ts,
        include_zero_only_attractions=True,
        exclude_non_queue_candidates=False,
        only_operating_hours=False,
    ),
    width="stretch",
)

with st.expander("Filtered data preview"):
    st.dataframe(pressure_df.head(250), width="stretch")
