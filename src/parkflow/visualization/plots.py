from __future__ import annotations

import pandas as pd
import plotly.express as px


def plot_average_wait_by_ride(df: pd.DataFrame):
    summary = (
        df[df["is_open"] == True]  # noqa: E712
        .groupby("ride_name", as_index=False)["wait_time"]
        .mean()
        .sort_values("wait_time", ascending=False)
    )
    return px.bar(summary, x="wait_time", y="ride_name", orientation="h", title="Average wait time by ride")


def plot_hourly_heatmap(df: pd.DataFrame):
    pivot = df.pivot_table(index="ride_name", columns="hour", values="wait_time", aggfunc="mean")
    return px.imshow(pivot, aspect="auto", title="Average wait time heatmap: ride × hour")
