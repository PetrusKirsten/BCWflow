from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from parkflow.analysis.eda import filter_queue_pressure_records, prepare_queue_dataset
from parkflow.visualization.plots import plot_average_wait_by_ride, plot_hourly_heatmap

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "data" / "processed" / "modeling_dataset.csv"
QUEUE_PATH = PROJECT_ROOT / "data" / "processed" / "queue_times.csv"

st.set_page_config(page_title="ParkFlow Analytics", page_icon="🎢", layout="wide")

st.title("🎢 ParkFlow Analytics")
st.caption("Queue time, visitor flow and weather intelligence for theme park operations.")

st.info("Powered by Queue-Times.com. Independent portfolio project; not affiliated with the park.")

path = DATA_PATH if DATA_PATH.exists() else QUEUE_PATH

if not path.exists():
    st.warning("No processed data found yet. Run the queue-time collector and dataset builder first.")
    st.code("python -m parkflow.data.collect_queue_times\npython -m parkflow.data.build_queue_times_dataset")
    st.stop()


df = prepare_queue_dataset(pd.read_csv(path))
reported = df[df["wait_time_reported"]] if "wait_time_reported" in df.columns else df
pressure = filter_queue_pressure_records(df)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Rows", f"{len(df):,}")
col2.metric("Attractions", df["ride_name"].nunique() if "ride_name" in df else 0)
col3.metric("Reported wait records", f"{len(reported):,}")
col4.metric("Queue-pressure records", f"{len(pressure):,}")

st.caption(
    "Queue-pressure charts hide likely shows/photo/non-queue experiences and zero-only attractions by default. "
    "Nothing is deleted; use Data Coverage to audit the full dataset."
)

st.subheader("Average wait by attraction")
st.plotly_chart(plot_average_wait_by_ride(df, top_n=15), width="stretch")

st.subheader("Operational heatmap")
if "hour" in df.columns:
    st.plotly_chart(plot_hourly_heatmap(df, top_n=20), width="stretch")
else:
    st.warning("Run the feature builder/dataset builder to create hour-level features.")

with st.expander("Raw preview"):
    st.dataframe(df.head(100), width="stretch")
