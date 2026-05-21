from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from parkflow.data.data_quality import (
    add_audit_time_columns,
    build_coverage_summary,
    hourly_coverage_report,
    load_best_available_dataset,
    missingness_report,
    ride_coverage_report,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]

st.set_page_config(page_title="Data Coverage | ParkFlow", page_icon="📊", layout="wide")

st.title("📊 Data Coverage")
st.caption("A transparent view of how much queue-time data has been collected so far.")

st.info("Powered by Queue-Times.com. Independent portfolio project; not affiliated with the park.")

df, path = load_best_available_dataset()

if path is None or df.empty:
    st.warning("No processed data found yet.")
    st.code(
        "python -m parkflow.data.collect_queue_times\n"
        "python -m parkflow.data.build_queue_times_dataset",
        language="bash",
    )
    st.stop()

st.caption(f"Using dataset: `{path.relative_to(PROJECT_ROOT)}`")

df = add_audit_time_columns(df)
summary = build_coverage_summary(df)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Rows", f"{summary['rows']:,}")
col2.metric("Snapshots", f"{summary['snapshots']:,}")
col3.metric("Attractions", f"{summary['attractions']:,}")
col4.metric("Days covered", f"{summary['days_covered']:,}")

col5, col6, col7, col8 = st.columns(4)
col5.metric("First snapshot", str(summary["first_snapshot_local"]))
col6.metric("Last snapshot", str(summary["last_snapshot_local"]))
col7.metric(
    "Avg wait",
    "—" if summary["average_wait_min"] is None else f"{summary['average_wait_min']:.1f} min",
)
col8.metric("P90 wait", "—" if summary["p90_wait_min"] is None else f"{summary['p90_wait_min']:.1f} min")

st.divider()

st.subheader("Coverage over time")
hourly = hourly_coverage_report(df)
if hourly.empty:
    st.warning("Not enough timestamp information to build time coverage charts.")
else:
    daily = hourly.groupby("audit_date_local", as_index=False).agg(
        rows=("rows", "sum"),
        snapshots=("snapshots", "sum") if "snapshots" in hourly.columns else ("rows", "count"),
        avg_wait_min=("avg_wait_min", "mean") if "avg_wait_min" in hourly.columns else ("rows", "mean"),
    )
    daily["audit_date_local"] = pd.to_datetime(daily["audit_date_local"])

    fig_daily = px.bar(
        daily,
        x="audit_date_local",
        y="snapshots",
        title="Collected snapshots by day",
        labels={"audit_date_local": "Local date", "snapshots": "Snapshots"},
    )
    st.plotly_chart(fig_daily, use_container_width=True)

    heat = hourly.pivot_table(
        index="audit_date_local", columns="audit_hour_local", values="snapshots", aggfunc="sum", fill_value=0
    )
    fig_heat = px.imshow(
        heat,
        aspect="auto",
        title="Snapshot coverage heatmap: local date × hour",
        labels={"x": "Local hour", "y": "Local date", "color": "Snapshots"},
    )
    st.plotly_chart(fig_heat, use_container_width=True)

st.subheader("Attraction coverage")
ride_report = ride_coverage_report(df)
if ride_report.empty:
    st.warning("No attraction-level report could be generated.")
else:
    chart_cols = st.columns([2, 1])
    with chart_cols[0]:
        fig_rides = px.bar(
            ride_report.head(25).sort_values("rows"),
            x="rows",
            y="ride_name",
            orientation="h",
            title="Rows collected by attraction",
            labels={"rows": "Rows", "ride_name": "Attraction"},
        )
        st.plotly_chart(fig_rides, use_container_width=True)
    with chart_cols[1]:
        display_cols = [
            col
            for col in ["ride_name", "rows", "snapshots", "days_seen", "open_rate", "avg_wait_min", "p90_wait_min"]
            if col in ride_report.columns
        ]
        st.dataframe(ride_report[display_cols], use_container_width=True, hide_index=True)

st.subheader("Missing values")
miss = missingness_report(df)
if miss.empty:
    st.success("No columns to inspect.")
else:
    st.dataframe(miss, use_container_width=True, hide_index=True)

with st.expander("Dataset preview"):
    st.dataframe(df.head(200), use_container_width=True)
