"""
Configuration module — backward-compatible bridge to Pydantic Settings.

All configuration values are now sourced from :mod:`app.settings` which
uses ``pydantic-settings`` for typed, validated configuration.

Legacy imports like ``from app.config import APP_NAME`` continue to work.
New code should prefer ``from app.settings import settings``.

Example
-------
    # Legacy (still works):
    from app.config import MAX_REPAIR_RETRIES

    # Preferred:
    from app.settings import settings
    print(settings.MAX_REPAIR_RETRIES)
"""

from app.settings import settings as _s

# Application metadata
APP_NAME: str = _s.APP_NAME
APP_VERSION: str = _s.APP_VERSION
API_VERSION: str = _s.API_VERSION
ENVIRONMENT: str = _s.ENVIRONMENT
APP_DESCRIPTION: str = _s.APP_DESCRIPTION
CONTACT: dict = {"name": "OneInbox Team", "url": "https://oneinbox.ai"}
LICENSE_INFO: dict = {"name": "MIT", "url": "https://opensource.org/licenses/MIT"}
SERVERS: list = [{"url": "http://localhost:8000", "description": "Development server"}]

# LLM Provider
LLM_PROVIDER: str = _s.LLM_PROVIDER

# Featherless AI (default provider)
FEATHERLESS_API_KEY: str = _s.FEATHERLESS_API_KEY
FEATHERLESS_BASE_URL: str = _s.FEATHERLESS_BASE_URL
FEATHERLESS_MODEL: str = _s.FEATHERLESS_MODEL

# Groq (optional alternate provider)
GROQ_API_KEY: str = _s.GROQ_API_KEY
GROQ_MODEL: str = _s.GROQ_MODEL

# Extraction
MAX_REPAIR_RETRIES: int = _s.MAX_REPAIR_RETRIES

# Database
DB_PATH: str = _s.DB_PATH
DATABASE_URL: str = _s.DATABASE_URL

# Evaluation
EVALUATION_RECORDS_PATH: str = _s.EVALUATION_RECORDS_PATH
SCHEMA_VERSION: str = _s.SCHEMA_VERSION

# Server
HOST: str = _s.HOST
PORT: int = _s.PORT

# ── Resolved provider / model (single source of truth) ────────────────────
ACTIVE_PROVIDER: str = _s.LLM_PROVIDER

ACTIVE_MODEL: str
if _s.LLM_PROVIDER == "groq":
    ACTIVE_MODEL = _s.GROQ_MODEL or "llama-3.3-70b-versatile"
elif _s.LLM_PROVIDER == "featherless":
    ACTIVE_MODEL = _s.FEATHERLESS_MODEL or "google/gemma-4-31B-it"
else:
    ACTIVE_MODEL = "unknown"
