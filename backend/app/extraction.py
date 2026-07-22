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

import random
import time
from dataclasses import dataclass, field

import instructor
from groq import APIStatusError as GroqAPIStatusError
from groq import APITimeoutError as GroqAPITimeoutError
from groq import Groq
from groq import RateLimitError as GroqRateLimitError
from openai import APIStatusError as OpenAIAPIStatusError
from openai import APITimeoutError as OpenAIAPITimeoutError
from openai import OpenAI
from openai import RateLimitError as OpenAIRateLimitError
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
from app.repair_logging import RepairLog, create_repair_log
from app.repair_logging import record_attempt as _record_repair_entry
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
    GroqRateLimitError: "rate_limit",
    GroqAPITimeoutError: "timeout",
    GroqAPIStatusError: "api_error",
    OpenAIRateLimitError: "rate_limit",
    OpenAIAPITimeoutError: "timeout",
    OpenAIAPIStatusError: "api_error",
}


# ── Dataclasses ──────────────────────────────────────────────────────────


FINAL_STATUS_SUCCESS = "SUCCESS"
FINAL_STATUS_REPAIRED = "REPAIRED"
FINAL_STATUS_NEEDS_REVIEW = "NEEDS_REVIEW"
FINAL_STATUS_FAILED = "FAILED"
FINAL_STATUS_PROVIDER_RATE_LIMIT = "PROVIDER_RATE_LIMIT"
FINAL_STATUS_PROVIDER_TIMEOUT = "PROVIDER_TIMEOUT"
FINAL_STATUS_NETWORK_ERROR = "NETWORK_ERROR"
FINAL_STATUS_MODEL_ERROR = "MODEL_ERROR"


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
    final_status: str = FINAL_STATUS_NEEDS_REVIEW
    needs_review_reasons: list[str] = field(default_factory=list)

    @property
    def retry_count(self) -> int:
        return max(0, len(self.attempts) - 1)

    def set_final_status(self, status: str) -> None:
        self.final_status = status


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
    return "rate_limit" in lower or "429" in lower or "503" in lower or "timeout" in lower or "connection" in lower


def _map_infra_to_status(error_msg: str) -> str:
    lower = error_msg.lower()
    if "rate_limit" in lower or "429" in lower:
        return FINAL_STATUS_PROVIDER_RATE_LIMIT
    if "timeout" in lower:
        return FINAL_STATUS_PROVIDER_TIMEOUT
    if "connection" in lower:
        return FINAL_STATUS_NETWORK_ERROR
    return FINAL_STATUS_MODEL_ERROR


# ── LLM client factory ───────────────────────────────────────────────────

_client_cache: instructor.Instructor | None = None


def _get_instructor_mode() -> instructor.Mode:
    if LLM_PROVIDER == "groq":
        return instructor.Mode.TOOLS
    return instructor.Mode.JSON


def _get_client() -> instructor.Instructor:
    """Get a cached instructor client for the configured LLM provider."""
    global _client_cache
    if _client_cache is not None:
        return _client_cache
    mode = _get_instructor_mode()
    if LLM_PROVIDER == "featherless":
        raw_client = OpenAI(
            api_key=FEATHERLESS_API_KEY,
            base_url=FEATHERLESS_BASE_URL,
        )
        _client_cache = instructor.from_openai(raw_client, mode=mode)
    elif LLM_PROVIDER == "groq":
        _client_cache = instructor.from_groq(Groq(api_key=GROQ_API_KEY), mode=mode)
    else:
        raise RuntimeError(f"Unsupported LLM_PROVIDER: {LLM_PROVIDER}")
    return _client_cache


def _reset_client_cache() -> None:
    global _client_cache
    _client_cache = None


# ── Helper functions ─────────────────────────────────────────────────────


def _call_llm(
    client: instructor.Instructor,
    model_name: str,
    messages: list[dict],
    request_id: str | None = None,
    max_rate_retries: int = 2,
    timeout_seconds: float | None = None,
) -> TicketExtraction:
    """Make a single LLM call with structured output extraction.

    Automatically retries on 429 / rate-limit errors with exponential backoff
    so the UI never sees a raw provider error for transient throttling.
    """
    from app.settings import settings

    timeout = timeout_seconds or settings.LLM_TIMEOUT_SECONDS
    last_exc: Exception | None = None
    for attempt in range(max_rate_retries + 1):
        try:
            log_event(
                logger,
                event="llm_request",
                stage="llm",
                status="sending",
                request_id=request_id,
                model=model_name,
                messages=[{"role": m["role"], "content_preview": m["content"][:200]} for m in messages],
            )

            result = client.chat.completions.create(
                model=model_name,
                response_model=TicketExtraction,
                messages=messages,  # type: ignore[arg-type]
                max_retries=0,
                temperature=0,
                timeout=timeout,
            )

            log_event(
                logger,
                event="llm_response",
                stage="llm",
                status="received",
                request_id=request_id,
                model=model_name,
                response_preview=str(result)[:500] if result else "EMPTY",
            )

            return result

        except (GroqRateLimitError, OpenAIRateLimitError) as e:
            last_exc = e
            if attempt < max_rate_retries:
                delay = (2**attempt) + random.uniform(0, 1)
                log_event(
                    logger,
                    event="llm_rate_retry",
                    stage="llm",
                    status="retrying",
                    request_id=request_id,
                    model=model_name,
                    attempt=attempt + 1,
                    delay_seconds=round(delay, 2),
                )
                time.sleep(delay)
                continue
            raise

    raise last_exc  # type: ignore[misc]


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
    _record_repair_entry(
        repair_log,
        attempt_num,
        status,  # type: ignore[arg-type]
        error,
        time.monotonic() - attempt_start,
        request_id=request_id,
    )


def _build_repair_prompt(
    error_str: str,
    original_text: str,
) -> dict:
    """Create a user message that asks the LLM to fix a validation error.

    Includes the original ticket and exact validation errors so the model
    has full context to correct itself — eliminating guesswork.
    """
    parts = [
        "Your previous output failed schema validation with this error:",
        error_str,
        "",
        "Here is the original ticket text again:",
        original_text,
        "",
        "Re-extract the SAME ticket, fixing this specific issue. "
        "Do not change fields that were already correct. "
        "Return valid JSON matching the expected schema.",
    ]
    return {
        "role": "user",
        "content": "\n".join(parts),
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
        log_event(
            logger,
            event="extraction_attempt",
            stage="extraction",
            status="started",
            request_id=request_id,
            ticket_id=ticket_id,
            attempt=attempt_num,
            provider=ACTIVE_PROVIDER,
            model=model_name,
        )

        try:
            result_obj = _call_llm(client, model_name, messages, request_id=request_id)
            elapsed = time.monotonic() - start
            _record_extraction_attempt(
                repair_log, attempts, attempt_num, attempt_start, success=True, request_id=request_id
            )
            attempt_latency = round((time.monotonic() - attempt_start) * 1000)
            log_event(
                logger,
                event="extraction_success",
                stage="extraction",
                status="success",
                request_id=request_id,
                ticket_id=ticket_id,
                attempt=attempt_num,
                latency_ms=attempt_latency,
            )

            first_attempt = len(attempts) <= 1
            needs_review = _check_needs_review(result_obj)
            if first_attempt and not needs_review:
                final_status = FINAL_STATUS_SUCCESS
            elif not needs_review:
                final_status = FINAL_STATUS_REPAIRED
            else:
                final_status = FINAL_STATUS_NEEDS_REVIEW

            return ExtractionResult(
                ticket_id=ticket_id,
                success=True,
                data=result_obj,
                attempts=attempts,
                latency_seconds=elapsed,
                repair_log=repair_log,
                request_id=request_id,
                final_status=final_status,
                needs_review_reasons=needs_review,
            )

        except ValidationError as e:
            last_error = str(e)
            _record_extraction_attempt(
                repair_log, attempts, attempt_num, attempt_start, success=False, error=last_error, request_id=request_id
            )
            attempt_latency = round((time.monotonic() - attempt_start) * 1000)
            log_event(
                logger,
                event="validation_failed",
                stage="validation",
                status="failed",
                request_id=request_id,
                ticket_id=ticket_id,
                attempt=attempt_num,
                validation_error=last_error,
                latency_ms=attempt_latency,
            )

            if attempt_num > MAX_REPAIR_RETRIES:
                log_event(
                    logger,
                    event="retries_exhausted",
                    stage="extraction",
                    status="failed",
                    request_id=request_id,
                    ticket_id=ticket_id,
                    attempt=attempt_num,
                    reason="exhausted_retries",
                )
                break

            log_event(
                logger,
                event="repair_retry",
                stage="repair",
                status="retrying",
                request_id=request_id,
                ticket_id=ticket_id,
                attempt=attempt_num,
            )

            messages.append(_build_repair_prompt(last_error, clean_text))

        except (
            GroqRateLimitError,
            GroqAPITimeoutError,
            GroqAPIStatusError,
            OpenAIRateLimitError,
            OpenAIAPITimeoutError,
            OpenAIAPIStatusError,
        ) as e:
            last_error = str(e)
            _record_extraction_attempt(
                repair_log, attempts, attempt_num, attempt_start, success=False, error=last_error, request_id=request_id
            )
            reason = _INFRA_REASON.get(type(e), "provider_error")
            attempt_latency = round((time.monotonic() - attempt_start) * 1000)
            log_event(
                logger,
                event="infrastructure_failure",
                stage="extraction",
                status="failed",
                request_id=request_id,
                ticket_id=ticket_id,
                attempt=attempt_num,
                reason=reason,
                latency_ms=attempt_latency,
            )
            elapsed = time.monotonic() - start
            return ExtractionResult(
                ticket_id=ticket_id,
                success=False,
                data=None,
                attempts=attempts,
                failure_category=reason,
                latency_seconds=elapsed,
                repair_log=repair_log,
                request_id=request_id,
                final_status=_map_infra_to_status(last_error),
                needs_review_reasons=[f"Provider error: {reason}"],
            )

        except Exception as e:
            last_error = str(e)
            _record_extraction_attempt(
                repair_log, attempts, attempt_num, attempt_start, success=False, error=last_error, request_id=request_id
            )
            reason = _classify_failure(last_error)
            attempt_latency = round((time.monotonic() - attempt_start) * 1000)
            log_event(
                logger,
                event="extraction_error",
                stage="extraction",
                status="failed",
                request_id=request_id,
                ticket_id=ticket_id,
                attempt=attempt_num,
                reason=reason,
                latency_ms=attempt_latency,
            )

            if _is_non_retryable(last_error):
                log_event(
                    logger,
                    event="extraction_aborted",
                    stage="extraction",
                    status="failed",
                    request_id=request_id,
                    ticket_id=ticket_id,
                    attempt=attempt_num,
                    reason="non_retryable",
                )
                elapsed = time.monotonic() - start
                return ExtractionResult(
                    ticket_id=ticket_id,
                    success=False,
                    data=None,
                    attempts=attempts,
                    failure_category=reason,
                    latency_seconds=elapsed,
                    repair_log=repair_log,
                    request_id=request_id,
                    final_status=_map_infra_to_status(last_error),
                    needs_review_reasons=[f"Provider error: {reason}"],
                )

            if attempt_num > MAX_REPAIR_RETRIES:
                log_event(
                    logger,
                    event="retries_exhausted",
                    stage="extraction",
                    status="failed",
                    request_id=request_id,
                    ticket_id=ticket_id,
                    attempt=attempt_num,
                    reason="exhausted_retries",
                )
                break

            log_event(
                logger,
                event="repair_retry",
                stage="repair",
                status="retrying",
                request_id=request_id,
                ticket_id=ticket_id,
                attempt=attempt_num,
            )

            messages.append(_build_repair_prompt(last_error, clean_text))

    elapsed = time.monotonic() - start
    category = _classify_failure(last_error or "unknown")

    reasons = []
    if last_error:
        reasons.append(f"Validation failed: {_classify_failure(last_error)}")

    log_event(
        logger,
        event="extraction_failed",
        stage="extraction",
        status="failed",
        request_id=request_id,
        ticket_id=ticket_id,
        reason=category,
        latency_ms=round(elapsed * 1000),
    )

    if category in ("rate_limit", "timeout", "provider_error"):
        final_status = _map_infra_to_status(last_error or "")
    else:
        final_status = FINAL_STATUS_FAILED

    return ExtractionResult(
        ticket_id=ticket_id,
        success=False,
        data=None,
        attempts=attempts,
        failure_category=category,
        latency_seconds=elapsed,
        repair_log=repair_log,
        request_id=request_id,
        final_status=final_status,
        needs_review_reasons=reasons if reasons else ["Extraction failed"],
    )


def _check_needs_review(data: TicketExtraction) -> list[str]:
    """Determine if a successful extraction needs human review.

    Only flag when critical data is genuinely missing — not just when
    optional entities are absent (many valid tickets lack order IDs).

    Most demo tickets naturally contain customer names and account IDs,
    so only truly ambiguous extractions should trigger NEEDS_REVIEW.
    """
    reasons = []
    if (
        data.customer.name is None
        and data.customer.account_id is None
        and data.issue.subcategory is None
        and data.issue.product_or_service is None
    ):
        reasons.append("Insufficient customer, product, or issue details")
    if data.issue.category.value == "other" and data.issue.subcategory is None and data.requested_action is None:
        reasons.append("Category is 'other' with no clarifying details")
    if (
        data.issue.category.value == "other"
        and data.issue.subcategory is None
        and data.customer.name is None
        and data.customer.account_id is None
    ):
        reasons.append("No actionable information extracted")
    return reasons
