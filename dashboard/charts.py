from __future__ import annotations

import logging
from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from dashboard.styles import COLORS, DANGER, DARK, GRAY, PRIMARY, SUCCESS, WARNING

logger = logging.getLogger(__name__)


def _default_layout(
    title: str,
    xlabel: str | None = None,
    ylabel: str | None = None,
    height: int = 300,
) -> dict[str, Any]:
    """Return a shared layout dict applied to every chart.

    Args:
        title: Chart title.
        xlabel: X-axis label.
        ylabel: Y-axis label.
        height: Chart height in pixels.

    Returns:
        Layout keyword arguments for fig.update_layout().
    """
    layout: dict[str, Any] = {
        "title": dict(text=title, font=dict(size=14, color=DARK), x=0, xanchor="left"),
        "height": height,
        "margin": dict(l=10, r=10, t=32, b=24),
        "plot_bgcolor": "rgba(0,0,0,0)",
        "paper_bgcolor": "rgba(0,0,0,0)",
        "font": dict(color=GRAY, size=11),
        "hovermode": "x unified",
        "xaxis": dict(
            title=dict(text=xlabel, font=dict(size=11)),
            tickfont=dict(size=10),
            showgrid=True,
            gridcolor="rgba(0,0,0,0.06)",
        ),
        "yaxis": dict(
            title=dict(text=ylabel, font=dict(size=11)),
            tickfont=dict(size=10),
            showgrid=True,
            gridcolor="rgba(0,0,0,0.06)",
        ),
    }
    return layout


def retry_distribution(df: pd.DataFrame) -> go.Figure:
    """Histogram of retry_count across all evaluations.

    Args:
        df: Filtered evaluation records DataFrame.

    Returns:
        Plotly histogram figure.
    """
    fig = px.histogram(
        df,
        x="retry_count",
        nbins=max(1, int(df["retry_count"].nunique())),
        color_discrete_sequence=[PRIMARY],
        labels={"retry_count": "Retries", "count": "Tickets"},
    )
    fig.update_traces(
        marker=dict(line=dict(width=0.5, color="white")),
        hovertemplate="Retries: %{x}<br>Tickets: %{y}<extra></extra>",
    )
    fig.update_layout(**_default_layout("Retry Distribution", xlabel="Retry Count", ylabel="Tickets"))
    return fig


def repair_success_chart(df: pd.DataFrame) -> go.Figure:
    """Bar chart of repair success vs failure for repairs that were attempted.

    Args:
        df: Filtered evaluation records DataFrame.

    Returns:
        Plotly bar figure.
    """
    repaired = df[df["repair_attempted"]]
    if repaired.empty:
        fig = go.Figure()
        fig.add_annotation(text="No repair attempts in filtered data", showarrow=False)
        fig.update_layout(**_default_layout("Repair Success"))
        return fig
    counts = repaired["repair_success"].value_counts().reindex([True, False], fill_value=0)
    labels = ["Success", "Failed"]
    colors = [SUCCESS, DANGER]
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=labels,
            y=counts.values,
            marker_color=colors,
            text=counts.values,
            textposition="outside",
            hovertemplate="%{x}: %{y}<extra></extra>",
        )
    )
    fig.update_layout(
        **_default_layout("Repair Success", xlabel="Outcome", ylabel="Tickets"),
        yaxis=dict(range=[0, counts.max() * 1.2]),
    )
    return fig


def failure_types_chart(df: pd.DataFrame) -> go.Figure:
    """Horizontal bar chart of failure reason counts.

    Args:
        df: Filtered evaluation records DataFrame.

    Returns:
        Plotly horizontal bar figure.
    """
    col = df["failure_reason"].dropna()
    if col.empty:
        fig = go.Figure()
        fig.add_annotation(text="No failures in filtered data", showarrow=False)
        fig.update_layout(**_default_layout("Failure Types"))
        return fig
    freq = col.value_counts().reset_index()
    freq.columns = ["reason", "count"]
    fig = px.bar(
        freq,
        x="count",
        y="reason",
        orientation="h",
        text="count",
        color_discrete_sequence=[DANGER],
        labels={"reason": "", "count": "Tickets"},
    )
    fig.update_traces(
        textposition="outside",
        marker=dict(line=dict(width=0)),
        hovertemplate="%{y}: %{x}<extra></extra>",
    )
    fig.update_layout(**_default_layout("Failure Types", xlabel="Tickets", ylabel=""), height=260)
    fig.update_yaxes(autorange="reversed")
    return fig


def latency_histogram(df: pd.DataFrame) -> go.Figure:
    """Histogram of latency_ms distribution.

    Args:
        df: Filtered evaluation records DataFrame.

    Returns:
        Plotly histogram figure.
    """
    fig = px.histogram(
        df,
        x="latency_ms",
        nbins=30,
        color_discrete_sequence=[PRIMARY],
        labels={"latency_ms": "Latency (ms)", "count": "Tickets"},
    )
    fig.update_traces(
        marker=dict(line=dict(width=0.5, color="white")),
        hovertemplate="Latency: %{x} ms<br>Tickets: %{y}<extra></extra>",
    )
    fig.update_layout(**_default_layout("Latency Distribution", xlabel="Latency (ms)", ylabel="Tickets"))
    return fig


def category_distribution_chart(df: pd.DataFrame) -> go.Figure:
    """Improved horizontal bar chart of predicted category distribution.

    Improves on the existing chart by adding percentage labels and
    a cleaner layout.

    Args:
        df: Filtered evaluation records DataFrame.

    Returns:
        Plotly horizontal bar figure.
    """
    col = df["predicted_category"].dropna()
    if col.empty:
        fig = go.Figure()
        fig.add_annotation(text="No category data in filtered records", showarrow=False)
        fig.update_layout(**_default_layout("Category Distribution"))
        return fig
    freq = col.value_counts().reset_index()
    freq.columns = ["category", "count"]
    total = freq["count"].sum()
    freq["pct"] = (freq["count"] / total * 100).round(1)
    freq["label"] = freq.apply(lambda r: f"{r['count']}  ({r['pct']}%)", axis=1)
    fig = px.bar(
        freq,
        x="count",
        y="category",
        orientation="h",
        color="category",
        color_discrete_map=COLORS,
        text="label",
        labels={"category": "", "count": "Tickets"},
    )
    fig.update_traces(
        textposition="outside",
        showlegend=False,
        marker=dict(line=dict(width=0)),
        hovertemplate="%{y}: %{x}<extra></extra>",
    )
    fig.update_layout(**_default_layout("Category Distribution", xlabel="Tickets", ylabel=""), height=280)
    fig.update_yaxes(autorange="reversed")
    return fig


def schema_valid_trend(daily: pd.DataFrame) -> go.Figure:
    """Line chart of schema valid rate over time.

    Args:
        daily: Pre-computed daily aggregate DataFrame with columns:
            ``date``, ``schema_valid_rate``.

    Returns:
        Plotly line figure.
    """
    fig = px.line(
        daily,
        x="date",
        y="schema_valid_rate",
        markers=True,
        color_discrete_sequence=[SUCCESS],
        labels={"date": "Date", "schema_valid_rate": "Valid Rate"},
    )
    fig.update_traces(
        hovertemplate="%{x}<br>Valid: %{y:.1%}<extra></extra>",
        line=dict(width=2),
    )
    fig.update_layout(
        **_default_layout("Schema Valid Trend", xlabel="Date", ylabel="Valid Rate"),
        yaxis=dict(tickformat=".0%", range=[0, 1]),
    )
    return fig


def field_accuracy_trend(daily: pd.DataFrame) -> go.Figure:
    """Line chart of average field accuracy over time.

    Args:
        daily: Pre-computed daily aggregate DataFrame with columns:
            ``date``, ``field_accuracy``.

    Returns:
        Plotly line figure.
    """
    da = daily.dropna(subset=["field_accuracy"])
    if da.empty:
        fig = go.Figure()
        fig.add_annotation(text="No field accuracy data available", showarrow=False)
        fig.update_layout(**_default_layout("Field Accuracy Trend"))
        return fig
    fig = px.line(
        da,
        x="date",
        y="field_accuracy",
        markers=True,
        color_discrete_sequence=[PRIMARY],
        labels={"date": "Date", "field_accuracy": "Avg Field Accuracy"},
    )
    fig.update_traces(
        hovertemplate="%{x}<br>Accuracy: %{y:.1%}<extra></extra>",
        line=dict(width=2),
    )
    fig.update_layout(
        **_default_layout("Field Accuracy Trend", xlabel="Date", ylabel="Avg Accuracy"),
        yaxis=dict(tickformat=".0%", range=[0, 1]),
    )
    return fig


def daily_performance_chart(daily: pd.DataFrame) -> go.Figure:
    """Multi-metric daily performance summary with shared x-axis.

    Displays four subplots stacked vertically:
        - Record count
        - Success rate
        - Average latency
        - Average retries

    Args:
        daily: Pre-computed daily aggregate DataFrame with columns:
            ``date``, ``total``, ``schema_valid_rate``,
            ``avg_latency_ms``, ``avg_retries``.

    Returns:
        Plotly figure with 4 subplots.
    """
    fig = make_subplots(
        rows=4,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.06,
        subplot_titles=("Records", "Success Rate", "Avg Latency (ms)", "Avg Retries"),
    )

    fig.add_trace(
        go.Scatter(
            x=daily["date"],
            y=daily["total"],
            mode="lines+markers",
            name="Records",
            line=dict(color=PRIMARY, width=2),
            hovertemplate="%{x}<br>Records: %{y}<extra></extra>",
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=daily["date"],
            y=daily["schema_valid_rate"],
            mode="lines+markers",
            name="Success Rate",
            line=dict(color=SUCCESS, width=2),
            hovertemplate="%{x}<br>Rate: %{y:.1%}<extra></extra>",
        ),
        row=2,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=daily["date"],
            y=daily["avg_latency_ms"],
            mode="lines+markers",
            name="Avg Latency",
            line=dict(color=WARNING, width=2),
            hovertemplate="%{x}<br>Latency: %{y:.0f} ms<extra></extra>",
        ),
        row=3,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=daily["date"],
            y=daily["avg_retries"],
            mode="lines+markers",
            name="Avg Retries",
            line=dict(color=DANGER, width=2),
            hovertemplate="%{x}<br>Retries: %{y:.2f}<extra></extra>",
        ),
        row=4,
        col=1,
    )

    fig.update_layout(
        title=dict(
            text="Daily Performance Summary",
            font=dict(size=14, color=DARK),
            x=0,
            xanchor="left",
        ),
        height=520,
        margin=dict(l=10, r=10, t=36, b=10),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color=GRAY, size=10),
        hovermode="x unified",
        showlegend=False,
    )

    for row in range(1, 5):
        fig.update_xaxes(
            row=row,
            col=1,
            showgrid=True,
            gridcolor="rgba(0,0,0,0.06)",
            tickfont=dict(size=9),
        )
        fig.update_yaxes(
            row=row,
            col=1,
            showgrid=True,
            gridcolor="rgba(0,0,0,0.06)",
            tickfont=dict(size=9),
        )

    fig.update_yaxes(row=2, col=1, tickformat=".0%", range=[0, 1])
    return fig
