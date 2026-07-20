"""Tests for the Model-Driven Repair Loop."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from app.schema import TicketExtraction


class TestRepairLog:
    def test_create_empty_repair_log(self):
        from app.repair_logging import create_repair_log

        log = create_repair_log()
        assert log.total_attempts == 0
        assert log.successful_attempts == 0
        assert log.failed_attempts == 0

    def test_record_successful_attempt(self, repair_log_with_entries):
        log = repair_log_with_entries
        assert log.total_attempts == 2
        assert log.successful_attempts == 1
        assert log.failed_attempts == 1

    def test_repair_log_summary(self, repair_log_with_entries):
        log = repair_log_with_entries
        summary = log.summary()
        assert summary["attempts"] == 2
        assert summary["successful"] == 1
        assert summary["failed"] == 1
        assert summary["total_latency_ms"] == 1700

    def test_repair_log_entry_fields(self, repair_log_with_entries):
        entry = repair_log_with_entries.entries[0]
        assert entry.attempt == 1
        assert entry.status == "success"
        assert entry.error_type is None
        assert entry.error_message is None
        assert entry.latency_ms == 500
        assert entry.request_id is None

    def test_repair_log_entry_with_request_id(self):
        from datetime import datetime, timezone

        from app.repair_logging import RepairLog, record_attempt

        log = RepairLog()
        record_attempt(log, 1, "success", None, 0.5, timestamp=datetime.now(timezone.utc), request_id="REQ-TEST")
        assert log.entries[0].request_id == "REQ-TEST"


class TestErrorParsing:
    def test_parse_validation_error(self):
        from app.repair_logging import _parse_error

        error_type, error_message = _parse_error("validation error: field required")
        assert error_type == "ValidationError"
        assert error_message == "validation error: field required"

    def test_parse_rate_limit_error(self):
        from app.repair_logging import _parse_error

        error_type, error_message = _parse_error("rate_limit: too many requests")
        assert error_type == "RateLimitError"

    def test_parse_rate_limit_429(self):
        from app.repair_logging import _parse_error

        error_type, error_message = _parse_error("429 Too Many Requests")
        assert error_type == "RateLimitError"

    def test_parse_timeout_error(self):
        from app.repair_logging import _parse_error

        error_type, error_message = _parse_error("timeout: connection timed out")
        assert error_type == "TimeoutError"

    def test_parse_connection_error(self):
        from app.repair_logging import _parse_error

        error_type, error_message = _parse_error("connection refused")
        assert error_type == "TimeoutError"

    def test_parse_503_error(self):
        from app.repair_logging import _parse_error

        error_type, error_message = _parse_error("503 Service Unavailable")
        assert error_type == "APIStatusError"

    def test_parse_none_error(self):
        from app.repair_logging import _parse_error

        error_type, error_message = _parse_error(None)
        assert error_type is None
        assert error_message is None

    def test_parse_unknown_error(self):
        from app.repair_logging import _parse_error

        error_type, error_message = _parse_error("SomeRandomError: something went wrong")
        assert error_type == "SomeRandomError"

    def test_parse_unrecognized_format(self):
        from app.repair_logging import _parse_error

        error_type, error_message = _parse_error("completely unrecognized string")
        assert error_type == "UnknownError"


class TestErrorClassification:
    def test_classify_rate_limit(self):
        from app.extraction import _classify_failure

        assert _classify_failure("rate_limit exceeded") == "rate_limit"
        assert _classify_failure("429 too many requests") == "rate_limit"

    def test_classify_timeout(self):
        from app.extraction import _classify_failure

        assert _classify_failure("timeout error") == "timeout"
        assert _classify_failure("connection refused") == "timeout"

    def test_classify_provider_error(self):
        from app.extraction import _classify_failure

        assert _classify_failure("503 service unavailable") == "provider_error"

    def test_classify_validation_error(self):
        from app.extraction import _classify_failure

        assert _classify_failure("enum error: invalid value") == "validation_error"
        assert _classify_failure("field required") == "validation_error"
        assert _classify_failure("JSON decode error") == "validation_error"
        assert _classify_failure("extra fields not permitted") == "validation_error"

    def test_classify_unexpected(self):
        from app.extraction import _classify_failure

        assert _classify_failure("something completely unexpected") == "unexpected_error"

    def test_non_retryable_detection(self):
        from app.extraction import _is_non_retryable

        assert _is_non_retryable("rate_limit error") is True
        assert _is_non_retryable("429 error") is True
        assert _is_non_retryable("503 error") is True
        assert _is_non_retryable("timeout error") is True
        assert _is_non_retryable("connection error") is True
        assert _is_non_retryable("validation error") is False
        assert _is_non_retryable("field required") is False


class TestRepairLoopExecution:
    def make_mock_ticket(self) -> TicketExtraction:
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

        return TicketExtraction(
            ticket_id="TKT-001",
            customer=Customer(name="John", account_id="ACC-001"),
            issue=Issue(
                category=IssueCategory.technical,
                subcategory="login",
                product_or_service="account",
                urgency=Urgency.high,
            ),
            sentiment=Sentiment.frustrated,
            entities=Entities(order_ids=["ORD-001"]),
            requested_action="reset password",
            resolution_status=ResolutionStatus.unresolved,
        )

    def test_repair_executes_on_validation_failure(self):
        """When validation fails, the repair loop re-prompts the LLM."""
        from app.extraction import extract_ticket

        valid_ticket = self.make_mock_ticket()
        mock_client = MagicMock()

        call_count = [0]

        def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                msg = "validation error: field required"
                raise ValidationError.from_exception_data("TicketExtraction", [{"type": "missing", "loc": ("field",), "msg": msg, "input": None}])
            return valid_ticket

        mock_client.chat.completions.create.side_effect = side_effect

        result = extract_ticket("TKT-001", "Some ticket text", client=mock_client)
        assert result.success is True
        assert result.data is not None
        assert result.retry_count == 1

    def test_retry_counter_increments_correctly(self):
        from app.extraction import extract_ticket

        mock_client = MagicMock()
        call_count = [0]

        def side_effect(*args, **kwargs):
            call_count[0] += 1
            msg = f"validation error: attempt {call_count[0]}"
            raise ValidationError.from_exception_data("TicketExtraction", [{"type": "missing", "loc": ("field",), "msg": msg, "input": None}])

        mock_client.chat.completions.create.side_effect = side_effect

        result = extract_ticket("TKT-002", "Some text", client=mock_client)
        assert result.success is False
        assert result.data is None
        assert result.retry_count == 3

    def test_stops_after_max_retries(self):
        from app.config import MAX_REPAIR_RETRIES
        from app.extraction import extract_ticket

        mock_client = MagicMock()

        def always_fails(*args, **kwargs):
            raise ValidationError.from_exception_data("TicketExtraction", [{"type": "missing", "loc": ("field",), "msg": "field required", "input": None}])

        mock_client.chat.completions.create.side_effect = always_fails

        result = extract_ticket("TKT-003", "Some text", client=mock_client)
        assert result.success is False
        assert result.retry_count == MAX_REPAIR_RETRIES
        assert len(result.attempts) == MAX_REPAIR_RETRIES + 1

    def test_returns_failure_object_correctly(self):
        from app.extraction import extract_ticket

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = ValidationError.from_exception_data(
            "TicketExtraction", [{"type": "missing", "loc": ("field",), "msg": "field required", "input": None}]
        )

        result = extract_ticket("TKT-004", "Some text", client=mock_client)
        assert result.success is False
        assert result.data is None
        assert result.failure_category is not None
        assert result.latency_seconds >= 0
        assert result.repair_log is not None
        assert result.ticket_id == "TKT-004"

    def test_successful_first_attempt_no_repair(self):
        from app.extraction import extract_ticket

        valid_ticket = self.make_mock_ticket()
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = valid_ticket

        result = extract_ticket("TKT-005", "Some text", client=mock_client)
        assert result.success is True
        assert result.retry_count == 0
        assert len(result.attempts) == 1

    def test_non_retryable_error_stops_immediately(self):
        from app.extraction import extract_ticket

        from groq import RateLimitError

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = RateLimitError(
            "rate_limit_exceeded",
            response=MagicMock(status_code=429),
            body={"error": "rate limit exceeded"},
        )

        result = extract_ticket("TKT-006", "Some text", client=mock_client)
        assert result.success is False
        assert result.retry_count == 0
