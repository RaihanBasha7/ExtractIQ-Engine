from __future__ import annotations

import logging
from typing import Any

import streamlit as st

from dashboard.styles import DARK, INFO, PRIMARY, SUCCESS

logger = logging.getLogger(__name__)


def render_header(
    total_records: int,
    model_name: str | None,
    provider: str | None,
    last_updated: str | None,
) -> None:
    """Render the top header bar with title, subtitle, and metadata."""
    st.markdown('<div class="main-header">', unsafe_allow_html=True)
    st.markdown("<h1>ExtractIQ Engine</h1>", unsafe_allow_html=True)
    st.markdown(
        '<p class="subtitle">Structured Extraction Evaluation Harness</p>',
        unsafe_allow_html=True,
    )
    parts: list[str] = []
    if last_updated:
        parts.append(
            f'<span class="meta-item">Last Updated: <strong>{last_updated}</strong></span>'
        )
    parts.append(
        f'<span class="meta-item">Total Records: <strong>{total_records}</strong></span>'
    )
    if model_name:
        parts.append(
            f'<span class="meta-item">Model: <strong>{model_name}</strong></span>'
        )
    if provider:
        parts.append(
            f'<span class="meta-item">Provider: <strong>{provider}</strong></span>'
        )
    meta_html = f'<div class="header-meta">{"".join(parts)}</div>'
    st.markdown(meta_html, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


def render_kpi_row(
    metrics: dict[str, Any],
    deltas: dict[str, Any] | None = None,
) -> None:
    """Render a responsive grid of KPI metric cards.

    Args:
        metrics: Dict of computed KPI values from compute_metrics.
        deltas: Optional dict of delta strings from compute_deltas.
    """
    deltas = deltas or {}
    cards = [
        {
            "icon": "\u2713",
            "value": f"{metrics['schema_valid_rate']:.1%}",
            "label": "Schema Valid",
            "desc": "Extractions passing schema validation.",
            "delta": deltas.get("schema_valid_rate"),
            "color": SUCCESS,
        },
        {
            "icon": "\u25CB",
            "value": (
                f"{metrics['field_accuracy']:.1%}"
                if metrics.get("field_accuracy")
                else "\u2014"
            ),
            "label": "Field Accuracy",
            "desc": "Average fraction of matched fields.",
            "delta": deltas.get("field_accuracy"),
            "color": PRIMARY,
        },
        {
            "icon": "\u21BB",
            "value": f"{metrics['repair_success_rate']:.1%}",
            "label": "Repair Success",
            "desc": "Repair attempts yielding valid output.",
            "delta": deltas.get("repair_success_rate"),
            "color": INFO,
        },
        {
            "icon": "\u23F1",
            "value": f"{metrics['avg_latency_ms']:.0f} ms",
            "label": "Average Latency",
            "desc": "Mean extraction time.",
            "delta": deltas.get("avg_latency_ms"),
            "color": DARK,
        },
        {
            "icon": "\u27F3",
            "value": f"{metrics['avg_retries']:.2f}",
            "label": "Average Retries",
            "desc": "Mean retry attempts per extraction.",
            "delta": deltas.get("avg_retries"),
            "color": DARK,
        },
        {
            "icon": "\u26A0",
            "value": str(metrics["infra_errors"]),
            "label": "Infrastructure Errors",
            "desc": "Rate limits, timeouts, provider errors.",
            "delta": deltas.get("infra_errors"),
            "color": "#F59E0B",
        },
        {
            "icon": "\u2717",
            "value": str(metrics["extraction_failures"]),
            "label": "Extraction Failures",
            "desc": "Failed extractions after all retries.",
            "delta": deltas.get("extraction_failures"),
            "color": "#EF4444",
        },
    ]
    st.markdown(
        '<div class="kpi-grid">', unsafe_allow_html=True
    )
    for card in cards:
        _kpi_card(**card)
    st.markdown("</div>", unsafe_allow_html=True)


def _kpi_card(
    icon: str,
    value: str,
    label: str,
    desc: str,
    delta: str | None = None,
    color: str = DARK,
) -> None:
    """Render a single KPI metric card.

    Args:
        icon: Emoji or symbol for the card header.
        value: Formatted metric value as a string.
        label: Short uppercase label.
        desc: One-line description.
        delta: Optional delta string (e.g. "+5.2%").
        color: Accent color for the icon and value.
    """
    delta_class = "neutral"
    if delta:
        if delta.startswith("+"):
            delta_class = "positive"
        elif delta.startswith("-"):
            delta_class = "negative"

    delta_html = ""
    if delta and delta != "\u2014":
        arrow = "\u2191" if delta_class == "positive" else "\u2193"
        delta_html = (
            f'<div class="kpi-footer">'
            f'<span class="kpi-delta {delta_class}">{arrow} {delta}</span>'
            f'</div>'
        )

    st.markdown(
        f"""
<div class="kpi-card">
    <div class="kpi-top">
        <div class="kpi-icon" style="color:{color};">{icon}</div>
    </div>
    <div class="kpi-value" style="color:{color};">{value}</div>
    <div class="kpi-label">{label}</div>
    <div class="kpi-desc">{desc}</div>
    {delta_html}
</div>
""",
        unsafe_allow_html=True,
    )


def render_recent_table(df: pd.DataFrame) -> None:
    """Render an interactive dataframe of recent evaluation records.

    Args:
        df: Evaluation records DataFrame, pre-sorted by timestamp descending.
    """
    if df.empty:
        st.info("No evaluation records to display.")
        return
    display_cols = [
        "ticket_id",
        "predicted_category",
        "latency_ms",
        "retry_count",
        "schema_valid",
        "repair_success",
        "failure_reason",
        "timestamp",
    ]
    present = [c for c in display_cols if c in df.columns]
    view = df[present].copy()
    view["schema_valid"] = view["schema_valid"].map({True: "\u2713", False: "\u2717"})
    if "repair_success" in view.columns:
        view["repair_success"] = (
            view["repair_success"].map({True: "\u2713", False: "\u2717"}).fillna("\u2014")
        )
    if "failure_reason" in view.columns:
        view["failure_reason"] = view["failure_reason"].fillna("\u2014")
    view["timestamp"] = view["timestamp"].dt.strftime("%Y-%m-%d %H:%M UTC")
    rename = {
        "ticket_id": "Ticket ID",
        "predicted_category": "Category",
        "latency_ms": "Latency (ms)",
        "retry_count": "Retries",
        "schema_valid": "Valid",
        "repair_success": "Repair",
        "failure_reason": "Failure Reason",
        "timestamp": "Timestamp",
    }
    view = view.rename(columns=rename)
    st.dataframe(
        view,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Latency (ms)": st.column_config.NumberColumn(format="%d"),
            "Retries": st.column_config.NumberColumn(format="%d"),
        },
    )
