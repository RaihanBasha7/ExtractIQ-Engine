import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from the backend/ directory (parent of app/)
dotenv_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=dotenv_path)

# Application metadata
APP_NAME = os.getenv("APP_NAME", "OneInbox API")
APP_VERSION = os.getenv("APP_VERSION", "0.1.0")
API_VERSION = os.getenv("API_VERSION", "v1")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
APP_DESCRIPTION = os.getenv(
    "APP_DESCRIPTION",
    "Extracts structured JSON from noisy support tickets with a model-driven repair loop.",
)
CONTACT = {"name": "OneInbox Team", "url": "https://oneinbox.ai"}
LICENSE_INFO = {"name": "MIT", "url": "https://opensource.org/licenses/MIT"}
SERVERS = [{"url": "http://localhost:8000", "description": "Development server"}]

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

MAX_REPAIR_RETRIES = int(os.getenv("MAX_REPAIR_RETRIES", "3"))

DB_PATH = os.getenv("DB_PATH", "data/extractions.db")

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")

EVALUATION_RECORDS_PATH = os.getenv("EVALUATION_RECORDS_PATH", "data/evaluation_records.jsonl")
SCHEMA_VERSION = os.getenv("SCHEMA_VERSION", "1.0")

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq")

FEATHERLESS_API_KEY = os.getenv("FEATHERLESS_API_KEY", "")
FEATHERLESS_BASE_URL = os.getenv("FEATHERLESS_BASE_URL", "https://api.featherless.ai/v1")

MODEL = os.getenv("MODEL", "")

if LLM_PROVIDER == "featherless":
    if not FEATHERLESS_API_KEY:
        raise RuntimeError(
            "FEATHERLESS_API_KEY is not set. Copy .env.example to .env and add your Featherless key."
        )
    if not MODEL:
        raise RuntimeError(
            "MODEL is not set. Copy .env.example to .env and add your model name."
        )

if not GROQ_API_KEY and LLM_PROVIDER == "groq":
    raise RuntimeError(
        "GROQ_API_KEY is not set. Copy .env.example to .env and add your Groq key."
    )

# ── Resolved provider / model (single source of truth) ────────────────────

ACTIVE_PROVIDER: str = LLM_PROVIDER

ACTIVE_MODEL: str
if LLM_PROVIDER == "groq":
    ACTIVE_MODEL = GROQ_MODEL or "llama-3.3-70b-versatile"
elif LLM_PROVIDER == "featherless":
    ACTIVE_MODEL = MODEL or "unknown"
else:
    ACTIVE_MODEL = "unknown"
