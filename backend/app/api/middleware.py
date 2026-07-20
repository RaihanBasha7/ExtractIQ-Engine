"""
Request ID & Correlation ID middleware.

Provides every HTTP request with a unique ``request_id`` (format ``REQ-XXXXXX``)
and an ``X-Correlation-ID`` response header (currently set to the same value).

.. note::
    The current :class:`RequestIDGenerator` is a **process-local, monotonic
    counter** intended for the MVP / single-worker development phase.  It is
    not safe across multiple processes or horizontally scaled replicas.

    For production deployments consider one of:

    * **UUIDv7** (time-ordered, DB-friendly, no coordination) — ``uuid.uuid7()``
    * **ULID** (26-char Crockford Base32, lexicographically sortable)
    * **Snowflake-style IDs** (twitter-style, requires worker-id coordination)
    * **Distributed ID service** (e.g. Redis ``INCR`` with shard prefix,
      or a dedicated ID generation service)
"""

import threading

from fastapi import Request


class RequestIDGenerator:
    """Monotonic counter generating ``REQ-XXXXXX`` IDs.

    .. caution::
        **Process-local only.**  If the application is restarted, the counter
        resets to zero.  For distributed / multi-worker environments, replace
        this with a globally unique strategy (see module docstring).
    """

    _counter: int
    _lock: threading.Lock

    def __init__(self) -> None:
        self._counter = 0
        self._lock = threading.Lock()

    def __call__(self) -> str:
        with self._lock:
            self._counter += 1
            return f"REQ-{self._counter:06d}"


_request_id_gen = RequestIDGenerator()


async def request_id_middleware(request: Request, call_next):
    """Attach ``request_id`` to ``request.state`` and set both
    ``X-Request-ID`` and ``X-Correlation-ID`` response headers."""
    request_id = _request_id_gen()
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Correlation-ID"] = request_id
    return response
