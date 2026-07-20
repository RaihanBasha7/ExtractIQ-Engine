from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from dashboard.config import EXPORT_DIR

logger = logging.getLogger(__name__)


def _ensure_export_dir() -> Path:
    """Create the export directory if it does not exist."""
    path = Path(EXPORT_DIR)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def _safe_filename(name: str, ext: str) -> str:
    return f"{name}_{_timestamp()}.{ext}"


def export_dataframe(df: pd.DataFrame, name: str = "filtered_data") -> str:
    """Export a DataFrame to CSV inside the export directory.

    Args:
        df: DataFrame to export.
        name: Base filename (without extension).

    Returns:
        Absolute path to the written file.
    """
    if df.empty:
        logger.warning("export_dataframe called with empty DataFrame — nothing written")
        return ""
    out_dir = _ensure_export_dir()
    path = out_dir / _safe_filename(name, "csv")
    df.to_csv(path, index=False)
    logger.info("exported DataFrame (%d rows) to %s", len(df), path)
    return str(path)


def export_json(data: list[dict[str, Any]] | dict[str, Any], name: str = "export") -> str:
    """Export a JSON-serialisable object to a JSON file.

    Args:
        data: Object to serialise.
        name: Base filename (without extension).

    Returns:
        Absolute path to the written file.
    """
    if not data:
        logger.warning("export_json called with empty data — nothing written")
        return ""
    out_dir = _ensure_export_dir()
    path = out_dir / _safe_filename(name, "json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)
    logger.info("exported JSON to %s", path)
    return str(path)


def export_metrics(metrics: dict[str, Any]) -> str:
    """Export the current metrics summary as JSON.

    Args:
        metrics: Dict from ``compute_metrics()``.

    Returns:
        Path to the written file.
    """
    return export_json(metrics, name="metrics")


def export_category_performance(cat_df: pd.DataFrame) -> str:
    """Export the category performance table as CSV.

    Args:
        cat_df: DataFrame from ``compute_category_performance()``.

    Returns:
        Path to the written file.
    """
    return export_dataframe(cat_df, name="category_performance")


def export_failure_breakdown(fail_df: pd.DataFrame) -> str:
    """Export the failure breakdown table as CSV.

    Args:
        fail_df: DataFrame from ``compute_failure_breakdown()``.

    Returns:
        Path to the written file.
    """
    return export_dataframe(fail_df, name="failure_breakdown")


def export_field_analysis(field_df: pd.DataFrame) -> str:
    """Export the field error summary as CSV.

    Args:
        field_df: DataFrame from ``compute_field_error_summary()``.

    Returns:
        Path to the written file.
    """
    return export_dataframe(field_df, name="field_analysis")
