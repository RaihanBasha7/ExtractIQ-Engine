"""
Centralised configuration using Pydantic Settings.

Replaces ad-hoc ``os.getenv`` calls in ``config.py`` with validated,
typed settings that fail early with meaningful error messages.

Usage
-----
    from app.settings import settings

    settings.LLM_PROVIDER        # "groq" | "featherless"
    settings.FEATHERLESS_API_KEY  # str
    settings.MAX_REPAIR_RETRIES   # int
"""

from __future__ import annotations

from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ── Application metadata ───────────────────────────────────────────────
    APP_NAME: str = "OneInbox API"
    APP_VERSION: str = "0.1.0"
    API_VERSION: str = "v1"
    ENVIRONMENT: Literal["development", "staging", "production", "test"] = "development"
    APP_DESCRIPTION: str = "Extracts structured JSON from noisy support tickets with a model-driven repair loop."

    # ── LLM Provider ──────────────────────────────────────────────────────
    LLM_PROVIDER: Literal["groq", "featherless"] = "featherless"

    # Featherless AI (default provider)
    FEATHERLESS_API_KEY: str = ""
    FEATHERLESS_BASE_URL: str = "https://api.featherless.ai/v1"
    FEATHERLESS_MODEL: str = "google/gemma-4-31B-it"

    # Groq (optional alternate provider)
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    # ── Extraction ─────────────────────────────────────────────────────────
    MAX_REPAIR_RETRIES: int = 3

    # ── Database ───────────────────────────────────────────────────────────
    DB_PATH: str = "data/extractions.db"
    DATABASE_URL: str = "sqlite:///data/extractions.db"

    # ── Evaluation ─────────────────────────────────────────────────────────
    EVALUATION_RECORDS_PATH: str = "data/evaluation_records.jsonl"
    SCHEMA_VERSION: str = "1.0"

    # ── Server ─────────────────────────────────────────────────────────────
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # ── File upload / ingestion ─────────────────────────────────────────────
    MAX_UPLOAD_SIZE_MB: int = 100
    TEMP_UPLOAD_DIR: str = "/tmp/extractiq_uploads"
    INGESTION_CHUNK_SIZE: int = 50  # Max tickets per chunk for large documents

    # ── Batch processing ────────────────────────────────────────────────────
    BATCH_MAX_CONCURRENT_REQUESTS: int = 2
    BATCH_MAX_RETRIES: int = 3
    BATCH_RETRY_DELAYS: list[float] = [1.0, 2.0, 4.0]

    def model_post_init(self, __context) -> None:
        """Validate configuration after initialisation."""
        if self.LLM_PROVIDER == "featherless":
            if not self.FEATHERLESS_API_KEY:
                raise RuntimeError(
                    "FEATHERLESS_API_KEY is required when LLM_PROVIDER='featherless'. "
                    "Set it in .env or as an environment variable."
                )
            if not self.FEATHERLESS_MODEL:
                raise RuntimeError(
                    "FEATHERLESS_MODEL is required when LLM_PROVIDER='featherless'. "
                    "Set it in .env or as an environment variable."
                )
        elif self.LLM_PROVIDER == "groq":
            if not self.GROQ_API_KEY:
                raise RuntimeError(
                    "GROQ_API_KEY is required when LLM_PROVIDER='groq'. "
                    "Set it in .env or as an environment variable."
                )
        else:
            raise RuntimeError(f"Unsupported LLM_PROVIDER: {self.LLM_PROVIDER}")

        if self.MAX_REPAIR_RETRIES < 0:
            raise RuntimeError("MAX_REPAIR_RETRIES must be >= 0")

        if self.ENVIRONMENT not in ("development", "staging", "production", "test"):
            raise RuntimeError(f"Invalid ENVIRONMENT: {self.ENVIRONMENT}")


settings = Settings()
"""
Global settings instance.

Import this in any module that needs configuration:

    from app.settings import settings
    print(settings.LLM_PROVIDER)
"""
