import os
import time
from datetime import datetime, timezone
from pathlib import Path

from groq import Groq
from openai import OpenAI
from sqlalchemy import text

from app.api.models import HealthCheckDetail, HealthResponse
from app.config import (
    DB_PATH,
    FEATHERLESS_API_KEY,
    FEATHERLESS_BASE_URL,
    FEATHERLESS_MODEL,
    GROQ_API_KEY,
    GROQ_MODEL,
    LLM_PROVIDER,
)
from app.database.database import engine
from app.logging import get_logger, log_event

logger = get_logger(__name__)


class HealthService:
    """Lightweight dependency checker for the /health endpoint.

    Each ``_check_*`` method returns a dict of metadata to include in the
    ``HealthCheckDetail`` (or raises on failure).  The public ``check_all()``
    method runs every check, continues on failure, and aggregates results.
    """

    _REQUIRED_DIRS: list[str] = [
        "data",
    ]

    _REQUIRED_FILES: list[str] = [DB_PATH]

    def check_all(self, request_id: str | None = None) -> HealthResponse:
        overall_start = time.monotonic()
        log_event(logger, event="health_check_started", stage="api", status="started", request_id=request_id)

        checks: dict[str, HealthCheckDetail] = {
            "api": self._run_check(self._check_api, request_id=request_id),
            "database": self._run_check(self._check_database, request_id=request_id),
            "llm_provider": self._run_check(self._check_llm_provider, request_id=request_id),
            "disk": self._run_check(self._check_disk, request_id=request_id),
        }

        overall_status = "healthy" if all(c.status == "ok" for c in checks.values()) else "degraded"
        overall_elapsed = round((time.monotonic() - overall_start) * 1000, 2)

        log_event(
            logger, event="health_check_completed", stage="api", status="success",
            request_id=request_id, response_time_ms=overall_elapsed,
            overall_status=overall_status,
        )

        return HealthResponse(
            status=overall_status,
            timestamp=datetime.now(timezone.utc),
            response_time_ms=overall_elapsed,
            checks=checks,
        )

    # ── Critical dependency detection ─────────────────────────────────────

    @staticmethod
    def has_critical_failure(checks: dict[str, HealthCheckDetail]) -> bool:
        """Return *True* when a core dependency is down (database).

        ``health`` returns **503** when this is *True*, **200** otherwise.
        """
        db = checks.get("database")
        return db is not None and db.status != "ok"

    # ── Internal helpers ──────────────────────────────────────────────────

    @staticmethod
    def _run_check(
        check_fn, request_id: str | None = None
    ) -> HealthCheckDetail:
        start = time.monotonic()
        try:
            metadata = check_fn() if callable(check_fn) else {}
            elapsed = round((time.monotonic() - start) * 1000, 2)
            return HealthCheckDetail(
                status="ok", response_time_ms=elapsed,
                checked_at=datetime.now(timezone.utc),
                **{k: v for k, v in (metadata or {}).items() if v is not None},
            )
        except Exception as exc:
            elapsed = round((time.monotonic() - start) * 1000, 2)
            log_event(
                logger, event="health_check_failed", stage="api", status="failed",
                level="WARNING", request_id=request_id,
                check=check_fn.__name__, error=str(exc),
            )
            return HealthCheckDetail(
                status="degraded", response_time_ms=elapsed,
                error=str(exc), checked_at=datetime.now(timezone.utc),
            )

    @staticmethod
    def _check_api() -> dict:
        return {"provider": LLM_PROVIDER}

    @staticmethod
    def _check_database() -> dict:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"database_type": "sqlite"}

    @staticmethod
    def _check_llm_provider() -> dict:
        if LLM_PROVIDER == "groq":
            if not GROQ_API_KEY:
                raise RuntimeError("GROQ_API_KEY is not configured")
            Groq(api_key=GROQ_API_KEY)
            return {"provider": "groq", "model": GROQ_MODEL}
        elif LLM_PROVIDER == "featherless":
            if not FEATHERLESS_API_KEY:
                raise RuntimeError("FEATHERLESS_API_KEY is not configured")
            OpenAI(api_key=FEATHERLESS_API_KEY, base_url=FEATHERLESS_BASE_URL)
            return {"provider": "featherless", "model": FEATHERLESS_MODEL}
        else:
            return {"provider": LLM_PROVIDER}

    @staticmethod
    def _check_disk() -> dict:
        for dir_str in HealthService._REQUIRED_DIRS:
            p = Path(dir_str)
            if not p.is_dir():
                raise RuntimeError(f"required directory does not exist: {dir_str}")
            if not os.access(str(p), os.R_OK):
                raise RuntimeError(f"required directory is not readable: {dir_str}")
        for file_str in HealthService._REQUIRED_FILES:
            p = Path(file_str)
            if not p.parent.is_dir():
                raise RuntimeError(f"parent directory does not exist: {p.parent}")
        return {}
