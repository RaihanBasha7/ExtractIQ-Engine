from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field


class EvaluationRecord(BaseModel):
    ticket_id: str = Field(description="Unique identifier of the processed ticket.")
    schema_valid: bool = Field(description="Whether the extraction passed schema validation.")
    repair_attempted: bool = Field(description="Whether at least one repair retry was attempted.")
    repair_success: bool = Field(description="Whether the repair loop produced a valid result.")
    retry_count: int = Field(ge=0, description="Number of retry attempts made during extraction.")
    latency_ms: int = Field(ge=0, description="Total extraction latency in milliseconds.")
    infra_error: bool = Field(description="Whether failure was caused by infrastructure (rate limit, timeout, etc.).")
    failure_reason: str | None = Field(default=None, description="Categorised reason for failure, if any.")
    expected_category: str | None = Field(default=None, description="Ground-truth issue category.")
    predicted_category: str | None = Field(default=None, description="Category predicted by the model.")
    field_accuracy: float | None = Field(
        default=None, ge=0.0, le=1.0, description="Fraction of expected fields that matched the prediction."
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), description="When this record was created."
    )

    failure_stage: str | None = Field(
        default=None,
        description="Stage at which the failure occurred "
        "(validation, infrastructure, unexpected, configuration, "
        "or None if successful).",
    )
    field_breakdown: dict[str, str] | None = Field(
        default=None, description="Per-field match status keyed by dotted path."
    )
    processing_time: float | None = Field(default=None, description="Total end-to-end processing time in seconds.")
    model_name: str | None = Field(default=None, description="Name of the model used for extraction.")
    provider: str | None = Field(default=None, description="LLM provider used (groq, featherless, etc.).")
    repair_attempts: int = Field(default=0, ge=0, description="Number of repair attempts made.")
    schema_version: str = Field(default="1.0", description="Version of the extraction schema used.")
