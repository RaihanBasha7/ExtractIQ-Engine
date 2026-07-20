"""
Extraction & Repair Agent — Model-Driven Repair Loop.

Core differentiator: instead of falling back to regex on schema validation
failure, we feed the exact Pydantic error back to the LLM in a follow-up
turn and ask it to fix only the specific violation.

The loop is implemented manually (not relying on instructor's built-in
``max_retries``) so that every attempt produces honest telemetry — retry
count, per-attempt validation error, and per-attempt latency — which the
Evaluation Harness and ``RepairLog`` depend on.

Every log line includes ``request_id`` (when available) so that a single
extraction can be traced across the entire pipeline.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

import instructor
from groq import APIStatusError, APITimeoutError, Groq, RateLimitError
from openai import OpenAI
from pydantic import ValidationError

from app.config import (
    ACTIVE_MODEL,
    ACTIVE_PROVIDER,
    FEATHERLESS_API_KEY,
    FEATHERLESS_BASE_URL,
    GROQ_API_KEY,
    LLM_PROVIDER,
    MAX_REPAIR_RETRIES,
)
from app.logging import get_logger, log_event
from app.repair_logging import RepairLog, create_repair_log, record_attempt as _record_repair_entry
from app.schema import TicketExtraction

logger = get_logger(__name__)

SYSTEM_PROMPT = """You are a structured-data extraction engine for a customer support platform.
Extract the ticket into the exact JSON schema provided. Rules:
- Only use information explicitly present in the text. Never invent names, IDs, dates, or amounts.
- If a field is not mentioned, use null (or an empty list for array fields).
- category, urgency, sentiment, and resolution_status MUST be one of the allowed enum values —
  pick the closest reasonable match based on tone and content, never leave them ambiguous.
- entities.order_ids / dates_mentioned / amounts_mentioned should only include values that
  literally appear in the text.
"""

# ── Infrastructure error → log reason mapping ────────────────────────────

_INFRA_REASON: dict[type, str] = {
    RateLimitError: "rate_limit",
    APITimeoutError: "timeout",
    APIStatusError: "api_error",
}


# ── Dataclasses ──────────────────────────────────────────────────────────


@dataclass
class ExtractionAttempt:
    """A single LLM invocation during the repair loop."""

    attempt_number: int
    success: bool
    error: str | None = None


@dataclass
class ExtractionResult:
    """Result of the full Model-Driven Repair Loop for one ticket."""

    ticket_id: str
    success: bool
    data: TicketExtraction | None
    attempts: list[ExtractionAttempt] = field(default_factory=list)
    failure_category: str | None = None
    latency_seconds: float = 0.0
    repair_log: RepairLog | None = None
    request_id: str | None = None

    @property
    def retry_count(self) -> int:
        return max(0, len(self.attempts) - 1)


# ── Error classification ─────────────────────────────────────────────────


def _classify_failure(error_msg: str) -> str:
    lower = error_msg.lower()
    if "rate_limit" in lower or "429" in lower:
        return "rate_limit"
    if "timeout" in lower:
        return "timeout"
    if "connection" in lower:
        return "timeout"
    if "503" in lower:
        return "provider_error"
    if "enum" in lower or "not a valid" in lower:
        return "validation_error"
    if "field required" in lower or "missing" in lower:
        return "validation_error"
    if "json" in lower or "decode" in lower:
        return "validation_error"
    if "extra" in lower:
        return "validation_error"
    return "unexpected_error"


def _is_non_retryable(error_msg: str) -> bool:
    """Provider-side errors (rate limits, timeouts, 5xx) that won't be fixed by
    re-prompting. Fail fast instead of burning retries on infrastructure problems."""
    lower = error_msg.lower()
    return (
        "rate_limit" in lower
        or "429" in lower
        or "503" in lower
        or "timeout" in lower
        or "connection" in lower
    )


# ── LLM client factory ───────────────────────────────────────────────────

_client_cache: instructor.Instructor | None = None


def _get_client() -> instructor.Instructor:
    """Get a cached instructor client for the configured LLM provider."""
    global _client_cache
    if _client_cache is not None:
        return _client_cache
    if LLM_PROVIDER == "featherless":
        raw_client = OpenAI(
            api_key=FEATHERLESS_API_KEY,
            base_url=FEATHERLESS_BASE_URL,
        )
        _client_cache = instructor.from_openai(raw_client, mode=instructor.Mode.TOOLS)
    elif LLM_PROVIDER == "groq":
        _client_cache = instructor.from_groq(Groq(api_key=GROQ_API_KEY), mode=instructor.Mode.TOOLS)
    else:
        raise RuntimeError(f"Unsupported LLM_PROVIDER: {LLM_PROVIDER}")
    return _client_cache


# ── Helper functions ─────────────────────────────────────────────────────


def _call_llm(
    client: instructor.Instructor,
    model_name: str,
    messages: list[dict],
) -> TicketExtraction:
    """Make a single LLM call with structured output extraction."""
    return client.chat.completions.create(
        model=model_name,
        response_model=TicketExtraction,
        messages=messages,
        max_retries=0,
        temperature=0,
    )


def _record_extraction_attempt(
    repair_log: RepairLog,
    attempts: list[ExtractionAttempt],
    attempt_num: int,
    attempt_start: float,
    success: bool,
    error: str | None = None,
    request_id: str | None = None,
) -> None:
    attempts.append(ExtractionAttempt(attempt_number=attempt_num, success=success, error=error))
    status = "success" if success else "failed"
    _record_repair_entry(repair_log, attempt_num, status, error, time.monotonic() - attempt_start, request_id=request_id)


def _build_repair_prompt(error_str: str) -> dict:
    """Create a user message that asks the LLM to fix a validation error."""
    return {
        "role": "user",
        "content": (
            "Your previous output failed schema validation with this error:\n"
            f"{error_str}\n\n"
            "Re-extract the SAME ticket, fixing this specific issue. "
            "Do not change fields that were already correct."
        ),
    }


# ── Main pipeline ────────────────────────────────────────────────────────


def extract_ticket(
    ticket_id: str,
    clean_text: str,
    client: instructor.Instructor | None = None,
    request_id: str | None = None,
) -> ExtractionResult:
    """
    Run extraction with the Model-Driven Repair Loop.

    Attempt 1: plain extraction call.
    On ValidationError: re-prompt with the original text PLUS the specific
    Pydantic error, up to MAX_REPAIR_RETRIES total additional attempts.
    On exhausting retries: return success=False with failure_category set —
    NEVER fall back to regex or return a hallucinated "valid" object.
    """
    client = client or _get_client()
    model_name = ACTIVE_MODEL

    attempts: list[ExtractionAttempt] = []
    repair_log = create_repair_log()
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"ticket_id: {ticket_id}\n\nTicket text:\n{clean_text}"},
    ]

    start = time.monotonic()
    last_error: str | None = None

    for attempt_num in range(1, MAX_REPAIR_RETRIES + 2):
        attempt_start = time.monotonic()
        log_event(logger, event="extraction_attempt", stage="extraction", status="started", request_id=request_id, ticket_id=ticket_id, attempt=attempt_num, provider=ACTIVE_PROVIDER, model=model_name)

        try:
            result = _call_llm(client, model_name, messages)
            elapsed = time.monotonic() - start
            _record_extraction_attempt(repair_log, attempts, attempt_num, attempt_start, success=True, request_id=request_id)
            attempt_latency = round((time.monotonic() - attempt_start) * 1000)
            log_event(logger, event="extraction_success", stage="extraction", status="success", request_id=request_id, ticket_id=ticket_id, attempt=attempt_num, latency_ms=attempt_latency)
            return ExtractionResult(
                ticket_id=ticket_id,
                success=True,
                data=result,
                attempts=attempts,
                latency_seconds=elapsed,
                repair_log=repair_log,
                request_id=request_id,
            )

        except ValidationError as e:
            last_error = str(e)
            _record_extraction_attempt(repair_log, attempts, attempt_num, attempt_start, success=False, error=last_error, request_id=request_id)
            attempt_latency = round((time.monotonic() - attempt_start) * 1000)
            log_event(logger, event="validation_failed", stage="validation", status="failed", request_id=request_id, ticket_id=ticket_id, attempt=attempt_num, validation_error=last_error, latency_ms=attempt_latency)

            if attempt_num > MAX_REPAIR_RETRIES:
                log_event(logger, event="retries_exhausted", stage="extraction", status="failed", request_id=request_id, ticket_id=ticket_id, attempt=attempt_num, reason="exhausted_retries")
                break

            log_event(logger, event="repair_retry", stage="repair", status="retrying", request_id=request_id, ticket_id=ticket_id, attempt=attempt_num)
            messages.append(_build_repair_prompt(last_error))

        except (RateLimitError, APITimeoutError, APIStatusError) as e:
            last_error = str(e)
            _record_extraction_attempt(repair_log, attempts, attempt_num, attempt_start, success=False, error=last_error, request_id=request_id)
            reason = _INFRA_REASON[type(e)]
            attempt_latency = round((time.monotonic() - attempt_start) * 1000)
            log_event(logger, event="infrastructure_failure", stage="extraction", status="failed", request_id=request_id, ticket_id=ticket_id, attempt=attempt_num, reason=reason, latency_ms=attempt_latency)
            break

        except Exception as e:
            last_error = str(e)
            _record_extraction_attempt(repair_log, attempts, attempt_num, attempt_start, success=False, error=last_error, request_id=request_id)
            reason = _classify_failure(last_error)
            attempt_latency = round((time.monotonic() - attempt_start) * 1000)
            log_event(logger, event="extraction_error", stage="extraction", status="failed", request_id=request_id, ticket_id=ticket_id, attempt=attempt_num, reason=reason, latency_ms=attempt_latency)

            if _is_non_retryable(last_error):
                log_event(logger, event="extraction_aborted", stage="extraction", status="failed", request_id=request_id, ticket_id=ticket_id, attempt=attempt_num, reason="non_retryable")
                break

            if attempt_num > MAX_REPAIR_RETRIES:
                log_event(logger, event="retries_exhausted", stage="extraction", status="failed", request_id=request_id, ticket_id=ticket_id, attempt=attempt_num, reason="exhausted_retries")
                break

            log_event(logger, event="repair_retry", stage="repair", status="retrying", request_id=request_id, ticket_id=ticket_id, attempt=attempt_num)
            messages.append(_build_repair_prompt(last_error))

    elapsed = time.monotonic() - start
    category = _classify_failure(last_error or "unknown")
    log_event(logger, event="extraction_failed", stage="extraction", status="failed", request_id=request_id, ticket_id=ticket_id, reason=category, latency_ms=round(elapsed * 1000))
    return ExtractionResult(
        ticket_id=ticket_id,
        success=False,
        data=None,
        attempts=attempts,
        failure_category=category,
        latency_seconds=elapsed,
        repair_log=repair_log,
        request_id=request_id,
    )
