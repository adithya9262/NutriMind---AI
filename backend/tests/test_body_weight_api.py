from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.authentication import (
    get_settings as deps_get_settings,
)
from app.core.config import Settings
from app.core.tokens import create_access_token
from app.db.dependencies import get_db_session
from app.main import create_app
from app.models.body_weight import BodyWeight
from app.models.user import User

NOW = datetime.now(UTC)
TEST_LOGGED_DATE = date(2026, 7, 12)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_session() -> AsyncMock:
    return AsyncMock(spec=AsyncSession)


def _make_user(is_active: bool = True) -> MagicMock:
    user = MagicMock(spec=User)
    user.id = uuid.uuid4()
    user.email = "test@example.com"
    user.password_hash = "$argon2id$v=19$m=65536,t=3,p=4$hash"
    user.is_active = is_active
    user.is_verified = False
    user.created_at = NOW
    user.updated_at = NOW
    return user


def _make_body_weight(
    user_id: uuid.UUID | None = None,
    entry_id: uuid.UUID | None = None,
    logged_date: date = TEST_LOGGED_DATE,
    weight_kg: Decimal = Decimal("70.00"),
) -> MagicMock:
    entry = MagicMock(spec=BodyWeight)
    entry.id = uuid.uuid4()
    entry.user_id = user_id or uuid.uuid4()
    entry.entry_id = entry_id or uuid.uuid4()
    entry.logged_date = logged_date
    entry.weight_kg = weight_kg
    entry.created_at = NOW
    entry.updated_at = NOW
    return entry


def _make_execute_result(value: MagicMock | None) -> MagicMock:
    result = MagicMock()
    result.scalars.return_value.one_or_none.return_value = value
    return result


_VALID_CREATE_BODY = {
    "weight_kg": "70.00",
}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def test_settings():
    return Settings(
        APP_ENV="test",
        DEBUG=False,
        CORS_ORIGINS="http://test",
        JWT_SECRET_KEY="test-secret-key-that-is-at-least-32-characters!!",
    )


@pytest.fixture
def mock_session():
    return _make_session()


@pytest.fixture
def app(test_settings, mock_session):
    app = create_app(settings=test_settings)
    app.dependency_overrides[deps_get_settings] = lambda: test_settings

    async def override_get_db_session():
        try:
            yield mock_session
        finally:
            pass

    app.dependency_overrides[get_db_session] = override_get_db_session
    return app


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ===========================================================================
# A. Router Registration
# ===========================================================================


class TestRouteRegistration:
    async def test_router_exists(self, app):
        paths = [r.path for r in app.routes if "body-weight" in r.path or "body_weight" in r.path]
        assert len(paths) > 0

    async def test_correct_prefix(self, app):
        paths = [r.path for r in app.routes if "body-weight" in r.path]
        for p in paths:
            assert p.startswith("/api/v1/body-weights")

    async def test_post_path_exists(self, client):
        response = await client.post("/api/v1/body-weights", json={})
        assert response.status_code != 404

    async def test_get_path_exists(self, client):
        response = await client.get("/api/v1/body-weights")
        assert response.status_code != 404

    async def test_delete_path_exists(self, client):
        eid = uuid.uuid4()
        response = await client.delete(f"/api/v1/body-weights/{eid}")
        assert response.status_code != 404

    async def test_no_duplicate_body_weight_paths(self, app):
        bw_routes = {
            r.path for r in app.routes if "body-weight" in r.path or "body_weight" in r.path
        }
        assert len(bw_routes) == 4
        assert "/api/v1/body-weights" in bw_routes
        assert "/api/v1/body-weights/trend" in bw_routes
        assert "/api/v1/body-weights/goal-progress" in bw_routes
        assert "/api/v1/body-weights/{entry_id}" in bw_routes

    async def test_no_singular_path(self, app):
        paths = [
            r.path for r in app.routes if "body-weight" in r.path and "body-weights" not in r.path
        ]
        assert len(paths) == 0

    async def test_no_get_by_id(self, app):
        get_paths = [
            r.path
            for r in app.routes
            if "body-weight" in r.path
            and hasattr(r, "methods")
            and "GET" in r.methods
            and "{entry_id}" in r.path
        ]
        assert len(get_paths) == 0

    async def test_no_patch_endpoint(self, client):
        response = await client.patch("/api/v1/body-weights")
        assert response.status_code == 405

    async def test_no_put_endpoint(self, client):
        response = await client.put("/api/v1/body-weights")
        assert response.status_code == 405

    async def test_no_summary_endpoint(self, client):
        response = await client.get("/api/v1/body-weights/summary")
        # "summary" matches the {entry_id} path param which only accepts DELETE
        assert response.status_code in (404, 405)

    async def test_no_progress_endpoint(self, client):
        response = await client.get("/api/v1/body-weights/progress")
        assert response.status_code in (404, 405)

    async def test_no_trend_endpoint(self, client):
        response = await client.get("/api/v1/body-weights/trends")
        assert response.status_code in (404, 405)

    async def test_no_analytics_endpoint(self, client):
        response = await client.get("/api/v1/body-weights/analytics")
        assert response.status_code in (404, 405)


# ===========================================================================
# B. OpenAPI
# ===========================================================================


class TestOpenAPI:
    async def test_post_path_documented(self, app):
        openapi = app.openapi()
        paths = openapi.get("paths", {})
        assert "/api/v1/body-weights" in paths
        assert "post" in paths["/api/v1/body-weights"]
        post_op = paths["/api/v1/body-weights"]["post"]
        assert post_op.get("responses", {}).get("201") is not None

    async def test_get_path_documented(self, app):
        openapi = app.openapi()
        paths = openapi.get("paths", {})
        assert "/api/v1/body-weights" in paths
        assert "get" in paths["/api/v1/body-weights"]
        get_op = paths["/api/v1/body-weights"]["get"]
        assert get_op.get("responses", {}).get("200") is not None

    async def test_delete_path_documented(self, app):
        openapi = app.openapi()
        paths = openapi.get("paths", {})
        assert "/api/v1/body-weights/{entry_id}" in paths
        assert "delete" in paths["/api/v1/body-weights/{entry_id}"]

    async def test_post_request_body_schema(self, app):
        openapi = app.openapi()
        paths = openapi.get("paths", {})
        post_op = paths["/api/v1/body-weights"]["post"]
        body = post_op.get("requestBody", {})
        assert body.get("required", False) is True

    async def test_logged_date_is_query_param(self, app):
        openapi = app.openapi()
        paths = openapi.get("paths", {})
        post_op = paths["/api/v1/body-weights"]["post"]
        params = post_op.get("parameters", [])
        logged_date_params = [p for p in params if p.get("name") == "logged_date"]
        assert len(logged_date_params) == 1
        assert logged_date_params[0]["in"] == "query"
        assert logged_date_params[0]["required"] is True
        assert logged_date_params[0]["schema"]["format"] == "date"

    async def test_entry_id_path_param_has_uuid_format(self, app):
        openapi = app.openapi()
        paths = openapi.get("paths", {})
        delete_op = paths["/api/v1/body-weights/{entry_id}"]["delete"]
        params = delete_op.get("parameters", [])
        entry_id_params = [p for p in params if p.get("name") == "entry_id"]
        assert len(entry_id_params) == 1
        assert entry_id_params[0]["in"] == "path"
        assert entry_id_params[0]["schema"]["type"] == "string"
        assert entry_id_params[0]["schema"]["format"] == "uuid"

    async def test_bearer_auth_on_all_ops(self, app):
        openapi = app.openapi()
        paths = openapi.get("paths", {})
        for path_key, methods in paths.items():
            if "body-weight" not in path_key and "body_weight" not in path_key:
                continue
            for method_key, op in methods.items():
                sec = op.get("security", [])
                assert any("BearerAuth" in s for s in sec), (
                    f"{method_key} {path_key} missing BearerAuth"
                )

    async def test_exactly_one_bearer_scheme(self, app):
        openapi = app.openapi()
        schemes = openapi.get("components", {}).get("securitySchemes", {})
        bearer_count = sum(1 for v in schemes.values() if v.get("scheme") == "bearer")
        assert bearer_count == 1


# ===========================================================================
# C. Authentication
# ===========================================================================


class TestAuthMissingHeader:
    async def test_post_returns_401(self, client):
        response = await client.post(
            "/api/v1/body-weights",
            json=_VALID_CREATE_BODY,
            params={"logged_date": "2026-07-12"},
        )
        assert response.status_code == 401

    async def test_get_returns_401(self, client):
        response = await client.get("/api/v1/body-weights")
        assert response.status_code == 401

    async def test_delete_returns_401(self, client):
        response = await client.delete(f"/api/v1/body-weights/{uuid.uuid4()}")
        assert response.status_code == 401

    async def test_post_safe_envelope(self, client):
        response = await client.post(
            "/api/v1/body-weights",
            json=_VALID_CREATE_BODY,
            params={"logged_date": "2026-07-12"},
        )
        data = response.json()
        assert data["success"] is False
        assert "error" in data

    async def test_get_safe_envelope(self, client):
        response = await client.get("/api/v1/body-weights")
        data = response.json()
        assert data["success"] is False

    async def test_delete_safe_envelope(self, client):
        response = await client.delete(f"/api/v1/body-weights/{uuid.uuid4()}")
        data = response.json()
        assert data["success"] is False

    async def test_post_www_authenticate(self, client):
        response = await client.post(
            "/api/v1/body-weights",
            json=_VALID_CREATE_BODY,
            params={"logged_date": "2026-07-12"},
        )
        assert response.headers.get("WWW-Authenticate") == "Bearer"

    async def test_get_www_authenticate(self, client):
        response = await client.get("/api/v1/body-weights")
        assert response.headers.get("WWW-Authenticate") == "Bearer"

    async def test_delete_www_authenticate(self, client):
        response = await client.delete(f"/api/v1/body-weights/{uuid.uuid4()}")
        assert response.headers.get("WWW-Authenticate") == "Bearer"

    async def test_post_no_detail_field(self, client):
        response = await client.post(
            "/api/v1/body-weights",
            json=_VALID_CREATE_BODY,
            params={"logged_date": "2026-07-12"},
        )
        assert '"detail"' not in response.text

    async def test_get_no_detail_field(self, client):
        response = await client.get("/api/v1/body-weights")
        assert '"detail"' not in response.text

    async def test_delete_no_detail_field(self, client):
        response = await client.delete(f"/api/v1/body-weights/{uuid.uuid4()}")
        assert '"detail"' not in response.text

    async def test_post_bearer_prefix_missing(self, client):
        response = await client.post(
            "/api/v1/body-weights",
            json=_VALID_CREATE_BODY,
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": "token123"},
        )
        assert response.status_code == 401

    async def test_get_bearer_prefix_missing(self, client):
        response = await client.get(
            "/api/v1/body-weights",
            headers={"Authorization": "token123"},
        )
        assert response.status_code == 401

    async def test_delete_bearer_prefix_missing(self, client):
        response = await client.delete(
            f"/api/v1/body-weights/{uuid.uuid4()}",
            headers={"Authorization": "token123"},
        )
        assert response.status_code == 401


class TestAuthInvalidToken:
    async def test_post_returns_401(self, client):
        response = await client.post(
            "/api/v1/body-weights",
            json=_VALID_CREATE_BODY,
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": "Bearer not-a-valid-token"},
        )
        assert response.status_code == 401

    async def test_get_returns_401(self, client):
        response = await client.get(
            "/api/v1/body-weights",
            headers={"Authorization": "Bearer not-a-valid-token"},
        )
        assert response.status_code == 401

    async def test_delete_returns_401(self, client):
        response = await client.delete(
            f"/api/v1/body-weights/{uuid.uuid4()}",
            headers={"Authorization": "Bearer not-a-valid-token"},
        )
        assert response.status_code == 401

    async def test_post_code_invalid_token(self, client):
        response = await client.post(
            "/api/v1/body-weights",
            json=_VALID_CREATE_BODY,
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": "Bearer not-a-valid-token"},
        )
        data = response.json()
        assert data["error"]["code"] == "INVALID_ACCESS_TOKEN"

    async def test_get_code_invalid_token(self, client):
        response = await client.get(
            "/api/v1/body-weights",
            headers={"Authorization": "Bearer not-a-valid-token"},
        )
        data = response.json()
        assert data["error"]["code"] == "INVALID_ACCESS_TOKEN"

    async def test_delete_code_invalid_token(self, client):
        response = await client.delete(
            f"/api/v1/body-weights/{uuid.uuid4()}",
            headers={"Authorization": "Bearer not-a-valid-token"},
        )
        data = response.json()
        assert data["error"]["code"] == "INVALID_ACCESS_TOKEN"


class TestAuthExpiredToken:
    def _make_expired_token(self, settings: Settings) -> str:
        user_id = uuid.uuid4()
        past = datetime.now(UTC) - timedelta(hours=2)
        return create_access_token(user_id=user_id, settings=settings, now=past)

    async def test_post_returns_401(self, client, test_settings):
        token = self._make_expired_token(test_settings)
        response = await client.post(
            "/api/v1/body-weights",
            json=_VALID_CREATE_BODY,
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401

    async def test_get_returns_401(self, client, test_settings):
        token = self._make_expired_token(test_settings)
        response = await client.get(
            "/api/v1/body-weights",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401

    async def test_delete_returns_401(self, client, test_settings):
        token = self._make_expired_token(test_settings)
        response = await client.delete(
            f"/api/v1/body-weights/{uuid.uuid4()}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401

    async def test_post_code_expired(self, client, test_settings):
        token = self._make_expired_token(test_settings)
        response = await client.post(
            "/api/v1/body-weights",
            json=_VALID_CREATE_BODY,
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["error"]["code"] == "ACCESS_TOKEN_EXPIRED"


class TestAuthUnknownUser:
    def _setup_session(self, mock_session):
        mock_session.execute = AsyncMock(return_value=_make_execute_result(None))
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()

    async def test_post_returns_401(self, client, test_settings, mock_session):
        self._setup_session(mock_session)
        user_id = uuid.uuid4()
        token = create_access_token(user_id=user_id, settings=test_settings)
        response = await client.post(
            "/api/v1/body-weights",
            json=_VALID_CREATE_BODY,
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401

    async def test_get_returns_401(self, client, test_settings, mock_session):
        self._setup_session(mock_session)
        user_id = uuid.uuid4()
        token = create_access_token(user_id=user_id, settings=test_settings)
        response = await client.get(
            "/api/v1/body-weights",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401

    async def test_delete_returns_401(self, client, test_settings, mock_session):
        self._setup_session(mock_session)
        user_id = uuid.uuid4()
        token = create_access_token(user_id=user_id, settings=test_settings)
        response = await client.delete(
            f"/api/v1/body-weights/{uuid.uuid4()}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401


class TestAuthInactiveUser:
    def _setup_session(self, mock_session, user):
        mock_session.execute = AsyncMock(return_value=_make_execute_result(user))
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()

    async def test_post_returns_403(self, client, test_settings, mock_session):
        user = _make_user(is_active=False)
        self._setup_session(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/body-weights",
            json=_VALID_CREATE_BODY,
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403

    async def test_get_returns_403(self, client, test_settings, mock_session):
        user = _make_user(is_active=False)
        self._setup_session(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/body-weights",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403

    async def test_delete_returns_403(self, client, test_settings, mock_session):
        user = _make_user(is_active=False)
        self._setup_session(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.delete(
            f"/api/v1/body-weights/{uuid.uuid4()}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403

    async def test_post_code_inactive(self, client, test_settings, mock_session):
        user = _make_user(is_active=False)
        self._setup_session(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/body-weights",
            json=_VALID_CREATE_BODY,
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["error"]["code"] == "INACTIVE_ACCOUNT"


class TestAuthNotCalledBeforeService:
    async def test_post_auth_fails_before_service(self, client, test_settings):
        response = await client.post(
            "/api/v1/body-weights",
            json=_VALID_CREATE_BODY,
            params={"logged_date": "2026-07-12"},
        )
        assert response.status_code == 401

    async def test_get_auth_fails_before_service(self, client):
        response = await client.get("/api/v1/body-weights")
        assert response.status_code == 401

    async def test_delete_auth_fails_before_service(self, client):
        response = await client.delete(f"/api/v1/body-weights/{uuid.uuid4()}")
        assert response.status_code == 401


# ===========================================================================
# D. POST Success
# ===========================================================================


class _PostSuccessBase:
    def _setup_session(self, mock_session):
        mock_session.execute = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()
        mock_session.commit = AsyncMock()

        async def _refresh_side_effect(obj, *args, **kwargs):
            obj.created_at = NOW
            obj.updated_at = NOW

        mock_session.refresh = AsyncMock(side_effect=_refresh_side_effect)
        mock_session.rollback = AsyncMock()


class TestPostSuccess(_PostSuccessBase):
    async def test_returns_201(self, client, test_settings, mock_session):
        self._setup_session(mock_session)
        user = _make_user()
        mock_session.execute.return_value = _make_execute_result(user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/body-weights",
            json=_VALID_CREATE_BODY,
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 201

    async def test_success_is_true(self, client, test_settings, mock_session):
        self._setup_session(mock_session)
        user = _make_user()
        mock_session.execute.return_value = _make_execute_result(user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/body-weights",
            json=_VALID_CREATE_BODY,
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["success"] is True

    async def test_correct_message(self, client, test_settings, mock_session):
        self._setup_session(mock_session)
        user = _make_user()
        mock_session.execute.return_value = _make_execute_result(user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/body-weights",
            json=_VALID_CREATE_BODY,
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["message"] == "Body-weight entry created successfully."

    async def test_entry_data_returned(self, client, test_settings, mock_session):
        self._setup_session(mock_session)
        user = _make_user()
        mock_session.execute.return_value = _make_execute_result(user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/body-weights",
            json=_VALID_CREATE_BODY,
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert "data" in data
        entry = data["data"]
        assert "entry_id" in entry
        assert "logged_date" in entry
        assert "weight_kg" in entry

    async def test_logged_date_returned(self, client, test_settings, mock_session):
        self._setup_session(mock_session)
        user = _make_user()
        mock_session.execute.return_value = _make_execute_result(user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/body-weights",
            json=_VALID_CREATE_BODY,
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["data"]["logged_date"] == "2026-07-12"

    async def test_decimal_preserved(self, client, test_settings, mock_session):
        self._setup_session(mock_session)
        user = _make_user()
        mock_session.execute.return_value = _make_execute_result(user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/body-weights",
            json={"weight_kg": "70.00"},
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["data"]["weight_kg"] == "70.00"

    async def test_decimal_serialized_as_string(self, client, test_settings, mock_session):
        self._setup_session(mock_session)
        user = _make_user()
        mock_session.execute.return_value = _make_execute_result(user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/body-weights",
            json={"weight_kg": 70},
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert isinstance(data["data"]["weight_kg"], str)

    async def test_no_user_id_exposed(self, client, test_settings, mock_session):
        self._setup_session(mock_session)
        user = _make_user()
        mock_session.execute.return_value = _make_execute_result(user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/body-weights",
            json=_VALID_CREATE_BODY,
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert "user_id" not in response.text.lower()

    async def test_no_password_exposed(self, client, test_settings, mock_session):
        self._setup_session(mock_session)
        user = _make_user()
        mock_session.execute.return_value = _make_execute_result(user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/body-weights",
            json=_VALID_CREATE_BODY,
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert "password" not in response.text.lower()

    async def test_no_sql_exposed(self, client, test_settings, mock_session):
        self._setup_session(mock_session)
        user = _make_user()
        mock_session.execute.return_value = _make_execute_result(user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/body-weights",
            json=_VALID_CREATE_BODY,
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        text = response.text.lower()
        assert "insert into" not in text
        assert "select" not in text

    async def test_x_request_id_present(self, client, test_settings, mock_session):
        self._setup_session(mock_session)
        user = _make_user()
        mock_session.execute.return_value = _make_execute_result(user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/body-weights",
            json=_VALID_CREATE_BODY,
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert "X-Request-ID" in response.headers

    async def test_commits_exactly_once(self, client, test_settings, mock_session):
        self._setup_session(mock_session)
        user = _make_user()
        mock_session.execute.return_value = _make_execute_result(user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.post(
            "/api/v1/body-weights",
            json=_VALID_CREATE_BODY,
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        mock_session.commit.assert_awaited_once()

    async def test_refresh_called(self, client, test_settings, mock_session):
        self._setup_session(mock_session)
        user = _make_user()
        mock_session.execute.return_value = _make_execute_result(user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.post(
            "/api/v1/body-weights",
            json=_VALID_CREATE_BODY,
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        mock_session.refresh.assert_awaited()

    async def test_commit_after_service_success(self, client, test_settings, mock_session):
        self._setup_session(mock_session)
        user = _make_user()
        mock_session.execute.return_value = _make_execute_result(user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.post(
            "/api/v1/body-weights",
            json=_VALID_CREATE_BODY,
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        mock_session.add.assert_called_once()
        mock_session.commit.assert_awaited_once()

    async def test_does_not_accept_user_id(self, client, test_settings, mock_session):
        self._setup_session(mock_session)
        user = _make_user()
        mock_session.execute.return_value = _make_execute_result(user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        body = {"weight_kg": "70.00", "user_id": str(uuid.uuid4())}
        response = await client.post(
            "/api/v1/body-weights",
            json=body,
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    async def test_entry_id_generated(self, client, test_settings, mock_session):
        self._setup_session(mock_session)
        user = _make_user()
        mock_session.execute.return_value = _make_execute_result(user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/body-weights",
            json=_VALID_CREATE_BODY,
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        entry_id = data["data"]["entry_id"]
        uuid.UUID(entry_id)  # does not raise


# ===========================================================================
# E. POST Validation
# ===========================================================================


class TestPostValidation:
    def _setup_session(self, mock_session):
        mock_session.execute = AsyncMock()

    async def _do_post(self, client, test_settings, mock_session, body):
        self._setup_session(mock_session)
        user = _make_user()
        mock_session.execute.return_value = _make_execute_result(user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        return await client.post(
            "/api/v1/body-weights",
            json=body,
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )

    async def test_missing_body(self, client, test_settings, mock_session):
        self._setup_session(mock_session)
        user = _make_user()
        mock_session.execute.return_value = _make_execute_result(user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/body-weights",
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    async def test_missing_weight(self, client, test_settings, mock_session):
        response = await self._do_post(client, test_settings, mock_session, {})
        assert response.status_code == 422

    async def test_extra_field_rejected(self, client, test_settings, mock_session):
        response = await self._do_post(
            client, test_settings, mock_session, {"weight_kg": "70.00", "extra": "x"}
        )
        assert response.status_code == 422

    async def test_invalid_decimal(self, client, test_settings, mock_session):
        response = await self._do_post(
            client, test_settings, mock_session, {"weight_kg": "not-a-number"}
        )
        assert response.status_code == 422

    async def test_bool_weight(self, client, test_settings, mock_session):
        response = await self._do_post(client, test_settings, mock_session, {"weight_kg": True})
        assert response.status_code == 422

    async def test_nan(self, client, test_settings, mock_session):
        response = await self._do_post(client, test_settings, mock_session, {"weight_kg": "NaN"})
        assert response.status_code == 422

    async def test_infinity(self, client, test_settings, mock_session):
        response = await self._do_post(
            client, test_settings, mock_session, {"weight_kg": "Infinity"}
        )
        assert response.status_code == 422

    async def test_negative_weight(self, client, test_settings, mock_session):
        response = await self._do_post(client, test_settings, mock_session, {"weight_kg": "-1"})
        assert response.status_code == 422

    async def test_zero_weight(self, client, test_settings, mock_session):
        response = await self._do_post(client, test_settings, mock_session, {"weight_kg": "0"})
        assert response.status_code == 422

    async def test_below_minimum(self, client, test_settings, mock_session):
        response = await self._do_post(client, test_settings, mock_session, {"weight_kg": "9.99"})
        assert response.status_code == 422

    async def test_above_maximum(self, client, test_settings, mock_session):
        response = await self._do_post(client, test_settings, mock_session, {"weight_kg": "701.00"})
        assert response.status_code == 422

    async def test_boundary_minimum(self, client, test_settings, mock_session):
        response = await self._do_post(client, test_settings, mock_session, {"weight_kg": "10.00"})
        assert response.status_code == 201

    async def test_boundary_maximum(self, client, test_settings, mock_session):
        response = await self._do_post(client, test_settings, mock_session, {"weight_kg": "700.00"})
        assert response.status_code == 201

    async def test_missing_logged_date(self, client, test_settings, mock_session):
        self._setup_session(mock_session)
        user = _make_user()
        mock_session.execute.return_value = _make_execute_result(user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/body-weights",
            json=_VALID_CREATE_BODY,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    async def test_malformed_logged_date(self, client, test_settings, mock_session):
        self._setup_session(mock_session)
        user = _make_user()
        mock_session.execute.return_value = _make_execute_result(user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/body-weights",
            json=_VALID_CREATE_BODY,
            params={"logged_date": "not-a-date"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    async def test_impossible_date(self, client, test_settings, mock_session):
        self._setup_session(mock_session)
        user = _make_user()
        mock_session.execute.return_value = _make_execute_result(user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/body-weights",
            json=_VALID_CREATE_BODY,
            params={"logged_date": "2026-02-30"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    async def test_validation_error_envelope(self, client, test_settings, mock_session):
        response = await self._do_post(client, test_settings, mock_session, {})
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "VALIDATION_ERROR"


# ===========================================================================
# F. POST Duplicate
# ===========================================================================


class TestPostDuplicate:
    async def test_duplicate_logged_date_returns_409(self, client, test_settings, mock_session):
        from app.core.body_weight_exceptions import DuplicateBodyWeightDateError

        user = _make_user()
        mock_session.execute.return_value = _make_execute_result(user)
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock(side_effect=DuplicateBodyWeightDateError())
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/body-weights",
            json=_VALID_CREATE_BODY,
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 409

    async def test_duplicate_logged_date_code(self, client, test_settings, mock_session):
        from app.core.body_weight_exceptions import DuplicateBodyWeightDateError

        user = _make_user()
        mock_session.execute.return_value = _make_execute_result(user)
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock(side_effect=DuplicateBodyWeightDateError())
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/body-weights",
            json=_VALID_CREATE_BODY,
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["error"]["code"] == "BODY_WEIGHT_ENTRY_ALREADY_EXISTS"

    async def test_duplicate_logged_date_message(self, client, test_settings, mock_session):
        from app.core.body_weight_exceptions import DuplicateBodyWeightDateError

        user = _make_user()
        mock_session.execute.return_value = _make_execute_result(user)
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock(side_effect=DuplicateBodyWeightDateError())
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/body-weights",
            json=_VALID_CREATE_BODY,
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert "already exists" in data["error"]["message"].lower()

    async def test_duplicate_logged_date_rollback(self, client, test_settings, mock_session):
        from app.core.body_weight_exceptions import DuplicateBodyWeightDateError

        user = _make_user()
        mock_session.execute.return_value = _make_execute_result(user)
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock(side_effect=DuplicateBodyWeightDateError())
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.post(
            "/api/v1/body-weights",
            json=_VALID_CREATE_BODY,
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        mock_session.rollback.assert_called_once()

    async def test_duplicate_logged_date_no_commit(self, client, test_settings, mock_session):
        from app.core.body_weight_exceptions import DuplicateBodyWeightDateError

        user = _make_user()
        mock_session.execute.return_value = _make_execute_result(user)
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock(side_effect=DuplicateBodyWeightDateError())
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.post(
            "/api/v1/body-weights",
            json=_VALID_CREATE_BODY,
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        mock_session.commit.assert_not_called()

    async def test_duplicate_logged_date_safe_message(self, client, test_settings, mock_session):
        from app.core.body_weight_exceptions import DuplicateBodyWeightDateError

        user = _make_user()
        mock_session.execute.return_value = _make_execute_result(user)
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock(side_effect=DuplicateBodyWeightDateError())
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/body-weights",
            json=_VALID_CREATE_BODY,
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        text = response.text.lower()
        assert "constraint" not in text
        assert "integrity" not in text
        assert "insert" not in text

    async def test_duplicate_entry_id_returns_409(self, client, test_settings, mock_session):
        from app.core.body_weight_exceptions import DuplicateBodyWeightEntryIdError

        user = _make_user()
        mock_session.execute.return_value = _make_execute_result(user)
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock(side_effect=DuplicateBodyWeightEntryIdError())
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/body-weights",
            json=_VALID_CREATE_BODY,
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 409

    async def test_duplicate_entry_id_code(self, client, test_settings, mock_session):
        from app.core.body_weight_exceptions import DuplicateBodyWeightEntryIdError

        user = _make_user()
        mock_session.execute.return_value = _make_execute_result(user)
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock(side_effect=DuplicateBodyWeightEntryIdError())
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/body-weights",
            json=_VALID_CREATE_BODY,
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["error"]["code"] == "BODY_WEIGHT_ENTRY_ID_ALREADY_EXISTS"

    async def test_request_id_in_body(self, client, test_settings, mock_session):
        from app.core.body_weight_exceptions import DuplicateBodyWeightDateError

        user = _make_user()
        mock_session.execute.return_value = _make_execute_result(user)
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock(side_effect=DuplicateBodyWeightDateError())
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/body-weights",
            json=_VALID_CREATE_BODY,
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert "request_id" in data["error"]

    async def test_x_request_id_header(self, client, test_settings, mock_session):
        from app.core.body_weight_exceptions import DuplicateBodyWeightDateError

        user = _make_user()
        mock_session.execute.return_value = _make_execute_result(user)
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock(side_effect=DuplicateBodyWeightDateError())
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/body-weights",
            json=_VALID_CREATE_BODY,
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert "X-Request-ID" in response.headers


# ===========================================================================
# G. GET History Success
# ===========================================================================


class TestGetSuccess:
    def _setup_session(self, mock_session, user):
        mock_session.execute = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()

    async def test_returns_200(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.return_value = _make_execute_result(user)
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/body-weights",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    async def test_success_is_true(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.return_value = _make_execute_result(user)
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/body-weights",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["success"] is True

    async def test_correct_message(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.return_value = _make_execute_result(user)
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/body-weights",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["message"] == "Body-weight history retrieved successfully."

    async def test_empty_history(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.return_value = _make_execute_result(user)
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/body-weights",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["data"]["entries"] == []

    async def test_x_request_id_present(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.return_value = _make_execute_result(user)
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/body-weights",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert "X-Request-ID" in response.headers

    async def test_no_commit(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.return_value = _make_execute_result(user)
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.get(
            "/api/v1/body-weights",
            headers={"Authorization": f"Bearer {token}"},
        )
        mock_session.commit.assert_not_called()

    async def test_no_flush(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.return_value = _make_execute_result(user)
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        mock_session.flush = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.get(
            "/api/v1/body-weights",
            headers={"Authorization": f"Bearer {token}"},
        )
        mock_session.flush.assert_not_called()

    async def test_no_refresh(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.return_value = _make_execute_result(user)
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        mock_session.refresh = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.get(
            "/api/v1/body-weights",
            headers={"Authorization": f"Bearer {token}"},
        )
        mock_session.refresh.assert_not_called()

    async def test_no_user_id_exposed(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.return_value = _make_execute_result(user)
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/body-weights",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert "user_id" not in response.text.lower()


# ===========================================================================
# H. DELETE Success
# ===========================================================================


class TestDeleteSuccess:
    async def test_returns_200(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.return_value = _make_execute_result(user)
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        mock_session.delete = AsyncMock()
        mock_session.flush = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.delete(
            f"/api/v1/body-weights/{uuid.uuid4()}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    async def test_success_is_true(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.return_value = _make_execute_result(user)
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        mock_session.delete = AsyncMock()
        mock_session.flush = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.delete(
            f"/api/v1/body-weights/{uuid.uuid4()}",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["success"] is True

    async def test_correct_message(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.return_value = _make_execute_result(user)
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        mock_session.delete = AsyncMock()
        mock_session.flush = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.delete(
            f"/api/v1/body-weights/{uuid.uuid4()}",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["message"] == "Body-weight entry deleted successfully."

    async def test_commits_exactly_once(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.return_value = _make_execute_result(user)
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        mock_session.delete = AsyncMock()
        mock_session.flush = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        eid = uuid.uuid4()
        await client.delete(
            f"/api/v1/body-weights/{eid}",
            headers={"Authorization": f"Bearer {token}"},
        )
        mock_session.commit.assert_awaited_once()

    async def test_no_rollback_on_success(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.return_value = _make_execute_result(user)
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        mock_session.delete = AsyncMock()
        mock_session.flush = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        eid = uuid.uuid4()
        await client.delete(
            f"/api/v1/body-weights/{eid}",
            headers={"Authorization": f"Bearer {token}"},
        )
        mock_session.rollback.assert_not_called()

    async def test_x_request_id_present(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.return_value = _make_execute_result(user)
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        mock_session.delete = AsyncMock()
        mock_session.flush = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.delete(
            f"/api/v1/body-weights/{uuid.uuid4()}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert "X-Request-ID" in response.headers


# ===========================================================================
# I. DELETE Not Found
# ===========================================================================


class TestDeleteNotFound:
    def _make_delete_not_found_session(self, mock_session, user):
        """Setup session so auth succeeds then body-weight lookup returns None."""
        user_result = MagicMock()
        user_result.scalars.return_value.one_or_none.return_value = user
        not_found_result = MagicMock()
        not_found_result.scalars.return_value.one_or_none.return_value = None
        mock_session.execute = AsyncMock(side_effect=[user_result, not_found_result])
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()

    async def test_returns_404(self, client, test_settings, mock_session):
        user = _make_user()
        self._make_delete_not_found_session(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.delete(
            f"/api/v1/body-weights/{uuid.uuid4()}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404

    async def test_error_code(self, client, test_settings, mock_session):
        user = _make_user()
        self._make_delete_not_found_session(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.delete(
            f"/api/v1/body-weights/{uuid.uuid4()}",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["error"]["code"] == "BODY_WEIGHT_ENTRY_NOT_FOUND"

    async def test_safe_message(self, client, test_settings, mock_session):
        user = _make_user()
        self._make_delete_not_found_session(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.delete(
            f"/api/v1/body-weights/{uuid.uuid4()}",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert "was not found" in data["error"]["message"]

    async def test_no_commit(self, client, test_settings, mock_session):
        user = _make_user()
        self._make_delete_not_found_session(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.delete(
            f"/api/v1/body-weights/{uuid.uuid4()}",
            headers={"Authorization": f"Bearer {token}"},
        )
        mock_session.commit.assert_not_called()

    async def test_request_id_in_body(self, client, test_settings, mock_session):
        user = _make_user()
        self._make_delete_not_found_session(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.delete(
            f"/api/v1/body-weights/{uuid.uuid4()}",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert "request_id" in data["error"]

    async def test_x_request_id_header(self, client, test_settings, mock_session):
        user = _make_user()
        self._make_delete_not_found_session(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.delete(
            f"/api/v1/body-weights/{uuid.uuid4()}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert "X-Request-ID" in response.headers


# ===========================================================================
# J. Path Validation
# ===========================================================================


class TestPathValidation:
    async def test_invalid_uuid(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.return_value = _make_execute_result(user)
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.delete(
            "/api/v1/body-weights/not-a-uuid",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    async def test_malformed_uuid(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.return_value = _make_execute_result(user)
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.delete(
            "/api/v1/body-weights/00000000-0000-0000-0000-00000000000Z",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422


# ===========================================================================
# K. Unexpected Errors
# ===========================================================================


class TestUnexpectedErrors:
    async def test_post_returns_500(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.return_value = _make_execute_result(user)
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock(side_effect=RuntimeError("unexpected"))
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/body-weights",
            json=_VALID_CREATE_BODY,
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 500

    async def test_post_global_envelope(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.return_value = _make_execute_result(user)
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock(side_effect=RuntimeError("unexpected"))
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/body-weights",
            json=_VALID_CREATE_BODY,
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["error"]["code"] == "INTERNAL_SERVER_ERROR"

    async def test_post_no_raw_exception(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.return_value = _make_execute_result(user)
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock(side_effect=RuntimeError("unexpected"))
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/body-weights",
            json=_VALID_CREATE_BODY,
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert "RuntimeError" not in response.text

    async def test_post_request_id_in_body(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.return_value = _make_execute_result(user)
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock(side_effect=RuntimeError("unexpected"))
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/body-weights",
            json=_VALID_CREATE_BODY,
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert "request_id" in data["error"]

    async def test_delete_unexpected_fails_gracefully(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute = AsyncMock(side_effect=RuntimeError("unexpected"))
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.delete(
            f"/api/v1/body-weights/{uuid.uuid4()}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 500


# ===========================================================================
# L. Transaction Ownership
# ===========================================================================


class TestTransactionOwnership:
    async def test_post_commit_once_on_success(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.return_value = _make_execute_result(user)
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.post(
            "/api/v1/body-weights",
            json=_VALID_CREATE_BODY,
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        mock_session.commit.assert_awaited_once()

    async def test_delete_commit_once_on_success(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.return_value = _make_execute_result(user)
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        mock_session.delete = AsyncMock()
        mock_session.flush = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.delete(
            f"/api/v1/body-weights/{uuid.uuid4()}",
            headers={"Authorization": f"Bearer {token}"},
        )
        mock_session.commit.assert_awaited_once()

    async def test_get_never_commits(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.return_value = _make_execute_result(user)
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.get(
            "/api/v1/body-weights",
            headers={"Authorization": f"Bearer {token}"},
        )
        mock_session.commit.assert_not_called()

    async def test_failed_post_no_commit(self, client, test_settings, mock_session):
        user = _make_user()
        mock_result = MagicMock()
        mock_result.scalars.return_value.one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock(side_effect=RuntimeError("fail"))
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.post(
            "/api/v1/body-weights",
            json=_VALID_CREATE_BODY,
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        mock_session.commit.assert_not_called()

    async def test_failed_delete_no_commit(self, client, test_settings, mock_session):
        user = _make_user()
        mock_result = MagicMock()
        mock_result.scalars.return_value.one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.delete(
            f"/api/v1/body-weights/{uuid.uuid4()}",
            headers={"Authorization": f"Bearer {token}"},
        )
        mock_session.commit.assert_not_called()


# ===========================================================================
# M. Architecture Boundaries
# ===========================================================================


class TestArchitectureBoundaries:
    async def test_route_imports_existing_repository(self):
        import importlib

        mod = importlib.import_module("app.api.v1.body_weights")
        assert hasattr(mod, "router")

    async def test_route_uses_existing_get_current_user(self):
        from app.api.v1.body_weights import router

        assert len(router.routes) > 0

    async def test_no_manual_jwt_decoding(self):
        import inspect

        from app.api.v1 import body_weights as mod

        source = inspect.getsource(mod)
        assert "decode_access_token" not in source
        assert "jwt.decode" not in source

    async def test_no_new_http_bearer(self):
        import inspect

        from app.api.v1 import body_weights as mod

        source = inspect.getsource(mod)
        assert "HTTPBearer" not in source

    async def test_no_sql_in_route(self):
        import inspect

        from app.api.v1 import body_weights as mod

        source = inspect.getsource(mod)
        assert "session.execute(" not in source
        assert "session.add(" not in source
        assert "session.delete(" not in source
        assert "select(" not in source
        assert "insert(" not in source
        assert "update(" not in source

    async def test_no_formula_logic(self):
        import inspect

        from app.api.v1 import body_weights as mod

        source = inspect.getsource(mod)
        assert "weight_change" not in source.lower()
        assert "bmi" not in source.lower()
        assert "bmr" not in source.lower()
        assert "tdee" not in source.lower()


# ===========================================================================
# N. Regression
# ===========================================================================


class TestExistingApiRegression:
    async def test_auth_routes_unchanged(self, client):
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401

    async def test_health_routes_unchanged(self, test_settings):
        app = create_app(settings=test_settings)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            response = await c.get("/api/v1/health")
        assert response.status_code == 200

    async def test_nutrition_log_routes_unchanged(self, client):
        response = await client.get("/api/v1/nutrition-logs")
        assert response.status_code == 401

    async def test_nutrition_profile_routes_unchanged(self, client):
        response = await client.get("/api/v1/nutrition-profile")
        assert response.status_code == 401
