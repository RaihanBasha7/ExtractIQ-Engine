from __future__ import annotations

from unittest.mock import patch


class TestHealthService:
    def test_has_critical_failure_database_down(self):
        from app.api.models import HealthCheckDetail
        from app.services.health_service import HealthService

        checks = {
            "database": HealthCheckDetail(status="degraded", response_time_ms=1.0, error="DB down"),
            "api": HealthCheckDetail(status="ok", response_time_ms=0.5),
        }
        assert HealthService.has_critical_failure(checks) is True

    def test_no_critical_failure(self):
        from app.api.models import HealthCheckDetail
        from app.services.health_service import HealthService

        checks = {
            "database": HealthCheckDetail(status="ok", response_time_ms=1.0),
            "api": HealthCheckDetail(status="ok", response_time_ms=0.5),
        }
        assert HealthService.has_critical_failure(checks) is False

    def test_check_database_ok(self):
        from app.services.health_service import HealthService

        result = HealthService._check_database()
        assert "database_type" in result

    def test_check_api_returns_provider(self):
        from app.services.health_service import HealthService

        result = HealthService._check_api()
        assert "provider" in result

    def test_check_disk_ok(self):
        from app.services.health_service import HealthService

        result = HealthService._check_disk()
        assert result == {}

    def test_check_all_returns_health_response(self):
        from app.services.health_service import HealthService

        service = HealthService()
        result = service.check_all(request_id="REQ-TEST")
        assert result.status in ("healthy", "degraded")
        assert result.timestamp is not None
        assert "api" in result.checks
        assert "database" in result.checks
        assert "llm_provider" in result.checks
        assert "disk" in result.checks

    def test_check_all_with_db_error(self):
        from app.services.health_service import HealthService

        original = HealthService._check_database

        def failing_check():
            raise RuntimeError("DB error")

        HealthService._check_database = staticmethod(failing_check)
        try:
            service = HealthService()
            result = service.check_all()
            assert result.status == "degraded"
            assert result.checks["database"].status == "degraded"
        finally:
            HealthService._check_database = original


class TestVersionService:
    def test_version_has_correct_fields(self):
        from app.services.version_service import VersionService

        service = VersionService()
        info = service.get_version()
        assert info.service is not None
        assert info.version is not None
        assert info.api_version is not None
        assert info.provider is not None
        assert info.model is not None
        assert info.environment is not None
        assert info.python_version is not None
        assert info.timestamp is not None


class TestMetricsService:
    def test_get_metrics_returns_all_fields(self):
        from app.services.metrics_service import MetricsService

        service = MetricsService()
        metrics = service.get_metrics()
        assert hasattr(metrics, "total_requests")
        assert hasattr(metrics, "successful_extractions")
        assert hasattr(metrics, "failed_extractions")
        assert hasattr(metrics, "failure_breakdown")
        assert hasattr(metrics, "average_confidence")
        assert hasattr(metrics, "needs_review_count")
        assert hasattr(metrics, "repair_count")
        assert hasattr(metrics, "failure_rate")
