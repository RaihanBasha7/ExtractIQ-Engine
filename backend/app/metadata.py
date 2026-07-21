"""
Extraction metadata builder.

Produces the ``ExtractionMetadata`` payload attached to every API response.

Responsible for:
    - Converting seconds to milliseconds
    - Determining validation status (``passed`` / ``failed``)
    - Reading the active provider and model from :mod:`app.config`

This module has zero dependency on the extraction pipeline internals.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field

from app.config import ACTIVE_MODEL, ACTIVE_PROVIDER


class ExtractionMetadata(BaseModel):
    """Metadata attached to every extraction response."""

    repair_attempts: int = Field(description="Number of repair retries performed.")
    latency_ms: int = Field(description="Processing time in milliseconds.")
    provider: str = Field(description="LLM provider used.")
    model: str = Field(description="Model name used.")
    validation: Literal["passed", "failed"] = Field(description="Schema validation outcome.")
    timestamp: datetime = Field(description="When the extraction completed (ISO-8601 UTC).")
    confidence_score: float = Field(default=0.0, description="Confidence score 0–100.")
    final_status: str = Field(default="NEEDS_REVIEW", description="SUCCESS, REPAIRED, or NEEDS_REVIEW.")
    needs_review_reason: str | None = Field(default=None, description="Reasons if final_status is NEEDS_REVIEW.")


def build_metadata(
    repair_attempts: int,
    latency_seconds: float,
    success: bool,
    confidence_score: float = 0.0,
    final_status: str = "NEEDS_REVIEW",
    needs_review_reason: str | None = None,
) -> ExtractionMetadata:
    return ExtractionMetadata(
        repair_attempts=repair_attempts,
        latency_ms=round(latency_seconds * 1000),
        provider=ACTIVE_PROVIDER,
        model=ACTIVE_MODEL,
        validation="passed" if success else "failed",
        timestamp=datetime.now(timezone.utc),
        confidence_score=confidence_score,
        final_status=final_status,
        needs_review_reason=needs_review_reason,
    )
