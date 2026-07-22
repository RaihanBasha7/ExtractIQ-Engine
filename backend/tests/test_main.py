from __future__ import annotations


class TestAppCreation:
    def test_app_has_title(self, app):
        assert app.title == "OneInbox API"

    def test_app_has_version(self, app):
        assert app.version == "0.1.0"

    def test_app_has_health_endpoint(self, client):
        response = client.get("/health")
        assert response.status_code in (200, 503)

    def test_app_has_version_endpoint(self, client):
        response = client.get("/version")
        assert response.status_code == 200

    def test_app_security_headers(self, client):
        response = client.get("/health")
        headers = response.headers
        assert "X-Request-ID" in headers
        assert "X-Content-Type-Options" in headers

    def test_404_returns_json_not_html(self, client):
        response = client.get("/nonexistent_route_xyz")
        assert response.status_code == 404
        assert response.headers["content-type"] == "application/json"

    def test_cors_headers_present(self, client):
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert "access-control-allow-origin" in response.headers or response.status_code == 200


class TestExceptionHandlers:
    def test_unhandled_exception_returns_500(self, client):
        from unittest.mock import patch

        with patch("app.api.routes.health_service.check_all") as mock:
            mock.side_effect = RuntimeError("Unexpected crash")
            response = client.get("/health")
        assert response.status_code == 500
        data = response.json()
        assert data["error_code"] == "INTERNAL_ERROR"
        assert "request_id" in data

    def test_validation_error_returns_422(self, client):
        response = client.post("/v1/extract", json={"invalid": "data"})
        assert response.status_code == 422
        data = response.json()
        assert data["error_code"] == "VALIDATION_ERROR"

    def test_404_response_has_detail(self, client):
        response = client.get("/nonexistent")
        data = response.json()
        assert "detail" in data
