"""
Confidence scoring for ticket extractions.

This module is decoupled from the extraction pipeline internals.

Formula
-------
Start Score = 100

Penalties (subtracted from start score):
    15  ×  repair_attempts       each re-prompt after a failed extraction
    5   ×  missing_fields        optional/list fields left as ``None`` or empty
    25     if repaired           extraction required at least one re-prompt

Special rule
~~~~~~~~~~~~
If the extraction ultimately failed (``success=False``), the score is always
10 — the minimum — regardless of how many retries were attempted.

Clamping
~~~~~~~~
Final score clamped to ``[10, 100]``.

Rounding
~~~~~~~~
Rounded to integer.

Threshold
~~~~~~~~~
CONFIDENCE_THRESHOLD = 70
Extractions below this threshold should be flagged NEEDS_REVIEW.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.schema import TicketExtraction

CONFIDENCE_THRESHOLD: int = 70


@dataclass
class ConfidenceMetrics:
    """Lightweight input for confidence calculation."""

    success: bool
    retry_count: int
    data: TicketExtraction | None = None


_OPTIONAL_FIELD_PATHS: tuple[tuple[str, ...], ...] = (
    ("requested_action",),
    ("customer", "name"),
    ("customer", "account_id"),
    ("issue", "subcategory"),
    ("issue", "product_or_service"),
    ("entities", "order_ids"),
    ("entities", "dates_mentioned"),
    ("entities", "amounts_mentioned"),
)


def _get_field_value(data: TicketExtraction, path: tuple[str, ...]):
    value = data
    for attr in path:
        value = getattr(value, attr)
    return value


def _count_missing_optional_fields(data: TicketExtraction) -> int:
    count = 0
    for path in _OPTIONAL_FIELD_PATHS:
        value = _get_field_value(data, path)
        if value is None or (isinstance(value, list) and not value):
            count += 1
    return count


def compute_confidence(metrics: ConfidenceMetrics) -> float:
    if not metrics.success:
        return 10.0

    score = 100.0
    score -= 15.0 * metrics.retry_count

    if metrics.data is not None:
        score -= 5.0 * _count_missing_optional_fields(metrics.data)

    if metrics.retry_count > 0:
        score -= 25.0

    score = max(10.0, min(100.0, score))
    return round(score, 1)
