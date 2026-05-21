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
    build_wait_time_availability,
    filter_queue_pressure_records,
    prepare_queue_dataset,
)

WAIT_TIME_COLORSCALE = [
    [0.00, "#2FBF71"],  # low wait: green
    [0.35, "#F7D154"],  # moderate wait: yellow
    [0.65, "#F28E2B"],  # high wait: orange
    [1.00, "#D7263D"],  # very high wait: red
]
OBSERVATION_COLORSCALE = [
    [0.00, "#E8F1F2"],
    [0.45, "#72B7B2"],
    [1.00, "#2F4B7C"],
]
BAR_COLOR = "#4ECDC4"
LINE_COLOR = "#4ECDC4"
ZERO_LINE_COLOR = "rgba(255,255,255,0.35)"


def _dynamic_height(n_rows: int, min_height: int = 420, row_height: int = 30, extra: int = 170) -> int:
    """Return a chart height that keeps y-axis labels visible."""

    return max(min_height, min(1100, int(extra + max(n_rows, 1) * row_height)))


def _transparent_layout(fig: go.Figure, height: int | None = None) -> go.Figure:
    """Apply a consistent dashboard-friendly layout."""

    fig.update_layout(
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=30, t=70, b=45),
        font=dict(size=13),
        legend_title_text="",
    )
    fig.update_xaxes(showgrid=True, gridcolor="rgba(255,255,255,0.08)", zerolinecolor=ZERO_LINE_COLOR)
    fig.update_yaxes(showgrid=False, automargin=True)
    return fig


def _force_all_y_labels(fig: go.Figure, labels: list[str]) -> go.Figure:
    """Prevent Plotly from hiding categorical y-axis labels in dense bar charts."""

    fig.update_yaxes(tickmode="array", tickvals=labels, ticktext=labels, automargin=True)
    return fig


def empty_figure(title: str, message: str = "Not enough data yet") -> go.Figure:
    """Return a lightweight placeholder figure for empty/insufficient data."""

    fig = go.Figure()
    fig.update_layout(title=title, xaxis={"visible": False}, yaxis={"visible": False})
    fig.add_annotation(text=message, showarrow=False, x=0.5, y=0.5, xref="paper", yref="paper")
    return _transparent_layout(fig, height=360)


def plot_average_wait_by_ride(
    df: pd.DataFrame,
    top_n: int = 15,
    include_zero_only_attractions: bool = False,
    exclude_non_queue_candidates: bool = True,
):
    summary = build_attraction_summary(
        df,
        only_open=True,
        include_zero_only_attractions=include_zero_only_attractions,
        exclude_non_queue_candidates=exclude_non_queue_candidates,
    )
    if summary.empty:
        return empty_figure("Average wait by attraction", "No queue-pressure candidates under the current filters")

    chart = summary.head(top_n).sort_values("mean_wait", ascending=True)
    labels = chart["ride_name"].tolist()
    fig = px.bar(
        chart,
        x="mean_wait",
        y="ride_name",
        orientation="h",
        color="mean_wait",
        color_continuous_scale=WAIT_TIME_COLORSCALE,
        hover_data=[col for col in ["median_wait", "p90_wait", "max_wait", "observations", "open_rate", "mode_hint"] if col in chart],
        title=f"Top {min(top_n, len(chart))} attractions by average wait",
        labels={
            "mean_wait": "Average wait (min)",
            "ride_name": "Attraction",
            "median_wait": "Median wait",
            "p90_wait": "P90 wait",
            "max_wait": "Max wait",
            "observations": "Observations",
            "open_rate": "Open rate",
            "mode_hint": "Mode hint",
        },
    )
    fig.update_layout(coloraxis_colorbar_title="Mean wait")
    _force_all_y_labels(fig, labels)
    return _transparent_layout(fig, height=_dynamic_height(len(chart)))


def plot_p90_wait_by_ride(
    df: pd.DataFrame,
    top_n: int = 15,
    include_zero_only_attractions: bool = False,
    exclude_non_queue_candidates: bool = True,
):
    summary = build_attraction_summary(
        df,
        only_open=True,
        include_zero_only_attractions=include_zero_only_attractions,
        exclude_non_queue_candidates=exclude_non_queue_candidates,
    )
    if summary.empty:
        return empty_figure("P90 wait by attraction", "No queue-pressure candidates under the current filters")

    chart = summary.head(top_n).sort_values("p90_wait", ascending=True)
    labels = chart["ride_name"].tolist()
    fig = px.bar(
        chart,
        x="p90_wait",
        y="ride_name",
        orientation="h",
        color="p90_wait",
        color_continuous_scale=WAIT_TIME_COLORSCALE,
        hover_data=[col for col in ["mean_wait", "median_wait", "max_wait", "observations", "mode_hint"] if col in chart],
        title=f"Top {min(top_n, len(chart))} attractions by p90 wait",
        labels={"p90_wait": "P90 wait (min)", "ride_name": "Attraction"},
    )
    fig.update_layout(coloraxis_colorbar_title="P90 wait")
    _force_all_y_labels(fig, labels)
    return _transparent_layout(fig, height=_dynamic_height(len(chart)))


def plot_hourly_heatmap(
    df: pd.DataFrame,
    metric: str = "mean_wait",
    top_n: int | None = 20,
    include_zero_only_attractions: bool = False,
    exclude_non_queue_candidates: bool = True,
):
    matrix = build_heatmap_matrix(
        df,
        metric=metric,
        only_open=True,
        include_zero_only_attractions=include_zero_only_attractions,
        exclude_non_queue_candidates=exclude_non_queue_candidates,
        top_n=top_n,
    )
    if matrix.empty:
        return empty_figure("Operational heatmap: attraction × hour", "No queue-pressure candidates under the current filters")

    metric_labels = {
        "mean_wait": "Mean wait (min)",
        "median_wait": "Median wait (min)",
        "p90_wait": "P90 wait (min)",
        "max_wait": "Max wait (min)",
        "observations": "Observations",
    }
    label = metric_labels.get(metric, "Wait time")
    x_labels = [f"{int(hour):02d}:00" if pd.notna(hour) else "unknown" for hour in matrix.columns]
    y_labels = matrix.index.astype(str).tolist()
    values = matrix.astype(float).values
    colorscale = OBSERVATION_COLORSCALE if metric == "observations" else WAIT_TIME_COLORSCALE

    fig = go.Figure(
        data=go.Heatmap(
            z=values,
            x=x_labels,
            y=y_labels,
            colorscale=colorscale,
            colorbar=dict(title=label),
            hovertemplate="Attraction: %{y}<br>Hour: %{x}<br>" + label + ": %{z:.1f}<extra></extra>",
            zsmooth=False,
        )
    )
    fig.update_layout(title="Operational heatmap: attraction × local hour")
    fig.update_xaxes(title="Local hour", type="category", tickmode="array", tickvals=x_labels, ticktext=x_labels)
    fig.update_yaxes(title="Attraction", tickmode="array", tickvals=y_labels, ticktext=y_labels, automargin=True)
    return _transparent_layout(fig, height=_dynamic_height(len(y_labels), min_height=460, row_height=31, extra=180))


def plot_hourly_wait_profile(
    df: pd.DataFrame,
    include_zero_only_attractions: bool = False,
    exclude_non_queue_candidates: bool = True,
):
    hourly = build_hourly_summary(
        df,
        only_open=True,
        include_zero_only_attractions=include_zero_only_attractions,
        exclude_non_queue_candidates=exclude_non_queue_candidates,
    )
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
    fig.update_traces(line=dict(width=3), marker=dict(size=8))
    fig.update_xaxes(dtick=1)
    return _transparent_layout(fig, height=430)


def plot_wait_distribution(
    df: pd.DataFrame,
    rides: list[str] | None = None,
    include_zero_only_attractions: bool = False,
    exclude_non_queue_candidates: bool = True,
):
    data = filter_queue_pressure_records(
        df,
        rides=rides,
        only_open=True,
        require_wait_time=True,
        include_zero_only_attractions=include_zero_only_attractions,
        exclude_non_queue_candidates=exclude_non_queue_candidates,
    )
    if data.empty:
        return empty_figure("Wait-time distribution")

    ride_order = data.groupby("ride_name")["wait_time"].median().sort_values(ascending=True).index.tolist()
    fig = px.box(
        data,
        x="wait_time",
        y="ride_name",
        category_orders={"ride_name": ride_order},
        points="all",
        title="Wait-time distribution by attraction",
        labels={"wait_time": "Wait time (min)", "ride_name": "Attraction"},
    )
    _force_all_y_labels(fig, ride_order)
    return _transparent_layout(fig, height=_dynamic_height(len(ride_order)))


def plot_attraction_time_series(
    df: pd.DataFrame,
    ride_name: str | None = None,
    include_zero_only_attractions: bool = True,
    exclude_non_queue_candidates: bool = True,
):
    ts = build_time_series_summary(
        df,
        ride_name=ride_name,
        only_open=True,
        include_zero_only_attractions=include_zero_only_attractions,
        exclude_non_queue_candidates=exclude_non_queue_candidates,
    )
    if ts.empty:
        title = f"Wait-time time series: {ride_name}" if ride_name else "Wait-time time series"
        return empty_figure(title)

    if ride_name:
        fig = px.line(
            ts,
            x="analysis_timestamp_local",
            y="mean_wait",
            markers=True,
            title=f"Wait-time time series: {ride_name}",
            labels={"analysis_timestamp_local": "Local timestamp", "mean_wait": "Mean wait (min)"},
        )
        fig.update_traces(line=dict(width=3, color=LINE_COLOR), marker=dict(size=8))
        return _transparent_layout(fig, height=430)

    fig = px.line(
        ts,
        x="analysis_timestamp_local",
        y="mean_wait",
        color="ride_name",
        markers=True,
        title="Wait-time time series by attraction",
        labels={"analysis_timestamp_local": "Local timestamp", "mean_wait": "Mean wait (min)", "ride_name": "Attraction"},
    )
    fig.update_traces(line=dict(width=2), marker=dict(size=7))
    return _transparent_layout(fig, height=520)


def plot_weather_wait_comparison(
    df: pd.DataFrame,
    include_zero_only_attractions: bool = False,
    exclude_non_queue_candidates: bool = True,
):
    summary = build_weather_summary(
        df,
        only_open=True,
        include_zero_only_attractions=include_zero_only_attractions,
        exclude_non_queue_candidates=exclude_non_queue_candidates,
    )
    if summary.empty:
        return empty_figure("Weather × wait-time comparison", "Weather fields are not available or coverage is too small")

    fig = px.bar(
        summary,
        x="bucket_value",
        y="mean_wait",
        color="mean_wait",
        color_continuous_scale=WAIT_TIME_COLORSCALE,
        facet_col="weather_dimension",
        hover_data=["observations", "p90_wait"],
        title="Exploratory weather comparison",
        labels={"bucket_value": "Weather bucket", "mean_wait": "Mean wait (min)", "weather_dimension": "Weather dimension"},
    )
    return _transparent_layout(fig, height=430)


def plot_temperature_vs_wait(
    df: pd.DataFrame,
    include_zero_only_attractions: bool = False,
    exclude_non_queue_candidates: bool = True,
):
    data = filter_queue_pressure_records(
        df,
        only_open=True,
        require_wait_time=True,
        include_zero_only_attractions=include_zero_only_attractions,
        exclude_non_queue_candidates=exclude_non_queue_candidates,
    )
    if data.empty or not {"temperature_2m", "wait_time"}.issubset(data.columns) or data["temperature_2m"].notna().sum() < 2:
        return empty_figure("Temperature × wait time", "Temperature data is not available yet")

    fig = px.scatter(
        data,
        x="temperature_2m",
        y="wait_time",
        color="wait_time",
        color_continuous_scale=WAIT_TIME_COLORSCALE,
        hover_data=[col for col in ["ride_name", "hour", "precipitation"] if col in data.columns],
        title="Temperature × wait time",
        labels={"temperature_2m": "Temperature (°C)", "wait_time": "Wait time (min)"},
    )
    fig.update_traces(marker=dict(size=9, opacity=0.85))
    return _transparent_layout(fig, height=460)


def plot_wait_time_reporting_by_ride(df: pd.DataFrame, top_n: int | None = None):
    availability = build_wait_time_availability(df)
    if availability.empty:
        return empty_figure("Wait-time reporting by attraction")

    chart = availability.sort_values(["wait_time_reported_rate", "positive_wait_records"], ascending=[True, True])
    if top_n:
        chart = chart.head(top_n)
    labels = chart["ride_name"].tolist()
    fig = px.bar(
        chart,
        x="wait_time_reported_rate",
        y="ride_name",
        orientation="h",
        color="wait_time_reported_rate",
        color_continuous_scale=OBSERVATION_COLORSCALE,
        hover_data=[
            col
            for col in [
                "records",
                "wait_time_reported_records",
                "missing_wait_time_records",
                "positive_wait_records",
                "max_reported_wait",
                "open_rate",
                "mode_hint",
                "queue_pressure_exclusion_reason",
                "zero_only_reported_wait",
            ]
            if col in chart
        ],
        title="Wait-time reporting rate by attraction",
        labels={
            "wait_time_reported_rate": "Reported wait-time rate",
            "ride_name": "Attraction",
            "records": "Records",
            "wait_time_reported_records": "Reported wait records",
            "missing_wait_time_records": "Missing wait records",
            "positive_wait_records": "Positive wait records",
            "max_reported_wait": "Max reported wait",
            "open_rate": "Open rate",
            "mode_hint": "Mode hint",
            "queue_pressure_exclusion_reason": "Queue chart rule",
            "zero_only_reported_wait": "Zero-only reported wait",
        },
    )
    _force_all_y_labels(fig, labels)
    fig.update_layout(coloraxis_colorbar_title="Report rate")
    return _transparent_layout(fig, height=_dynamic_height(len(chart)))
