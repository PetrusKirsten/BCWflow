from __future__ import annotations

from pathlib import Path

import streamlit as st

from parkflow.analysis.eda import (
    build_attraction_summary,
    build_initial_insights,
    build_wait_time_availability,
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
        default=rides[: min(8, len(rides))],
        help="Keep this smaller when the dataset grows to make plots easier to read.",
    )
    only_open = st.checkbox("Only open attraction records", value=True)
    require_wait_time = st.checkbox(
        "Only records with reported wait time",
        value=True,
        help="Recommended for queue-pressure analysis. Turn off only when auditing missing/non-applicable values.",
    )
    min_wait = st.slider("Minimum wait time", min_value=0, max_value=120, value=0, step=5)

filtered = df.copy()
if selected_rides:
    filtered = filtered[filtered["ride_name"].isin(selected_rides)]
if only_open:
    filtered = filtered[filtered["is_open_bool"].fillna(False)]

records_before_wait_filter = len(filtered)
if require_wait_time:
    filtered = filtered[filtered["wait_time_reported"]]
filtered = filtered[filtered["wait_time"] >= min_wait]

summary = build_attraction_summary(filtered, only_open=False, require_wait_time=require_wait_time)
availability = build_wait_time_availability(df)
no_wait_current = availability[availability["wait_time_reported_rate"].fillna(0) == 0] if not availability.empty else availability

col1, col2, col3, col4 = st.columns(4)
col1.metric("Filtered rows", f"{len(filtered):,}")
col2.metric("Attractions", f"{filtered['ride_name'].nunique() if 'ride_name' in filtered else 0:,}")
col3.metric("Reported wait records", f"{filtered['wait_time_reported'].sum():,}" if "wait_time_reported" in filtered else "—")
col4.metric("Mean wait", "—" if filtered.empty else f"{filtered['wait_time'].mean():.1f} min")

if require_wait_time and records_before_wait_filter > len(filtered):
    st.caption(
        f"Excluded {records_before_wait_filter - len(filtered):,} record(s) without reported wait time from queue-pressure charts."
    )

if no_wait_current is not None and not no_wait_current.empty:
    with st.expander("Attractions currently without reported wait-time values"):
        st.write(
            "These are kept in the dataset for coverage, but excluded from queue rankings by default. They may be shows, scheduled experiences or attractions whose wait times are not published by the source."
        )
        st.dataframe(no_wait_current, width="stretch", hide_index=True)

if len(df) < 100:
    st.warning(
        "The dataset is still very small. Use this page to validate the analytical structure; stronger conclusions need more snapshots."
    )

st.subheader("Initial read")
for insight in build_initial_insights(df):
    st.write(f"- {insight}")

st.subheader("Attraction ranking")
left, right = st.columns([1, 1])
with left:
    st.plotly_chart(plot_p90_wait_by_ride(filtered, top_n=20), width="stretch")
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
        st.info("No reported wait-time records in the current filter.")
    else:
        st.dataframe(summary[display_cols], width="stretch", hide_index=True)

st.subheader("Distribution")
st.plotly_chart(plot_wait_distribution(filtered, rides=selected_rides), width="stretch")

st.subheader("Time series")
ride_for_ts = st.selectbox(
    "Select one attraction", options=[None] + rides, format_func=lambda x: "All selected attractions" if x is None else x
)
st.plotly_chart(plot_attraction_time_series(filtered, ride_name=ride_for_ts), width="stretch")

with st.expander("Filtered data preview"):
    st.dataframe(filtered.head(250), width="stretch")
