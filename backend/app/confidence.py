"""
Confidence scoring for ticket extractions.

This module is decoupled from the extraction pipeline internals.
It depends only on Pydantic schema models and a lightweight
``ConfidenceMetrics`` dataclass.

Formula
-------
Start Score = 1.00

Penalties (subtracted from start score):
    0.15  ×  repair_attempts       each re-prompt after a failed extraction
    0.05  ×  missing_fields        optional/list fields left as ``None`` or empty
    0.25     if repaired           extraction required at least one re-prompt

Special rule
~~~~~~~~~~~~
If the extraction ultimately failed (``success=False``), the score is always
0.10 — the minimum — regardless of how many retries were attempted.

Clamping
~~~~~~~~
Final score clamped to ``[0.10, 1.00]``.

Rounding
~~~~~~~~
Rounded to two decimal places.

Examples
--------
    Perfect extraction (zero repairs, all fields populated)
        → 1.00

    One repair needed, no missing fields
        → 1.00 - 0.15 - 0.25 = 0.60

    One repair needed, 5 optional fields missing
        → 1.00 - 0.15 - 0.25 - 0.25 = 0.35

    Extraction ultimately failed
        → 0.10
"""

from __future__ import annotations

from dataclasses import dataclass

from app.schema import TicketExtraction


@dataclass
class ConfidenceMetrics:
    """Lightweight input for confidence calculation.

    Carries only the fields required for scoring so that
    :func:`compute_confidence` has no dependency on
    :class:`app.extraction.ExtractionResult`.
    """

    success: bool
    retry_count: int
    data: TicketExtraction | None = None


# ── Centralised field catalogue ──────────────────────────────────────────
# Each entry is a dotted path from the root ``TicketExtraction`` object.
# To add a new optional field, insert its path here — nothing else needs
# to change.

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
    """Walk *path* of attribute names and return the final value."""
    value = data
    for attr in path:
        value = getattr(value, attr)
    return value


def _count_missing_optional_fields(data: TicketExtraction) -> int:
    """Return how many optional / list fields are unpopulated.

    A field counts as missing when it is ``None`` (for ``Optional[...]``
    fields) or an empty list (for ``list[...]`` fields with a default
    factory of ``[]``).
    """
    count = 0
    for path in _OPTIONAL_FIELD_PATHS:
        value = _get_field_value(data, path)
        if value is None or (isinstance(value, list) and not value):
            count += 1
    return count


def compute_confidence(metrics: ConfidenceMetrics) -> float:
    """Compute an intelligent confidence score for an extraction result.

    Parameters
    ----------
    metrics : ConfidenceMetrics
        Lightweight struct containing ``success``, ``retry_count`` and
        the extracted ``data`` (if any).

    Returns
    -------
    float
        Confidence score clamped to ``[0.10, 1.00]`` and rounded to two
        decimal places.
    """
    if not metrics.success:
        return 0.10

    score = 1.0
    score -= 0.15 * metrics.retry_count

    if metrics.data is not None:
        score -= 0.05 * _count_missing_optional_fields(metrics.data)

    if metrics.retry_count > 0:
        score -= 0.25

    score = max(0.10, min(1.00, score))
    return round(score, 2)
