from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from parkflow.config import PROCESSED_DIR

PROJECT_ROOT = Path(__file__).resolve().parents[2]
HISTORICAL_DIR = PROCESSED_DIR / "historical_context"

st.set_page_config(page_title="Historical Context | ParkFlow", page_icon="🗓️", layout="wide")

st.title("🗓️ Historical Context")
st.caption("Aggregate historical context collected from public pages. This is not row-level queue history.")
st.info("Powered by Queue-Times.com. Independent portfolio project; not affiliated with the park.")

if not HISTORICAL_DIR.exists():
    st.warning("No historical context files found yet.")
    st.code(
        "python -m parkflow.data.historical_context --year 2026 --collect-calendar --start-date 2026-01-01 --end-date 2026-05-21",
        language="bash",
    )
    st.stop()

files = sorted(HISTORICAL_DIR.glob("*.csv"))
if not files:
    st.warning("No historical context CSV files found yet.")
    st.code(
        "python -m parkflow.data.historical_context --year 2026 --collect-calendar --start-date 2026-01-01 --end-date 2026-05-21",
        language="bash",
    )
    st.stop()

selected = st.selectbox(
    "Historical/context file",
    files,
    format_func=lambda p: str(p.relative_to(PROJECT_ROOT)),
)

df = pd.read_csv(selected)
st.caption(f"Using file: `{selected.relative_to(PROJECT_ROOT)}`")

col1, col2, col3 = st.columns(3)
col1.metric("Rows", f"{len(df):,}")
col2.metric("Columns", f"{len(df.columns):,}")
col3.metric("File", selected.name)

if "date" in df.columns:
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

if {"date", "crowd_level_pct"}.issubset(df.columns):
    st.subheader("Crowd level by day")
    chart_df = df.dropna(subset=["date", "crowd_level_pct"]).copy()
    if chart_df.empty:
        st.info("No crowd-level values available in this file.")
    else:
        fig = px.line(
            chart_df,
            x="date",
            y="crowd_level_pct",
            markers=True,
            color="crowd_label" if "crowd_label" in chart_df.columns else None,
            title="Historical crowd-calendar context",
            labels={"date": "Date", "crowd_level_pct": "Crowd level (%)", "crowd_label": "Crowd label"},
        )
        st.plotly_chart(fig, width="stretch")

if {"open_time", "close_time"}.issubset(df.columns):
    st.subheader("Operating-hours context")
    st.dataframe(
        df[[col for col in ["date", "operating_hours", "open_time", "close_time", "crowd_level_pct", "crowd_label"] if col in df.columns]],
        width="stretch",
        hide_index=True,
    )

st.subheader("Raw table")
st.dataframe(df, width="stretch", hide_index=True)

st.caption(
    "Interpretation note: these files are useful for context and documentation, but the model/EDA should rely on row-level snapshots collected by ParkFlow."
)
