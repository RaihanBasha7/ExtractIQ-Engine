from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, Field


class ErrorDetails(BaseModel):
    field: Optional[str] = None
    issue: Optional[str] = None
    suggestion: Optional[str] = None


class ErrorResponse(BaseModel):
    success: bool = Field(default=False, description="Indicates the request failed.")
    error_code: str = Field(description="Machine-readable error code.", example="HTTP_400")
    message: str = Field(description="Human-readable error message.", example="Invalid request payload")
    details: dict[str, Any] | ErrorDetails | None = Field(default=None, description="Additional error details (validation errors, etc.).")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When the error occurred (ISO 8601 format).",
    )
    request_id: Optional[str] = Field(default=None, description="Unique identifier for the request.", example="550e8400-e29b-41d4-a716-446655440000")