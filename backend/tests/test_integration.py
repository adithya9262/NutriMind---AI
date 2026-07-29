"""End-to-end integration tests that start the FastAPI server as a subprocess.

These tests verify the real HTTP layer (not just ASGI transport) including
CORS headers, request/response lifecycle, and overall server behavior.

Only endpoints that work without a database are covered here. Auth endpoints
require a database connection and are thoroughly covered by ASGI-level unit
tests in test_auth_api.py and test_current_user.py.
"""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from contextlib import closing, suppress

import httpx
import pytest

PORT_ENV_VAR = "NUTRIMIND_INTEGRATION_PORT"


def _find_free_port() -> int:
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(("127.0.0.1", 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


def _wait_for_server(base_url: str, timeout: int = 30, interval: float = 0.5) -> bool:
    start = time.monotonic()
    while time.monotonic() - start < timeout:
        with suppress(Exception):
            r = httpx.get(f"{base_url}/api/v1/health", timeout=2)
            if r.status_code == 200:
                return True
        time.sleep(interval)
    return False


@pytest.fixture(scope="session")
def integration_port() -> int:
    port = int(os.environ.get(PORT_ENV_VAR, "0"))
    return port if port > 0 else _find_free_port()


@pytest.fixture(scope="session")
def integration_base_url(integration_port: int) -> str:
    return f"http://127.0.0.1:{integration_port}"


@pytest.fixture(scope="session")
def integration_settings_env() -> dict[str, str]:
    return {
        "APP_ENV": "test",
        "DEBUG": "false",
        "BACKEND_HOST": "127.0.0.1",
        "CORS_ORIGINS": "http://localhost:3000,http://127.0.0.1:3000",
        "JWT_SECRET_KEY": "integration-test-secret-key-at-least-32-chars!!",
    }


@pytest.fixture(scope="session")
def server_process(
    integration_port: int,
    integration_base_url: str,
    integration_settings_env: dict[str, str],
) -> subprocess.Popen:
    env = os.environ.copy()
    env["BACKEND_PORT"] = str(integration_port)
    for k, v in integration_settings_env.items():
        env[k] = v

    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(integration_port),
            "--log-level",
            "warning",
        ],
        cwd=os.path.join(os.path.dirname(__file__), ".."),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    if not _wait_for_server(integration_base_url, timeout=20):
        proc.terminate()
        with suppress(Exception):
            proc.wait(timeout=5)
        pytest.fail("Integration server failed to start within timeout")

    yield proc

    proc.terminate()
    with suppress(Exception):
        proc.wait(timeout=5)


@pytest.fixture(scope="session")
def integration_client(server_process: subprocess.Popen, integration_base_url: str) -> httpx.Client:
    return httpx.Client(base_url=integration_base_url, timeout=10)


# ---------------------------------------------------------------------------
# Health endpoint
# ---------------------------------------------------------------------------


class TestHealthEndpoint:
    def test_returns_200(self, integration_client: httpx.Client):
        response = integration_client.get("/api/v1/health")
        assert response.status_code == 200

    def test_expected_structure(self, integration_client: httpx.Client):
        response = integration_client.get("/api/v1/health")
        assert response.json() == {
            "success": True,
            "message": "NutriMind API is healthy",
            "data": {"status": "healthy"},
        }

    def test_returns_x_request_id(self, integration_client: httpx.Client):
        response = integration_client.get("/api/v1/health")
        assert "X-Request-ID" in response.headers
        assert len(response.headers["X-Request-ID"]) > 0

    def test_valid_request_id_is_preserved(self, integration_client: httpx.Client):
        custom_id = "test-req-123"
        response = integration_client.get("/api/v1/health", headers={"X-Request-ID": custom_id})
        assert response.headers["X-Request-ID"] == custom_id

    def test_health_not_at_unversioned_path(self, integration_client: httpx.Client):
        response = integration_client.get("/health")
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------


class TestCORS:
    def test_allowed_origin_receives_header(self, integration_client: httpx.Client):
        response = integration_client.get(
            "/api/v1/health",
            headers={"Origin": "http://localhost:3000"},
        )
        assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"

    def test_disallowed_origin_omits_allow_origin(self, integration_client: httpx.Client):
        response = integration_client.get(
            "/api/v1/health",
            headers={"Origin": "http://evil.com"},
        )
        allow = response.headers.get("access-control-allow-origin")
        assert allow is None or allow != "http://evil.com"

    def test_preflight_returns_cors_headers(self, integration_client: httpx.Client):
        response = integration_client.options(
            "/api/v1/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.status_code == 200
        assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"

    def test_exposes_x_request_id(self, integration_client: httpx.Client):
        response = integration_client.get(
            "/api/v1/health",
            headers={"Origin": "http://localhost:3000"},
        )
        exposed = response.headers.get("access-control-expose-headers", "")
        assert "X-Request-ID" in exposed

    def test_preflight_allows_x_request_id(self, integration_client: httpx.Client):
        response = integration_client.options(
            "/api/v1/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "X-Request-ID, Content-Type",
            },
        )
        headers = response.headers.get("access-control-allow-headers", "")
        assert "X-Request-ID" in headers
        assert "Content-Type" in headers


# ---------------------------------------------------------------------------
# Route registration (no database required)
# ---------------------------------------------------------------------------


class TestRouteRegistration:
    def test_health_path(self, integration_client: httpx.Client):
        response = integration_client.get("/api/v1/health")
        assert response.status_code == 200

    def test_root_endpoint(self, integration_client: httpx.Client):
        response = integration_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "status" in data
        assert data["status"] == "running"

    def test_docs_endpoint(self, integration_client: httpx.Client):
        response = integration_client.get("/docs")
        assert response.status_code == 200

    def test_openapi_json(self, integration_client: httpx.Client):
        response = integration_client.get("/openapi.json")
        assert response.status_code == 200
        paths = response.json()["paths"]
        assert "/api/v1/health" in paths
        assert "/api/v1/auth/register" in paths
        assert "/api/v1/auth/login" in paths
        assert "/api/v1/auth/me" in paths

    def test_redoc_endpoint(self, integration_client: httpx.Client):
        response = integration_client.get("/redoc")
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# Error handling (no database required)
# ---------------------------------------------------------------------------


class TestErrorHandling:
    def test_unknown_route_returns_404(self, integration_client: httpx.Client):
        response = integration_client.get("/api/v1/nonexistent")
        assert response.status_code == 404

    def test_unknown_api_route_returns_404(self, integration_client: httpx.Client):
        response = integration_client.get("/api/unknown")
        assert response.status_code == 404

    def test_wrong_method_returns_405(self, integration_client: httpx.Client):
        response = integration_client.post("/api/v1/health")
        assert response.status_code == 405


# ---------------------------------------------------------------------------
# Security headers and X-Request-ID propagation
# ---------------------------------------------------------------------------


class TestSecurityHeaders:
    def test_x_request_id_on_root(self, integration_client: httpx.Client):
        response = integration_client.get("/")
        assert "X-Request-ID" in response.headers
        assert len(response.headers["X-Request-ID"]) > 0

    def test_x_request_id_on_404(self, integration_client: httpx.Client):
        response = integration_client.get("/api/v1/nonexistent")
        assert "X-Request-ID" in response.headers
        assert len(response.headers["X-Request-ID"]) > 0

    def test_x_request_id_on_405(self, integration_client: httpx.Client):
        response = integration_client.post("/api/v1/health")
        assert "X-Request-ID" in response.headers
        assert len(response.headers["X-Request-ID"]) > 0

    def test_x_request_id_on_health(self, integration_client: httpx.Client):
        response = integration_client.get("/api/v1/health")
        assert "X-Request-ID" in response.headers
        assert len(response.headers["X-Request-ID"]) > 0
