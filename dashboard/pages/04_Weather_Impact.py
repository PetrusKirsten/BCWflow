from __future__ import annotations

from pathlib import Path

import plotly.express as px
import streamlit as st

from parkflow.analysis.eda import build_weather_summary, prepare_queue_dataset
from parkflow.data.data_quality import load_best_available_dataset
from parkflow.visualization.plots import plot_temperature_vs_wait, plot_weather_wait_comparison

PROJECT_ROOT = Path(__file__).resolve().parents[2]

st.set_page_config(page_title="Weather Impact | ParkFlow", page_icon="🌦️", layout="wide")

st.title("🌦️ Weather Impact")
st.caption("Explore whether weather variables appear related to queue-time variation.")
st.info("Powered by Queue-Times.com. Independent portfolio project; not affiliated with the park.")

df, path = load_best_available_dataset()
if path is None or df.empty:
    st.warning("No processed data found yet.")
    st.code("python -m parkflow.data.make_modeling_dataset", language="bash")
    st.stop()

st.caption(f"Using dataset: `{path.relative_to(PROJECT_ROOT)}`")
df = prepare_queue_dataset(df)

weather_cols = [col for col in ["temperature_2m", "relative_humidity_2m", "precipitation", "wind_speed_10m", "weather_code"] if col in df.columns]
if not weather_cols:
    st.warning(
        "Weather columns were not found in the loaded dataset. Run weather collection and rebuild the modeling dataset first."
    )
    st.code(
        "python -m parkflow.data.collect_weather --start-date YYYY-MM-DD --end-date YYYY-MM-DD\n"
        "python -m parkflow.data.make_modeling_dataset",
        language="bash",
    )
    st.stop()

with st.sidebar:
    st.header("Filters")
    rides = sorted(df["ride_name"].dropna().unique().tolist()) if "ride_name" in df.columns else []
    selected_rides = st.multiselect("Attractions", rides, default=[])
    only_open = st.checkbox("Only open attraction records", value=True)

plot_df = df.copy()
if selected_rides:
    plot_df = plot_df[plot_df["ride_name"].isin(selected_rides)]
if only_open:
    plot_df = plot_df[plot_df["is_open_bool"].fillna(False)]

col1, col2, col3, col4 = st.columns(4)
col1.metric("Rows used", f"{len(plot_df):,}")
col2.metric("Weather fields", f"{len(weather_cols):,}")
col3.metric("Mean temperature", "—" if "temperature_2m" not in plot_df or plot_df["temperature_2m"].dropna().empty else f"{plot_df['temperature_2m'].mean():.1f} °C")
col4.metric("Mean precipitation", "—" if "precipitation" not in plot_df or plot_df["precipitation"].dropna().empty else f"{plot_df['precipitation'].mean():.2f} mm")

if len(plot_df) < 100:
    st.warning(
        "Weather comparisons are exploratory only, especially with few snapshots. Do not interpret them as causal effects."
    )

st.subheader("Weather buckets")
st.plotly_chart(plot_weather_wait_comparison(plot_df), width='stretch')

st.subheader("Temperature scatter")
st.plotly_chart(plot_temperature_vs_wait(plot_df), width='stretch')

st.subheader("Summary table")
weather_summary = build_weather_summary(plot_df, only_open=False)
if weather_summary.empty:
    st.info("No weather summary could be generated yet.")
else:
    st.dataframe(weather_summary, width='stretch', hide_index=True)

with st.expander("Weather columns preview"):
    preview_cols = [col for col in ["analysis_timestamp_local", "ride_name", "wait_time", *weather_cols] if col in plot_df.columns]
    st.dataframe(plot_df[preview_cols].head(250), width='stretch', hide_index=True)
