import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import Settings
from app.main import create_app


@pytest.fixture
def test_settings():
    return Settings(
        APP_ENV="test",
        DEBUG=False,
        CORS_ORIGINS="http://test",
    )


@pytest.fixture
def app(test_settings):
    return create_app(settings=test_settings)


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestHealthEndpoint:
    async def test_returns_200(self, client):
        response = await client.get("/api/v1/health")
        assert response.status_code == 200

    async def test_returns_expected_structure(self, client):
        response = await client.get("/api/v1/health")
        data = response.json()
        assert data == {
            "success": True,
            "message": "NutriMind API is healthy",
            "data": {"status": "healthy"},
        }

    async def test_returns_x_request_id(self, client):
        response = await client.get("/api/v1/health")
        assert "X-Request-ID" in response.headers
        assert len(response.headers["X-Request-ID"]) > 0


class TestRequestID:
    async def test_valid_request_id_is_preserved(self, client):
        custom_id = "test-req-123"
        response = await client.get("/api/v1/health", headers={"X-Request-ID": custom_id})
        assert response.headers["X-Request-ID"] == custom_id

    async def test_missing_request_id_generates_new(self, client):
        response = await client.get("/api/v1/health")
        req_id = response.headers["X-Request-ID"]
        assert len(req_id) == 32
        assert all(c in "0123456789abcdef" for c in req_id)

    async def test_invalid_characters_are_replaced(self, client):
        bad_id = "<script>alert('xss')</script>"
        response = await client.get("/api/v1/health", headers={"X-Request-ID": bad_id})
        req_id = response.headers["X-Request-ID"]
        assert req_id != bad_id
        assert len(req_id) == 32

    async def test_excessively_long_id_is_replaced(self, client):
        long_id = "a" * 100
        response = await client.get("/api/v1/health", headers={"X-Request-ID": long_id})
        req_id = response.headers["X-Request-ID"]
        assert req_id != long_id
        assert len(req_id) == 32


class TestConfiguration:
    async def test_api_prefix_is_correctly_applied(self, client):
        response = await client.get("/api/v1/health")
        assert response.status_code == 200

    async def test_health_not_at_unversioned_path(self, client):
        response = await client.get("/health")
        assert response.status_code == 404

    async def test_root_endpoint_exists(self, client):
        response = await client.get("/")
        assert response.status_code == 200


class TestRequestIDExtended:
    async def test_empty_id_is_replaced(self, client):
        response = await client.get("/api/v1/health", headers={"X-Request-ID": ""})
        req_id = response.headers["X-Request-ID"]
        assert len(req_id) == 32

    async def test_whitespace_only_id_is_replaced(self, client):
        response = await client.get("/api/v1/health", headers={"X-Request-ID": "   "})
        req_id = response.headers["X-Request-ID"]
        assert len(req_id) == 32

    async def test_id_with_spaces_is_replaced(self, client):
        response = await client.get("/api/v1/health", headers={"X-Request-ID": "my id"})
        req_id = response.headers["X-Request-ID"]
        assert len(req_id) == 32

    async def test_id_with_newline_is_replaced(self, client):
        response = await client.get("/api/v1/health", headers={"X-Request-ID": "id\nid"})
        req_id = response.headers["X-Request-ID"]
        assert len(req_id) == 32

    async def test_id_at_max_length_is_preserved(self, client):
        exact_id = "a" * 64
        response = await client.get("/api/v1/health", headers={"X-Request-ID": exact_id})
        assert response.headers["X-Request-ID"] == exact_id

    async def test_id_one_over_max_length_is_replaced(self, client):
        long_id = "a" * 65
        response = await client.get("/api/v1/health", headers={"X-Request-ID": long_id})
        req_id = response.headers["X-Request-ID"]
        assert len(req_id) == 32


class TestErrorHandling:
    @pytest.fixture
    def error_app(self, test_settings):
        app = create_app(settings=test_settings)

        @app.get("/api/v1/test-error")
        async def test_error():
            raise RuntimeError("This is a controlled test error")

        return app

    @pytest.fixture
    async def error_client(self, error_app):
        transport = ASGITransport(app=error_app, raise_app_exceptions=False)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac

    async def test_returns_500(self, error_client):
        response = await error_client.get("/api/v1/test-error")
        assert response.status_code == 500

    async def test_response_structure(self, error_client):
        response = await error_client.get("/api/v1/test-error")
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "INTERNAL_SERVER_ERROR"
        assert data["error"]["message"] == "An unexpected error occurred."
        assert "request_id" in data["error"]

    async def test_does_not_expose_exception_message(self, error_client):
        response = await error_client.get("/api/v1/test-error")
        assert "This is a controlled test error" not in response.text

    async def test_does_not_expose_stack_trace(self, error_client):
        response = await error_client.get("/api/v1/test-error")
        assert "Traceback" not in response.text
        assert "File" not in response.text

    async def test_request_id_in_body_matches_header(self, error_client):
        response = await error_client.get("/api/v1/test-error")
        header_id = response.headers.get("X-Request-ID")
        body_id = response.json()["error"]["request_id"]
        assert header_id is not None
        assert body_id is not None
        assert header_id == body_id

    async def test_x_request_id_header_present(self, error_client):
        response = await error_client.get("/api/v1/test-error")
        assert "X-Request-ID" in response.headers
        assert len(response.headers["X-Request-ID"]) > 0


class TestFrameworkBehavior:
    async def test_unknown_route_returns_404(self, client):
        response = await client.get("/api/v1/nonexistent")
        assert response.status_code == 404

    async def test_wrong_method_returns_405(self, client):
        response = await client.post("/api/v1/health")
        assert response.status_code == 405


class TestCORSExtended:
    async def test_configured_origin_receives_cors_headers(self, client, test_settings):
        origin = test_settings.cors_origins_list[0]
        response = await client.get(
            "/api/v1/health",
            headers={"Origin": origin},
        )
        assert response.headers.get("access-control-allow-origin") == origin

    async def test_exposes_x_request_id(self, client, test_settings):
        origin = test_settings.cors_origins_list[0]
        response = await client.get(
            "/api/v1/health",
            headers={"Origin": origin},
        )
        exposed = response.headers.get("access-control-expose-headers", "")
        assert "X-Request-ID" in exposed

    async def test_disallowed_origin_omits_allow_origin(self, client):
        response = await client.get(
            "/api/v1/health",
            headers={"Origin": "http://evil.com"},
        )
        allow_origin = response.headers.get("access-control-allow-origin")
        assert allow_origin is None or allow_origin != "http://evil.com"

    async def test_preflight_returns_cors_headers(self, client, test_settings):
        origin = test_settings.cors_origins_list[0]
        response = await client.options(
            "/api/v1/health",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.status_code == 200
        assert response.headers.get("access-control-allow-origin") == origin

    async def test_preflight_exposes_expected_headers(self, client, test_settings):
        origin = test_settings.cors_origins_list[0]
        response = await client.options(
            "/api/v1/health",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "X-Request-ID, Content-Type",
            },
        )
        allow_headers = response.headers.get("access-control-allow-headers", "")
    async def test_production_frontend_preflight_login(self, client):
        response = await client.options(
            "/api/v1/auth/login",
            headers={
                "Origin": "https://nutrimind-frontend.onrender.com",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Authorization, Content-Type",
            },
        )
        assert response.status_code == 200
        assert response.headers.get("access-control-allow-origin") == "https://nutrimind-frontend.onrender.com"
        assert response.headers.get("access-control-allow-credentials") == "true"
        allow_methods = response.headers.get("access-control-allow-methods", "")
        assert "POST" in allow_methods
        allow_headers = response.headers.get("access-control-allow-headers", "").lower()
        assert "authorization" in allow_headers
        assert "content-type" in allow_headers

    async def test_production_frontend_preflight_register(self, client):
        response = await client.options(
            "/api/v1/auth/register",
            headers={
                "Origin": "https://nutrimind-frontend.onrender.com",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Authorization, Content-Type",
            },
        )
        assert response.status_code == 200
        assert response.headers.get("access-control-allow-origin") == "https://nutrimind-frontend.onrender.com"
        assert response.headers.get("access-control-allow-credentials") == "true"


class TestAppFactory:
    def test_two_apps_can_be_created(self, test_settings):
        app1 = create_app(settings=test_settings)
        app2 = create_app(settings=test_settings)
        assert app1 is not app2

    def test_each_app_has_expected_middleware(self, test_settings):
        from fastapi.middleware.cors import CORSMiddleware

        from app.core.middleware import RequestIDMiddleware

        app = create_app(settings=test_settings)
        classes = [m.cls for m in app.user_middleware]
        assert CORSMiddleware in classes
        assert RequestIDMiddleware in classes
        assert len(classes) == 2

    def test_apps_do_not_share_middleware_state(self, test_settings):
        app1 = create_app(settings=test_settings)
        app2 = create_app(settings=test_settings)
        mw1 = [(m.cls, m.kwargs) for m in app1.user_middleware]
        mw2 = [(m.cls, m.kwargs) for m in app2.user_middleware]
        assert mw1 == mw2
        assert mw1 is not mw2
