from __future__ import annotations

import logging
import time
from datetime import datetime

import streamlit as st

from dashboard.analytics import render_analytics_section
from dashboard.components import (
    render_header,
    render_kpi_row,
    render_recent_table,
)
from dashboard.error_analysis import render_error_analysis_section
from dashboard.exporter import (
    export_category_performance,
    export_dataframe,
    export_failure_breakdown,
    export_field_analysis,
    export_metrics,
)
from dashboard.health import run_all_checks
from dashboard.loaders import (
    apply_filters,
    compute_deltas,
    compute_metrics,
    get_unique_values,
    load_data,
    split_run_data,
    summarize_filters,
)
from dashboard.styles import DANGER, GRAY, SUCCESS, WARNING, inject_css
from dashboard.error_analysis import compute_category_performance, compute_failure_breakdown, compute_field_error_summary

logger = logging.getLogger(__name__)


def _build_sidebar_filters(df: pd.DataFrame) -> dict:
    """Construct sidebar filter widgets and return their current values."""
    st.sidebar.markdown("## \u2699\uFE0F Filters")
    date_range: tuple[datetime, datetime] | None = None
    categories: list[str] | None = None
    schema_valid: bool | None = None
    repair_success: bool | None = None
    failure_types: list[str] | None = None
    models: list[str] | None = None
    providers: list[str] | None = None
    retry_range: tuple[int, int] | None = None
    search_query: str | None = None

    if not df.empty:
        min_d = df["timestamp"].min().to_pydatetime()
        max_d = df["timestamp"].max().to_pydatetime()
        date_range = st.sidebar.date_input(
            "Date Range",
            value=(min_d.date(), max_d.date()),
            min_value=min_d.date(),
            max_value=max_d.date(),
        )
        if isinstance(date_range, tuple) and len(date_range) == 2:
            lo, hi = date_range
            date_range = (
                datetime.combine(lo, datetime.min.time()),
                datetime.combine(hi, datetime.max.time()),
            )
        else:
            date_range = None

        cat_opts = get_unique_values(df, "predicted_category")
        if cat_opts:
            categories = st.sidebar.multiselect(
                "Issue Category", options=cat_opts, placeholder="All categories"
            )
            categories = categories or None

        st.sidebar.markdown("#### Status")
        col1, col2 = st.sidebar.columns(2)
        with col1:
            sv = st.sidebar.selectbox(
                "Schema Valid", options=["All", "Valid", "Invalid"]
            )
            schema_valid = {"All": None, "Valid": True, "Invalid": False}[sv]
        with col2:
            rs = st.sidebar.selectbox(
                "Repair Success", options=["All", "Success", "Failed"]
            )
            repair_success = {"All": None, "Success": True, "Failed": False}[rs]

        ft_opts = get_unique_values(df, "failure_reason")
        if ft_opts:
            failure_types = st.sidebar.multiselect(
                "Failure Type", options=ft_opts, placeholder="All types"
            )
            failure_types = failure_types or None

        st.sidebar.markdown("#### Model / Provider")
        m_opts = get_unique_values(df, "model_name")
        if m_opts:
            models = st.sidebar.multiselect(
                "Model", options=m_opts, placeholder="All models"
            )
            models = models or None
        p_opts = get_unique_values(df, "provider")
        if p_opts:
            providers = st.sidebar.multiselect(
                "Provider", options=p_opts, placeholder="All providers"
            )
            providers = providers or None

        max_retries = int(df["retry_count"].max()) if not df.empty else 10
        retry_range = st.sidebar.slider(
            "Retry Count",
            min_value=0,
            max_value=max_retries,
            value=(0, max_retries),
        )

        search_query = st.sidebar.text_input(
            "Search Ticket ID", placeholder="e.g. TKT-001"
        )
        search_query = search_query or None

    st.sidebar.markdown("---")
    if st.sidebar.button("\u21BB Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.sidebar.checkbox(
        "Auto-refresh every 30s",
        value=st.session_state.get("auto_refresh", False),
        key="auto_refresh",
    )

    return {
        "date_range": date_range,
        "categories": categories,
        "schema_valid": schema_valid,
        "repair_success": repair_success,
        "failure_types": failure_types,
        "models": models,
        "providers": providers,
        "retry_range": retry_range,
        "search_query": search_query,
    }


def _extract_meta(filtered: pd.DataFrame) -> tuple[int, str | None, str | None, str | None]:
    """Extract header metadata from the filtered DataFrame."""
    has_data = not filtered.empty
    total = len(filtered)
    model_name = (
        filtered["model_name"].dropna().iloc[0]
        if has_data and "model_name" in filtered.columns
        else None
    )
    provider = (
        filtered["provider"].dropna().iloc[0]
        if has_data and "provider" in filtered.columns
        else None
    )
    last_updated = None
    if has_data and "timestamp" in filtered.columns:
        last_ts = filtered["timestamp"].max()
        last_updated = last_ts.strftime("%Y-%m-%d %H:%M UTC")
    return total, model_name, provider, last_updated


def _render_health_indicator() -> None:
    """Run health checks and display a status badge in the sidebar."""
    health = run_all_checks(st.session_state.get("data_path"))
    color_map = {"healthy": SUCCESS, "warning": WARNING, "critical": DANGER}
    icons = {"healthy": "\u2713", "warning": "\u26A0", "critical": "\u2717"}
    status = health["overall"]
    color = color_map.get(status, GRAY)
    icon = icons.get(status, "?")
    st.sidebar.markdown("---")
    st.sidebar.markdown(
        f'<span style="color:{color};font-weight:600;">{icon} System: {status}</span>',
        unsafe_allow_html=True,
    )
    if status != "healthy":
        for check in health["checks"]:
            if check["status"] != "healthy":
                st.sidebar.caption(f"{check['status']}: {check['message']}")


def _render_export_section(df: pd.DataFrame, metrics: dict) -> None:
    """Render export buttons in the sidebar for filtered data and computed tables."""
    st.sidebar.markdown("#### Export")
    if st.sidebar.button("Export Filtered Data (CSV)", use_container_width=True):
        path = export_dataframe(df)
        if path:
            st.sidebar.success(f"Exported to {path}")
            logger.info("Export: filtered data -> %s", path)

    if st.sidebar.button("Export Metrics (JSON)", use_container_width=True):
        path = export_metrics(metrics)
        if path:
            st.sidebar.success(f"Exported to {path}")
            logger.info("Export: metrics -> %s", path)

    cat_perf = compute_category_performance(df)
    if not cat_perf.empty and st.sidebar.button("Export Category Perf (CSV)", use_container_width=True):
        path = export_category_performance(cat_perf)
        if path:
            st.sidebar.success(f"Exported to {path}")

    fail_breakdown = compute_failure_breakdown(df)
    if not fail_breakdown.empty and st.sidebar.button("Export Failure Breakdown (CSV)", use_container_width=True):
        path = export_failure_breakdown(fail_breakdown)
        if path:
            st.sidebar.success(f"Exported to {path}")

    field_summary = compute_field_error_summary(df)
    if not field_summary.empty and st.sidebar.button("Export Field Analysis (CSV)", use_container_width=True):
        path = export_field_analysis(field_summary)
        if path:
            st.sidebar.success(f"Exported to {path}")


def render_page(jsonl_path: str | None = None) -> None:
    """Render the full dashboard page.

    Orchestrates sidebar filters, data loading, metric computation,
    header rendering, KPI cards, analytics, error analysis, and
    the recent evaluations table.

    Args:
        jsonl_path: Path to evaluation_records.jsonl.
    """
    inject_css()
    st.session_state["data_path"] = jsonl_path

    # Track refresh timing
    refresh_start = time.monotonic()
    if "last_refresh" not in st.session_state:
        st.session_state["last_refresh"] = datetime.now().strftime("%H:%M:%S")

    df = load_data(jsonl_path)
    total_before = len(df)

    filters = _build_sidebar_filters(df)
    filtered = apply_filters(df, **filters)
    has_data = not filtered.empty

    # Record refresh
    refresh_duration = time.monotonic() - refresh_start
    st.session_state["last_refresh"] = datetime.now().strftime("%H:%M:%S")
    logger.info(
        "Dashboard refreshed: %d total, %d after filters (%.2fs)",
        total_before,
        len(filtered),
        refresh_duration,
    )

    total, model_name, provider, last_updated = _extract_meta(filtered)
    render_header(total, model_name, provider, last_updated)

    # Health indicator in sidebar
    _render_health_indicator()

    if not has_data:
        st.info(
            "\u2139\uFE0F No evaluation records found. Run the extraction pipeline "
            "to generate data, or check that the JSONL path is correct."
        )
        st.caption(
            f"Expected path: {jsonl_path}  |  "
            f"Last refresh: {st.session_state['last_refresh']}  |  "
            f"Refresh: {refresh_duration:.2f}s"
        )
        return

    with st.spinner("Computing metrics..."):
        metrics = compute_metrics(filtered)
        current_run, previous_run = split_run_data(filtered)
        prev_metrics = compute_metrics(previous_run) if previous_run is not None else None
        deltas = compute_deltas(metrics, prev_metrics)

    # Filter summary bar
    filter_summary = summarize_filters(filtered, total_before, **filters)
    data_size_kb = filtered.memory_usage(deep=True).sum() / 1024
    st.markdown(
        f'<div style="font-size:0.78rem;color:{GRAY};margin-bottom:0.5rem;">'
        f"{filter_summary}  |  Dataset: {data_size_kb:.1f} KB  |  "
        f"Refreshed: {st.session_state['last_refresh']} ({refresh_duration:.2f}s)"
        f"</div>",
        unsafe_allow_html=True,
    )

    st.markdown("### Key Metrics")
    render_kpi_row(metrics, deltas)

    # Export section in sidebar
    _render_export_section(filtered, metrics)

    render_analytics_section(filtered)
    render_error_analysis_section(filtered)

    st.markdown("### Recent Evaluations")
    render_recent_table(filtered.sort_values("timestamp", ascending=False))
