"""Tests for error handling throughout the application."""

from __future__ import annotations

from unittest.mock import MagicMock, patch


class TestInvalidRequestBody:
    def test_invalid_json_body(self, client):
        response = client.post(
            "/v1/extract",
            data="not valid json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422

    def test_empty_body(self, client):
        response = client.post("/v1/extract", json={})
        assert response.status_code == 422

    def test_wrong_field_types(self, client):
        response = client.post(
            "/v1/extract",
            json={"ticket_id": 123, "raw_text": True},
        )
        assert response.status_code == 422


class TestMissingText:
    def test_extract_missing_text_field(self, client):
        response = client.post(
            "/v1/extract",
            json={"ticket_id": "TKT-001"},
        )
        assert response.status_code == 422

    def test_extract_empty_text(self, client):
        response = client.post(
            "/v1/extract",
            json={"ticket_id": "TKT-001", "raw_text": ""},
        )
        assert response.status_code == 400


class TestEmptyInput:
    def test_batch_with_all_empty(self, client):
        response = client.post(
            "/v1/extract/batch",
            json={"tickets": []},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 0

    def test_batch_with_mixed_empty(self, client):
        response = client.post(
            "/v1/extract/batch",
            json={
                "tickets": [
                    {"ticket_id": "T1", "raw_text": ""},
                    {"ticket_id": "T2", "raw_text": "valid"},
                ]
            },
        )
        data = response.json()
        assert data["results"][0]["success"] is False
        assert data["results"][0]["failure_category"] == "empty_text"


class TestInternalExceptions:
    def test_unhandled_exception_returns_500(self, client):
        with patch("app.api.routes.process_ticket") as mock:
            mock.side_effect = RuntimeError("Unexpected internal error")
            response = client.post(
                "/v1/extract",
                json={"ticket_id": "TKT-001", "raw_text": "Some text"},
            )
        assert response.status_code == 500
        data = response.json()
        assert data["error_code"] == "INTERNAL_ERROR"

    def test_500_response_structure(self, client):
        with patch("app.api.routes.process_ticket") as mock:
            mock.side_effect = RuntimeError("Boom")
            response = client.post(
                "/v1/extract",
                json={"ticket_id": "TKT-001", "raw_text": "Some text"},
            )
        data = response.json()
        assert "error_code" in data
        assert "message" in data
        assert "timestamp" in data
        assert "request_id" in data


class TestErrorResponseModel:
    def test_error_response_minimal(self):
        from app.api.error_models import ErrorResponse

        error = ErrorResponse(
            error_code="HTTP_400",
            message="Bad request",
        )
        assert error.success is False
        assert error.details is None
        assert error.request_id is None
        assert error.timestamp is not None

    def test_error_response_with_details(self):
        from app.api.error_models import ErrorDetails, ErrorResponse

        details = ErrorDetails(field="email", issue="invalid format", suggestion="provide valid email")
        error = ErrorResponse(
            error_code="HTTP_422",
            message="Validation error",
            details=details,
            request_id="REQ-001",
        )
        assert error.details.field == "email"
        assert error.details.issue == "invalid format"
        assert error.request_id == "REQ-001"

    def test_error_response_serialization(self):
        from app.api.error_models import ErrorResponse

        error = ErrorResponse(error_code="HTTP_500", message="Server error")
        dumped = error.model_dump(mode="json")
        assert dumped["error_code"] == "HTTP_500"
        assert dumped["success"] is False
        assert "timestamp" in dumped


class TestHTTPExceptionHandler:
    def test_400_error_format(self, client):
        response = client.post(
            "/v1/extract",
            json={"ticket_id": "TKT-001", "raw_text": ""},
        )
        data = response.json()
        assert data["error_code"] == "HTTP_400"
        assert data["success"] is False
        assert "request_id" in data

    def test_404_error_format(self, client):
        response = client.get("/nonexistent-path-xyz")
        assert response.status_code == 404
        assert response.headers["content-type"] == "application/json"


class TestValidationErrorHandler:
    def test_request_validation_error_422(self, client):
        response = client.post(
            "/v1/extract",
            json={"invalid": "data"},
        )
        assert response.status_code == 422
        data = response.json()
        assert "VALIDATION_ERROR" in data.get("error_code", "")


class TestTimeoutHandling:
    def test_timeout_during_extraction(self, client):
        """APITimeoutError in extract_ticket is caught by process_ticket.
        Returns a 200 with success=False, not a 500."""
        from groq import APITimeoutError

        with patch("app.api.service.extract_ticket") as mock:
            mock.side_effect = APITimeoutError("Request timed out")
            response = client.post(
                "/v1/extract",
                json={"ticket_id": "TKT-001", "raw_text": "Some text"},
            )
        data = response.json()
        assert data["success"] is False


class TestRateLimitHandling:
    def test_rate_limit_during_extraction(self, client):
        """RateLimitError in extract_ticket is caught by process_ticket.
        Returns a 200 with success=False."""
        from groq import RateLimitError

        with patch("app.api.service.extract_ticket") as mock_extract:
            mock_extract.side_effect = RateLimitError(
                "rate_limit",
                response=MagicMock(status_code=429),
                body={"error": "rate limit"},
            )
            response = client.post(
                "/v1/extract",
                json={"ticket_id": "TKT-001", "raw_text": "Some text"},
            )
        data = response.json()
        assert data["success"] is False


class TestServiceErrorHandling:
    def test_process_ticket_handles_exceptions(self):
        from app.api.service import process_ticket

        with patch("app.api.service.extract_ticket") as mock_extract:
            mock_extract.side_effect = RuntimeError("API key error")
            result = process_ticket("TKT-001", "Some text", request_id="REQ-TEST")
        assert result.success is False
        assert result.data is None
        assert result.retry_count == 0
