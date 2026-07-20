from __future__ import annotations

import logging
from collections import Counter
from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from dashboard.styles import COLORS, DANGER, DARK, GRAY, PRIMARY, SUCCESS, WARNING

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
#  1. Confusion Matrix
# ──────────────────────────────────────────────


def compute_confusion_matrix(df: pd.DataFrame) -> pd.DataFrame | None:
    """Build a confusion matrix from expected vs predicted category.

    Returns a DataFrame with categories as both index and columns,
    containing raw counts.  Returns None when either column is missing
    or the cross-tab would be empty.
    """
    needed = {"expected_category", "predicted_category"}
    if not needed.issubset(df.columns):
        return None
    sub = df[["expected_category", "predicted_category"]].dropna()
    if sub.empty:
        return None
    matrix = pd.crosstab(
        sub["expected_category"],
        sub["predicted_category"],
        rownames=["expected"],
        colnames=["predicted"],
    )
    return matrix


def confusion_matrix_heatmap(matrix: pd.DataFrame) -> go.Figure:
    """Render a confusion matrix as a Plotly heatmap with counts and percentages.

    Args:
        matrix: Crosstab DataFrame from compute_confusion_matrix.

    Returns:
        Plotly heatmap figure.
    """
    total = matrix.values.sum()
    pct_matrix = matrix / total  # cell-level percentage
    categories = list(matrix.index)
    z = matrix.values
    text: list[list[str]] = []
    for i in range(len(categories)):
        row_text: list[str] = []
        for j in range(len(categories)):
            count = z[i][j]
            pct = pct_matrix.values[i][j]
            row_text.append(f"{int(count)}<br>({pct:.1%})")
        text.append(row_text)

    fig = go.Figure(
        data=go.Heatmap(
            z=z,
            x=categories,
            y=categories,
            text=text,
            texttemplate="%{text}",
            textfont=dict(size=10),
            colorscale="Blues",
            hoverongaps=False,
            hovertemplate=(
                "Expected: %{y}<br>"
                "Predicted: %{x}<br>"
                "Count: %{z}<extra></extra>"
            ),
        )
    )
    fig.update_layout(
        title=dict(
            text="Confusion Matrix",
            font=dict(size=14, color=DARK),
            x=0,
            xanchor="left",
        ),
        xaxis=dict(title="Predicted Category", side="bottom", tickfont=dict(size=10)),
        yaxis=dict(title="Expected Category", tickfont=dict(size=10), autorange="reversed"),
        height=400,
        margin=dict(l=10, r=10, t=36, b=10),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    fig.update_xaxes(tickangle=30)
    return fig


# ──────────────────────────────────────────────
#  2. Category Performance Table
# ──────────────────────────────────────────────


def compute_category_performance(df: pd.DataFrame) -> pd.DataFrame:
    """Compute per-category accuracy, precision-like, and latency stats.

    For each expected_category:
        - total samples
        - correct predictions (predicted == expected)
        - accuracy %
        - false positives (predicted == this category but expected != it)
        - false negatives (expected == this category but predicted != it)
        - average latency and retries

    Returns:
        DataFrame sorted by accuracy ascending (worst first).
    """
    needed = {"expected_category", "predicted_category"}
    if not needed.issubset(df.columns):
        return pd.DataFrame()

    sub = df[["expected_category", "predicted_category", "latency_ms", "retry_count"]].dropna(
        subset=["expected_category", "predicted_category"]
    )
    if sub.empty:
        return pd.DataFrame()

    categories = sorted(
        set(sub["expected_category"].unique()) | set(sub["predicted_category"].unique())
    )
    rows: list[dict[str, Any]] = []
    for cat in categories:
        total = len(sub[sub["predicted_category"] == cat])
        correct = len(sub[(sub["expected_category"] == cat) & (sub["predicted_category"] == cat)])
        fp = len(sub[(sub["predicted_category"] == cat) & (sub["expected_category"] != cat)])
        fn = len(sub[(sub["expected_category"] == cat) & (sub["predicted_category"] != cat)])
        cat_rows = sub[sub["expected_category"] == cat]
        avg_lat = cat_rows["latency_ms"].mean()
        avg_ret = cat_rows["retry_count"].mean()
        rows.append(
            {
                "Category": cat,
                "Total Samples": total,
                "Correct": correct,
                "Accuracy": round(correct / total, 4) if total else 0.0,
                "False Positives": fp,
                "False Negatives": fn,
                "Avg Latency (ms)": round(avg_lat, 1),
                "Avg Retries": round(avg_ret, 2),
            }
        )
    result = pd.DataFrame(rows).sort_values("Accuracy", ascending=True).reset_index(drop=True)
    return result


# ──────────────────────────────────────────────
#  3. Failure Breakdown
# ──────────────────────────────────────────────


def compute_failure_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    """Group failed records by failure_reason with aggregate stats.

    Returns:
        DataFrame sorted by count descending.
    """
    failed = df[df["failure_reason"].notna()].copy()
    if failed.empty:
        return pd.DataFrame()

    grouped = failed.groupby("failure_reason")
    rows: list[dict[str, Any]] = []
    total_failures = len(failed)
    for reason, group in grouped:
        rows.append(
            {
                "Failure Reason": reason,
                "Count": len(group),
                "Percentage": round(len(group) / total_failures, 4),
                "Avg Retries": round(group["retry_count"].mean(), 2),
                "Avg Latency (ms)": round(group["latency_ms"].mean(), 1),
                "Most Common Category": (
                    group["predicted_category"].mode().iloc[0]
                    if not group["predicted_category"].dropna().empty
                    else "\u2014"
                ),
            }
        )
    result = pd.DataFrame(rows).sort_values("Count", ascending=False).reset_index(drop=True)
    return result


# ──────────────────────────────────────────────
#  4. Field Error Analysis
# ──────────────────────────────────────────────


def _explode_field_breakdowns(df: pd.DataFrame) -> pd.DataFrame:
    """Expand the field_breakdown dict column into a long-format DataFrame.

    Each row in the output corresponds to one field path from one ticket,
    with columns: ``ticket_id``, ``field``, ``status``.
    """
    records: list[dict[str, Any]] = []
    for _, row in df.iterrows():
        breakdown = row.get("field_breakdown")
        if not isinstance(breakdown, dict):
            continue
        for field_path, status in breakdown.items():
            records.append(
                {"ticket_id": row.get("ticket_id"), "field": field_path, "status": status}
            )
    return pd.DataFrame(records)


def compute_field_error_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate field-level errors across all records.

    Returns:
        DataFrame with columns:
            ``field``, ``total``, ``match``, ``mismatch``, ``missing``,
            ``error_rate`` — sorted by error_rate descending.
    """
    exploded = _explode_field_breakdowns(df)
    if exploded.empty:
        return pd.DataFrame()

    grouped = exploded.groupby("field")["status"].value_counts().unstack(fill_value=0)
    for col in ["match", "mismatch", "missing"]:
        if col not in grouped.columns:
            grouped[col] = 0
    grouped = grouped[["match", "mismatch", "missing"]]
    grouped["total"] = grouped.sum(axis=1)
    grouped["error_rate"] = (
        (grouped["mismatch"] + grouped["missing"]) / grouped["total"]
    ).round(4)
    grouped = grouped.sort_values("error_rate", ascending=False).reset_index()
    grouped.columns.name = None
    return grouped


def field_error_chart(field_summary: pd.DataFrame, top_n: int = 15) -> go.Figure:
    """Horizontal bar chart of the top-N fields by error rate.

    Args:
        field_summary: DataFrame from compute_field_error_summary.
        top_n: Number of worst fields to show.

    Returns:
        Plotly horizontal bar figure.
    """
    if field_summary.empty:
        fig = go.Figure()
        fig.add_annotation(text="No field breakdown data available", showarrow=False)
        return fig

    top = field_summary.head(top_n).copy()
    top["error_label"] = top.apply(
        lambda r: f"mismatch={r['mismatch']}  missing={r['missing']}", axis=1
    )
    fig = px.bar(
        top,
        x="error_rate",
        y="field",
        orientation="h",
        text="error_label",
        color="error_rate",
        color_continuous_scale="Reds",
        labels={"error_rate": "Error Rate", "field": ""},
    )
    fig.update_traces(
        textposition="outside",
        showlegend=False,
        hovertemplate="%{y}<br>Error rate: %{x:.1%}<extra></extra>",
    )
    fig.update_layout(
        title=dict(
            text=f"Top-{top_n} Fields by Error Rate",
            font=dict(size=14, color=DARK),
            x=0,
            xanchor="left",
        ),
        height=max(200, top_n * 22),
        margin=dict(l=10, r=80, t=36, b=10),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color=GRAY, size=10),
        xaxis=dict(tickformat=".0%", showgrid=True, gridcolor="rgba(0,0,0,0.06)"),
        yaxis=dict(tickfont=dict(size=10)),
        coloraxis_showscale=False,
    )
    fig.update_yaxes(autorange="reversed")
    return fig


# ──────────────────────────────────────────────
#  5. Retry Analysis
# ──────────────────────────────────────────────


def compute_retry_analysis(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Analyze how retry count relates to success.

    Returns:
        Tuple of (retry_summary, success_table):
            - retry_summary: one row per retry_count with total, success rate, etc.
            - success_table: summary stats for retry-success vs retry-failure groups.
    """
    retry_summary = (
        df.groupby("retry_count")
        .agg(
            total=("ticket_id", "count"),
            success_count=("schema_valid", "sum"),
            avg_latency_ms=("latency_ms", "mean"),
        )
        .reset_index()
    )
    retry_summary["success_rate"] = (
        retry_summary["success_count"] / retry_summary["total"]
    ).round(4)
    retry_summary["failure_count"] = retry_summary["total"] - retry_summary["success_count"]
    retry_summary["avg_latency_ms"] = retry_summary["avg_latency_ms"].round(1)
    retry_summary = retry_summary.sort_values("retry_count")

    succeeded = df[df["schema_valid"]]
    failed = df[~df["schema_valid"]]
    success_table = pd.DataFrame(
        [
            {
                "Group": "Succeeded",
                "Count": len(succeeded),
                "Avg Retries": round(succeeded["retry_count"].mean(), 2),
                "Avg Latency (ms)": round(succeeded["latency_ms"].mean(), 1),
            },
            {
                "Group": "Failed",
                "Count": len(failed),
                "Avg Retries": round(failed["retry_count"].mean(), 2),
                "Avg Latency (ms)": round(failed["latency_ms"].mean(), 1),
            },
        ]
    )
    return retry_summary, success_table


def retry_success_chart(retry_summary: pd.DataFrame) -> go.Figure:
    """Line chart showing success rate per retry count.

    Args:
        retry_summary: DataFrame from compute_retry_analysis.

    Returns:
        Plotly line + bar figure.
    """
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=retry_summary["retry_count"],
            y=retry_summary["total"],
            name="Total Tickets",
            marker_color=GRAY,
            opacity=0.3,
            hovertemplate="Retries: %{x}<br>Tickets: %{y}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=retry_summary["retry_count"],
            y=retry_summary["success_rate"],
            mode="lines+markers",
            name="Success Rate",
            yaxis="y2",
            line=dict(color=SUCCESS, width=3),
            hovertemplate="Retries: %{x}<br>Success: %{y:.1%}<extra></extra>",
        )
    )
    fig.update_layout(
        title=dict(
            text="Retry Success Analysis",
            font=dict(size=14, color=DARK),
            x=0,
            xanchor="left",
        ),
        xaxis=dict(title="Retry Count", dtick=1, tickfont=dict(size=10)),
        yaxis=dict(
            title="Tickets",
            showgrid=True,
            gridcolor="rgba(0,0,0,0.06)",
            tickfont=dict(size=10),
        ),
        yaxis2=dict(
            title="Success Rate",
            overlaying="y",
            side="right",
            tickformat=".0%",
            range=[0, 1],
            tickfont=dict(size=10),
        ),
        height=320,
        margin=dict(l=10, r=50, t=36, b=10),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color=GRAY, size=11),
        legend=dict(orientation="h", y=1.1, x=0),
    )
    return fig


# ──────────────────────────────────────────────
#  6. Latency vs Accuracy Scatter
# ──────────────────────────────────────────────


def latency_vs_accuracy_scatter(df: pd.DataFrame) -> go.Figure:
    """Scatter plot of latency vs field accuracy, colored by schema_valid.

    Args:
        df: Filtered evaluation records DataFrame.

    Returns:
        Plotly scatter figure.
    """
    plot_df = df.dropna(subset=["latency_ms", "field_accuracy"]).copy()
    if plot_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No latency/accuracy data available", showarrow=False)
        return fig

    plot_df["status_label"] = plot_df["schema_valid"].map({True: "Valid", False: "Invalid"})
    fig = px.scatter(
        plot_df,
        x="latency_ms",
        y="field_accuracy",
        color="status_label",
        color_discrete_map={"Valid": SUCCESS, "Invalid": DANGER},
        hover_data={
            "ticket_id": True,
            "predicted_category": True,
            "provider": True,
            "model_name": True,
            "latency_ms": False,
            "field_accuracy": False,
        },
        labels={
            "latency_ms": "Latency (ms)",
            "field_accuracy": "Field Accuracy",
            "status_label": "Status",
        },
    )
    fig.update_traces(
        marker=dict(size=6, line=dict(width=0.5, color="white")),
        hovertemplate=(
            "Ticket: %{customdata[0]}<br>"
            "Category: %{customdata[1]}<br>"
            "Provider: %{customdata[2]}<br>"
            "Model: %{customdata[3]}<br>"
            "Latency: %{x} ms<br>"
            "Accuracy: %{y:.1%}<br>"
            "<extra></extra>"
        ),
    )
    fig.update_layout(
        title=dict(
            text="Latency vs Field Accuracy",
            font=dict(size=14, color=DARK),
            x=0,
            xanchor="left",
        ),
        xaxis=dict(title="Latency (ms)", showgrid=True, gridcolor="rgba(0,0,0,0.06)"),
        yaxis=dict(
            title="Field Accuracy",
            tickformat=".0%",
            range=[0, 1],
            showgrid=True,
            gridcolor="rgba(0,0,0,0.06)",
        ),
        height=380,
        margin=dict(l=10, r=10, t=36, b=10),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color=GRAY, size=11),
        legend=dict(orientation="h", y=1.1, x=0),
    )
    return fig


# ──────────────────────────────────────────────
#  7. Error Inspector
# ──────────────────────────────────────────────


def prepare_error_inspector(df: pd.DataFrame) -> pd.DataFrame:
    """Prepare a detailed error inspection table.

    Returns a DataFrame with columns suitable for interactive exploration,
    including ticket, expected vs predicted, failure info, latencies,
    provider/model, and field accuracy.
    """
    cols = [
        "ticket_id",
        "expected_category",
        "predicted_category",
        "failure_reason",
        "retry_count",
        "latency_ms",
        "provider",
        "model_name",
        "field_accuracy",
        "schema_valid",
    ]
    present = [c for c in cols if c in df.columns]
    view = df[present].copy()
    view.columns = [c.replace("_", " ").title() for c in view.columns]
    rename = {
        "Ticket Id": "Ticket ID",
        "Expected Category": "Expected",
        "Predicted Category": "Predicted",
        "Failure Reason": "Failure",
        "Retry Count": "Retries",
        "Latency Ms": "Latency (ms)",
        "Provider": "Provider",
        "Model Name": "Model",
        "Field Accuracy": "Field Acc",
        "Schema Valid": "Valid",
    }
    view = view.rename(columns=rename)
    if "Field Acc" in view.columns:
        view["Field Acc"] = view["Field Acc"].apply(
            lambda v: f"{v:.1%}" if pd.notna(v) else "\u2014"
        )
    if "Valid" in view.columns:
        view["Valid"] = view["Valid"].map({True: "\u2713", False: "\u2717"})
    if "Failure" in view.columns:
        view["Failure"] = view["Failure"].fillna("\u2014")
    return view


# ──────────────────────────────────────────────
#  Streamlit Renderer
# ──────────────────────────────────────────────


def render_error_analysis_section(df: pd.DataFrame) -> None:
    """Render the complete error analysis section.

    Displays confusion matrix, category performance, failure breakdown,
    field error analysis, retry analysis, latency-vs-accuracy scatter,
    and the error inspector table.

    Args:
        df: Filtered evaluation records DataFrame.
    """
    if df.empty:
        st.info("No data available for error analysis.")
        return

    st.markdown("## Error Analysis")

    # ── 1. Confusion Matrix ──
    with st.expander("Confusion Matrix", expanded=True):
        matrix = compute_confusion_matrix(df)
        if matrix is not None:
            fig_cm = confusion_matrix_heatmap(matrix)
            st.plotly_chart(fig_cm, use_container_width=True)
        else:
            st.info("Confusion matrix requires both expected and predicted categories.")

    # ── 2. Category Performance ──
    with st.expander("Category Performance", expanded=True):
        cat_perf = compute_category_performance(df)
        if not cat_perf.empty:
            cat_perf_display = cat_perf.copy()
            cat_perf_display["Accuracy"] = cat_perf_display["Accuracy"].apply(
                lambda v: f"{v:.1%}"
            )
            st.dataframe(cat_perf_display, use_container_width=True, hide_index=True)
        else:
            st.info("No category performance data available.")

    # ── 3. Failure Breakdown ──
    with st.expander("Failure Breakdown", expanded=False):
        fail_breakdown = compute_failure_breakdown(df)
        if not fail_breakdown.empty:
            fail_display = fail_breakdown.copy()
            fail_display["Percentage"] = fail_display["Percentage"].apply(
                lambda v: f"{v:.1%}"
            )
            st.dataframe(fail_display, use_container_width=True, hide_index=True)
        else:
            st.info("No failure data available.")

    # ── 4. Field Error Analysis ──
    with st.expander("Field Error Analysis", expanded=False):
        field_summary = compute_field_error_summary(df)
        if not field_summary.empty:
            col1, col2 = st.columns([3, 2])
            with col1:
                fig_field = field_error_chart(field_summary)
                st.plotly_chart(fig_field, use_container_width=True)
            with col2:
                field_display = field_summary.head(20).copy()
                field_display["error_rate"] = field_display["error_rate"].apply(
                    lambda v: f"{v:.1%}"
                )
                st.dataframe(field_display, use_container_width=True, hide_index=True)
        else:
            st.info("No field breakdown data available.")

    # ── 5. Retry Analysis ──
    with st.expander("Retry Analysis", expanded=False):
        retry_summary, success_table = compute_retry_analysis(df)
        if not retry_summary.empty:
            col1, col2 = st.columns([3, 2])
            with col1:
                fig_retry = retry_success_chart(retry_summary)
                st.plotly_chart(fig_retry, use_container_width=True)
            with col2:
                st.dataframe(success_table, use_container_width=True, hide_index=True)
                retry_summary_display = retry_summary.copy()
                retry_summary_display["success_rate"] = retry_summary_display[
                    "success_rate"
                ].apply(lambda v: f"{v:.1%}")
                st.dataframe(retry_summary_display, use_container_width=True, hide_index=True)
        else:
            st.info("No retry data available.")

    # ── 6. Latency vs Accuracy ──
    with st.expander("Latency vs Accuracy", expanded=False):
        fig_scatter = latency_vs_accuracy_scatter(df)
        st.plotly_chart(fig_scatter, use_container_width=True)

    # ── 7. Error Inspector ──
    with st.expander("Error Inspector", expanded=True):
        inspector_df = prepare_error_inspector(df)
        if not inspector_df.empty:
            st.dataframe(
                inspector_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Latency (ms)": st.column_config.NumberColumn(format="%d"),
                    "Retries": st.column_config.NumberColumn(format="%d"),
                },
            )
        else:
            st.info("No records to inspect.")
