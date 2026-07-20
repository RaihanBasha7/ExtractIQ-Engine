from __future__ import annotations

import logging
from typing import Any

import pandas as pd
import streamlit as st

from dashboard.charts import (
    category_distribution_chart,
    daily_performance_chart,
    failure_types_chart,
    field_accuracy_trend,
    latency_histogram,
    repair_success_chart,
    retry_distribution,
    schema_valid_trend,
)

logger = logging.getLogger(__name__)


@st.cache_data(ttl=30)
def _compute_daily_aggregates(df: pd.DataFrame) -> pd.DataFrame:
    """Pre-compute daily aggregate metrics from evaluation records.

    The result is cached with a 30-second TTL so that all trend charts
    share the same grouped computation.

    Args:
        df: Filtered evaluation records DataFrame.

    Returns:
        DataFrame grouped by ``date`` with columns:
            ``total``, ``schema_valid_rate``, ``field_accuracy``,
            ``avg_latency_ms``, ``avg_retries``.
    """
    if df.empty:
        return pd.DataFrame()

    grouped = df.groupby("date", sort=True)
    daily = grouped.agg(
        total=("ticket_id", "count"),
        schema_valid_rate=("schema_valid", "mean"),
        field_accuracy=("field_accuracy", "mean"),
        avg_latency_ms=("latency_ms", "mean"),
        avg_retries=("retry_count", "mean"),
    ).reset_index()
    daily["schema_valid_rate"] = daily["schema_valid_rate"].round(4)
    daily["field_accuracy"] = daily["field_accuracy"].round(4)
    daily["avg_latency_ms"] = daily["avg_latency_ms"].round(1)
    daily["avg_retries"] = daily["avg_retries"].round(2)
    logger.info("Computed daily aggregates for %d dates", len(daily))
    return daily


def _render_executive_summary(df: pd.DataFrame) -> None:
    """Render a compact executive summary bar with 7 key metrics.

    Args:
        df: Filtered evaluation records DataFrame.
    """
    total = len(df)
    avg_schema_valid = df["schema_valid"].mean()
    avg_field_acc = df["field_accuracy"].dropna().mean()

    cat_perf = df.groupby("predicted_category")["schema_valid"].mean().dropna()
    best_cat = cat_perf.idxmax() if not cat_perf.empty else "\u2014"
    worst_cat = cat_perf.idxmin() if not cat_perf.empty else "\u2014"

    fail_reason = df["failure_reason"].dropna()
    top_fail = fail_reason.mode().iloc[0] if not fail_reason.empty else "\u2014"

    highest_latency = int(df["latency_ms"].max())

    items = [
        ("Total Records", str(total)),
        ("Best Category", best_cat),
        ("Worst Category", worst_cat),
        ("Top Failure", top_fail),
        ("Highest Latency", f"{highest_latency} ms"),
        ("Avg Schema Valid", f"{avg_schema_valid:.1%}"),
        ("Avg Field Acc", f"{avg_field_acc:.1%}" if pd.notna(avg_field_acc) else "\u2014"),
    ]

    html_parts = []
    for label, value in items:
        html_parts.append(
            f'<div class="exec-item">'
            f'<div class="exec-label">{label}</div>'
            f'<div class="exec-value">{value}</div>'
            f"</div>"
        )
    st.markdown(
        f'<div class="exec-summary">{"".join(html_parts)}</div>',
        unsafe_allow_html=True,
    )


def _render_insight_cards(df: pd.DataFrame) -> None:
    """Render 4 insight cards highlighting outlier records and patterns.

    Args:
        df: Filtered evaluation records DataFrame.
    """
    idx_max_retry = df["retry_count"].idxmax()
    highest_retry_ticket = df.loc[idx_max_retry, "ticket_id"]
    highest_retry_val = int(df.loc[idx_max_retry, "retry_count"])

    idx_max_lat = df["latency_ms"].idxmax()
    slowest_ticket = df.loc[idx_max_lat, "ticket_id"]
    slowest_val = int(df.loc[idx_max_lat, "latency_ms"])

    fail_reason = df["failure_reason"].dropna()
    most_common_fail = fail_reason.mode().iloc[0] if not fail_reason.empty else "\u2014"
    fail_count = fail_reason.value_counts().iloc[0] if not fail_reason.empty else 0

    cats = df["predicted_category"].dropna()
    most_common_cat = cats.mode().iloc[0] if not cats.empty else "\u2014"
    cat_count = cats.value_counts().iloc[0] if not cats.empty else 0

    cards = [
        ("Highest Retry", highest_retry_ticket, f"{highest_retry_val} retries"),
        ("Slowest Ticket", slowest_ticket, f"{slowest_val} ms"),
        ("Most Common Failure", most_common_fail, f"{fail_count} occurrences"),
        ("Most Common Category", most_common_cat, f"{cat_count} tickets"),
    ]

    html_parts = []
    for label, value, detail in cards:
        html_parts.append(
            f'<div class="insight-card">'
            f'<div class="insight-label">{label}</div>'
            f'<div class="insight-value">{value}</div>'
            f'<div class="insight-detail">{detail}</div>'
            f"</div>"
        )
    st.markdown(
        f'<div class="insight-grid">{"".join(html_parts)}</div>',
        unsafe_allow_html=True,
    )


def render_analytics_section(df: pd.DataFrame) -> None:
    """Render the full analytics section.

    Shows executive summary, insight cards, and 8 analytics charts.
    Accepts the already-filtered DataFrame so sidebar filters are
    automatically respected.

    Args:
        df: Filtered evaluation records DataFrame.
    """
    if df.empty:
        st.info("No data available for analytics.")
        return

    st.markdown("## Extraction Analytics")

    _render_executive_summary(df)
    _render_insight_cards(df)

    with st.spinner("Computing analytics..."):
        daily = _compute_daily_aggregates(df)

    # Row 1: Retry Distribution + Latency Histogram
    col1, col2 = st.columns(2)
    with col1:
        fig_retry = retry_distribution(df)
        st.plotly_chart(fig_retry, use_container_width=True)
    with col2:
        fig_latency = latency_histogram(df)
        st.plotly_chart(fig_latency, use_container_width=True)

    # Row 2: Repair Success + Failure Types
    col1, col2 = st.columns(2)
    with col1:
        fig_repair = repair_success_chart(df)
        st.plotly_chart(fig_repair, use_container_width=True)
    with col2:
        fig_fail = failure_types_chart(df)
        st.plotly_chart(fig_fail, use_container_width=True)

    # Row 3: Category Distribution (improved) — full width
    fig_cat = category_distribution_chart(df)
    st.plotly_chart(fig_cat, use_container_width=True)

    # Row 4: Schema Valid Trend + Field Accuracy Trend
    col1, col2 = st.columns(2)
    with col1:
        fig_schema = schema_valid_trend(daily)
        st.plotly_chart(fig_schema, use_container_width=True)
    with col2:
        fig_acc = field_accuracy_trend(daily)
        st.plotly_chart(fig_acc, use_container_width=True)

    # Row 5: Daily Performance Summary — full width
    fig_daily = daily_performance_chart(daily)
    st.plotly_chart(fig_daily, use_container_width=True)
