from __future__ import annotations


class TestSettings:
    def test_settings_custom_values(self):
        from app.settings import Settings

        settings = Settings(
            LLM_PROVIDER="featherless",
            FEATHERLESS_API_KEY="test-key",
            FEATHERLESS_MODEL="test-model",
            ENVIRONMENT="test",
            APP_NAME="Custom Name",
            MAX_REPAIR_RETRIES=5,
        )
        assert settings.APP_NAME == "Custom Name"
        assert settings.MAX_REPAIR_RETRIES == 5
        assert settings.LLM_TIMEOUT_SECONDS == 60.0
        assert settings.EXTRACTION_TIMEOUT_SECONDS == 120.0

    def test_settings_llm_timeout_config(self):
        from app.settings import Settings

        settings = Settings(
            LLM_PROVIDER="featherless",
            FEATHERLESS_API_KEY="key",
            FEATHERLESS_MODEL="m",
            LLM_TIMEOUT_SECONDS=30.0,
            ENVIRONMENT="test",
        )
        assert settings.LLM_TIMEOUT_SECONDS == 30.0

    def test_settings_featherless_validation_fails_without_key(self):
        from app.settings import Settings

        import pytest

        with pytest.raises(RuntimeError):
            Settings(LLM_PROVIDER="featherless", FEATHERLESS_API_KEY="", FEATHERLESS_MODEL="test", ENVIRONMENT="test")

    def test_settings_groq_validation_fails_without_key(self):
        from app.settings import Settings

        import pytest

        with pytest.raises(RuntimeError):
            Settings(LLM_PROVIDER="groq", GROQ_API_KEY="", ENVIRONMENT="test")

    def test_settings_negative_retries_fails(self):
        from app.settings import Settings

        import pytest

        with pytest.raises(RuntimeError):
            Settings(
                LLM_PROVIDER="featherless",
                FEATHERLESS_API_KEY="key",
                FEATHERLESS_MODEL="m",
                MAX_REPAIR_RETRIES=-1,
                ENVIRONMENT="test",
            )

    def test_settings_batch_defaults(self):
        from app.settings import Settings

        settings = Settings(
            LLM_PROVIDER="featherless",
            FEATHERLESS_API_KEY="key",
            FEATHERLESS_MODEL="m",
            ENVIRONMENT="test",
        )
        assert settings.BATCH_MAX_CONCURRENT_REQUESTS == 2
        assert settings.BATCH_MAX_RETRIES == 3
        assert settings.BATCH_RETRY_DELAYS == [1.0, 2.0, 4.0]


class TestConfigBridge:
    def test_config_exports(self):
        import app.config

        assert app.config.ENVIRONMENT == "test"
        assert app.config.ACTIVE_PROVIDER in ("featherless", "groq")
        assert app.config.ACTIVE_MODEL is not None

    def test_config_contact_and_servers(self):
        import app.config

        assert "OneInbox Team" in str(app.config.CONTACT)
        assert len(app.config.SERVERS) > 0

    def test_config_database_url(self):
        import app.config

        assert app.config.DATABASE_URL.startswith("sqlite://")
        assert app.config.DB_PATH is not None
