"""
Business-logic orchestrator for the extraction pipeline.

Coordinates the full flow:
    preprocess → extract_ticket → compute_confidence → build_metadata → ExtractResponse

``request_id`` is threaded through to ``extract_ticket`` and all log calls so
that a single extraction can be correlated across the entire pipeline.
"""

import time

from app.api.models import ExtractResponse
from app.database.repository import ExtractionRepository, RawTicketRepository
from app.confidence import ConfidenceMetrics, compute_confidence
from app.evaluation.collector import EvaluationCollector
from app.evaluation.repository import EvaluationRepository
from app.extraction import (
    FINAL_STATUS_FAILED,
    FINAL_STATUS_MODEL_ERROR,
    FINAL_STATUS_NEEDS_REVIEW,
    FINAL_STATUS_NETWORK_ERROR,
    FINAL_STATUS_PROVIDER_RATE_LIMIT,
    FINAL_STATUS_PROVIDER_TIMEOUT,
    FINAL_STATUS_REPAIRED,
    FINAL_STATUS_SUCCESS,
    extract_ticket,
    ExtractionResult,
)
from app.config import ACTIVE_MODEL, ACTIVE_PROVIDER
from app.logging import get_logger, log_event
from app.metadata import build_metadata
from app.preprocessing import preprocess

logger = get_logger(__name__)

raw_ticket_repo = RawTicketRepository()
extraction_repo = ExtractionRepository()
evaluation_collector = EvaluationCollector()
evaluation_repo = EvaluationRepository()


def _map_exception_category(exc: Exception) -> str:
    if isinstance(exc, RuntimeError) and "API_KEY" in str(exc).upper():
        return "authentication"
    return "unexpected_error"


def _build_repair_attempts(result: ExtractionResult) -> list:
    if not result.repair_log or not result.repair_log.entries:
        return []
    return [
        {
            "attempt": e.attempt,
            "status": e.status,
            "error": e.error_message if e.status == "failed" else None,
        }
        for e in result.repair_log.entries
    ]


def process_ticket(ticket_id: str, raw_text: str, request_id: str | None = None) -> ExtractResponse:
    log_event(logger, event="preprocessing_started", stage="preprocessing", status="started", request_id=request_id, ticket_id=ticket_id)
    pre = preprocess(raw_text)
    log_event(logger, event="preprocessing_completed", stage="preprocessing", status="success", request_id=request_id, ticket_id=ticket_id, language=pre.language)

    raw_ticket_repo.save(
        ticket_id=ticket_id,
        raw_text=raw_text,
        cleaned_text=pre.clean_text,
        language=pre.language,
    )

    start = time.monotonic()
    log_event(logger, event="extraction_started", stage="extraction", status="started", request_id=request_id, ticket_id=ticket_id, provider=ACTIVE_PROVIDER, model=ACTIVE_MODEL)
    try:
        result = extract_ticket(ticket_id, pre.clean_text, request_id=request_id)
    except Exception as exc:
        elapsed = time.monotonic() - start
        category = _map_exception_category(exc)
        log_event(logger, event="extraction_error", stage="extraction", status="failed", level="ERROR", exc_info=True, request_id=request_id, ticket_id=ticket_id, category=category)
        extraction_repo.save(
            ticket_id=ticket_id,
            structured_json=None,
            schema_valid=False,
            retry_count=0,
            failure_category=category,
            latency_seconds=elapsed,
            confidence_score=10.0,
            validation_status="failed",
            final_status="NEEDS_REVIEW",
            needs_review_reason=f"Exception: {category}",
        )
        eval_result = ExtractionResult(
            ticket_id=ticket_id,
            success=False,
            data=None,
            failure_category=category,
            latency_seconds=elapsed,
            request_id=request_id,
        )
        record = evaluation_collector.add(eval_result)
        evaluation_repo.save(record)
        log_event(logger, event="response_sent", stage="api", status="failed", request_id=request_id, ticket_id=ticket_id, latency_ms=round(elapsed * 1000), category=category)
        return ExtractResponse(
            ticket_id=ticket_id,
            success=False,
            data=None,
            confidence=compute_confidence(ConfidenceMetrics(success=False, retry_count=0)),
            metadata=build_metadata(
                repair_attempts=0,
                latency_seconds=elapsed,
                success=False,
                confidence_score=10.0,
                final_status="NEEDS_REVIEW",
                needs_review_reason=f"Exception: {category}",
            ),
            retry_count=0,
            failure_category=category,
            latency_seconds=elapsed,
            language=pre.language,
            request_id=request_id,
            cleaned_text=pre.clean_text,
            confidence_score=10.0,
            validation_status="failed",
            final_status="NEEDS_REVIEW",
            needs_review_reason=f"Exception: {category}",
        )

    elapsed = time.monotonic() - start
    log_event(logger, event="extraction_completed", stage="extraction", status="success", request_id=request_id, ticket_id=ticket_id, retries=result.retry_count, latency_ms=round(elapsed * 1000))

    log_event(logger, event="persist_started", stage="extraction", status="started", request_id=request_id, ticket_id=ticket_id, action="persist")
    structured = result.data.model_dump() if result.data else None

    repair_attempts_data = _build_repair_attempts(result)
    confidence = compute_confidence(ConfidenceMetrics(
        success=result.success,
        retry_count=result.retry_count,
        data=result.data,
    ))

    validation_status = "passed" if result.success else "failed"
    needs_review_reason_str = "; ".join(result.needs_review_reasons) if result.needs_review_reasons else None

    infra_statuses = {FINAL_STATUS_PROVIDER_RATE_LIMIT, FINAL_STATUS_PROVIDER_TIMEOUT,
                       FINAL_STATUS_NETWORK_ERROR, FINAL_STATUS_MODEL_ERROR, FINAL_STATUS_FAILED}
    if result.success and confidence < 50 and result.final_status not in infra_statuses:
        result.final_status = FINAL_STATUS_NEEDS_REVIEW
        review_reasons = list(result.needs_review_reasons)
        review_reasons.append(f"Confidence {confidence}% below threshold")
        needs_review_reason_str = "; ".join(review_reasons)

    extraction_repo.save(
        ticket_id=ticket_id,
        structured_json=structured,
        schema_valid=result.success,
        retry_count=result.retry_count,
        failure_category=result.failure_category,
        latency_seconds=elapsed,
        repair_attempts_json=repair_attempts_data if repair_attempts_data else None,
        confidence_score=confidence,
        validation_status=validation_status,
        repair_attempts_count=result.retry_count,
        final_status=result.final_status,
        needs_review_reason=needs_review_reason_str,
    )
    log_event(logger, event="persist_completed", stage="extraction", status="success", request_id=request_id, ticket_id=ticket_id, action="persist")
    record = evaluation_collector.add(result, processing_time_seconds=elapsed)
    evaluation_repo.save(record)
    log_event(logger, event="response_sent", stage="api", status="success", request_id=request_id, ticket_id=ticket_id, latency_ms=round(elapsed * 1000))
    return ExtractResponse(
        ticket_id=ticket_id,
        success=result.success,
        data=result.data,
        confidence=confidence / 100.0,
        metadata=build_metadata(
            repair_attempts=result.retry_count,
            latency_seconds=elapsed,
            success=result.success,
            confidence_score=confidence,
            final_status=result.final_status,
            needs_review_reason=needs_review_reason_str,
        ),
        retry_count=result.retry_count,
        failure_category=result.failure_category,
        latency_seconds=elapsed,
        language=pre.language,
        request_id=request_id,
        cleaned_text=pre.clean_text,
        repair_attempts=repair_attempts_data,
        confidence_score=confidence,
        validation_status=validation_status,
        final_status=result.final_status,
        needs_review_reason=needs_review_reason_str,
    )
