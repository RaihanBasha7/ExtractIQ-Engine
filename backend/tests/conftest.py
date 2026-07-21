"""Shared test fixtures and configuration."""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Ensure backend/ is on sys.path
_backend_root = str(Path(__file__).resolve().parent.parent)
if _backend_root not in sys.path:
    sys.path.insert(0, _backend_root)

# Set test environment BEFORE any app imports
os.environ["LLM_PROVIDER"] = "featherless"
os.environ["FEATHERLESS_API_KEY"] = "test-featherless-key"
os.environ["FEATHERLESS_MODEL"] = "deepseek-ai/DeepSeek-V4-Pro"
os.environ["FEATHERLESS_BASE_URL"] = "https://api.featherless.ai/v1"
os.environ["MAX_REPAIR_RETRIES"] = "3"
os.environ["ENVIRONMENT"] = "test"

# Optional: Groq test credentials (for tests that exercise Groq-specific paths)
os.environ["GROQ_API_KEY"] = "test-groq-key"
os.environ["GROQ_MODEL"] = "llama-3.3-70b-versatile"

# Use a temporary file for the test database so it persists across connections
_test_db_fd, _test_db_path = tempfile.mkstemp(suffix=".test.db")
os.environ["DB_PATH"] = _test_db_path
os.environ["DATABASE_URL"] = f"sqlite:///{_test_db_path}"

# Create database tables eagerly so they exist for all tests
from app.database.database import create_database  # noqa: E402
create_database()


def _cleanup_test_db():
    """Remove the temporary test database file."""
    try:
        os.close(_test_db_fd)
    except OSError:
        pass
    try:
        os.unlink(_test_db_path)
    except OSError:
        pass


# Register cleanup at exit
import atexit
atexit.register(_cleanup_test_db)


# ---------------------------------------------------------------------------
# Schema fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def valid_extraction_dict() -> dict[str, Any]:
    return {
        "ticket_id": "TKT-001",
        "customer": {"name": "John Doe", "account_id": "ACC-001"},
        "issue": {
            "category": "technical",
            "subcategory": "login failure",
            "product_or_service": "account",
            "urgency": "high",
        },
        "sentiment": "frustrated",
        "entities": {
            "order_ids": ["ORD-12345"],
            "dates_mentioned": [],
            "amounts_mentioned": [],
        },
        "requested_action": "reset password",
        "resolution_status": "unresolved",
    }


@pytest.fixture
def invalid_extraction_dict() -> dict[str, Any]:
    return {
        "ticket_id": "TKT-002",
        "customer": {"name": "Jane", "account_id": None},
        "issue": {
            "category": "invalid_category",
            "subcategory": None,
            "product_or_service": None,
            "urgency": "unknown_urgency",
        },
        "sentiment": "unknown",
        "entities": {"order_ids": [], "dates_mentioned": [], "amounts_mentioned": []},
        "requested_action": None,
        "resolution_status": "invalid_status",
    }


# ---------------------------------------------------------------------------
# Database fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def db_session():
    """Provide a SQLAlchemy session with transaction rollback for isolation."""
    from app.database.database import SessionLocal, engine
    from sqlalchemy.orm import close_all_sessions

    # Close all existing sessions and begin a transaction
    connection = engine.connect()
    transaction = connection.begin()
    session = SessionLocal(bind=connection)
    session.expire_on_commit = False
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture(autouse=True)
def _clear_db_between_tests(request):
    """Clear all database tables between tests in test_database.py."""
    if "test_database" in request.node.fspath.strpath:
        from app.database.database import Base, engine

        for table in reversed(Base.metadata.sorted_tables):
            with engine.connect() as conn:
                conn.execute(table.delete())
                conn.commit()


# ---------------------------------------------------------------------------
# FastAPI app / TestClient fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function")
def app() -> FastAPI:
    """Create a fresh FastAPI app for each test."""
    from app.main import app as _app

    return _app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """Provide a TestClient for API tests."""
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


# ---------------------------------------------------------------------------
# Repair log fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def repair_log_with_entries():
    """Return a RepairLog with sample entries."""
    from datetime import datetime, timezone

    from app.repair_logging import RepairLog, record_attempt

    log = RepairLog()
    record_attempt(log, 1, "success", None, 0.5, timestamp=datetime.now(timezone.utc))
    record_attempt(
        log, 2, "failed", "validation error: field required", 1.2, timestamp=datetime.now(timezone.utc)
    )
    return log


# ---------------------------------------------------------------------------
# Temporary directory
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_data_dir(tmp_path: Path) -> Path:
    """Provide a temporary data directory."""
    d = tmp_path / "data"
    d.mkdir(parents=True, exist_ok=True)
    return d
