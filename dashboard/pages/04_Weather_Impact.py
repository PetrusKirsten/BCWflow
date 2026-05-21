from __future__ import annotations

from pathlib import Path

import streamlit as st

from parkflow.analysis.eda import build_weather_summary, filter_queue_pressure_records, prepare_queue_dataset
from parkflow.data.data_quality import load_best_available_dataset
from parkflow.visualization.plots import plot_temperature_vs_wait, plot_weather_wait_comparison

PROJECT_ROOT = Path(__file__).resolve().parents[2]

st.set_page_config(page_title="Weather Impact | ParkFlow", page_icon="🌦️", layout="wide")

st.title("🌦️ Weather Impact")
st.caption("Explore how weather variables relate to queue-pressure records. Exploratory only, not causal.")
st.info("Powered by Queue-Times.com. Independent portfolio project; not affiliated with the park.")

df, path = load_best_available_dataset()
if path is None or df.empty:
    st.warning("No processed data found yet.")
    st.code("python -m parkflow.data.make_modeling_dataset", language="bash")
    st.stop()

st.caption(f"Using dataset: `{path.relative_to(PROJECT_ROOT)}`")
df = prepare_queue_dataset(df)

with st.sidebar:
    st.header("Filters")
    only_open = st.checkbox("Only open attraction records", value=True)
    exclude_non_queue_candidates = st.checkbox("Hide likely shows/photo/non-queue experiences", value=True)
    only_operating_hours = st.checkbox(
        "Only nominal operating hours",
        value=True,
        help="Recommended. Excludes after-hours snapshots from exploratory weather comparisons.",
    )
    include_zero_only_attractions = st.checkbox("Include zero-only attractions", value=False)

plot_df = filter_queue_pressure_records(
    df,
    only_open=only_open,
    require_wait_time=True,
    include_zero_only_attractions=include_zero_only_attractions,
    exclude_non_queue_candidates=exclude_non_queue_candidates,
    only_operating_hours=only_operating_hours,
)

weather_cols = [col for col in ["temperature_2m", "precipitation", "rain_flag"] if col in plot_df.columns]

col1, col2, col3 = st.columns(3)
col1.metric("Queue-pressure rows", f"{len(plot_df):,}")
col2.metric("Weather fields", len(weather_cols))
col3.metric("Mean wait", "—" if plot_df.empty else f"{plot_df['wait_time'].mean():.1f} min")

if not weather_cols:
    st.warning("No weather variables were found in the current dataset. Run the weather collector and modeling dataset builder.")
    st.code(
        "python -m parkflow.data.collect_weather --start-date YYYY-MM-DD --end-date YYYY-MM-DD\n"
        "python -m parkflow.data.make_modeling_dataset",
        language="bash",
    )
    st.stop()

if len(plot_df) < 100:
    st.warning("Weather comparisons need more queue snapshots before they become analytically meaningful.")

st.subheader("Weather buckets")
st.plotly_chart(
    plot_weather_wait_comparison(
        plot_df,
        include_zero_only_attractions=True,
        exclude_non_queue_candidates=False,
    ),
    width="stretch",
)

st.subheader("Temperature × wait time")
st.plotly_chart(
    plot_temperature_vs_wait(
        plot_df,
        include_zero_only_attractions=True,
        exclude_non_queue_candidates=False,
    ),
    width="stretch",
)

with st.expander("Weather summary table"):
    weather_summary = build_weather_summary(
        plot_df,
        only_open=False,
        require_wait_time=False,
        include_zero_only_attractions=True,
        exclude_non_queue_candidates=False,
    )
    if weather_summary.empty:
        st.info("No weather summary available yet.")
    else:
        st.dataframe(weather_summary, width="stretch", hide_index=True)

with st.expander("Weather-linked data preview"):
    preview_cols = [col for col in ["analysis_timestamp_local", "ride_name", "wait_time", *weather_cols] if col in plot_df.columns]
    st.dataframe(plot_df[preview_cols].head(250), width="stretch", hide_index=True)
