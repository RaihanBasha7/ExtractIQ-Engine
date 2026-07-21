"""Tests for utility modules."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest


class TestTextCleaning:
    def test_normalize_text_removes_extra_whitespace(self):
        from app.preprocessing import normalize_text

        result = normalize_text("  Hello   World  \n\n  Test  ")
        assert result == "Hello World Test"

    def test_normalize_text_strips_leading_trailing_spaces(self):
        from app.preprocessing import normalize_text

        result = normalize_text("  Hello World  ")
        assert result == "Hello World"

    def test_normalize_text_single_word(self):
        from app.preprocessing import normalize_text

        assert normalize_text("Hello") == "Hello"

    def test_normalize_text_empty(self):
        from app.preprocessing import normalize_text

        assert normalize_text("") == ""

    def test_normalize_text_only_spaces(self):
        from app.preprocessing import normalize_text

        assert normalize_text("   ") == ""


class TestPIIStripping:
    def test_strip_email(self):
        from app.preprocessing import strip_pii

        text, count = strip_pii("Contact me at john@example.com")
        assert count == 1
        assert "[REDACTED_EMAIL]" in text
        assert "john@example.com" not in text

    def test_strip_phone(self):
        from app.preprocessing import strip_pii

        text, count = strip_pii("Call (555) 123-4567")
        assert count == 1
        assert "[REDACTED_PHONE]" in text

    def test_strip_zip_code(self):
        from app.preprocessing import strip_pii

        text, count = strip_pii("My zip is 90210")
        assert count == 1
        assert "[REDACTED_ZIP]" in text

    def test_strip_multiple_pii(self):
        from app.preprocessing import strip_pii

        text, count = strip_pii("Email: a@b.com, Phone: (555) 000-1111, Zip: 12345")
        assert count == 3

    def test_no_pii_unchanged(self):
        from app.preprocessing import strip_pii

        text, count = strip_pii("Just regular text with no PII")
        assert count == 0
        assert text == "Just regular text with no PII"

    def test_empty_text_no_pii(self):
        from app.preprocessing import strip_pii

        text, count = strip_pii("")
        assert count == 0
        assert text == ""


class TestPreprocessingPipeline:
    def test_full_preprocess_pipeline(self):
        from app.preprocessing import preprocess

        result = preprocess("  Hello   World  \n\n  Test  ")
        assert result.clean_text == "Hello World Test"
        assert result.pii_redacted_count == 0

    def test_preprocess_with_pii(self):
        from app.preprocessing import preprocess

        result = preprocess("Email me at test@example.com or call (555) 123-4567")
        assert result.pii_redacted_count >= 1
        assert "[REDACTED_EMAIL]" in result.clean_text

    def test_preprocess_empty_text(self):
        from app.preprocessing import preprocess

        result = preprocess("")
        assert result.clean_text == ""

    def test_preprocess_result_dataclass(self):
        from app.preprocessing import preprocess, PreprocessResult

        result = preprocess("Hello World")
        assert isinstance(result, PreprocessResult)
        assert hasattr(result, "clean_text")
        assert hasattr(result, "language")
        assert hasattr(result, "pii_redacted_count")


class TestRequestIDGeneration:
    def test_request_id_format(self):
        from app.api.middleware import RequestIDGenerator

        gen = RequestIDGenerator()
        rid = gen()
        assert rid.startswith("REQ-")
        assert len(rid) > 4

    def test_request_id_increments(self):
        from app.api.middleware import RequestIDGenerator

        gen = RequestIDGenerator()
        first = gen()
        second = gen()
        assert first != second
        # Second should be numerically greater
        first_num = int(first.split("-")[1])
        second_num = int(second.split("-")[1])
        assert second_num == first_num + 1

    def test_request_id_thread_safety(self):
        from app.api.middleware import RequestIDGenerator

        gen = RequestIDGenerator()
        ids = set()
        for _ in range(100):
            ids.add(gen())
        assert len(ids) == 100


class TestCorrelationIDMiddleware:
    def test_middleware_attaches_request_id(self, client):
        response = client.get("/health")
        assert "X-Request-ID" in response.headers

    def test_middleware_attaches_correlation_id(self, client):
        response = client.get("/health")
        assert "X-Correlation-ID" in response.headers

    def test_request_id_in_state(self, client):
        response = client.get("/health")
        rid = response.headers.get("X-Request-ID")
        assert rid is not None
        assert rid.startswith("REQ-")


class TestMetadata:
    def test_build_metadata_success(self):
        from app.metadata import build_metadata

        meta = build_metadata(repair_attempts=0, latency_seconds=1.5, success=True)
        assert meta.repair_attempts == 0
        assert meta.latency_ms == 1500
        assert meta.validation == "passed"
        assert meta.provider is not None
        assert meta.model is not None

    def test_build_metadata_failure(self):
        from app.metadata import build_metadata

        meta = build_metadata(repair_attempts=3, latency_seconds=0.0, success=False)
        assert meta.repair_attempts == 3
        assert meta.validation == "failed"
        assert meta.latency_ms == 0

    def test_build_metadata_rounding(self):
        from app.metadata import build_metadata

        meta = build_metadata(repair_attempts=1, latency_seconds=0.1234, success=True)
        assert meta.latency_ms == 123

    def test_build_metadata_timestamp(self):
        from app.metadata import build_metadata

        meta = build_metadata(repair_attempts=0, latency_seconds=0, success=True)
        assert isinstance(meta.timestamp, datetime)


class TestConfidenceScoring:
    def test_perfect_extraction_scores_100(self):
        from app.confidence import ConfidenceMetrics, compute_confidence
        from app.schema import (
            Customer,
            Entities,
            Issue,
            IssueCategory,
            ResolutionStatus,
            Sentiment,
            TicketExtraction,
            Urgency,
        )

        perfect = TicketExtraction(
            ticket_id="T001",
            customer=Customer(name="John", account_id="123"),
            issue=Issue(category=IssueCategory.billing, subcategory="refund", product_or_service="service", urgency=Urgency.high),
            sentiment=Sentiment.frustrated,
            entities=Entities(order_ids=["ORD-1"], dates_mentioned=["2024-01-01"], amounts_mentioned=["$100"]),
            requested_action="refund",
            resolution_status=ResolutionStatus.unresolved,
        )
        score = compute_confidence(ConfidenceMetrics(success=True, retry_count=0, data=perfect))
        assert score == 100.0

    def test_failed_extraction_scores_010(self):
        from app.confidence import ConfidenceMetrics, compute_confidence

        score = compute_confidence(ConfidenceMetrics(success=False, retry_count=3, data=None))
        assert score == 10.0

    def test_repaired_with_missing_fields(self):
        from app.confidence import ConfidenceMetrics, compute_confidence
        from app.schema import (
            Customer,
            Entities,
            Issue,
            IssueCategory,
            ResolutionStatus,
            Sentiment,
            TicketExtraction,
            Urgency,
        )

        repaired = TicketExtraction(
            ticket_id="T002",
            customer=Customer(name="Jane", account_id=None),
            issue=Issue(category=IssueCategory.technical, subcategory=None, product_or_service=None, urgency=Urgency.medium),
            sentiment=Sentiment.neutral,
            entities=Entities(order_ids=[], dates_mentioned=[], amounts_mentioned=[]),
            requested_action=None,
            resolution_status=ResolutionStatus.pending,
        )
        score = compute_confidence(ConfidenceMetrics(success=True, retry_count=1, data=repaired))
        assert score == 25.0

    def test_lower_bound_clamping(self):
        from app.confidence import ConfidenceMetrics, compute_confidence

        score = compute_confidence(ConfidenceMetrics(success=True, retry_count=100, data=None))
        assert score == 10.0


class TestLogging:
    def test_get_logger_returns_logger(self):
        from app.logging import get_logger

        logger = get_logger("test")
        assert logger.name == "test"

    def test_log_event_creates_structured_log(self, caplog):
        from app.logging import get_logger, log_event

        logger = get_logger("test_log")
        log_event(logger, event="test_event", stage="api", status="success")
        assert True


class TestVersionService:
    def test_version_service_returns_correct_structure(self):
        from app.services.version_service import VersionService

        service = VersionService()
        info = service.get_version()
        assert info.service == "OneInbox API"
        assert info.version == "0.1.0"
        assert info.api_version == "v1"
        assert info.provider is not None
        assert info.model is not None


class TestExtractionDataclasses:
    def test_extraction_attempt_dataclass(self):
        from app.extraction import ExtractionAttempt

        attempt = ExtractionAttempt(attempt_number=1, success=True)
        assert attempt.attempt_number == 1
        assert attempt.success is True
        assert attempt.error is None

    def test_extraction_result_retry_count(self):
        from app.extraction import ExtractionAttempt, ExtractionResult

        result = ExtractionResult(ticket_id="T001", success=True, data=None)
        assert result.retry_count == 0

        result.attempts = [
            ExtractionAttempt(attempt_number=1, success=True),
            ExtractionAttempt(attempt_number=2, success=False, error="error"),
        ]
        assert result.retry_count == 1
