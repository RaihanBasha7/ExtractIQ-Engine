import json
import logging
import sys
from datetime import datetime, timezone
from enum import Enum

_LOG_RECORD_ATTRS = {
    "args",
    "asctime",
    "created",
    "exc_info",
    "exc_text",
    "filename",
    "funcName",
    "id",
    "levelname",
    "levelno",
    "lineno",
    "module",
    "msecs",
    "message",
    "msg",
    "name",
    "pathname",
    "process",
    "processName",
    "relativeCreated",
    "stack_info",
    "taskName",
    "thread",
    "threadName",
}


class Stage(str, Enum):
    API = "api"
    PREPROCESSING = "preprocessing"
    EXTRACTION = "extraction"
    VALIDATION = "validation"
    REPAIR = "repair"
    EVALUATION = "evaluation"


class Status(str, Enum):
    STARTED = "started"
    SUCCESS = "success"
    RETRYING = "retrying"
    FAILED = "failed"


class StructuredFormatter(logging.Formatter):
    """JSON formatter that merges ``extra`` kwargs into the output dict.

    Example output::

        {"timestamp": "2026-07-19T10:30:00Z", "level": "INFO",
         "event": "request_received", "stage": "api", "status": "started",
         "request_id": "REQ-000001", "ticket_id": "TKT-001"}
    """

    def format(self, record: logging.LogRecord) -> str:
        event = {
            "timestamp": (datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat().replace("+00:00", "Z")),
            "level": record.levelname,
        }
        for key, value in record.__dict__.items():
            if key not in _LOG_RECORD_ATTRS:
                event[key] = value
        if record.exc_info and record.exc_info[0]:
            event["exception"] = self.formatException(record.exc_info)
        return json.dumps(event, default=str)


def configure_logging() -> None:
    """Configure root logger with a single JSON stream handler."""
    root = logging.getLogger()
    root.setLevel(logging.INFO)

    if not root.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredFormatter())
        root.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """Return a module-level logger."""
    return logging.getLogger(name)


_LOG_LEVEL_MAP = {
    "DEBUG": "debug",
    "INFO": "info",
    "WARNING": "warning",
    "ERROR": "error",
    "CRITICAL": "critical",
}


def log_event(
    logger: logging.Logger,
    *,
    event: str | None = None,
    stage: str | Stage,
    status: str | Status,
    level: str = "INFO",
    exc_info: bool = False,
    **fields,
) -> None:
    """Emit a structured JSON log entry.

    Every entry includes ``timestamp``, ``level``, ``stage``, and ``status``.

    Common optional fields
    (passed as ``**fields`` — ``None`` values are omitted):
        ``request_id``, ``ticket_id``, ``attempt``, ``latency_ms``,
        ``validation_error``, ``provider``, ``model``.

    Parameters
    ----------
    logger:
        Logger instance (obtained via :func:`get_logger`).
    event:
        Descriptive event name (e.g. ``"request_received"``,
        ``"preprocessing_completed"``, ``"validation_failed"``).
    stage:
        Pipeline stage — use :class:`Stage` enum or a string.
    status:
        Event status — use :class:`Status` enum or a string.
    level:
        Log level — ``DEBUG``, ``INFO``, ``WARNING``, ``ERROR``, ``CRITICAL``.
    exc_info:
        When *True* the current exception traceback is serialised into
        an ``exception`` key (same behaviour as ``logger.exception``).
    **fields:
        Any additional key-value pairs.  ``None`` values are silently dropped.
    """
    method_name = _LOG_LEVEL_MAP.get(level.upper(), "info")
    method = getattr(logger, method_name)
    entry: dict = {"stage": stage, "status": status}
    if event is not None:
        entry["event"] = event
    entry.update(fields)
    entry = {k: v for k, v in entry.items() if v is not None}
    method("", extra=entry, exc_info=exc_info)
