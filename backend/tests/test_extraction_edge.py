from __future__ import annotations

from unittest.mock import MagicMock, patch


class TestExtractionUtilities:
    def test_get_instructor_mode_groq(self):
        with patch("app.extraction.LLM_PROVIDER", "groq"):
            import instructor

            from app.extraction import _get_instructor_mode

            assert _get_instructor_mode() == instructor.Mode.TOOLS

    def test_get_instructor_mode_featherless(self):
        with patch("app.extraction.LLM_PROVIDER", "featherless"):
            import instructor

            from app.extraction import _get_instructor_mode

            assert _get_instructor_mode() == instructor.Mode.JSON

    def test_reset_client_cache(self):
        import app.extraction

        app.extraction._client_cache = MagicMock()
        from app.extraction import _reset_client_cache

        _reset_client_cache()
        assert app.extraction._client_cache is None

    def test_build_repair_prompt_format(self):
        from app.extraction import _build_repair_prompt

        result = _build_repair_prompt("validation error: field required", "original text")
        assert result["role"] == "user"
        assert "validation error: field required" in result["content"]
        assert "original text" in result["content"]

    def test_map_infra_to_status_rate_limit(self):
        from app.extraction import _map_infra_to_status

        assert _map_infra_to_status("rate_limit") == "PROVIDER_RATE_LIMIT"
        assert _map_infra_to_status("429 error") == "PROVIDER_RATE_LIMIT"
        assert _map_infra_to_status("timeout") == "PROVIDER_TIMEOUT"
        assert _map_infra_to_status("connection error") == "NETWORK_ERROR"
        assert _map_infra_to_status("unknown") == "MODEL_ERROR"

    def test_check_needs_review_sufficient_data(self):
        from app.extraction import _check_needs_review
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

        ticket = TicketExtraction(
            ticket_id="T001",
            customer=Customer(name="John", account_id="ACC-001"),
            issue=Issue(category=IssueCategory.billing, subcategory="refund", urgency=Urgency.high),
            sentiment=Sentiment.neutral,
            entities=Entities(),
            resolution_status=ResolutionStatus.unresolved,
        )
        reasons = _check_needs_review(ticket)
        assert reasons == []

    def test_check_needs_review_insufficient_data(self):
        from app.extraction import _check_needs_review
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

        ticket = TicketExtraction(
            ticket_id="T001",
            customer=Customer(name=None, account_id=None),
            issue=Issue(category=IssueCategory.other, subcategory=None, urgency=Urgency.low),
            sentiment=Sentiment.neutral,
            entities=Entities(),
            resolution_status=ResolutionStatus.unresolved,
        )
        reasons = _check_needs_review(ticket)
        assert len(reasons) >= 1

    def test_final_status_constants(self):
        from app.extraction import (
            FINAL_STATUS_FAILED,
            FINAL_STATUS_MODEL_ERROR,
            FINAL_STATUS_NEEDS_REVIEW,
            FINAL_STATUS_NETWORK_ERROR,
            FINAL_STATUS_PROVIDER_RATE_LIMIT,
            FINAL_STATUS_PROVIDER_TIMEOUT,
            FINAL_STATUS_REPAIRED,
            FINAL_STATUS_SUCCESS,
        )

        assert FINAL_STATUS_SUCCESS == "SUCCESS"
        assert FINAL_STATUS_REPAIRED == "REPAIRED"
        assert FINAL_STATUS_NEEDS_REVIEW == "NEEDS_REVIEW"
        assert FINAL_STATUS_FAILED == "FAILED"
        assert FINAL_STATUS_PROVIDER_RATE_LIMIT == "PROVIDER_RATE_LIMIT"
        assert FINAL_STATUS_PROVIDER_TIMEOUT == "PROVIDER_TIMEOUT"
        assert FINAL_STATUS_NETWORK_ERROR == "NETWORK_ERROR"
        assert FINAL_STATUS_MODEL_ERROR == "MODEL_ERROR"

    def test_extraction_result_set_final_status(self):
        from app.extraction import ExtractionResult

        result = ExtractionResult(ticket_id="T001", success=True, data=None)
        assert result.final_status == "NEEDS_REVIEW"
        result.set_final_status("SUCCESS")
        assert result.final_status == "SUCCESS"

    def test_extraction_attempt_defaults(self):
        from app.extraction import ExtractionAttempt

        attempt = ExtractionAttempt(attempt_number=1, success=True)
        assert attempt.error is None
        assert attempt.attempt_number == 1
        assert attempt.success is True

    def test_classify_failure_edge_cases(self):
        from app.extraction import _classify_failure

        assert _classify_failure("not a valid enum value") == "validation_error"
        assert _classify_failure("field required") == "validation_error"
        assert _classify_failure("missing field") == "validation_error"
        assert _classify_failure("JSON decode error at line 1") == "validation_error"
        assert _classify_failure("extra fields not permitted") == "validation_error"

    def test_non_retryable_false_for_validation(self):
        from app.extraction import _is_non_retryable

        assert _is_non_retryable("validation error") is False
        assert _is_non_retryable("field required") is False


class TestGetClient:
    def test_get_client_featherless(self):
        with patch("app.extraction.LLM_PROVIDER", "featherless"):
            with patch("app.extraction.FEATHERLESS_API_KEY", "test-key"):
                with patch("app.extraction.FEATHERLESS_BASE_URL", "https://test.ai/v1"):
                    with patch("app.extraction.instructor.from_openai") as mock_from_openai:
                        import app.extraction

                        app.extraction._reset_client_cache()
                        from app.extraction import _get_client

                        mock_client = MagicMock()
                        mock_from_openai.return_value = mock_client
                        client = _get_client()
                        assert client is not None
                        mock_from_openai.assert_called_once()

    def test_get_client_groq(self):
        with patch("app.extraction.LLM_PROVIDER", "groq"):
            with patch("app.extraction.GROQ_API_KEY", "test-key"):
                with patch("app.extraction.instructor.from_groq") as mock_from_groq:
                    import app.extraction

                    app.extraction._reset_client_cache()

                    mock_client = MagicMock()
                    mock_from_groq.return_value = mock_client
                    from app.extraction import _get_client

                    result = _get_client()
                    assert result is not None
                    mock_from_groq.assert_called_once()
