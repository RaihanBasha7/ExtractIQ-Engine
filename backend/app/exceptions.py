from __future__ import annotations


class ExtractIQError(Exception):
    """Base exception for all ExtractIQ errors."""


class ProviderError(ExtractIQError):
    """LLM provider returned an error (rate limit, timeout, API error)."""


class ProviderRateLimitError(ProviderError):
    """Provider rate limit exceeded."""


class ProviderTimeoutError(ProviderError):
    """Provider request timed out."""


class ProviderAPIError(ProviderError):
    """Provider returned a non-retryable API error."""


class ValidationError_(ExtractIQError):
    """Schema validation failed after all retries."""


class ConfigurationError(ExtractIQError):
    """Missing or invalid configuration."""


class IngestionError(ExtractIQError):
    """File ingestion/parsing failed."""


class ExtractionError(ExtractIQError):
    """Extraction pipeline failed."""


class DatabaseError(ExtractIQError):
    """Database operation failed."""


def map_provider_exception(exc: Exception) -> ProviderError:
    from groq import APIStatusError as GroqAPIStatusError
    from groq import APITimeoutError as GroqAPITimeoutError
    from groq import RateLimitError as GroqRateLimitError
    from openai import APIStatusError as OpenAIAPIStatusError
    from openai import APITimeoutError as OpenAIAPITimeoutError
    from openai import RateLimitError as OpenAIRateLimitError

    if isinstance(exc, (GroqRateLimitError, OpenAIRateLimitError)):
        return ProviderRateLimitError(str(exc))
    if isinstance(exc, (GroqAPITimeoutError, OpenAIAPITimeoutError)):
        return ProviderTimeoutError(str(exc))
    if isinstance(exc, (GroqAPIStatusError, OpenAIAPIStatusError)):
        return ProviderAPIError(str(exc))
    return ProviderError(str(exc))
