"""
Structured repair logging for extraction attempts.

Records every LLM call attempt made during the Model-Driven Repair Loop
in a consistent, machine-readable format.  Each entry carries the
``request_id`` from the originating HTTP request so that individual
attempts can be correlated across the entire pipeline.

Each extraction attempt produces one :class:`RepairLogEntry` carrying:
    - attempt number
    - success / failure status
    - error type and message (parsed automatically from the raw error string)
    - per-attempt latency in milliseconds
    - the correlation ``request_id`` (if available)
    - UTC timestamp

All entries are collected in a :class:`RepairLog` which is attached to
the :class:`~app.extraction.ExtractionResult` for downstream inspection.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal


@dataclass
class RepairLogEntry:
    """A single extraction attempt record, correlated via ``request_id``."""

    attempt: int
    status: Literal["success", "failed"]
    error_type: str | None
    error_message: str | None
    latency_ms: int
    timestamp: datetime
    request_id: str | None = None


@dataclass
class RepairLog:
    """Ordered collection of extraction attempt records."""

    entries: list[RepairLogEntry] = field(default_factory=list)

    def add_entry(self, entry: RepairLogEntry) -> None:
        self.entries.append(entry)

    @property
    def total_attempts(self) -> int:
        return len(self.entries)

    @property
    def successful_attempts(self) -> int:
        return sum(1 for e in self.entries if e.status == "success")

    @property
    def failed_attempts(self) -> int:
        return sum(1 for e in self.entries if e.status == "failed")

    def summary(self) -> dict:
        """Return a compact summary of the repair log.

        Example output::

            {
                "attempts": 2,
                "successful": 1,
                "failed": 1,
                "total_latency_ms": 727,
            }
        """
        return {
            "attempts": self.total_attempts,
            "successful": self.successful_attempts,
            "failed": self.failed_attempts,
            "total_latency_ms": sum(e.latency_ms for e in self.entries),
        }


# ── Error parsing ────────────────────────────────────────────────────────


def _parse_error(error: str | None) -> tuple[str | None, str | None]:
    """Split a raw error string into ``(error_type, error_message)``.

    Heuristic classification (by keyword in lowercased text):

    ====================  ===============================
    Keyword               Inferred type
    ====================  ===============================
    ``validation error``  ``ValidationError``
    ``rate_limit``        ``RateLimitError``
    ``429``               ``RateLimitError``
    ``timeout``           ``TimeoutError``
    ``connection``        ``TimeoutError``
    ``503``               ``APIStatusError``
    default               ``UnknownError``
    ====================  ===============================

    If none of the keywords match and the string follows an
    ``ExceptionType: message`` pattern, the colon-separated type is used.
    """
    if error is None:
        return None, None

    lower = error.lower()

    # Ordered by specificity — Pydantic ValidationError first.
    if "validation error" in lower:
        return "ValidationError", error
    if "rate_limit" in lower or "429" in lower:
        return "RateLimitError", error
    if "timeout" in lower or "connection" in lower:
        return "TimeoutError", error
    if "503" in lower:
        return "APIStatusError", error

    # Try "ExceptionType: message" convention (common for stdlib / SDK errors).
    if ": " in error:
        parts = error.split(": ", 1)
        candidate = parts[0].strip()
        if candidate and candidate[0].isupper():
            return candidate, parts[1]

    return "UnknownError", error


# ── Helper functions ─────────────────────────────────────────────────────


def create_repair_log() -> RepairLog:
    """Create an empty :class:`RepairLog`."""
    return RepairLog()


def record_attempt(
    log: RepairLog,
    attempt: int,
    status: Literal["success", "failed"],
    error: str | None,
    latency_seconds: float,
    timestamp: datetime | None = None,
    request_id: str | None = None,
) -> None:
    """Record a single extraction attempt into *log*.

    Parameters
    ----------
    log:
        The log to append to.
    attempt:
        1-based attempt number.
    status:
        ``"success"`` if the LLM returned valid structured data,
        ``"failed"`` otherwise.
    error:
        Raw error string, or ``None`` on success.  Automatically parsed
        into :attr:`RepairLogEntry.error_type` and
        :attr:`RepairLogEntry.error_message` by :func:`_parse_error`.
    latency_seconds:
        Wall-clock duration of this attempt in seconds (converted to
        milliseconds internally).
    timestamp:
        When the attempt finished. Defaults to UTC now.
    request_id:
        Correlation ID from the originating HTTP request.
    """
    error_type, error_message = _parse_error(error)
    log.add_entry(RepairLogEntry(
        attempt=attempt,
        status=status,
        error_type=error_type,
        error_message=error_message,
        latency_ms=round(latency_seconds * 1000),
        timestamp=timestamp or datetime.now(timezone.utc),
        request_id=request_id,
    ))



