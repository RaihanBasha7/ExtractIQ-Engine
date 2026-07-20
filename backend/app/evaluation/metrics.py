from __future__ import annotations

from collections.abc import Sequence

import pandas as pd

from app.evaluation.models import EvaluationRecord
from app.logging import get_logger, log_event

logger = get_logger(__name__)


def _to_dataframe(records: Sequence[EvaluationRecord]) -> pd.DataFrame:
    return pd.DataFrame([r.model_dump() for r in records])


def calculate_schema_valid_rate(
    records: Sequence[EvaluationRecord],
) -> float:
    if not records:
        log_event(logger, event="metrics_calculation", stage="evaluation", status="failed", level="WARNING", metric="schema_valid_rate", reason="empty record set")
        return 0.0
    df = _to_dataframe(records)
    rate = df["schema_valid"].mean()
    log_event(logger, event="metrics_calculation", stage="evaluation", status="success", metric="schema_valid_rate", value=round(rate, 4), n=len(records))
    return float(rate)


def calculate_average_latency(
    records: Sequence[EvaluationRecord],
    unit: str = "ms",
) -> float:
    if not records:
        log_event(logger, event="metrics_calculation", stage="evaluation", status="failed", level="WARNING", metric="average_latency", reason="empty record set")
        return 0.0
    df = _to_dataframe(records)
    avg = df["latency_ms"].mean()
    result = avg / 1000.0 if unit == "s" else avg
    log_event(logger, event="metrics_calculation", stage="evaluation", status="success", metric="average_latency", value=round(result, 2), unit=unit, n=len(records))
    return float(result)


def calculate_average_retries(
    records: Sequence[EvaluationRecord],
) -> float:
    if not records:
        log_event(logger, event="metrics_calculation", stage="evaluation", status="failed", level="WARNING", metric="average_retries", reason="empty record set")
        return 0.0
    df = _to_dataframe(records)
    avg = df["retry_count"].mean()
    log_event(logger, event="metrics_calculation", stage="evaluation", status="success", metric="average_retries", value=round(avg, 4), n=len(records))
    return float(avg)


def calculate_repair_success(
    records: Sequence[EvaluationRecord],
) -> float:
    if not records:
        log_event(logger, event="metrics_calculation", stage="evaluation", status="failed", level="WARNING", metric="repair_success", reason="empty record set")
        return 0.0
    df = _to_dataframe(records)
    repaired = df[df["repair_attempted"]]
    if repaired.empty:
        log_event(logger, event="metrics_calculation", stage="evaluation", status="success", metric="repair_success", value=1.0, reason="no repair attempts")
        return 1.0
    rate = repaired["repair_success"].mean()
    log_event(logger, event="metrics_calculation", stage="evaluation", status="success", metric="repair_success", value=round(rate, 4), repaired_count=len(repaired))
    return float(rate)


def calculate_failure_rate(
    records: Sequence[EvaluationRecord],
) -> float:
    if not records:
        log_event(logger, event="metrics_calculation", stage="evaluation", status="failed", level="WARNING", metric="failure_rate", reason="empty record set")
        return 0.0
    df = _to_dataframe(records)
    rate = (~df["schema_valid"]).mean()
    log_event(logger, event="metrics_calculation", stage="evaluation", status="success", metric="failure_rate", value=round(rate, 4), n=len(records))
    return float(rate)


def calculate_category_distribution(
    records: Sequence[EvaluationRecord],
    column: str = "predicted_category",
) -> dict[str, int]:
    if not records:
        log_event(logger, event="metrics_calculation", stage="evaluation", status="failed", level="WARNING", metric="category_distribution", reason="empty record set")
        return {}
    df = _to_dataframe(records)
    col = df[column].dropna()
    dist: dict[str, int] = col.value_counts().to_dict()
    log_event(logger, event="metrics_calculation", stage="evaluation", status="success", metric="category_distribution", distribution=dist, n=len(col))
    return dist


def calculate_field_accuracy(
    records: Sequence[EvaluationRecord],
) -> float:
    if not records:
        log_event(logger, event="metrics_calculation", stage="evaluation", status="failed", level="WARNING", metric="field_accuracy", reason="empty record set")
        return 0.0
    df = _to_dataframe(records)
    non_null = df["field_accuracy"].dropna()
    if non_null.empty:
        log_event(logger, event="metrics_calculation", stage="evaluation", status="failed", level="WARNING", metric="field_accuracy", reason="no ground-truth data available")
        return 0.0
    avg = non_null.mean()
    log_event(logger, event="metrics_calculation", stage="evaluation", status="success", metric="field_accuracy", value=round(avg, 4), n=len(non_null))
    return float(avg)
