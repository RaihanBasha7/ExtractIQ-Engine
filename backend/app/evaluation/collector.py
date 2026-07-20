from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timezone

from app.config import ACTIVE_MODEL, ACTIVE_PROVIDER, SCHEMA_VERSION
from app.evaluation.models import EvaluationRecord
from app.extraction import ExtractionResult
from app.logging import get_logger, log_event
from app.schema import TicketExtraction

logger = get_logger(__name__)

_FAILURE_STAGE_MAP: dict[str, str] = {
    "validation_error": "validation",
    "rate_limit": "infrastructure",
    "timeout": "infrastructure",
    "api_error": "infrastructure",
    "provider_error": "infrastructure",
    "unexpected_error": "unexpected",
    "authentication": "configuration",
    "unknown": "unexpected",
}

_INFRA_CATEGORIES: frozenset[str] = frozenset({
    "rate_limit", "timeout", "api_error", "provider_error",
})


def _compute_field_accuracy(
    expected: TicketExtraction | None,
    predicted: TicketExtraction | None,
) -> float | None:
    if expected is None or predicted is None:
        return None

    expected_dump = expected.model_dump()
    predicted_dump = predicted.model_dump()

    total = 0
    matches = 0

    def _walk(e: object, p: object, path: str) -> None:
        nonlocal total, matches
        if isinstance(e, dict):
            for key in e:
                child_path = f"{path}.{key}" if path else key
                _walk(e[key], p.get(key) if isinstance(p, dict) else None, child_path)
        elif isinstance(e, list):
            for i, item in enumerate(e):
                child_path = f"{path}[{i}]"
                _walk(item, p[i] if isinstance(p, list) and i < len(p) else None, child_path)
        else:
            total += 1
            if e == p:
                matches += 1

    _walk(expected_dump, predicted_dump, "")
    return matches / total if total > 0 else None


def _compute_field_breakdown(
    expected: TicketExtraction | None,
    predicted: TicketExtraction | None,
) -> dict[str, str] | None:
    if expected is None or predicted is None:
        return None

    result: dict[str, str] = {}

    def _walk(e: object, p: object, path: str) -> None:
        if isinstance(e, dict):
            if not isinstance(p, dict):
                for key in e:
                    child_path = f"{path}.{key}" if path else key
                    result[child_path] = "missing"
                return
            for key in e:
                child_path = f"{path}.{key}" if path else key
                if key in p:
                    _walk(e[key], p[key], child_path)
                else:
                    result[child_path] = "missing"
        elif isinstance(e, list):
            if not isinstance(p, list):
                for i in range(len(e)):
                    child_path = f"{path}[{i}]"
                    result[child_path] = "missing"
                return
            for i, item in enumerate(e):
                child_path = f"{path}[{i}]"
                if i < len(p):
                    _walk(item, p[i], child_path)
                else:
                    result[child_path] = "missing"
        else:
            status: str
            if isinstance(p, (dict, list)):
                status = "missing"
            else:
                status = "match" if e == p else "mismatch"
            result[path] = status

    _walk(expected.model_dump(), predicted.model_dump() if predicted else None, "")
    return result


class EvaluationCollector:
    """Creates evaluation records from extraction results.

    Transforms raw :class:`~app.extraction.ExtractionResult` objects into
    structured :class:`~app.evaluation.models.EvaluationRecord` instances,
    computing field accuracy and breakdowns when ground-truth data is available.
    """

    def add(
        self,
        result: ExtractionResult,
        expected: TicketExtraction | None = None,
        processing_time_seconds: float | None = None,
    ) -> EvaluationRecord:
        record = self.build_record(result, expected=expected, processing_time_seconds=processing_time_seconds)
        log_event(logger, event="evaluation_record_created", stage="evaluation", status="success", ticket_id=record.ticket_id, schema_valid=record.schema_valid, retry_count=record.retry_count, latency_ms=record.latency_ms, processing_time=record.processing_time)
        return record

    def extend(
        self,
        results: Sequence[tuple[ExtractionResult, TicketExtraction | None]],
    ) -> list[EvaluationRecord]:
        return [self.add(result, expected) for result, expected in results]

    @staticmethod
    def build_record(
        result: ExtractionResult,
        expected: TicketExtraction | None = None,
        processing_time_seconds: float | None = None,
    ) -> EvaluationRecord:
        predicted = result.data
        predicted_category = (
            predicted.issue.category.value
            if predicted and predicted.issue and predicted.issue.category
            else None
        )
        expected_category = (
            expected.issue.category.value
            if expected and expected.issue and expected.issue.category
            else None
        )

        failure_reason = result.failure_category
        failure_stage = _FAILURE_STAGE_MAP.get(failure_reason) if failure_reason else None

        return EvaluationRecord(
            ticket_id=result.ticket_id,
            schema_valid=result.success,
            repair_attempted=result.retry_count > 0,
            repair_success=result.success and result.retry_count > 0,
            retry_count=result.retry_count,
            latency_ms=round(result.latency_seconds * 1000),
            infra_error=failure_reason in _INFRA_CATEGORIES if failure_reason else False,
            failure_reason=failure_reason,
            expected_category=expected_category,
            predicted_category=predicted_category,
            field_accuracy=_compute_field_accuracy(expected, predicted),
            timestamp=datetime.now(timezone.utc),
            failure_stage=failure_stage,
            field_breakdown=_compute_field_breakdown(expected, predicted),
            processing_time=processing_time_seconds or result.latency_seconds,
            model_name=ACTIVE_MODEL,
            provider=ACTIVE_PROVIDER,
            repair_attempts=result.retry_count,
            schema_version=SCHEMA_VERSION,
        )
