"""Integration tests using mocked LLM responses.

These tests verify the full extraction pipeline works end-to-end
without calling any external APIs.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError as PydanticValidationError

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


@pytest.fixture
def sample_valid_ticket_extraction() -> TicketExtraction:
    return TicketExtraction(
        ticket_id="TKT-INT-001",
        customer=Customer(name="Alice Smith", account_id="ACC-999"),
        issue=Issue(
            category=IssueCategory.billing,
            subcategory="overcharge",
            product_or_service="subscription",
            urgency=Urgency.high,
        ),
        sentiment=Sentiment.frustrated,
        entities=Entities(
            order_ids=["ORD-888"],
            dates_mentioned=["2024-06-15"],
            amounts_mentioned=["$99.99"],
        ),
        requested_action="issue refund",
        resolution_status=ResolutionStatus.unresolved,
    )


class TestFullPipelineMocked:
    """Complete extraction pipeline using mocked LLM."""

    def test_pipeline_success_first_attempt(self, sample_valid_ticket_extraction, db_session):
        from app.api.service import process_ticket
        from app.database.repository import ExtractionRepository

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = sample_valid_ticket_extraction

        with patch("app.extraction._get_client", return_value=mock_client):
            result = process_ticket(
                "TKT-INT-001", "I was overcharged $99.99 for my subscription, please refund.", request_id="REQ-INT-001"
            )

        assert result.success is True
        assert result.data is not None
        assert result.data.ticket_id == "TKT-INT-001"
        assert result.confidence > 0.5
        assert result.metadata.validation == "passed"
        assert result.language is not None

        repo = ExtractionRepository()
        saved = repo.get_by_ticket_id("TKT-INT-001", db_session=db_session)
        assert len(saved) >= 1

    def test_pipeline_with_repair(self, db_session):
        from app.api.service import process_ticket

        valid_ticket = TicketExtraction(
            ticket_id="TKT-INT-002",
            customer=Customer(name="Bob", account_id=None),
            issue=Issue(
                category=IssueCategory.technical,
                subcategory="login issue",
                product_or_service=None,
                urgency=Urgency.medium,
            ),
            sentiment=Sentiment.neutral,
            entities=Entities(order_ids=[], dates_mentioned=[], amounts_mentioned=[]),
            requested_action=None,
            resolution_status=ResolutionStatus.pending,
        )

        mock_client = MagicMock()
        call_count = [0]

        def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise PydanticValidationError.from_exception_data(
                    "TicketExtraction",
                    [{"type": "missing", "loc": ("ticket_id",), "msg": "field required", "input": None}],
                )
            return valid_ticket

        mock_client.chat.completions.create.side_effect = side_effect

        with patch("app.extraction._get_client", return_value=mock_client):
            result = process_ticket("TKT-INT-002", "Cannot log in, need help", request_id="REQ-INT-002")

        assert result.success is True
        assert result.retry_count == 1
        assert result.metadata.validation == "passed"
        assert result.confidence > 0

    def test_pipeline_all_retries_exhausted(self, db_session):
        from app.api.service import process_ticket

        mock_client = MagicMock()

        def always_fails(*args, **kwargs):
            raise PydanticValidationError.from_exception_data(
                "TicketExtraction",
                [{"type": "missing", "loc": ("field",), "msg": "field required", "input": None}],
            )

        mock_client.chat.completions.create.side_effect = always_fails

        with patch("app.extraction._get_client", return_value=mock_client):
            result = process_ticket("TKT-INT-003", "Some ticket text", request_id="REQ-INT-003")

        assert result.success is False
        assert result.data is None
        assert result.retry_count == 3
        assert result.failure_category is not None
        assert result.metadata.validation == "failed"
        assert result.confidence == 0.10


class TestPipelineWithPreprocessing:
    """Tests that preprocessing integrates correctly with extraction."""

    def test_pii_redacted_before_extraction(self):
        from app.api.service import process_ticket

        mock_client = MagicMock()
        valid_ticket = TicketExtraction(
            ticket_id="TKT-PII-001",
            customer=Customer(name=None, account_id=None),
            issue=Issue(category=IssueCategory.other, urgency=Urgency.low),
            sentiment=Sentiment.neutral,
            entities=Entities(),
            resolution_status=ResolutionStatus.unresolved,
        )
        mock_client.chat.completions.create.return_value = valid_ticket

        with patch("app.extraction._get_client", return_value=mock_client):
            result = process_ticket(
                "TKT-PII-001",
                "My email is secret@example.com and phone is 555-123-4567",
                request_id="REQ-PII-001",
            )

        assert result.success is True
        assert result.cleaned_text is not None
        assert "[REDACTED_EMAIL]" in result.cleaned_text
        assert "secret@example.com" not in result.cleaned_text


class TestBatchProcessingMocked:
    """Tests batch extraction with mocked LLM."""

    def test_batch_all_successful(self, client):
        from tests.test_api import _make_extract_response

        valid_result = _make_extract_response("TKT-B01")

        with patch("app.api.routes.process_ticket", return_value=valid_result):
            response = client.post(
                "/v1/extract/batch",
                json={
                    "tickets": [
                        {"ticket_id": "TKT-B01", "raw_text": "Need refund"},
                        {"ticket_id": "TKT-B02", "raw_text": "Account locked"},
                    ]
                },
            )

        data = response.json()
        assert len(data["results"]) == 2
        assert data["results"][0]["success"] is True
        assert data["results"][1]["success"] is True

    def test_batch_mixed_results(self, client):
        from tests.test_api import _make_extract_response

        with patch("app.api.routes.process_ticket") as mock_process:

            def side_effect(ticket_id, raw_text, request_id=None):
                if not raw_text.strip():
                    mock = _make_extract_response(ticket_id, success=False)
                    mock["failure_category"] = "empty_text"
                    mock["confidence"] = 0.0
                    return mock
                return _make_extract_response(ticket_id)

            mock_process.side_effect = side_effect
            response = client.post(
                "/v1/extract/batch",
                json={
                    "tickets": [
                        {"ticket_id": "TKT-EMPTY", "raw_text": ""},
                        {"ticket_id": "TKT-VALID", "raw_text": "Help me"},
                    ]
                },
            )

        data = response.json()
        assert data["results"][0]["success"] is False
        assert data["results"][0]["failure_category"] == "empty_text"
        assert data["results"][1]["success"] is True
