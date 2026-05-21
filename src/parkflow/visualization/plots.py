from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from parkflow.analysis.eda import (
    build_attraction_summary,
    build_heatmap_matrix,
    build_hourly_summary,
    build_time_series_summary,
    build_weather_summary,
    prepare_queue_dataset,
)


def empty_figure(title: str, message: str = "Not enough data yet") -> go.Figure:
    """Return a lightweight placeholder figure for empty/insufficient data."""

    fig = go.Figure()
    fig.update_layout(title=title, xaxis={"visible": False}, yaxis={"visible": False})
    fig.add_annotation(text=message, showarrow=False, x=0.5, y=0.5, xref="paper", yref="paper")
    return fig


def plot_average_wait_by_ride(df: pd.DataFrame):
    summary = build_attraction_summary(df, only_open=True)
    if summary.empty:
        return empty_figure("Average wait by attraction")

    chart = summary.sort_values("mean_wait", ascending=True)
    return px.bar(
        chart,
        x="mean_wait",
        y="ride_name",
        orientation="h",
        hover_data=[col for col in ["median_wait", "p90_wait", "max_wait", "observations", "open_rate"] if col in chart],
        title="Average wait time by attraction",
        labels={
            "mean_wait": "Average wait (min)",
            "ride_name": "Attraction",
            "median_wait": "Median wait",
            "p90_wait": "P90 wait",
            "max_wait": "Max wait",
            "observations": "Observations",
            "open_rate": "Open rate",
        },
    )


def plot_p90_wait_by_ride(df: pd.DataFrame, top_n: int = 20):
    summary = build_attraction_summary(df, only_open=True)
    if summary.empty:
        return empty_figure("P90 wait by attraction")

    chart = summary.head(top_n).sort_values("p90_wait", ascending=True)
    return px.bar(
        chart,
        x="p90_wait",
        y="ride_name",
        orientation="h",
        hover_data=[col for col in ["mean_wait", "median_wait", "max_wait", "observations"] if col in chart],
        title=f"Top {min(top_n, len(chart))} attractions by p90 wait",
        labels={"p90_wait": "P90 wait (min)", "ride_name": "Attraction"},
    )


def plot_hourly_heatmap(df: pd.DataFrame, metric: str = "mean_wait"):
    matrix = build_heatmap_matrix(df, metric=metric, only_open=True)
    if matrix.empty:
        return empty_figure("Operational heatmap: attraction × hour")

    metric_labels = {
        "mean_wait": "Mean wait (min)",
        "median_wait": "Median wait (min)",
        "p90_wait": "P90 wait (min)",
        "max_wait": "Max wait (min)",
        "observations": "Observations",
    }
    return px.imshow(
        matrix,
        aspect="auto",
        title="Operational heatmap: attraction × local hour",
        labels={"x": "Local hour", "y": "Attraction", "color": metric_labels.get(metric, "Wait time")},
    )


def plot_hourly_wait_profile(df: pd.DataFrame):
    hourly = build_hourly_summary(df, only_open=True)
    if hourly.empty:
        return empty_figure("Hourly wait profile")

    fig = px.line(
        hourly,
        x="hour",
        y=[col for col in ["mean_wait", "median_wait", "p90_wait"] if col in hourly.columns],
        markers=True,
        title="Wait-time profile by local hour",
        labels={"hour": "Local hour", "value": "Wait time (min)", "variable": "Metric"},
    )
    fig.update_xaxes(dtick=1)
    return fig


def plot_wait_distribution(df: pd.DataFrame, rides: list[str] | None = None):
    data = prepare_queue_dataset(df)
    data = data[data["is_open_bool"].fillna(False)]
    if rides:
        data = data[data["ride_name"].isin(rides)]
    if data.empty:
        return empty_figure("Wait-time distribution")

    return px.box(
        data,
        x="wait_time",
        y="ride_name",
        points="all",
        title="Wait-time distribution by attraction",
        labels={"wait_time": "Wait time (min)", "ride_name": "Attraction"},
    )


def plot_attraction_time_series(df: pd.DataFrame, ride_name: str | None = None):
    ts = build_time_series_summary(df, ride_name=ride_name, only_open=True)
    if ts.empty:
        title = f"Wait-time time series: {ride_name}" if ride_name else "Wait-time time series"
        return empty_figure(title)

    if ride_name:
        return px.line(
            ts,
            x="analysis_timestamp_local",
            y="mean_wait",
            markers=True,
            title=f"Wait-time time series: {ride_name}",
            labels={"analysis_timestamp_local": "Local timestamp", "mean_wait": "Mean wait (min)"},
        )

    return px.line(
        ts,
        x="analysis_timestamp_local",
        y="mean_wait",
        color="ride_name",
        markers=True,
        title="Wait-time time series by attraction",
        labels={"analysis_timestamp_local": "Local timestamp", "mean_wait": "Mean wait (min)", "ride_name": "Attraction"},
    )


def plot_weather_wait_comparison(df: pd.DataFrame):
    summary = build_weather_summary(df, only_open=True)
    if summary.empty:
        return empty_figure("Weather × wait-time comparison", "Weather fields are not available or coverage is too small")

    return px.bar(
        summary,
        x="bucket_value",
        y="mean_wait",
        facet_col="weather_dimension",
        hover_data=["observations", "p90_wait"],
        title="Exploratory weather comparison",
        labels={"bucket_value": "Weather bucket", "mean_wait": "Mean wait (min)", "weather_dimension": "Weather dimension"},
    )


def plot_temperature_vs_wait(df: pd.DataFrame):
    data = prepare_queue_dataset(df)
    data = data[data["is_open_bool"].fillna(False)]
    if data.empty or not {"temperature_2m", "wait_time"}.issubset(data.columns) or data["temperature_2m"].notna().sum() < 2:
        return empty_figure("Temperature × wait time", "Temperature data is not available yet")

    return px.scatter(
        data,
        x="temperature_2m",
        y="wait_time",
        hover_data=[col for col in ["ride_name", "hour", "precipitation"] if col in data.columns],
        title="Temperature × wait time",
        labels={"temperature_2m": "Temperature (°C)", "wait_time": "Wait time (min)"},
    )
