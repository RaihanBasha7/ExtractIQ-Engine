"""Tests for API endpoints."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoint:
    def test_health_returns_200(self, client: TestClient):
        response = client.get("/health")
        assert response.status_code in (200, 503)

    def test_health_response_structure(self, client: TestClient):
        response = client.get("/health")
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "response_time_ms" in data
        assert "checks" in data
        assert "api" in data["checks"]
        assert "database" in data["checks"]

    def test_health_checks_have_required_fields(self, client: TestClient):
        response = client.get("/health")
        data = response.json()
        for name, check in data["checks"].items():
            assert "status" in check
            assert "response_time_ms" in check


class TestVersionEndpoint:
    def test_version_returns_200(self, client: TestClient):
        response = client.get("/version")
        assert response.status_code == 200

    def test_version_response_structure(self, client: TestClient):
        response = client.get("/version")
        data = response.json()
        assert "service" in data
        assert "version" in data
        assert "api_version" in data
        assert "provider" in data
        assert "model" in data
        assert "environment" in data
        assert "python_version" in data
        assert "timestamp" in data

    def test_version_values(self, client: TestClient):
        response = client.get("/version")
        data = response.json()
        assert data["service"] == "OneInbox API"
        assert data["version"] == "0.1.0"
        assert data["api_version"] == "v1"
        assert data["environment"] == "test"


class TestMetricsEndpoint:
    def test_metrics_returns_200(self, client: TestClient):
        response = client.get("/v1/metrics")
        assert response.status_code == 200

    def test_metrics_response_structure(self, client: TestClient):
        response = client.get("/v1/metrics")
        data = response.json()
        assert "total_requests" in data
        assert "successful_extractions" in data
        assert "failed_extractions" in data
        assert "schema_valid_rate" in data
        assert "average_retry_count" in data
        assert "average_processing_time" in data
        assert "failure_breakdown" in data


class TestHistoryEndpoint:
    def test_history_returns_200(self, client: TestClient):
        response = client.get("/v1/history")
        assert response.status_code == 200

    def test_history_default_pagination(self, client: TestClient):
        response = client.get("/v1/history")
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert data["limit"] == 50
        assert data["offset"] == 0

    def test_history_custom_pagination(self, client: TestClient):
        response = client.get("/v1/history?limit=10&offset=5")
        data = response.json()
        assert data["limit"] == 10
        assert data["offset"] == 5

    def test_history_invalid_limit_rejected(self, client: TestClient):
        response = client.get("/v1/history?limit=0")
        assert response.status_code == 422

    def test_history_invalid_limit_high_rejected(self, client: TestClient):
        response = client.get("/v1/history?limit=300")
        assert response.status_code == 422


def _make_extract_response(ticket_id="TKT-001", success=True, data=None):
    from datetime import datetime, timezone

    return {
        "ticket_id": ticket_id,
        "success": success,
        "data": data,
        "confidence": 0.95 if success else 0.0,
        "metadata": {
            "repair_attempts": 0,
            "latency_ms": 100,
            "provider": "groq",
            "model": "test",
            "validation": "passed" if success else "failed",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
        "retry_count": 0,
        "failure_category": None if success else "validation_error",
        "latency_seconds": 0.1,
        "language": "en",
        "request_id": "REQ-TEST",
        "cleaned_text": "cleaned text",
        "repair_attempts": [],
    }


class TestSingleExtractionEndpoint:

    def test_extract_with_valid_text(self, client: TestClient):
        with patch("app.api.routes.process_ticket") as mock_process:
            mock_process.return_value = _make_extract_response()
            response = client.post(
                "/v1/extract",
                json={"ticket_id": "TKT-001", "raw_text": "I need help with my order"},
            )
        assert response.status_code == 200

    def test_extract_with_empty_text_returns_400(self, client: TestClient):
        response = client.post(
            "/v1/extract",
            json={"ticket_id": "TKT-001", "raw_text": ""},
        )
        assert response.status_code == 400
        data = response.json()
        assert "raw_text must not be empty" in data["message"].lower()

    def test_extract_with_whitespace_text_returns_400(self, client: TestClient):
        response = client.post(
            "/v1/extract",
            json={"ticket_id": "TKT-001", "raw_text": "   "},
        )
        assert response.status_code == 400

    def test_extract_missing_ticket_id(self, client: TestClient):
        response = client.post(
            "/v1/extract",
            json={"raw_text": "I need help"},
        )
        assert response.status_code == 422

    def test_extract_missing_raw_text_field(self, client: TestClient):
        response = client.post(
            "/v1/extract",
            json={"ticket_id": "TKT-001"},
        )
        assert response.status_code == 422

    def test_extract_invalid_body_type(self, client: TestClient):
        response = client.post(
            "/v1/extract",
            data="not json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422

    @pytest.mark.integration
    def test_extract_response_structure(self, client: TestClient):
        with patch("app.api.service.process_ticket") as mock_process:
            mock_process.return_value = _make_extract_response()
            response = client.post(
                "/v1/extract",
                json={"ticket_id": "TKT-001", "raw_text": "I need help with my order"},
            )
        data = response.json()
        assert "ticket_id" in data
        assert "success" in data
        assert "confidence" in data
        assert "metadata" in data
        assert "retry_count" in data
        assert "latency_seconds" in data
        assert "language" in data


class TestBatchExtractionEndpoint:
    def test_batch_with_valid_tickets(self, client: TestClient):
        with patch("app.api.routes.process_ticket") as mock_process:
            mock_process.return_value = _make_extract_response("TKT-001")
            response = client.post(
                "/v1/extract/batch",
                json={
                    "tickets": [
                        {"ticket_id": "TKT-001", "raw_text": "Help with order"},
                        {"ticket_id": "TKT-002", "raw_text": "Account issue"},
                    ]
                },
            )
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert len(data["results"]) == 2

    def test_batch_handles_empty_text(self, client: TestClient):
        with patch("app.api.routes.process_ticket") as mock_process:
            mock_process.return_value = _make_extract_response("TKT-VALID")
            response = client.post(
                "/v1/extract/batch",
                json={
                    "tickets": [
                        {"ticket_id": "TKT-EMPTY", "raw_text": "   "},
                        {"ticket_id": "TKT-VALID", "raw_text": "real text"},
                    ]
                },
            )
        data = response.json()
        assert len(data["results"]) == 2
        assert data["results"][0]["success"] is False
        assert data["results"][0]["failure_category"] == "empty_text"
        assert data["results"][1]["success"] is True

    def test_batch_empty_request(self, client: TestClient):
        response = client.post(
            "/v1/extract/batch",
            json={"tickets": []},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 0


class TestSystemEndpoint:
    def test_system_returns_200(self, client: TestClient):
        response = client.get("/v1/system")
        assert response.status_code in (200, 503)

    def test_system_response_structure(self, client: TestClient):
        response = client.get("/v1/system")
        data = response.json()
        assert "health" in data
        assert "metrics" in data
        assert "status" in data["health"]
        assert "total_requests" in data["metrics"]


class TestErrorHandling:
    def test_404_returns_json(self, client: TestClient):
        response = client.get("/nonexistent")
        assert response.status_code == 404
        assert response.headers["content-type"] == "application/json"

    def test_request_id_in_response(self, client: TestClient):
        response = client.get("/health")
        assert "X-Request-ID" in response.headers
        assert response.headers["X-Request-ID"].startswith("REQ-")

    def test_correlation_id_in_response(self, client: TestClient):
        response = client.get("/health")
        assert "X-Correlation-ID" in response.headers
