from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query, Request, Response

from app.api.error_models import ErrorResponse
from app.api.models import (
    ExtractBatchRequest,
    ExtractBatchResponse,
    ExtractRequest,
    ExtractResponse,
    HealthResponse,
    HistoryItem,
    HistoryResponse,
    MetricsResponse,
    RepairAttemptDetail,
    SystemResponse,
    VersionResponse,
)
from app.api.service import process_ticket
from app.config import ACTIVE_MODEL, ACTIVE_PROVIDER
from app.database.database import SessionLocal
from app.database.repository import ExtractionRepository
from app.logging import get_logger, log_event
from app.metadata import ExtractionMetadata
from app.services.health_service import HealthService
from app.services.metrics_service import MetricsService
from app.services.version_service import VersionService

logger = get_logger(__name__)

router = APIRouter()

health_service = HealthService()
metrics_service = MetricsService()
version_service = VersionService()
extraction_repo = ExtractionRepository()


@router.get(
    "/health",
    response_model=HealthResponse,
    tags=["health"],
    summary="Health check",
    description="Returns structured health information for all service dependencies.",
    response_description="Service health with per-dependency check results.",
)
def health(request: Request, response: Response):
    request_id = _get_request_id(request)
    result = health_service.check_all(request_id=request_id)
    if health_service.has_critical_failure(result.checks):
        response.status_code = 503
    return result


@router.get(
    "/version",
    response_model=VersionResponse,
    tags=["health"],
    summary="Version information",
    description="Returns service version, active LLM provider/model, and runtime metadata.",
    response_description="Version and runtime metadata.",
)
def version(request: Request):
    request_id = _get_request_id(request)
    log_event(logger, event="version_request_started", stage="api", status="started", request_id=request_id)
    info = version_service.get_version()
    log_event(
        logger, event="version_request_completed", stage="api", status="success",
        request_id=request_id, version=info.version, provider=info.provider, model=info.model,
    )
    return info


def _get_request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


@router.post(
    "/v1/extract",
    response_model=ExtractResponse,
    status_code=200,
    tags=["extraction"],
    summary="Extract structured data from a single ticket",
    description="Preprocesses raw ticket text (PII redaction, normalization), then runs "
    "the model-driven extraction with up to 3 repair retries on schema validation failure.",
    response_description="Extraction result for the requested ticket.",
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request"},
        422: {"model": ErrorResponse, "description": "Validation Error"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def extract(req: ExtractRequest, request: Request):
    if not req.raw_text.strip():
        raise HTTPException(status_code=400, detail="raw_text must not be empty")
    request_id = _get_request_id(request)
    log_event(logger, event="request_received", stage="api", status="started", request_id=request_id, ticket_id=req.ticket_id)
    return process_ticket(req.ticket_id, req.raw_text, request_id=request_id)


@router.get(
    "/v1/metrics",
    response_model=MetricsResponse,
    tags=["metrics"],
    summary="Get extraction metrics",
    description="Returns aggregated extraction statistics including success rates, "
    "average processing times, and a breakdown of failures by category.",
    response_description="Aggregated extraction metrics with per-field summaries.",
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request"},
        422: {"model": ErrorResponse, "description": "Validation Error"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_metrics(request: Request):
    request_id = _get_request_id(request)
    log_event(logger, event="metrics_requested", stage="api", status="started", request_id=request_id)
    result = metrics_service.get_metrics()
    log_event(logger, event="metrics_returned", stage="api", status="success", request_id=request_id, total=result.total_requests)
    return result


@router.post(
    "/v1/extract/batch",
    response_model=ExtractBatchResponse,
    status_code=200,
    tags=["extraction"],
    summary="Extract structured data from multiple tickets",
    description="Accepts a list of tickets and processes each independently. "
    "Empty raw_text entries are immediately rejected without calling the LLM.",
    response_description="Batch extraction results.",
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request"},
        422: {"model": ErrorResponse, "description": "Validation Error"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def extract_batch(req: ExtractBatchRequest, request: Request):
    request_id = _get_request_id(request)
    log_event(logger, event="batch_request_received", stage="api", status="started", request_id=request_id, batch_size=len(req.tickets))
    results: list[ExtractResponse] = []
    for ticket in req.tickets:
        if not ticket.raw_text.strip():
            results.append(
                ExtractResponse(
                    ticket_id=ticket.ticket_id,
                    success=False,
                    data=None,
                    confidence=0.0,
                    metadata=ExtractionMetadata(
                        repair_attempts=0,
                        latency_ms=0,
                        provider="unknown",
                        model="unknown",
                        validation="failed",
                        timestamp=datetime.now(timezone.utc),
                    ),
                    retry_count=0,
                    failure_category="empty_text",
                    latency_seconds=0.0,
                    language="unknown",
                    request_id=request_id,
                )
            )
            continue
        results.append(process_ticket(ticket.ticket_id, ticket.raw_text, request_id=request_id))
    return ExtractBatchResponse(results=results)


@router.get(
    "/v1/history",
    response_model=HistoryResponse,
    tags=["history"],
    summary="Get extraction history",
    description="Returns paginated extraction history with latest first.",
    response_description="Paginated history of extractions.",
    responses={
        422: {"model": ErrorResponse, "description": "Validation Error"},
    },
)
def get_history(
    request: Request,
    limit: int = Query(default=50, ge=1, le=200, description="Number of records per page"),
    offset: int = Query(default=0, ge=0, description="Number of records to skip"),
):
    request_id = _get_request_id(request)
    log_event(logger, event="history_requested", stage="api", status="started", request_id=request_id)
    with SessionLocal() as session:
        session.expire_on_commit = False
        total = extraction_repo.count_history(db_session=session)
        rows = extraction_repo.list_history(limit=limit, offset=offset, db_session=session)

    items = []
    for r in rows:
        raw = r.get("raw_text", "")
        structured = r.get("structured_json")
        latency = r.get("latency_seconds", 0)
        retry_count = r.get("retry_count", 0)
        status = "completed" if r.get("schema_valid") else "failure"

        attempt_details = []
        raw_attempts = r.get("repair_attempts") or []
        for a in raw_attempts:
            if isinstance(a, dict):
                attempt_details.append(RepairAttemptDetail(
                    attempt=a.get("attempt", 1),
                    status=a.get("status", "failed"),
                    error=a.get("error"),
                ))

        items.append(HistoryItem(
            request_id=str(r.get("id", "")),
            ticket_id=r.get("ticket_id", ""),
            original_ticket=raw[:500] if raw else "",
            extraction_summary=structured,
            confidence=0.9 if status == "completed" else 0.1,
            latency=latency,
            repair_attempts=attempt_details,
            provider=ACTIVE_PROVIDER,
            model=ACTIVE_MODEL,
            timestamp=r.get("created_at", ""),
            status=status,
        ))

    return HistoryResponse(items=items, total=total, limit=limit, offset=offset)


@router.get(
    "/v1/system",
    response_model=SystemResponse,
    tags=["system"],
    summary="Combined system health and metrics",
    description="Returns health check and metrics in a single request to reduce dashboard polling.",
    response_description="Combined health and metrics payload.",
)
def get_system(request: Request, response: Response):
    request_id = _get_request_id(request)
    health_result = health_service.check_all(request_id=request_id)
    if health_service.has_critical_failure(health_result.checks):
        response.status_code = 503
    metrics_result = metrics_service.get_metrics()
    return SystemResponse(health=health_result, metrics=metrics_result)
