from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from app.evaluation.repository import EvaluationRepository
from dashboard.config import CACHE_TTL, MAX_ROWS

logger = logging.getLogger(__name__)


@st.cache_data(ttl=CACHE_TTL, show_spinner="Loading evaluation records...")
def load_data(jsonl_path: str | Path | None = None) -> pd.DataFrame:
    """Load evaluation records from JSONL into a cached DataFrame.

    Handles empty files, malformed records, and missing columns gracefully.
    Logs dataset size and load duration for observability.

    Args:
        jsonl_path: Path to the evaluation_records.jsonl file.

    Returns:
        DataFrame with evaluation records, or empty DataFrame on failure.
    """
    start = time.monotonic()
    try:
        repo = EvaluationRepository(path=jsonl_path)
        records = repo.load()
    except FileNotFoundError:
        logger.warning("JSONL file not found at %s", jsonl_path)
        return pd.DataFrame()
    except PermissionError:
        logger.error("Permission denied reading %s", jsonl_path)
        return pd.DataFrame()
    except Exception as exc:
        logger.error("Failed to load evaluation records: %s", exc)
        return pd.DataFrame()

    if not records:
        logger.info("No evaluation records found at %s", repo.path)
        return pd.DataFrame()

    df = pd.DataFrame([r.model_dump() for r in records])

    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
        df["date"] = df["timestamp"].dt.date

    if "processing_time" not in df.columns or df["processing_time"].isna().all():
        df["processing_time"] = df["latency_ms"] / 1000.0

    # Apply row cap
    if len(df) > MAX_ROWS:
        logger.warning("Dataset exceeds MAX_ROWS (%d > %d), truncating", len(df), MAX_ROWS)
        df = df.tail(MAX_ROWS).reset_index(drop=True)

    elapsed = time.monotonic() - start
    logger.info(
        "Loaded %d records in %.2fs (cols=%s, size=%.1f KB)",
        len(df),
        elapsed,
        list(df.columns),
        df.memory_usage(deep=True).sum() / 1024,
    )
    return df


def compute_metrics(df: pd.DataFrame) -> dict[str, Any]:
    """Compute aggregate KPI metrics from a DataFrame of evaluation records.

    Args:
        df: Evaluation records DataFrame.

    Returns:
        Dictionary of computed metrics including rates, averages, and counts.
    """
    if df.empty:
        return {
            "total": 0,
            "schema_valid_rate": 0.0,
            "field_accuracy": 0.0,
            "repair_success_rate": 0.0,
            "avg_latency_ms": 0.0,
            "avg_retries": 0.0,
            "infra_errors": 0,
            "extraction_failures": 0,
        }
    total = len(df)
    valid_count = int(df["schema_valid"].sum())
    repaired = df[df["repair_attempted"]]
    repair_success_rate = (
        repaired["repair_success"].mean() if not repaired.empty else 1.0
    )
    fa = df["field_accuracy"].dropna()
    return {
        "total": total,
        "schema_valid_rate": round(valid_count / total, 4),
        "field_accuracy": round(fa.mean(), 4) if not fa.empty else 0.0,
        "repair_success_rate": round(repair_success_rate, 4),
        "avg_latency_ms": round(df["latency_ms"].mean(), 1),
        "avg_retries": round(df["retry_count"].mean(), 2),
        "infra_errors": int(df["infra_error"].sum()),
        "extraction_failures": total - valid_count,
    }


def compute_deltas(
    current: dict[str, Any],
    previous_run: dict[str, Any] | None,
) -> dict[str, Any]:
    """Compute percentage/absolute deltas between current and previous metrics.

    Args:
        current: Current metrics dict from compute_metrics.
        previous_run: Previous metrics dict, or None if no prior data.

    Returns:
        Dict keyed by metric name with delta strings, or empty dict.
    """
    if not previous_run:
        return {}
    deltas: dict[str, Any] = {}
    delta_fields = [
        ("schema_valid_rate", "pct"),
        ("field_accuracy", "pct"),
        ("repair_success_rate", "pct"),
        ("avg_latency_ms", "abs"),
        ("avg_retries", "abs"),
        ("infra_errors", "abs"),
        ("extraction_failures", "abs"),
    ]
    for field, kind in delta_fields:
        cur_val = current.get(field, 0)
        prev_val = previous_run.get(field, 0)
        if kind == "pct":
            if prev_val != 0:
                delta = (cur_val - prev_val) / prev_val
                deltas[field] = f"{delta:+.1%}"
            else:
                deltas[field] = f"{cur_val:+.1%}" if cur_val else "\u2014"
        else:
            diff = cur_val - prev_val
            if field == "avg_latency_ms":
                deltas[field] = f"{diff:+.0f} ms"
            elif field == "avg_retries":
                deltas[field] = f"{diff:+.2f}"
            else:
                deltas[field] = f"{diff:+d}"
    return deltas


def split_run_data(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame | None]:
    """Split data into current and previous run batches.

    Uses the timestamp column: the latest unique date is considered the
    current run; all earlier data is the previous run.

    Args:
        df: Full evaluation records DataFrame.

    Returns:
        Tuple of (current_run_df, previous_run_df_or_None).
    """
    if df.empty:
        return df, None
    dates = sorted(df["date"].unique())
    if len(dates) < 2:
        return df, None
    latest = dates[-1]
    current = df[df["date"] == latest]
    previous = df[df["date"] < latest]
    return current, previous if not previous.empty else None


def apply_filters(
    df: pd.DataFrame,
    date_range: tuple[datetime, datetime] | None = None,
    categories: list[str] | None = None,
    schema_valid: bool | None = None,
    repair_success: bool | None = None,
    failure_types: list[str] | None = None,
    models: list[str] | None = None,
    providers: list[str] | None = None,
    retry_range: tuple[int, int] | None = None,
    search_query: str | None = None,
) -> pd.DataFrame:
    """Apply sidebar filter selections to the DataFrame.

    All filter parameters are optional; only non-None values are applied.

    Returns:
        Filtered DataFrame copy.
    """
    if df.empty:
        return df
    result = df.copy()
    if date_range:
        lo, hi = date_range
        lo = pd.Timestamp(lo).tz_localize("UTC") if lo.tzinfo is None else pd.Timestamp(lo)
        hi = pd.Timestamp(hi).tz_localize("UTC") if hi.tzinfo is None else pd.Timestamp(hi)
        result = result[(result["timestamp"] >= lo) & (result["timestamp"] <= hi)]
    if categories:
        result = result[result["predicted_category"].isin(categories)]
    if schema_valid is not None:
        result = result[result["schema_valid"] == schema_valid]
    if repair_success is not None:
        result = result[result["repair_success"] == repair_success]
    if failure_types:
        result = result[result["failure_reason"].isin(failure_types)]
    if models:
        result = result[result["model_name"].isin(models)]
    if providers:
        result = result[result["provider"].isin(providers)]
    if retry_range:
        lo_r, hi_r = retry_range
        result = result[(result["retry_count"] >= lo_r) & (result["retry_count"] <= hi_r)]
    if search_query:
        q = search_query.strip().lower()
        result = result[result["ticket_id"].str.lower().str.contains(q, na=False)]
    return result


def get_unique_values(df: pd.DataFrame, column: str) -> list[str]:
    """Return sorted unique non-null values from a DataFrame column."""
    if df.empty or column not in df.columns:
        return []
    return sorted(df[column].dropna().unique().tolist())


def summarize_filters(
    df: pd.DataFrame,
    total_before: int,
    **filters: Any,
) -> str:
    """Build a human-readable filter summary string.

    Args:
        df: The filtered DataFrame.
        total_before: Row count before filtering.
        filters: The same keyword arguments passed to ``apply_filters``.

    Returns:
        Short description like "Showing 12 of 50 records".
    """
    if total_before == 0:
        return "No data"
    if len(df) == total_before:
        return f"Showing all {total_before} records"
    active = sum(
        1 for v in filters.values() if v is not None and v is not False and v != (0, 0)
    )
    return f"Showing {len(df)} of {total_before} records ({active} filter{'s' if active != 1 else ''} active)"
