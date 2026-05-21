from __future__ import annotations

from pathlib import Path

import streamlit as st

from parkflow.analysis.eda import build_heatmap_matrix, build_hourly_summary, filter_queue_pressure_records, prepare_queue_dataset
from parkflow.data.data_quality import load_best_available_dataset
from parkflow.visualization.plots import plot_hourly_heatmap, plot_hourly_wait_profile

PROJECT_ROOT = Path(__file__).resolve().parents[2]

st.set_page_config(page_title="Operational Heatmap | ParkFlow", page_icon="🔥", layout="wide")

st.title("🔥 Operational Heatmap")
st.caption("Identify attraction × hour patterns that may indicate operational pressure.")
st.info("Powered by Queue-Times.com. Independent portfolio project; not affiliated with the park.")

df, path = load_best_available_dataset()
if path is None or df.empty:
    st.warning("No processed data found yet.")
    st.code("python -m parkflow.data.build_queue_times_dataset", language="bash")
    st.stop()

st.caption(f"Using dataset: `{path.relative_to(PROJECT_ROOT)}`")
df = prepare_queue_dataset(df)

with st.sidebar:
    st.header("Heatmap settings")
    metric = st.selectbox(
        "Metric",
        options=["mean_wait", "median_wait", "p90_wait", "max_wait", "observations"],
        index=0,
    )
    only_open = st.checkbox("Only open attraction records", value=True)
    only_operating_hours = st.checkbox(
        "Only nominal operating hours",
        value=True,
        help="Recommended. Excludes snapshots collected outside the nominal 10:00-20:00 park window.",
    )
    exclude_non_queue_candidates = st.checkbox("Hide likely shows/photo/non-queue experiences", value=True)
    include_zero_only_attractions = st.checkbox("Include zero-only attractions", value=False)
    min_observations = st.number_input("Minimum observations per attraction", min_value=1, value=1, step=1)
    top_n = st.slider("Max attractions shown", min_value=5, max_value=40, value=20, step=1)

plot_df = filter_queue_pressure_records(
    df,
    only_open=only_open,
    require_wait_time=True,
    min_wait_time=None,
    include_zero_only_attractions=include_zero_only_attractions,
    exclude_non_queue_candidates=exclude_non_queue_candidates,
    only_operating_hours=only_operating_hours,
)
if "ride_name" in plot_df.columns:
    counts = plot_df.groupby("ride_name")["wait_time"].count()
    keep_rides = counts[counts >= min_observations].index
    plot_df = plot_df[plot_df["ride_name"].isin(keep_rides)]

summary = build_hourly_summary(
    plot_df,
    only_open=False,
    require_wait_time=False,
    include_zero_only_attractions=True,
    exclude_non_queue_candidates=False,
    only_operating_hours=False,
)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Rows used", f"{len(plot_df):,}")
col2.metric("Hours covered", f"{plot_df['hour'].nunique() if 'hour' in plot_df else 0:,}")
col3.metric("Attractions", f"{plot_df['ride_name'].nunique() if 'ride_name' in plot_df else 0:,}")
col4.metric("Mean wait", "—" if plot_df.empty else f"{plot_df['wait_time'].mean():.1f} min")

if len(plot_df) < 100:
    st.warning(
        "This heatmap is already useful for checking layout and data flow, but it needs more snapshots before it becomes operationally meaningful."
    )

st.caption(
    "Color scale: green = lower wait, yellow/orange = moderate wait, red = higher wait. Zero-only attractions are hidden by default to avoid mixing queue rides with likely non-queue experiences while coverage is small."
)

st.subheader("Attraction × hour heatmap")
st.plotly_chart(
    plot_hourly_heatmap(
        plot_df,
        metric=metric,
        top_n=top_n,
        include_zero_only_attractions=True,
        exclude_non_queue_candidates=False,
        only_operating_hours=False,
    ),
    width="stretch",
)

st.subheader("Hourly wait profile")
st.plotly_chart(
    plot_hourly_wait_profile(
        plot_df,
        include_zero_only_attractions=True,
        exclude_non_queue_candidates=False,
        only_operating_hours=False,
    ),
    width="stretch",
)

st.subheader("Hourly summary table")
if summary.empty:
    st.info("No hourly summary could be generated yet.")
else:
    st.dataframe(summary, width="stretch", hide_index=True)

with st.expander("Heatmap matrix"):
    matrix = build_heatmap_matrix(
        plot_df,
        metric=metric,
        only_open=False,
        require_wait_time=False,
        include_zero_only_attractions=True,
        exclude_non_queue_candidates=False,
        top_n=top_n,
        only_operating_hours=False,
    )
    st.dataframe(matrix, width="stretch")
