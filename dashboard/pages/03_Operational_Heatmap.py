from __future__ import annotations

from pathlib import Path

import plotly.express as px
import streamlit as st

from parkflow.analysis.eda import build_heatmap_matrix, build_hourly_summary, prepare_queue_dataset
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
    min_observations = st.number_input("Minimum observations per attraction", min_value=1, value=1, step=1)

plot_df = df[df["is_open_bool"].fillna(False)] if only_open else df.copy()
if "ride_name" in plot_df.columns:
    counts = plot_df.groupby("ride_name").size()
    keep_rides = counts[counts >= min_observations].index
    plot_df = plot_df[plot_df["ride_name"].isin(keep_rides)]

summary = build_hourly_summary(plot_df, only_open=False)

col1, col2, col3 = st.columns(3)
col1.metric("Rows used", f"{len(plot_df):,}")
col2.metric("Hours covered", f"{plot_df['hour'].nunique() if 'hour' in plot_df else 0:,}")
col3.metric("Attractions", f"{plot_df['ride_name'].nunique() if 'ride_name' in plot_df else 0:,}")

if len(plot_df) < 100:
    st.warning(
        "This heatmap is already useful for checking layout and data flow, but it needs more snapshots before it becomes operationally meaningful."
    )

st.subheader("Attraction × hour heatmap")
st.plotly_chart(plot_hourly_heatmap(plot_df, metric=metric), width='stretch')

st.subheader("Hourly wait profile")
st.plotly_chart(plot_hourly_wait_profile(plot_df), width='stretch')

st.subheader("Hourly summary table")
if summary.empty:
    st.info("No hourly summary could be generated yet.")
else:
    st.dataframe(summary, width='stretch', hide_index=True)

with st.expander("Heatmap matrix"):
    matrix = build_heatmap_matrix(plot_df, metric=metric, only_open=False)
    st.dataframe(matrix, width='stretch')
