from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class ErrorDetails(BaseModel):
    field: str | None = None
    issue: str | None = None
    suggestion: str | None = None


class ErrorResponse(BaseModel):
    success: bool = Field(default=False, description="Indicates the request failed.")
    error_code: str = Field(description="Machine-readable error code.")
    message: str = Field(description="Human-readable error message.")
    details: Any = Field(default=None, description="Additional error details (validation errors, etc.).")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When the error occurred (ISO 8601 format).",
    )
    request_id: str | None = Field(default=None, description="Unique identifier for the request.")