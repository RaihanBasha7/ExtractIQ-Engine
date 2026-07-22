from __future__ import annotations

import random
import time
from collections.abc import Callable
from typing import TypeVar

from app.logging import get_logger, log_event

logger = get_logger(__name__)

T = TypeVar("T")


def retry_on_provider_error(
    fn: Callable[..., T],
    max_retries: int = 2,
    base_delay: float = 1.0,
    max_delay: float = 8.0,
    backoff: float = 2.0,
    jitter: bool = True,
    request_id: str | None = None,
    **kwargs,
) -> T:
    from app.exceptions import ProviderRateLimitError, ProviderTimeoutError

    last_exc: Exception | None = None
    for attempt in range(max_retries + 1):
        try:
            return fn(**kwargs)
        except (ProviderRateLimitError, ProviderTimeoutError) as e:
            last_exc = e
            if attempt < max_retries:
                delay = min(base_delay * (backoff**attempt), max_delay)
                if jitter:
                    delay += random.uniform(0, 1)
                log_event(
                    logger,
                    event="provider_retry",
                    stage="llm",
                    status="retrying",
                    request_id=request_id,
                    attempt=attempt + 1,
                    max_retries=max_retries,
                    delay_seconds=round(delay, 2),
                    error_type=type(e).__name__,
                )
                time.sleep(delay)
                continue
            raise
        except Exception:
            raise
    raise last_exc
