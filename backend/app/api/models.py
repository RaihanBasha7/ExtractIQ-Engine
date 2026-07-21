from datetime import datetime

from pydantic import BaseModel, Field

from app.metadata import ExtractionMetadata
from app.schema import TicketExtraction


class ExtractRequest(BaseModel):
    ticket_id: str
    raw_text: str


class RepairAttemptDetail(BaseModel):
    attempt: int = Field(description="1-based attempt number")
    status: str = Field(description="success or failed")
    error: str | None = Field(default=None, description="Error message if failed")


class ExtractResponse(BaseModel):
    ticket_id: str
    success: bool
    data: TicketExtraction | None = None
    confidence: float = 0.0
    metadata: ExtractionMetadata
    retry_count: int
    failure_category: str | None = None
    latency_seconds: float
    language: str
    request_id: str | None = None
    cleaned_text: str | None = None
    repair_attempts: list[RepairAttemptDetail] = Field(default_factory=list)
    confidence_score: float = 0.0
    validation_status: str = "failed"
    final_status: str = "NEEDS_REVIEW"
    needs_review_reason: str | None = None


class ExtractBatchRequest(BaseModel):
    tickets: list[ExtractRequest]


class SegmentInfoResponse(BaseModel):
    index: int
    word_count: int = 0
    char_count: int = 0
    preview: str = ""
    boundary_type: str = "auto"
    valid: bool = True
    validation_message: str | None = None


class BatchUploadResponse(BaseModel):
    pages: int = 0
    tickets_detected: int = 0
    processed: int = 0
    successful: int = 0
    repaired: int = 0
    needs_review: int = 0
    failed: int = 0
    infrastructure_retry: int = 0
    results: list[ExtractResponse] = Field(default_factory=list)
    file_name: str | None = None
    file_size: int | None = None
    file_type: str | None = None
    warnings: list[str] = Field(default_factory=list)
    segments: list[SegmentInfoResponse] = Field(default_factory=list)
    segmentation_method: str | None = None
    session_id: str | None = None


class ModifySegmentsRequest(BaseModel):
    session_id: str
    tickets: list[str]


class ExtractBatchResponse(BaseModel):
    results: list[ExtractResponse]


class HealthCheckDetail(BaseModel):
    status: str
    response_time_ms: float
    error: str | None = None
    provider: str | None = None
    model: str | None = None
    database_type: str | None = None
    checked_at: datetime | None = None


class HealthResponse(BaseModel):
    status: str = Field(description="Overall health: healthy, degraded.")
    timestamp: datetime = Field(description="Response timestamp (ISO-8601 UTC).")
    response_time_ms: float = Field(description="Total check duration in milliseconds.")
    checks: dict[str, HealthCheckDetail] = Field(description="Per-dependency check results.")


class VersionResponse(BaseModel):
    service: str = Field(description="Human-readable service name.")
    version: str = Field(description="Application version (semver).")
    api_version: str = Field(description="API interface version.")
    provider: str = Field(description="Active LLM provider.")
    model: str = Field(description="Active LLM model.")
    environment: str = Field(description="Deployment environment (e.g. development, staging, production).")
    python_version: str = Field(description="Python runtime version.")
    timestamp: datetime = Field(description="Response (request) timestamp, not build timestamp (ISO-8601 UTC).")


class MetricsResponse(BaseModel):
    total_requests: int = Field(description="Total extraction requests processed.")
    successful_extractions: int = Field(description="Number of successful schema-valid extractions.")
    failed_extractions: int = Field(description="Number of failed extractions.")
    schema_valid_rate: float = Field(description="Percentage of extractions that passed schema validation.")
    average_retry_count: float = Field(description="Average number of retry attempts across all extractions.")
    average_processing_time: float = Field(description="Average processing time in seconds.")
    failure_breakdown: dict[str, int] = Field(description="Count of failures grouped by failure category.")
    last_updated: datetime | None = Field(description="Timestamp of the most recent extraction result, or null if none exist.")
    latency_history: list[dict] = Field(default_factory=list, description="Time-series of latency values.")
    success_history: list[dict] = Field(default_factory=list, description="Time-series of success/failure.")
    retry_history: list[dict] = Field(default_factory=list, description="Time-series of retry counts.")
    average_confidence: float = Field(default=0.0, description="Average confidence score (0–100).")
    needs_review_count: int = Field(default=0, description="Number of extractions flagged NEEDS_REVIEW.")
    repair_count: int = Field(default=0, description="Number of extractions that required repairs.")
    repair_success_count: int = Field(default=0, description="Number of extractions that succeeded after repairs.")
    failure_rate: float = Field(default=0.0, description="Percentage of extractions that failed or need review.")


class HistoryQueryParams(BaseModel):
    limit: int = Field(default=50, ge=1, le=200, description="Number of records to return.")
    offset: int = Field(default=0, ge=0, description="Number of records to skip.")


class HistoryItem(BaseModel):
    request_id: str = Field(description="Unique extraction identifier.")
    ticket_id: str = Field(description="Original ticket identifier.")
    original_ticket: str = Field(description="Raw ticket text before preprocessing.")
    extraction_summary: dict | None = Field(default=None, description="Extracted structured JSON.")
    confidence: float = Field(default=0.0, description="Confidence score (0–100).")
    latency: float = Field(default=0.0, description="Processing time in seconds.")
    repair_attempts: list[RepairAttemptDetail] = Field(default_factory=list, description="Detailed repair attempts.")
    provider: str = Field(default="", description="LLM provider.")
    model: str = Field(default="", description="LLM model.")
    timestamp: str = Field(default="", description="ISO-8601 timestamp of extraction.")
    status: str = Field(default="", description="completed, failure, or needs_review")
    final_status: str = Field(default="NEEDS_REVIEW", description="SUCCESS, REPAIRED, or NEEDS_REVIEW.")
    confidence_score: float = Field(default=0.0, description="Confidence score (0–100).")
    validation_status: str = Field(default="failed", description="passed or failed")
    needs_review_reason: str | None = Field(default=None, description="Reasons if NEEDS_REVIEW.")


class HistoryResponse(BaseModel):
    items: list[HistoryItem]
    total: int
    limit: int
    offset: int


class SystemResponse(BaseModel):
    health: HealthResponse
    metrics: MetricsResponse
