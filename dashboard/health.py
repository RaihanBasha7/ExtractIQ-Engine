from __future__ import annotations

import importlib
import logging
from pathlib import Path
from typing import Any

import pandas as pd

from app.evaluation.models import EvaluationRecord
from app.evaluation.repository import EvaluationRepository

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS: list[str] = [
    "ticket_id",
    "schema_valid",
    "retry_count",
    "latency_ms",
    "failure_reason",
    "predicted_category",
    "timestamp",
]

REQUIRED_PACKAGES: list[str] = [
    "streamlit",
    "pandas",
    "plotly",
]

HealthStatus = str  # "healthy" | "warning" | "critical"


def check_repository(data_path: str | Path | None = None) -> dict[str, Any]:
    """Check that the repository is reachable and readable.

    Returns:
        Dict with keys: ``status``, ``message``, ``record_count``.
    """
    try:
        repo = EvaluationRepository(path=data_path)
        records = repo.load()
        return {
            "status": "healthy",
            "message": f"Repository reachable, {len(records)} records loaded",
            "record_count": len(records),
        }
    except FileNotFoundError:
        return {"status": "warning", "message": "Repository file not found", "record_count": 0}
    except PermissionError:
        return {"status": "critical", "message": "Permission denied reading repository", "record_count": 0}
    except Exception as exc:
        return {"status": "critical", "message": f"Repository error: {exc}", "record_count": 0}


def check_columns(df: pd.DataFrame) -> dict[str, Any]:
    """Verify that required columns exist in the DataFrame.

    Returns:
        Dict with keys: ``status``, ``message``, ``missing``.
    """
    if df.empty:
        return {"status": "warning", "message": "No data loaded", "missing": REQUIRED_COLUMNS}
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        return {"status": "warning", "message": f"Missing columns: {missing}", "missing": missing}
    return {"status": "healthy", "message": "All required columns present", "missing": []}


def check_dependencies() -> dict[str, Any]:
    """Verify that required Python packages are installed.

    Returns:
        Dict with keys: ``status``, ``message``, ``missing``.
    """
    missing: list[str] = []
    for pkg in REQUIRED_PACKAGES:
        try:
            importlib.import_module(pkg)
        except ImportError:
            missing.append(pkg)
    if missing:
        return {"status": "critical", "message": f"Missing packages: {missing}", "missing": missing}
    return {"status": "healthy", "message": "All dependencies installed", "missing": []}


def run_all_checks(data_path: str | Path | None = None, df: pd.DataFrame | None = None) -> dict[str, Any]:
    """Run every health check and return aggregated results.

    The overall status is the worst of all individual checks.

    Args:
        data_path: Path to the JSONL file (optional).
        df: Pre-loaded DataFrame (optional, will be loaded if not provided).

    Returns:
        Dict with keys: ``overall``, ``checks`` (list of per-check dicts),
        ``summary``.
    """
    checks: list[dict[str, Any]] = [check_dependencies()]

    repo_check = check_repository(data_path)
    checks.append(repo_check)

    if df is None and data_path:
        try:
            repo = EvaluationRepository(path=data_path)
            records = repo.load()
            if records:
                df = pd.DataFrame([r.model_dump() for r in records])
        except Exception:
            df = pd.DataFrame()

    if df is not None:
        checks.append(check_columns(df))

    status_order: dict[str, int] = {"healthy": 0, "warning": 1, "critical": 2}
    overall = max(checks, key=lambda c: status_order.get(c["status"], 2))["status"]

    n_critical = sum(1 for c in checks if c["status"] == "critical")
    n_warning = sum(1 for c in checks if c["status"] == "warning")
    summary = f"{overall} — {n_critical} critical, {n_warning} warnings"

    return {
        "overall": overall,
        "checks": checks,
        "summary": summary,
    }
