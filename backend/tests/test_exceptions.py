from __future__ import annotations

from unittest.mock import MagicMock

import pytest


class TestExceptionHierarchy:
    def test_base_exception(self):
        from app.exceptions import ExtractIQError

        exc = ExtractIQError("base error")
        assert str(exc) == "base error"
        assert isinstance(exc, Exception)

    def test_provider_error(self):
        from app.exceptions import ProviderError, ProviderRateLimitError, ProviderTimeoutError

        assert issubclass(ProviderRateLimitError, ProviderError)
        assert issubclass(ProviderTimeoutError, ProviderError)
        exc = ProviderRateLimitError("rate limited")
        assert str(exc) == "rate limited"

    def test_configuration_error(self):
        from app.exceptions import ConfigurationError

        exc = ConfigurationError("missing key")
        assert str(exc) == "missing key"

    def test_ingestion_error(self):
        from app.exceptions import IngestionError

        exc = IngestionError("parse failed")
        assert str(exc) == "parse failed"

    def test_database_error(self):
        from app.exceptions import DatabaseError

        exc = DatabaseError("connection failed")
        assert str(exc) == "connection failed"

    def test_map_provider_exception_rate_limit(self):
        from app.exceptions import ProviderRateLimitError, map_provider_exception

        mock_response = MagicMock(status_code=429)
        from groq import RateLimitError

        exc = RateLimitError("rate limit", response=mock_response, body={})
        mapped = map_provider_exception(exc)
        assert isinstance(mapped, ProviderRateLimitError)

    def test_map_provider_exception_timeout(self):
        from groq import APITimeoutError

        from app.exceptions import ProviderTimeoutError, map_provider_exception

        exc = APITimeoutError("timed out")
        mapped = map_provider_exception(exc)
        assert isinstance(mapped, ProviderTimeoutError)

    def test_map_provider_exception_api_error(self):
        from app.exceptions import ProviderAPIError, map_provider_exception

        mock_response = MagicMock(status_code=500)
        from groq import APIStatusError

        exc = APIStatusError("server error", response=mock_response, body={})
        mapped = map_provider_exception(exc)
        assert isinstance(mapped, ProviderAPIError)

    def test_map_provider_exception_unknown(self):
        from app.exceptions import ProviderError, map_provider_exception

        mapped = map_provider_exception(RuntimeError("unknown"))
        assert isinstance(mapped, ProviderError)

    def test_extraction_error(self):
        from app.exceptions import ExtractionError

        exc = ExtractionError("extraction failed")
        assert str(exc) == "extraction failed"


class TestRetryWrapper:
    def test_retry_success_first_attempt(self):
        from app.retry import retry_on_provider_error

        fn = MagicMock(return_value="success")
        result = retry_on_provider_error(fn, max_retries=2)
        assert result == "success"
        assert fn.call_count == 1

    def test_retry_eventually_succeeds(self):
        from app.exceptions import ProviderRateLimitError
        from app.retry import retry_on_provider_error

        fn = MagicMock(side_effect=[ProviderRateLimitError("first"), ProviderRateLimitError("second"), "success"])
        result = retry_on_provider_error(fn, max_retries=3, base_delay=0.01)
        assert result == "success"
        assert fn.call_count == 3

    def test_retry_exhausted_raises(self):
        from app.exceptions import ProviderRateLimitError
        from app.retry import retry_on_provider_error

        fn = MagicMock(side_effect=ProviderRateLimitError("always fails"))
        with pytest.raises(ProviderRateLimitError):
            retry_on_provider_error(fn, max_retries=1, base_delay=0.01)

    def test_non_provider_error_does_not_retry(self):
        from app.retry import retry_on_provider_error

        fn = MagicMock(side_effect=ValueError("not a provider error"))
        with pytest.raises(ValueError):
            retry_on_provider_error(fn, max_retries=2, base_delay=0.01)
        assert fn.call_count == 1
