import asyncio
import os
import tempfile
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, File, Form, HTTPException, Query, Request, Response, UploadFile

from app.api.error_models import ErrorResponse
from app.api.models import (
    BatchUploadResponse,
    ExtractBatchRequest,
    ExtractBatchResponse,
    ExtractRequest,
    ExtractResponse,
    HealthResponse,
    HistoryItem,
    HistoryResponse,
    MetricsResponse,
    ModifySegmentsRequest,
    RepairAttemptDetail,
    SegmentInfoResponse,
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
from app.settings import settings

logger = get_logger(__name__)

router = APIRouter()

health_service = HealthService()
metrics_service = MetricsService()
version_service = VersionService()
extraction_repo = ExtractionRepository()

# ── In-memory segment cache (session-scoped) ──────────────────────────────

_segment_cache: dict[str, dict] = {}
_batch_semaphore = asyncio.Semaphore(settings.BATCH_MAX_CONCURRENT_REQUESTS)


@router.get(
    "/health",
    response_model=HealthResponse,
    tags=["health"],
    summary="Health check",
    description="Returns structured health information for all service dependencies.",
    response_description="Service health with per-dependency check results.",
    operation_id="get_health",
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
    operation_id="get_version",
)
def version(request: Request):
    request_id = _get_request_id(request)
    log_event(logger, event="version_request_started", stage="api", status="started", request_id=request_id)
    info = version_service.get_version()
    log_event(
        logger,
        event="version_request_completed",
        stage="api",
        status="success",
        request_id=request_id,
        version=info.version,
        provider=info.provider,
        model=info.model,
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
    operation_id="extract_ticket",
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request — missing or empty raw_text"},
        422: {"model": ErrorResponse, "description": "Validation Error — invalid request body"},
        500: {"model": ErrorResponse, "description": "Internal Server Error — extraction or provider failure"},
    },
)
def extract(req: ExtractRequest, request: Request):
    if not req.raw_text.strip():
        raise HTTPException(status_code=400, detail="raw_text must not be empty")
    request_id = _get_request_id(request)
    log_event(
        logger, event="request_received", stage="api", status="started", request_id=request_id, ticket_id=req.ticket_id
    )
    return process_ticket(req.ticket_id, req.raw_text, request_id=request_id)


@router.get(
    "/v1/metrics",
    response_model=MetricsResponse,
    tags=["metrics"],
    summary="Get extraction metrics",
    description="Returns aggregated extraction statistics including success rates, "
    "average processing times, and a breakdown of failures by category.",
    response_description="Aggregated extraction metrics with per-field summaries.",
    operation_id="get_metrics",
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
    log_event(
        logger,
        event="metrics_returned",
        stage="api",
        status="success",
        request_id=request_id,
        total=result.total_requests,
    )
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
    operation_id="extract_batch",
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request"},
        422: {"model": ErrorResponse, "description": "Validation Error"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def extract_batch(req: ExtractBatchRequest, request: Request):
    request_id = _get_request_id(request)
    log_event(
        logger,
        event="batch_request_received",
        stage="api",
        status="started",
        request_id=request_id,
        batch_size=len(req.tickets),
    )
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
                        confidence_score=10.0,
                        final_status="NEEDS_REVIEW",
                        needs_review_reason="Empty raw text",
                    ),
                    retry_count=0,
                    failure_category="empty_text",
                    latency_seconds=0.0,
                    language="unknown",
                    request_id=request_id,
                    confidence_score=10.0,
                    validation_status="failed",
                    final_status="NEEDS_REVIEW",
                    needs_review_reason="Empty raw text",
                )
            )
            continue
        results.append(process_ticket(ticket.ticket_id, ticket.raw_text, request_id=request_id))
    return ExtractBatchResponse(results=results)


# ── Batch helper ───────────────────────────────────────────────────────────


_INFRA_ERROR_KEYWORDS = [
    "rate_limit",
    "rate limit",
    "429",
    "too many requests",
    "provider_busy",
    "provider busy",
    "503",
    "timeout",
    "connection",
    "unavailable",
    "concurrency_limit",
    "concurrency limit",
]

_INFRA_STATUSES = {"PROVIDER_RATE_LIMIT", "PROVIDER_TIMEOUT", "NETWORK_ERROR", "MODEL_ERROR"}


def _is_infrastructure_error(final_status: str, failure_category: str | None, needs_review_reason: str | None) -> bool:
    if final_status in _INFRA_STATUSES:
        return True
    if final_status != "NEEDS_REVIEW":
        return False
    text = f"{failure_category or ''} {needs_review_reason or ''}".lower()
    return any(kw in text for kw in _INFRA_ERROR_KEYWORDS)


def _classify_infrastructure_error(resp: ExtractResponse) -> ExtractResponse:
    if resp.final_status in _INFRA_STATUSES:
        pass
    elif _is_infrastructure_error(resp.final_status, resp.failure_category, resp.needs_review_reason):
        resp.final_status = "PROVIDER_RATE_LIMIT"
        resp.needs_review_reason = "Provider rate limited. Please retry later."
    return resp


def _build_infra_error_response(idx: int, request_id: str | None, retry_count: int, reason: str) -> ExtractResponse:
    reason_lower = reason.lower()
    if "rate" in reason_lower or "429" in reason_lower:
        final_status = "PROVIDER_RATE_LIMIT"
    elif "timeout" in reason_lower:
        final_status = "PROVIDER_TIMEOUT"
    elif "connection" in reason_lower:
        final_status = "NETWORK_ERROR"
    else:
        final_status = "MODEL_ERROR"
    return ExtractResponse(
        ticket_id=f"seg_{idx}_infra",
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
            confidence_score=10.0,
            final_status=final_status,
            needs_review_reason="Provider rate limited. Please retry later.",
        ),
        retry_count=retry_count,
        failure_category="infrastructure_error",
        latency_seconds=0.0,
        language="unknown",
        request_id=request_id,
        confidence_score=10.0,
        validation_status="failed",
        final_status=final_status,
        needs_review_reason="Provider rate limited. Please retry later.",
    )


def _process_single_ticket(ticket_text: str, idx: int, request_id: str | None) -> ExtractResponse:
    ticket_id = f"seg_{datetime.now(timezone.utc).strftime('%H%M%S')}_{idx}_{os.urandom(2).hex()}"
    return process_ticket(ticket_id, ticket_text, request_id=request_id)


async def _process_ticket_with_retry(
    semaphore: asyncio.Semaphore,
    ticket_text: str,
    idx: int,
    request_id: str | None,
) -> ExtractResponse:
    max_retries = settings.BATCH_MAX_RETRIES
    retry_delays = settings.BATCH_RETRY_DELAYS

    for attempt in range(max_retries + 1):
        async with semaphore:
            try:
                resp = await asyncio.to_thread(_process_single_ticket, ticket_text, idx, request_id)
            except Exception as exc:
                logger.error("Ticket %d exception (attempt %d/%d): %s", idx, attempt + 1, max_retries, exc)
                if attempt < max_retries:
                    delay = retry_delays[attempt] if attempt < len(retry_delays) else retry_delays[-1]
                    logger.info("Ticket %d waiting %.1fs before retry %d/%d", idx, delay, attempt + 1, max_retries)
                    await asyncio.sleep(delay)
                    continue
                return _build_infra_error_response(idx, request_id, max_retries, str(exc))

        # Check if response is an infrastructure error
        if _is_infrastructure_error(resp.final_status, resp.failure_category, resp.needs_review_reason):
            if attempt < max_retries:
                delay = retry_delays[attempt] if attempt < len(retry_delays) else retry_delays[-1]
                logger.info(
                    "Ticket %d infra error (attempt %d/%d) -> retry in %.1fs | status=%s category=%s reason=%s",
                    idx,
                    attempt + 1,
                    max_retries,
                    delay,
                    resp.final_status,
                    resp.failure_category,
                    resp.needs_review_reason,
                )
                await asyncio.sleep(delay)
                continue
            # Exhausted retries — classify as infrastructure error
            resp = _classify_infrastructure_error(resp)
            logger.info(
                "Ticket %d infra retries exhausted after %d attempts | final_status=%s",
                idx,
                max_retries,
                resp.final_status,
            )
            return resp

        # Success or non-infra failure — return as-is
        logger.info(
            "Ticket %d completed | attempt=%d/%d status=%s retries=%d category=%s latency=%.2fs",
            idx,
            attempt + 1,
            max_retries,
            resp.final_status,
            resp.retry_count,
            resp.failure_category or "none",
            resp.latency_seconds,
        )
        return resp

    # Should not reach here, but safety net
    return _build_infra_error_response(idx, request_id, max_retries, "max retries exceeded")


async def _process_tickets_async(tickets: list[str], request_id: str | None) -> list[ExtractResponse]:
    semaphore = asyncio.Semaphore(settings.BATCH_MAX_CONCURRENT_REQUESTS)
    tasks = [_process_ticket_with_retry(semaphore, text, i, request_id) for i, text in enumerate(tickets)]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    final: list[ExtractResponse] = []
    for i, r in enumerate(results):
        if isinstance(r, Exception):
            logger.error("Ticket %d unhandled exception: %s", i, r)
            final.append(_build_infra_error_response(i, request_id, settings.BATCH_MAX_RETRIES, str(r)))
        else:
            final.append(r)  # type: ignore[arg-type]
    return final


def _build_segment_preview(text: str, max_preview: int = 120) -> str:
    clean = " ".join(text.split())
    if len(clean) <= max_preview:
        return clean
    return clean[:max_preview].rsplit(" ", 1)[0] + "..."


def _aggregate_results(results: list[ExtractResponse]) -> dict:
    successful = sum(1 for r in results if r.final_status == "SUCCESS")
    repaired = sum(1 for r in results if r.final_status == "REPAIRED")
    needs_review = sum(1 for r in results if r.final_status == "NEEDS_REVIEW")
    infra_errors = sum(1 for r in results if r.final_status in _INFRA_STATUSES)
    failed = sum(
        1
        for r in results
        if r.final_status == "FAILED"
        or (
            r.validation_status == "failed"
            and r.final_status not in _INFRA_STATUSES
            and r.final_status not in ("NEEDS_REVIEW", "FAILED")
        )
    )
    return {
        "processed": len(results),
        "successful": successful,
        "repaired": repaired,
        "needs_review": needs_review,
        "failed": failed,
        "infrastructure_retry": infra_errors,
    }


# ── Batch Upload (Preview) ─────────────────────────────────────────────────


@router.post(
    "/v1/extract/batch/upload",
    response_model=BatchUploadResponse,
    status_code=200,
    tags=["extraction"],
    summary="Upload a document, detect tickets, return preview",
    description="Upload a PDF, TXT, DOCX, CSV, or JSON file. The document is ingested, "
    "intelligently segmented into individual tickets, and the segments are returned "
    "for preview. Tickets are NOT extracted yet — call POST /v1/extract/batch/process "
    "to run the AI extraction.",
    operation_id="batch_upload",
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request — missing file/text or unsupported format"},
        413: {"description": "File too large — maximum 100 MB"},
        500: {"model": ErrorResponse, "description": "Internal Server Error — ingestion failure"},
    },
)
async def extract_batch_upload(
    request: Request,
    file: UploadFile | None = File(None),
    text: str | None = Form(None),
):
    request_id = _get_request_id(request)
    if not file and not text:
        raise HTTPException(status_code=400, detail="Either 'file' or 'text' field is required")

    raw_text = ""
    file_name = None
    file_size = None
    file_type = None
    pages = 1
    warnings: list[str] = []

    if file:
        file_name = file.filename or "unknown"
        file_size = 0
        ext = _get_ext(file_name)
        supported = {".pdf", ".txt", ".docx", ".csv", ".json"}
        if ext not in supported:
            raise HTTPException(
                status_code=400, detail=f"Unsupported file type '{ext}'. Supported: {', '.join(sorted(supported))}"
            )

        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
        try:
            content = await file.read()
            file_size = len(content)
            max_size = 100 * 1024 * 1024
            if file_size > max_size:
                os.unlink(tmp.name)
                raise HTTPException(
                    status_code=413, detail=f"File too large ({file_size / 1024 / 1024:.1f} MB). Maximum is 100 MB."
                )
            tmp.write(content)
            tmp.flush()
            tmp.close()

            from app.ingestion import ingest_file

            result = ingest_file(tmp.name, file_name, file_size)
            raw_text = result.text
            file_type = result.file_type
            pages = result.pages or 1
            warnings = result.warnings
            log_event(
                logger,
                event="file_ingested",
                stage="ingestion",
                status="success",
                request_id=request_id,
                file_name=file_name,
                file_type=file_type,
                pages=pages,
                tickets_detected=result.tickets_detected,
            )
        except HTTPException:
            raise
        except Exception as exc:
            log_event(
                logger,
                event="ingestion_error",
                stage="ingestion",
                status="failed",
                request_id=request_id,
                exc_info=True,
            )
            raise HTTPException(status_code=500, detail=f"Ingestion failed: {exc}")
        finally:
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)
    else:
        raw_text = text or ""
        file_type = "TEXT"

    if not raw_text.strip():
        raise HTTPException(status_code=400, detail="No extractable text found in the input")

    from app.ingestion.segmenter import segment_document

    seg_result = segment_document(raw_text, use_ai=True)

    segment_responses: list[SegmentInfoResponse] = []
    for seg in seg_result.segments:
        segment_responses.append(
            SegmentInfoResponse(
                index=seg.index,
                word_count=seg.word_count,
                char_count=seg.char_count,
                preview=_build_segment_preview(seg.text),
                boundary_type=seg.boundary_type,
                valid=seg.valid,
                validation_message=seg.validation_message,
            )
        )

    session_id = str(uuid.uuid4())
    _segment_cache[session_id] = {
        "segments": [s.text for s in seg_result.segments],
        "file_name": file_name,
        "file_size": file_size,
        "file_type": file_type,
        "pages": pages,
        "warnings": warnings + seg_result.warnings,
        "request_id": request_id,
    }

    log_event(
        logger,
        event="batch_segmented",
        stage="segmentation",
        status="success",
        request_id=request_id,
        file_name=file_name,
        segments=len(segment_responses),
        method=seg_result.method,
    )

    return BatchUploadResponse(
        pages=pages,
        tickets_detected=len(segment_responses),
        processed=0,
        successful=0,
        repaired=0,
        needs_review=0,
        failed=0,
        results=[],
        file_name=file_name,
        file_size=file_size,
        file_type=file_type,
        warnings=warnings + seg_result.warnings,
        segments=segment_responses,
        segmentation_method=seg_result.method,
        session_id=session_id,
    )


# ── Batch Process (Execute AI on segments) ────────────────────────────────


@router.post(
    "/v1/extract/batch/process",
    response_model=BatchUploadResponse,
    status_code=200,
    tags=["extraction"],
    summary="Run AI extraction on previously segmented tickets",
    description="Takes a session ID from /v1/extract/batch/upload and processes "
    "each detected ticket through the AI extraction pipeline in parallel.",
    operation_id="batch_process",
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request — no tickets to process"},
        404: {"model": ErrorResponse, "description": "Session not found — re-upload the document"},
        500: {"model": ErrorResponse, "description": "Internal Server Error — extraction failure"},
    },
)
async def process_segments(
    req: ModifySegmentsRequest,
    request: Request,
):
    request_id = _get_request_id(request)
    session_id = req.session_id

    cache_entry = _segment_cache.get(session_id)
    if not cache_entry:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found. Re-upload the document.")

    tickets = req.tickets if req.tickets else cache_entry["segments"]

    if not tickets:
        raise HTTPException(status_code=400, detail="No tickets to process")

    log_event(
        logger,
        event="batch_processing_started",
        stage="batch",
        status="started",
        request_id=request_id,
        session_id=session_id,
        ticket_count=len(tickets),
        max_concurrent=settings.BATCH_MAX_CONCURRENT_REQUESTS,
        max_retries=settings.BATCH_MAX_RETRIES,
    )

    results = await _process_tickets_async(tickets, request_id)
    agg = _aggregate_results(results)

    log_event(
        logger,
        event="batch_processing_completed",
        stage="batch",
        status="success",
        request_id=request_id,
        session_id=session_id,
        **agg,
    )

    return BatchUploadResponse(
        pages=cache_entry.get("pages", 1),
        tickets_detected=len(tickets),
        file_name=cache_entry.get("file_name"),
        file_size=cache_entry.get("file_size"),
        file_type=cache_entry.get("file_type"),
        warnings=cache_entry.get("warnings", []),
        **agg,
        results=results,
        session_id=session_id,
    )


def _get_ext(filename: str) -> str:
    idx = filename.rfind(".")
    if idx == -1 or idx == 0:
        return ""
    return filename[idx:].lower()


@router.get(
    "/v1/history",
    response_model=HistoryResponse,
    tags=["history"],
    summary="Get extraction history",
    description="Returns paginated extraction history with latest first.",
    response_description="Paginated history of extractions.",
    operation_id="get_history",
    responses={
        422: {"model": ErrorResponse, "description": "Validation Error — invalid limit/offset"},
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
        final_status = r.get("final_status", "NEEDS_REVIEW")
        confidence_score = r.get("confidence_score", 0.0)
        validation_status = r.get("validation_status", "failed")

        status_map = {"SUCCESS": "completed", "REPAIRED": "completed", "NEEDS_REVIEW": "needs_review"}
        status = status_map.get(final_status, "failure" if validation_status == "failed" else "completed")

        attempt_details = []
        raw_attempts = r.get("repair_attempts") or []
        for a in raw_attempts:
            if isinstance(a, dict):
                attempt_details.append(
                    RepairAttemptDetail(
                        attempt=a.get("attempt", 1),
                        status=a.get("status", "failed"),
                        error=a.get("error"),
                    )
                )

        items.append(
            HistoryItem(
                request_id=str(r.get("id", "")),
                ticket_id=r.get("ticket_id", ""),
                original_ticket=raw[:500] if raw else "",
                extraction_summary=structured,
                confidence=confidence_score / 100.0,
                latency=latency,
                repair_attempts=attempt_details,
                provider=ACTIVE_PROVIDER,
                model=ACTIVE_MODEL,
                timestamp=r.get("created_at", ""),
                status=status,
                final_status=final_status,
                confidence_score=confidence_score,
                validation_status=validation_status,
                needs_review_reason=r.get("needs_review_reason"),
            )
        )

    return HistoryResponse(items=items, total=total, limit=limit, offset=offset)


@router.get(
    "/v1/system",
    response_model=SystemResponse,
    tags=["system"],
    summary="Combined system health and metrics",
    description="Returns health check and metrics in a single request to reduce dashboard polling.",
    response_description="Combined health and metrics payload.",
    operation_id="get_system",
    responses={
        503: {"description": "Service degraded — one or more dependencies are unhealthy"},
    },
)
def get_system(request: Request, response: Response):
    request_id = _get_request_id(request)
    health_result = health_service.check_all(request_id=request_id)
    if health_service.has_critical_failure(health_result.checks):
        response.status_code = 503
    metrics_result = metrics_service.get_metrics()
    return SystemResponse(health=health_result, metrics=metrics_result)
