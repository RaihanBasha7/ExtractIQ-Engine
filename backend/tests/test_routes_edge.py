from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import patch

import pytest


class TestSystemEndpoint:
    def test_system_returns_health_and_metrics(self, client):
        response = client.get("/v1/system")
        assert response.status_code in (200, 503)
        data = response.json()
        assert "health" in data
        assert "metrics" in data

    def test_system_degraded_when_db_down(self, client):
        from app.api.models import HealthCheckDetail, HealthResponse, MetricsResponse

        now = datetime.now(timezone.utc)
        health = HealthResponse(
            status="degraded",
            timestamp=now,
            response_time_ms=5.0,
            checks={
                "database": HealthCheckDetail(status="degraded", response_time_ms=1.0, error="down"),
            },
        )
        metrics = MetricsResponse(
            total_requests=0,
            successful_extractions=0,
            failed_extractions=0,
            schema_valid_rate=0.0,
            average_retry_count=0.0,
            average_processing_time=0.0,
            failure_breakdown={},
            last_updated=now,
        )
        with (
            patch("app.api.routes.health_service.check_all", return_value=health),
            patch("app.api.routes.health_service.has_critical_failure", return_value=True),
            patch("app.api.routes.metrics_service.get_metrics", return_value=metrics),
        ):
            response = client.get("/v1/system")
            assert response.status_code == 503


class TestBatchHelpers:
    def test_is_infrastructure_error(self):
        from app.api.routes import _is_infrastructure_error

        assert _is_infrastructure_error("PROVIDER_RATE_LIMIT", None, None) is True
        assert _is_infrastructure_error("PROVIDER_TIMEOUT", None, None) is True
        assert _is_infrastructure_error("NEEDS_REVIEW", "rate_limit", None) is True
        assert _is_infrastructure_error("NEEDS_REVIEW", "validation_error", None) is False
        assert _is_infrastructure_error("SUCCESS", None, None) is False

    def test_build_infra_error_response(self):
        from app.api.routes import _build_infra_error_response

        resp = _build_infra_error_response(0, "REQ-001", 3, "rate limit exceeded")
        assert resp.final_status == "PROVIDER_RATE_LIMIT"
        assert resp.success is False

        resp = _build_infra_error_response(1, "REQ-001", 3, "timeout")
        assert resp.final_status == "PROVIDER_TIMEOUT"

        resp = _build_infra_error_response(2, "REQ-001", 3, "connection failed")
        assert resp.final_status == "NETWORK_ERROR"

        resp = _build_infra_error_response(3, "REQ-001", 3, "unknown error")
        assert resp.final_status == "MODEL_ERROR"

    def test_build_segment_preview(self):
        from app.api.routes import _build_segment_preview

        short = "Short text"
        assert _build_segment_preview(short) == short

        long_text = "word " * 100
        preview = _build_segment_preview(long_text, max_preview=50)
        assert len(preview) <= 55

    @pytest.fixture
    def mock_extract_response(self):
        from app.api.models import ExtractResponse
        from app.metadata import ExtractionMetadata

        def _make(status: str):
            m = ExtractionMetadata(
                repair_attempts=0,
                latency_ms=0,
                provider="test",
                model="test",
                validation="passed",
                timestamp=datetime.now(timezone.utc),
            )
            return ExtractResponse(
                ticket_id="T1",
                success=status == "SUCCESS",
                data=None,
                confidence=1.0 if status == "SUCCESS" else 0.0,
                metadata=m,
                retry_count=0,
                latency_seconds=0.0,
                language="en",
                final_status=status,
                validation_status="passed" if status != "FAILED" else "failed",
            )

        return _make

    def test_aggregate_results(self, mock_extract_response):
        from app.api.routes import _aggregate_results

        results = [
            mock_extract_response("SUCCESS"),
            mock_extract_response("REPAIRED"),
            mock_extract_response("NEEDS_REVIEW"),
            mock_extract_response("FAILED"),
        ]
        agg = _aggregate_results(results)
        assert agg["processed"] == 4, f"processed={agg['processed']}"
        assert agg["successful"] == 1, f"successful={agg['successful']}"
        assert agg["repaired"] == 1, f"repaired={agg['repaired']}"
        assert agg["needs_review"] == 1, f"needs_review={agg['needs_review']}"
        assert agg["failed"] == 1, f"failed={agg['failed']}"
        assert agg["infrastructure_retry"] == 0, f"infra={agg['infrastructure_retry']}"

    def test_get_ext(self):
        from app.api.routes import _get_ext

        assert _get_ext("file.txt") == ".txt"
        assert _get_ext("file.TXT") == ".txt"
        assert _get_ext("file") == ""
        assert _get_ext(".hidden") == ""

    def test_classify_infrastructure_error(self):
        from app.api.models import ExtractResponse
        from app.api.routes import _classify_infrastructure_error
        from app.metadata import ExtractionMetadata

        metadata = ExtractionMetadata(
            repair_attempts=0,
            latency_ms=0,
            provider="test",
            model="test",
            validation="failed",
            timestamp=datetime.now(timezone.utc),
        )
        resp = ExtractResponse(
            ticket_id="T1",
            success=False,
            data=None,
            confidence=0.0,
            metadata=metadata,
            retry_count=0,
            latency_seconds=0.0,
            language="en",
            final_status="NEEDS_REVIEW",
            failure_category="rate_limit",
            needs_review_reason="Provider rate limited",
        )

        result = _classify_infrastructure_error(resp)
        assert result.final_status == "PROVIDER_RATE_LIMIT"


class TestBatchUploadEndpoint:
    def test_batch_upload_no_file_no_text(self, client):
        response = client.post("/v1/extract/batch/upload")
        assert response.status_code == 400


class TestBatchProcessEndpoint:
    def test_batch_process_session_not_found(self, client):
        response = client.post(
            "/v1/extract/batch/process",
            json={"session_id": "nonexistent", "tickets": ["test"]},
        )
        assert response.status_code == 404

    def test_batch_process_no_tickets(self, client):
        response = client.post(
            "/v1/extract/batch/process",
            json={"session_id": "nonexistent", "tickets": []},
        )
        assert response.status_code == 404


class TestProcessTicketsAsync:
    def test_process_tickets_with_exception(self):
        import asyncio

        from app.api.routes import _process_tickets_async

        with patch("app.api.routes._process_ticket_with_retry") as mock:
            mock.side_effect = RuntimeError("Task failed")
            results = asyncio.run(_process_tickets_async(["text1", "text2"], "REQ-001"))
            assert len(results) == 2
            assert all(r.success is False for r in results)
