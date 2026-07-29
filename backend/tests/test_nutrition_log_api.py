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
from app.models.nutrition_log import NutritionLog
from app.models.user import User

NOW = datetime.now(UTC)
TEST_LOGGED_DATE = date(2026, 7, 12)
TEST_ENTRY_ID = uuid.uuid4()

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


def _make_nutrition_log(
    user_id: uuid.UUID | None = None,
    entry_id: uuid.UUID | None = None,
    logged_date: date = TEST_LOGGED_DATE,
) -> MagicMock:
    entry = MagicMock(spec=NutritionLog)
    entry.id = uuid.uuid4()
    entry.user_id = user_id or uuid.uuid4()
    entry.logged_date = logged_date
    entry.entry_id = entry_id or uuid.uuid4()
    entry.food_name = "Oatmeal"
    entry.meal_type = "breakfast"
    entry.serving_description = "1 bowl"
    entry.calories_kcal = Decimal("300.00")
    entry.protein_g = Decimal("10.00")
    entry.carbohydrate_g = Decimal("50.00")
    entry.fat_g = Decimal("5.00")
    entry.created_at = NOW
    entry.updated_at = NOW
    return entry


def _make_execute_result(value: MagicMock | None) -> MagicMock:
    result = MagicMock()
    result.scalars.return_value.one_or_none.return_value = value
    return result


_VALID_CREATE_BODY = {
    "entry_id": str(uuid.uuid4()),
    "food_name": "Oatmeal",
    "meal_type": "breakfast",
    "serving_description": "1 bowl",
    "calories_kcal": "300.00",
    "protein_g": "10.00",
    "carbohydrate_g": "50.00",
    "fat_g": "5.00",
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
        paths = [r.path for r in app.routes if "nutrition-logs" in r.path]
        assert len(paths) > 0

    async def test_correct_prefix(self, app):
        paths = [r.path for r in app.routes if "nutrition-logs" in r.path]
        for p in paths:
            assert p.startswith("/api/v1/nutrition-logs")

    async def test_post_path_exists(self, client):
        response = await client.post("/api/v1/nutrition-logs", json={})
        assert response.status_code != 404

    async def test_get_path_exists(self, client):
        response = await client.get("/api/v1/nutrition-logs")
        assert response.status_code != 404

    async def test_delete_path_exists(self, client):
        eid = uuid.uuid4()
        response = await client.delete(f"/api/v1/nutrition-logs/{eid}")
        assert response.status_code != 404

    async def test_no_duplicate_nutrition_log_paths(self, app):
        nutrition_routes = {r.path for r in app.routes if "nutrition-logs" in r.path}
        # POST and GET share /api/v1/nutrition-logs; GET /summary and GET /progress
        # are static; DELETE uses /{entry_id}
        assert len(nutrition_routes) == 4
        assert "/api/v1/nutrition-logs" in nutrition_routes
        assert "/api/v1/nutrition-logs/summary" in nutrition_routes
        assert "/api/v1/nutrition-logs/progress" in nutrition_routes
        assert "/api/v1/nutrition-logs/{entry_id}" in nutrition_routes

    async def test_no_singular_path(self, app):
        paths = [
            r.path
            for r in app.routes
            if "nutrition-log" in r.path and "nutrition-logs" not in r.path
        ]
        assert len(paths) == 0

    async def test_no_create_subpath(self, app):
        paths = [r.path for r in app.routes if "/nutrition-logs/create" in r.path]
        assert len(paths) == 0

    async def test_no_list_subpath(self, app):
        paths = [r.path for r in app.routes if "/nutrition-logs/list" in r.path]
        assert len(paths) == 0

    async def test_no_delete_subpath(self, app):
        paths = [r.path for r in app.routes if "/nutrition-logs/delete" in r.path]
        assert len(paths) == 0

    async def test_no_user_id_path(self, app):
        paths = [r.path for r in app.routes if "users/" in r.path and "nutrition-logs" in r.path]
        assert len(paths) == 0

    async def test_no_put_endpoint(self, client):
        response = await client.put("/api/v1/nutrition-logs")
        assert response.status_code == 405

    async def test_no_patch_endpoint(self, client):
        response = await client.patch("/api/v1/nutrition-logs")
        assert response.status_code == 405

    async def test_no_extra_post_endpoint(self, app):
        post_paths = [
            r.path
            for r in app.routes
            if "nutrition-logs" in r.path and hasattr(r, "methods") and "POST" in r.methods
        ]
        assert len(post_paths) == 1

    async def test_no_aggregation_endpoint(self, app):
        paths = [
            r.path
            for r in app.routes
            if "nutrition-logs" in r.path and "aggregat" in r.path.lower()
        ]
        assert len(paths) == 0

    async def test_daily_summary_endpoint_exists(self, app):
        paths = [
            r.path for r in app.routes if "nutrition-logs" in r.path and "summary" in r.path.lower()
        ]
        assert len(paths) == 1
        assert "/api/v1/nutrition-logs/summary" in paths

    async def test_registered_exactly_once(self, app):
        paths = [r.path for r in app.routes if "nutrition-logs" in r.path]
        expected = {
            "/api/v1/nutrition-logs",
            "/api/v1/nutrition-logs/summary",
            "/api/v1/nutrition-logs/progress",
            "/api/v1/nutrition-logs/{entry_id}",
        }
        found = set(paths)
        assert found == expected


# ===========================================================================
# B. Authentication
# ===========================================================================


class TestAuthMissingHeader:
    async def test_post_returns_401(self, client):
        response = await client.post(
            "/api/v1/nutrition-logs",
            json=_VALID_CREATE_BODY,
            params={"logged_date": "2026-07-12"},
        )
        assert response.status_code == 401

    async def test_get_returns_401(self, client):
        response = await client.get("/api/v1/nutrition-logs", params={"logged_date": "2026-07-12"})
        assert response.status_code == 401

    async def test_delete_returns_401(self, client):
        response = await client.delete(f"/api/v1/nutrition-logs/{uuid.uuid4()}")
        assert response.status_code == 401

    async def test_post_safe_envelope(self, client):
        response = await client.post(
            "/api/v1/nutrition-logs",
            json=_VALID_CREATE_BODY,
            params={"logged_date": "2026-07-12"},
        )
        data = response.json()
        assert data["success"] is False
        assert "error" in data

    async def test_get_safe_envelope(self, client):
        response = await client.get("/api/v1/nutrition-logs", params={"logged_date": "2026-07-12"})
        data = response.json()
        assert data["success"] is False

    async def test_delete_safe_envelope(self, client):
        response = await client.delete(f"/api/v1/nutrition-logs/{uuid.uuid4()}")
        data = response.json()
        assert data["success"] is False

    async def test_post_www_authenticate(self, client):
        response = await client.post(
            "/api/v1/nutrition-logs",
            json=_VALID_CREATE_BODY,
            params={"logged_date": "2026-07-12"},
        )
        assert response.headers.get("WWW-Authenticate") == "Bearer"

    async def test_get_www_authenticate(self, client):
        response = await client.get("/api/v1/nutrition-logs", params={"logged_date": "2026-07-12"})
        assert response.headers.get("WWW-Authenticate") == "Bearer"

    async def test_delete_www_authenticate(self, client):
        response = await client.delete(f"/api/v1/nutrition-logs/{uuid.uuid4()}")
        assert response.headers.get("WWW-Authenticate") == "Bearer"

    async def test_post_no_detail_field(self, client):
        response = await client.post(
            "/api/v1/nutrition-logs",
            json=_VALID_CREATE_BODY,
            params={"logged_date": "2026-07-12"},
        )
        assert '"detail"' not in response.text

    async def test_get_no_detail_field(self, client):
        response = await client.get("/api/v1/nutrition-logs", params={"logged_date": "2026-07-12"})
        assert '"detail"' not in response.text

    async def test_delete_no_detail_field(self, client):
        response = await client.delete(f"/api/v1/nutrition-logs/{uuid.uuid4()}")
        assert '"detail"' not in response.text

    async def test_post_bearer_prefix_missing(self, client):
        response = await client.post(
            "/api/v1/nutrition-logs",
            json=_VALID_CREATE_BODY,
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": "token123"},
        )
        assert response.status_code == 401

    async def test_get_bearer_prefix_missing(self, client):
        response = await client.get(
            "/api/v1/nutrition-logs",
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": "token123"},
        )
        assert response.status_code == 401

    async def test_delete_bearer_prefix_missing(self, client):
        response = await client.delete(
            f"/api/v1/nutrition-logs/{uuid.uuid4()}",
            headers={"Authorization": "token123"},
        )
        assert response.status_code == 401


class TestAuthInvalidToken:
    async def test_post_returns_401(self, client):
        response = await client.post(
            "/api/v1/nutrition-logs",
            json=_VALID_CREATE_BODY,
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": "Bearer not-a-valid-token"},
        )
        assert response.status_code == 401

    async def test_get_returns_401(self, client):
        response = await client.get(
            "/api/v1/nutrition-logs",
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": "Bearer not-a-valid-token"},
        )
        assert response.status_code == 401

    async def test_delete_returns_401(self, client):
        response = await client.delete(
            f"/api/v1/nutrition-logs/{uuid.uuid4()}",
            headers={"Authorization": "Bearer not-a-valid-token"},
        )
        assert response.status_code == 401

    async def test_post_code_invalid_token(self, client):
        response = await client.post(
            "/api/v1/nutrition-logs",
            json=_VALID_CREATE_BODY,
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": "Bearer not-a-valid-token"},
        )
        data = response.json()
        assert data["error"]["code"] == "INVALID_ACCESS_TOKEN"

    async def test_get_code_invalid_token(self, client):
        response = await client.get(
            "/api/v1/nutrition-logs",
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": "Bearer not-a-valid-token"},
        )
        data = response.json()
        assert data["error"]["code"] == "INVALID_ACCESS_TOKEN"

    async def test_delete_code_invalid_token(self, client):
        response = await client.delete(
            f"/api/v1/nutrition-logs/{uuid.uuid4()}",
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
            "/api/v1/nutrition-logs",
            json=_VALID_CREATE_BODY,
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401

    async def test_get_returns_401(self, client, test_settings):
        token = self._make_expired_token(test_settings)
        response = await client.get(
            "/api/v1/nutrition-logs",
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401

    async def test_delete_returns_401(self, client, test_settings):
        token = self._make_expired_token(test_settings)
        response = await client.delete(
            f"/api/v1/nutrition-logs/{uuid.uuid4()}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401

    async def test_post_code_expired(self, client, test_settings):
        token = self._make_expired_token(test_settings)
        response = await client.post(
            "/api/v1/nutrition-logs",
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
            "/api/v1/nutrition-logs",
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
            "/api/v1/nutrition-logs",
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401

    async def test_delete_returns_401(self, client, test_settings, mock_session):
        self._setup_session(mock_session)
        user_id = uuid.uuid4()
        token = create_access_token(user_id=user_id, settings=test_settings)
        response = await client.delete(
            f"/api/v1/nutrition-logs/{uuid.uuid4()}",
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
            "/api/v1/nutrition-logs",
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
            "/api/v1/nutrition-logs",
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403

    async def test_delete_returns_403(self, client, test_settings, mock_session):
        user = _make_user(is_active=False)
        self._setup_session(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.delete(
            f"/api/v1/nutrition-logs/{uuid.uuid4()}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403

    async def test_post_code_inactive(self, client, test_settings, mock_session):
        user = _make_user(is_active=False)
        self._setup_session(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/nutrition-logs",
            json=_VALID_CREATE_BODY,
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["error"]["code"] == "INACTIVE_ACCOUNT"


class TestAuthNotCalledBeforeService:
    async def test_post_auth_fails_before_service(self, client, test_settings):
        response = await client.post(
            "/api/v1/nutrition-logs",
            json=_VALID_CREATE_BODY,
            params={"logged_date": "2026-07-12"},
        )
        assert response.status_code == 401
        # No manual token parsing in response

    async def test_get_auth_fails_before_service(self, client):
        response = await client.get(
            "/api/v1/nutrition-logs",
            params={"logged_date": "2026-07-12"},
        )
        assert response.status_code == 401

    async def test_delete_auth_fails_before_service(self, client):
        response = await client.delete(
            f"/api/v1/nutrition-logs/{uuid.uuid4()}",
        )
        assert response.status_code == 401


# ===========================================================================
# C. POST Success
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
            "/api/v1/nutrition-logs",
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
            "/api/v1/nutrition-logs",
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
            "/api/v1/nutrition-logs",
            json=_VALID_CREATE_BODY,
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["message"] == "Nutrition log entry created successfully."

    async def test_entry_data_returned(self, client, test_settings, mock_session):
        self._setup_session(mock_session)
        user = _make_user()
        mock_session.execute.return_value = _make_execute_result(user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/nutrition-logs",
            json=_VALID_CREATE_BODY,
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert "data" in data
        entry = data["data"]
        assert "entry_id" in entry
        assert "food_name" in entry
        assert "meal_type" in entry
        assert "serving_description" in entry
        assert "calories_kcal" in entry
        assert "protein_g" in entry
        assert "carbohydrate_g" in entry
        assert "fat_g" in entry

    async def test_no_user_id_exposed(self, client, test_settings, mock_session):
        self._setup_session(mock_session)
        user = _make_user()
        mock_session.execute.return_value = _make_execute_result(user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/nutrition-logs",
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
            "/api/v1/nutrition-logs",
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
            "/api/v1/nutrition-logs",
            json=_VALID_CREATE_BODY,
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        text = response.text.lower()
        assert "insert into" not in text
        assert "select" not in text

    async def test_meal_type_lowercase(self, client, test_settings, mock_session):
        self._setup_session(mock_session)
        user = _make_user()
        mock_session.execute.return_value = _make_execute_result(user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/nutrition-logs",
            json=_VALID_CREATE_BODY,
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["data"]["meal_type"] == "breakfast"

    async def test_x_request_id_present(self, client, test_settings, mock_session):
        self._setup_session(mock_session)
        user = _make_user()
        mock_session.execute.return_value = _make_execute_result(user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/nutrition-logs",
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
            "/api/v1/nutrition-logs",
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
            "/api/v1/nutrition-logs",
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
            "/api/v1/nutrition-logs",
            json=_VALID_CREATE_BODY,
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        # Verify add was called before commit
        mock_session.add.assert_called_once()
        mock_session.commit.assert_awaited_once()

    async def test_does_not_accept_user_id(self, client, test_settings, mock_session):
        self._setup_session(mock_session)
        user = _make_user()
        mock_session.execute.return_value = _make_execute_result(user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        body = dict(_VALID_CREATE_BODY)
        body["user_id"] = str(uuid.uuid4())
        response = await client.post(
            "/api/v1/nutrition-logs",
            json=body,
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422


# ===========================================================================
# D. POST Validation
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
            "/api/v1/nutrition-logs",
            json=body,
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )

    async def test_missing_entry_id(self, client, test_settings, mock_session):
        body = dict(_VALID_CREATE_BODY)
        del body["entry_id"]
        response = await self._do_post(client, test_settings, mock_session, body)
        assert response.status_code == 422

    async def test_missing_food_name(self, client, test_settings, mock_session):
        body = dict(_VALID_CREATE_BODY)
        del body["food_name"]
        response = await self._do_post(client, test_settings, mock_session, body)
        assert response.status_code == 422

    async def test_missing_meal_type(self, client, test_settings, mock_session):
        body = dict(_VALID_CREATE_BODY)
        del body["meal_type"]
        response = await self._do_post(client, test_settings, mock_session, body)
        assert response.status_code == 422

    async def test_missing_calories(self, client, test_settings, mock_session):
        body = dict(_VALID_CREATE_BODY)
        del body["calories_kcal"]
        response = await self._do_post(client, test_settings, mock_session, body)
        assert response.status_code == 422

    async def test_extra_field_rejected(self, client, test_settings, mock_session):
        body = dict(_VALID_CREATE_BODY)
        body["extra_field"] = "value"
        response = await self._do_post(client, test_settings, mock_session, body)
        assert response.status_code == 422

    async def test_user_id_injection_rejected(self, client, test_settings, mock_session):
        body = dict(_VALID_CREATE_BODY)
        body["user_id"] = str(uuid.uuid4())
        response = await self._do_post(client, test_settings, mock_session, body)
        assert response.status_code == 422

    async def test_invalid_entry_id(self, client, test_settings, mock_session):
        body = dict(_VALID_CREATE_BODY)
        body["entry_id"] = "not-a-uuid"
        response = await self._do_post(client, test_settings, mock_session, body)
        assert response.status_code == 422

    async def test_invalid_meal_type(self, client, test_settings, mock_session):
        body = dict(_VALID_CREATE_BODY)
        body["meal_type"] = "brunch"
        response = await self._do_post(client, test_settings, mock_session, body)
        assert response.status_code == 422

    async def test_negative_calories(self, client, test_settings, mock_session):
        body = dict(_VALID_CREATE_BODY)
        body["calories_kcal"] = "-1"
        response = await self._do_post(client, test_settings, mock_session, body)
        assert response.status_code == 422

    async def test_negative_protein(self, client, test_settings, mock_session):
        body = dict(_VALID_CREATE_BODY)
        body["protein_g"] = "-1"
        response = await self._do_post(client, test_settings, mock_session, body)
        assert response.status_code == 422

    async def test_negative_carbohydrate(self, client, test_settings, mock_session):
        body = dict(_VALID_CREATE_BODY)
        body["carbohydrate_g"] = "-1"
        response = await self._do_post(client, test_settings, mock_session, body)
        assert response.status_code == 422

    async def test_negative_fat(self, client, test_settings, mock_session):
        body = dict(_VALID_CREATE_BODY)
        body["fat_g"] = "-1"
        response = await self._do_post(client, test_settings, mock_session, body)
        assert response.status_code == 422

    async def test_nan_calories(self, client, test_settings, mock_session):
        body = dict(_VALID_CREATE_BODY)
        body["calories_kcal"] = "NaN"
        response = await self._do_post(client, test_settings, mock_session, body)
        assert response.status_code == 422

    async def test_empty_food_name(self, client, test_settings, mock_session):
        body = dict(_VALID_CREATE_BODY)
        body["food_name"] = ""
        response = await self._do_post(client, test_settings, mock_session, body)
        assert response.status_code == 422

    async def test_validation_error_envelope(self, client, test_settings, mock_session):
        body = dict(_VALID_CREATE_BODY)
        del body["food_name"]
        response = await self._do_post(client, test_settings, mock_session, body)
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "VALIDATION_ERROR"

    async def test_missing_logged_date(self, client, test_settings, mock_session):
        self._setup_session(mock_session)
        user = _make_user()
        mock_session.execute.return_value = _make_execute_result(user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/nutrition-logs",
            json=_VALID_CREATE_BODY,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422


# ===========================================================================
# E. POST Duplicate
# ===========================================================================


class TestPostDuplicate:
    async def test_returns_409(self, client, test_settings, mock_session):
        from app.core.nutrition_log_exceptions import NutritionLogEntryAlreadyExistsError

        user = _make_user()
        mock_session.execute.return_value = _make_execute_result(user)
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock(side_effect=NutritionLogEntryAlreadyExistsError())
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/nutrition-logs",
            json=_VALID_CREATE_BODY,
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 409

    async def test_error_code(self, client, test_settings, mock_session):
        from app.core.nutrition_log_exceptions import NutritionLogEntryAlreadyExistsError

        user = _make_user()
        mock_session.execute.return_value = _make_execute_result(user)
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock(side_effect=NutritionLogEntryAlreadyExistsError())
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/nutrition-logs",
            json=_VALID_CREATE_BODY,
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["error"]["code"] == "NUTRITION_LOG_ENTRY_ALREADY_EXISTS"

    async def test_safe_message(self, client, test_settings, mock_session):
        from app.core.nutrition_log_exceptions import NutritionLogEntryAlreadyExistsError

        user = _make_user()
        mock_session.execute.return_value = _make_execute_result(user)
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock(side_effect=NutritionLogEntryAlreadyExistsError())
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/nutrition-logs",
            json=_VALID_CREATE_BODY,
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert "already exists" in data["error"]["message"].lower()

    async def test_rollback_called(self, client, test_settings, mock_session):
        from app.core.nutrition_log_exceptions import NutritionLogEntryAlreadyExistsError

        user = _make_user()
        mock_session.execute.return_value = _make_execute_result(user)
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock(side_effect=NutritionLogEntryAlreadyExistsError())
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.post(
            "/api/v1/nutrition-logs",
            json=_VALID_CREATE_BODY,
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        mock_session.rollback.assert_called_once()

    async def test_no_commit_on_duplicate(self, client, test_settings, mock_session):
        from app.core.nutrition_log_exceptions import NutritionLogEntryAlreadyExistsError

        user = _make_user()
        mock_session.execute.return_value = _make_execute_result(user)
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock(side_effect=NutritionLogEntryAlreadyExistsError())
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.post(
            "/api/v1/nutrition-logs",
            json=_VALID_CREATE_BODY,
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        mock_session.commit.assert_not_called()

    async def test_no_sql_exposed(self, client, test_settings, mock_session):
        from app.core.nutrition_log_exceptions import NutritionLogEntryAlreadyExistsError

        user = _make_user()
        mock_session.execute.return_value = _make_execute_result(user)
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock(side_effect=NutritionLogEntryAlreadyExistsError())
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/nutrition-logs",
            json=_VALID_CREATE_BODY,
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        text = response.text.lower()
        assert "constraint" not in text
        assert "integrity" not in text
        assert "insert" not in text

    async def test_request_id_in_body(self, client, test_settings, mock_session):
        from app.core.nutrition_log_exceptions import NutritionLogEntryAlreadyExistsError

        user = _make_user()
        mock_session.execute.return_value = _make_execute_result(user)
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock(side_effect=NutritionLogEntryAlreadyExistsError())
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/nutrition-logs",
            json=_VALID_CREATE_BODY,
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert "request_id" in data["error"]

    async def test_x_request_id_header(self, client, test_settings, mock_session):
        from app.core.nutrition_log_exceptions import NutritionLogEntryAlreadyExistsError

        user = _make_user()
        mock_session.execute.return_value = _make_execute_result(user)
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock(side_effect=NutritionLogEntryAlreadyExistsError())
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/nutrition-logs",
            json=_VALID_CREATE_BODY,
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert "X-Request-ID" in response.headers


# ===========================================================================
# F. POST Persistence Failure
# ===========================================================================


class TestPostPersistenceFailure:
    async def test_commit_failure_returns_503(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.return_value = _make_execute_result(user)
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()
        mock_session.commit = AsyncMock(side_effect=Exception("DB commit failed"))
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/nutrition-logs",
            json=_VALID_CREATE_BODY,
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 503

    async def test_commit_failure_code(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.return_value = _make_execute_result(user)
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()
        mock_session.commit = AsyncMock(side_effect=Exception("DB commit failed"))
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/nutrition-logs",
            json=_VALID_CREATE_BODY,
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["error"]["code"] == "NUTRITION_LOG_PERSISTENCE_ERROR"

    async def test_commit_failure_safe_message(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.return_value = _make_execute_result(user)
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()
        mock_session.commit = AsyncMock(side_effect=Exception("DB commit failed"))
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/nutrition-logs",
            json=_VALID_CREATE_BODY,
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert "DB commit failed" not in response.text
        data = response.json()
        assert "could not be saved" in data["error"]["message"].lower()

    async def test_commit_failure_rolls_back(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.return_value = _make_execute_result(user)
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()
        mock_session.commit = AsyncMock(side_effect=Exception("DB commit failed"))
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.post(
            "/api/v1/nutrition-logs",
            json=_VALID_CREATE_BODY,
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        mock_session.rollback.assert_called()

    async def test_service_persistence_error(self, client, test_settings, mock_session):
        from app.core.nutrition_log_exceptions import NutritionLogPersistenceError

        user = _make_user()
        mock_session.execute.return_value = _make_execute_result(user)
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock(side_effect=NutritionLogPersistenceError())
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/nutrition-logs",
            json=_VALID_CREATE_BODY,
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 503

    async def test_no_raw_exception(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.return_value = _make_execute_result(user)
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()
        mock_session.commit = AsyncMock(side_effect=Exception("hidden error"))
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/nutrition-logs",
            json=_VALID_CREATE_BODY,
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert "hidden error" not in response.text


# ===========================================================================
# G. POST Unexpected Failure
# ===========================================================================


class TestPostUnexpectedFailure:
    async def test_unexpected_error_rolls_back(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.return_value = _make_execute_result(user)
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock(side_effect=RuntimeError("unexpected"))
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/nutrition-logs",
            json=_VALID_CREATE_BODY,
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 500

    async def test_unexpected_error_global_envelope(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.return_value = _make_execute_result(user)
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock(side_effect=RuntimeError("unexpected"))
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/nutrition-logs",
            json=_VALID_CREATE_BODY,
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["error"]["code"] == "INTERNAL_SERVER_ERROR"

    async def test_no_raw_exception_text(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.return_value = _make_execute_result(user)
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock(side_effect=RuntimeError("unexpected"))
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/nutrition-logs",
            json=_VALID_CREATE_BODY,
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert "RuntimeError" not in response.text

    async def test_request_id_in_body(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.return_value = _make_execute_result(user)
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock(side_effect=RuntimeError("unexpected"))
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/nutrition-logs",
            json=_VALID_CREATE_BODY,
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert "request_id" in data["error"]

    async def test_x_request_id_header(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.return_value = _make_execute_result(user)
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock(side_effect=RuntimeError("unexpected"))
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/nutrition-logs",
            json=_VALID_CREATE_BODY,
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert "X-Request-ID" in response.headers


# ===========================================================================
# H. GET Success
# ===========================================================================


class TestGetSuccess:
    def _setup_session(self, mock_session, user, entries=None):
        mock_session.execute = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()

    async def test_returns_200(self, client, test_settings, mock_session):
        user = _make_user()
        self._setup_session(mock_session, user)
        mock_session.execute.return_value = _make_execute_result(user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/nutrition-logs",
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    async def test_success_true(self, client, test_settings, mock_session):
        user = _make_user()
        self._setup_session(mock_session, user)
        mock_session.execute.return_value = _make_execute_result(user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/nutrition-logs",
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["success"] is True

    async def test_correct_message(self, client, test_settings, mock_session):
        user = _make_user()
        self._setup_session(mock_session, user)
        mock_session.execute.return_value = _make_execute_result(user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/nutrition-logs",
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["message"] == "Nutrition log entries retrieved successfully."

    async def test_empty_list(self, client, test_settings, mock_session):
        user = _make_user()
        self._setup_session(mock_session, user)
        mock_session.execute.return_value = _make_execute_result(user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/nutrition-logs",
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["data"]["entries"] == []

    async def test_logged_date_in_response(self, client, test_settings, mock_session):
        user = _make_user()
        self._setup_session(mock_session, user)
        mock_session.execute.return_value = _make_execute_result(user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/nutrition-logs",
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["data"]["logged_date"] == "2026-07-12"

    async def test_no_user_id_exposed(self, client, test_settings, mock_session):
        user = _make_user()
        self._setup_session(mock_session, user)
        mock_session.execute.return_value = _make_execute_result(user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/nutrition-logs",
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert "user_id" not in response.text.lower()

    async def test_no_commit(self, client, test_settings, mock_session):
        user = _make_user()
        self._setup_session(mock_session, user)
        mock_session.execute.return_value = _make_execute_result(user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.get(
            "/api/v1/nutrition-logs",
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        mock_session.commit.assert_not_called()

    async def test_no_flush(self, client, test_settings, mock_session):
        user = _make_user()
        self._setup_session(mock_session, user)
        mock_session.execute.return_value = _make_execute_result(user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.get(
            "/api/v1/nutrition-logs",
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        mock_session.flush.assert_not_called()

    async def test_no_refresh(self, client, test_settings, mock_session):
        user = _make_user()
        self._setup_session(mock_session, user)
        mock_session.execute.return_value = _make_execute_result(user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.get(
            "/api/v1/nutrition-logs",
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        mock_session.refresh.assert_not_called()

    async def test_x_request_id_present(self, client, test_settings, mock_session):
        user = _make_user()
        self._setup_session(mock_session, user)
        mock_session.execute.return_value = _make_execute_result(user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/nutrition-logs",
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert "X-Request-ID" in response.headers


# ===========================================================================
# I. GET Date Validation
# ===========================================================================


class TestGetDateValidation:
    async def test_missing_logged_date_returns_422(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.return_value = _make_execute_result(user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/nutrition-logs",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    async def test_malformed_date_returns_422(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.return_value = _make_execute_result(user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/nutrition-logs",
            params={"logged_date": "not-a-date"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    async def test_impossible_date_returns_422(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.return_value = _make_execute_result(user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/nutrition-logs",
            params={"logged_date": "2026-13-01"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    async def test_valid_leap_date_accepted(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            _make_execute_result([]),
        ]
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/nutrition-logs",
            params={"logged_date": "2024-02-29"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    async def test_past_date_accepted(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            _make_execute_result([]),
        ]
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/nutrition-logs",
            params={"logged_date": "2020-01-01"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    async def test_future_date_accepted(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            _make_execute_result([]),
        ]
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/nutrition-logs",
            params={"logged_date": "2030-01-01"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    async def test_validation_error_envelope(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.return_value = _make_execute_result(user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/nutrition-logs",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "VALIDATION_ERROR"


# ===========================================================================
# J. GET Unexpected Failure
# ===========================================================================


class TestGetUnexpectedFailure:
    async def test_unexpected_error_returns_500(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            RuntimeError("list failed"),
        ]
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/nutrition-logs",
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 500

    async def test_global_envelope(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            RuntimeError("list failed"),
        ]
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/nutrition-logs",
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["error"]["code"] == "INTERNAL_SERVER_ERROR"

    async def test_no_raw_detail(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            RuntimeError("list failed"),
        ]
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/nutrition-logs",
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert "list failed" not in response.text.lower()

    async def test_x_request_id_present(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            RuntimeError("list failed"),
        ]
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/nutrition-logs",
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert "X-Request-ID" in response.headers


# ===========================================================================
# K. DELETE Success
# ===========================================================================


class TestDeleteSuccess:
    async def test_returns_200(self, client, test_settings, mock_session):
        user = _make_user()
        entry = _make_nutrition_log(user_id=user.id)
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            _make_execute_result(entry),
        ]
        mock_session.delete = AsyncMock()
        mock_session.flush = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.delete(
            f"/api/v1/nutrition-logs/{entry.entry_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    async def test_success_true(self, client, test_settings, mock_session):
        user = _make_user()
        entry = _make_nutrition_log(user_id=user.id)
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            _make_execute_result(entry),
        ]
        mock_session.delete = AsyncMock()
        mock_session.flush = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.delete(
            f"/api/v1/nutrition-logs/{entry.entry_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["success"] is True

    async def test_correct_message(self, client, test_settings, mock_session):
        user = _make_user()
        entry = _make_nutrition_log(user_id=user.id)
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            _make_execute_result(entry),
        ]
        mock_session.delete = AsyncMock()
        mock_session.flush = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.delete(
            f"/api/v1/nutrition-logs/{entry.entry_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["message"] == "Nutrition log entry deleted successfully."

    async def test_no_deleted_data_exposed(self, client, test_settings, mock_session):
        user = _make_user()
        entry = _make_nutrition_log(user_id=user.id)
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            _make_execute_result(entry),
        ]
        mock_session.delete = AsyncMock()
        mock_session.flush = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.delete(
            f"/api/v1/nutrition-logs/{entry.entry_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert "food_name" not in response.text.lower()

    async def test_no_user_id_exposed(self, client, test_settings, mock_session):
        user = _make_user()
        entry = _make_nutrition_log(user_id=user.id)
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            _make_execute_result(entry),
        ]
        mock_session.delete = AsyncMock()
        mock_session.flush = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.delete(
            f"/api/v1/nutrition-logs/{entry.entry_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert "user_id" not in response.text.lower()

    async def test_commits_exactly_once(self, client, test_settings, mock_session):
        user = _make_user()
        entry = _make_nutrition_log(user_id=user.id)
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            _make_execute_result(entry),
        ]
        mock_session.delete = AsyncMock()
        mock_session.flush = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.delete(
            f"/api/v1/nutrition-logs/{entry.entry_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        mock_session.commit.assert_awaited_once()

    async def test_no_refresh(self, client, test_settings, mock_session):
        user = _make_user()
        entry = _make_nutrition_log(user_id=user.id)
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            _make_execute_result(entry),
        ]
        mock_session.delete = AsyncMock()
        mock_session.flush = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.delete(
            f"/api/v1/nutrition-logs/{entry.entry_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        mock_session.refresh.assert_not_called()

    async def test_x_request_id_present(self, client, test_settings, mock_session):
        user = _make_user()
        entry = _make_nutrition_log(user_id=user.id)
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            _make_execute_result(entry),
        ]
        mock_session.delete = AsyncMock()
        mock_session.flush = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.delete(
            f"/api/v1/nutrition-logs/{entry.entry_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert "X-Request-ID" in response.headers

    async def test_commit_after_service_success(self, client, test_settings, mock_session):
        user = _make_user()
        entry = _make_nutrition_log(user_id=user.id)
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            _make_execute_result(entry),
        ]
        mock_session.delete = AsyncMock()
        mock_session.flush = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.delete(
            f"/api/v1/nutrition-logs/{entry.entry_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        mock_session.commit.assert_awaited_once()


# ===========================================================================
# L. DELETE Invalid UUID
# ===========================================================================


class TestDeleteInvalidUUID:
    async def test_invalid_uuid_returns_422(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.return_value = _make_execute_result(user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.delete(
            "/api/v1/nutrition-logs/not-a-uuid",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    async def test_validation_envelope(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.return_value = _make_execute_result(user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.delete(
            "/api/v1/nutrition-logs/not-a-uuid",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["error"]["code"] == "VALIDATION_ERROR"

    async def test_no_service_call(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.return_value = _make_execute_result(user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.delete(
            "/api/v1/nutrition-logs/not-a-uuid",
            headers={"Authorization": f"Bearer {token}"},
        )
        mock_session.delete.assert_not_called()


# ===========================================================================
# M. DELETE Missing / Cross-User Entry
# ===========================================================================


class TestDeleteNotFound:
    async def test_missing_entry_returns_404(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            _make_execute_result(None),
        ]
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.delete(
            f"/api/v1/nutrition-logs/{uuid.uuid4()}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404

    async def test_error_code(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            _make_execute_result(None),
        ]
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.delete(
            f"/api/v1/nutrition-logs/{uuid.uuid4()}",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["error"]["code"] == "NUTRITION_LOG_ENTRY_NOT_FOUND"

    async def test_safe_message(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            _make_execute_result(None),
        ]
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.delete(
            f"/api/v1/nutrition-logs/{uuid.uuid4()}",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert "not found" in data["error"]["message"].lower()

    async def test_no_commit_on_not_found(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            _make_execute_result(None),
        ]
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.delete(
            f"/api/v1/nutrition-logs/{uuid.uuid4()}",
            headers={"Authorization": f"Bearer {token}"},
        )
        mock_session.commit.assert_not_called()

    async def test_no_sensitive_data(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            _make_execute_result(None),
        ]
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.delete(
            f"/api/v1/nutrition-logs/{uuid.uuid4()}",
            headers={"Authorization": f"Bearer {token}"},
        )
        text = response.text.lower()
        assert "sql" not in text
        assert "select" not in text

    async def test_request_id_in_body(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            _make_execute_result(None),
        ]
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.delete(
            f"/api/v1/nutrition-logs/{uuid.uuid4()}",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert "request_id" in data["error"]


# ===========================================================================
# N. DELETE Persistence Failure
# ===========================================================================


class TestDeletePersistenceFailure:
    async def test_commit_failure_returns_503(self, client, test_settings, mock_session):
        user = _make_user()
        entry = _make_nutrition_log(user_id=user.id)
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            _make_execute_result(entry),
        ]
        mock_session.delete = AsyncMock()
        mock_session.flush = AsyncMock()
        mock_session.commit = AsyncMock(side_effect=Exception("commit error"))
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.delete(
            f"/api/v1/nutrition-logs/{entry.entry_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 503

    async def test_error_code(self, client, test_settings, mock_session):
        user = _make_user()
        entry = _make_nutrition_log(user_id=user.id)
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            _make_execute_result(entry),
        ]
        mock_session.delete = AsyncMock()
        mock_session.flush = AsyncMock()
        mock_session.commit = AsyncMock(side_effect=Exception("commit error"))
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.delete(
            f"/api/v1/nutrition-logs/{entry.entry_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["error"]["code"] == "NUTRITION_LOG_PERSISTENCE_ERROR"

    async def test_safe_message(self, client, test_settings, mock_session):
        user = _make_user()
        entry = _make_nutrition_log(user_id=user.id)
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            _make_execute_result(entry),
        ]
        mock_session.delete = AsyncMock()
        mock_session.flush = AsyncMock()
        mock_session.commit = AsyncMock(side_effect=Exception("commit error"))
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.delete(
            f"/api/v1/nutrition-logs/{entry.entry_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert "commit error" not in response.text
        data = response.json()
        assert "could not be saved" in data["error"]["message"].lower()

    async def test_rollback_called(self, client, test_settings, mock_session):
        user = _make_user()
        entry = _make_nutrition_log(user_id=user.id)
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            _make_execute_result(entry),
        ]
        mock_session.delete = AsyncMock()
        mock_session.flush = AsyncMock()
        mock_session.commit = AsyncMock(side_effect=Exception("commit error"))
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.delete(
            f"/api/v1/nutrition-logs/{entry.entry_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        mock_session.rollback.assert_called()


# ===========================================================================
# O. DELETE Unexpected Failure
# ===========================================================================


class TestDeleteUnexpectedFailure:
    async def test_unexpected_error_rolls_back(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            RuntimeError("delete failed"),
        ]
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.delete(
            f"/api/v1/nutrition-logs/{uuid.uuid4()}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 500

    async def test_global_envelope(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            RuntimeError("delete failed"),
        ]
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.delete(
            f"/api/v1/nutrition-logs/{uuid.uuid4()}",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["error"]["code"] == "INTERNAL_SERVER_ERROR"

    async def test_no_raw_exception(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            RuntimeError("delete failed"),
        ]
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.delete(
            f"/api/v1/nutrition-logs/{uuid.uuid4()}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert "delete failed" not in response.text.lower()

    async def test_x_request_id_present(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            RuntimeError("delete failed"),
        ]
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.delete(
            f"/api/v1/nutrition-logs/{uuid.uuid4()}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert "X-Request-ID" in response.headers


# ===========================================================================
# P. Read-Only and Phase-Boundary Tests
# ===========================================================================


class TestReadOnlyBoundary:
    async def test_get_does_not_mutate(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            _make_execute_result([]),
        ]
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        mock_session.add = MagicMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.get(
            "/api/v1/nutrition-logs",
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        mock_session.add.assert_not_called()

    async def test_get_does_not_delete(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            _make_execute_result([]),
        ]
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        mock_session.delete = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.get(
            "/api/v1/nutrition-logs",
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        mock_session.delete.assert_not_called()


# ===========================================================================
# Q. OpenAPI
# ===========================================================================


class TestOpenAPI:
    async def test_post_path_exists_in_schema(self, test_settings):
        app = create_app(settings=test_settings)
        schema = app.openapi()
        paths = schema["paths"]
        assert "/api/v1/nutrition-logs" in paths
        assert "post" in paths["/api/v1/nutrition-logs"]

    async def test_get_path_exists_in_schema(self, test_settings):
        app = create_app(settings=test_settings)
        schema = app.openapi()
        paths = schema["paths"]
        assert "/api/v1/nutrition-logs" in paths
        assert "get" in paths["/api/v1/nutrition-logs"]

    async def test_delete_path_exists_in_schema(self, test_settings):
        app = create_app(settings=test_settings)
        schema = app.openapi()
        paths = schema["paths"]
        assert "/api/v1/nutrition-logs/{entry_id}" in paths
        assert "delete" in paths["/api/v1/nutrition-logs/{entry_id}"]

    async def test_post_has_request_body(self, test_settings):
        app = create_app(settings=test_settings)
        schema = app.openapi()
        post_op = schema["paths"]["/api/v1/nutrition-logs"]["post"]
        assert "requestBody" in post_op

    async def test_post_response_model_201(self, test_settings):
        app = create_app(settings=test_settings)
        schema = app.openapi()
        post_op = schema["paths"]["/api/v1/nutrition-logs"]["post"]
        assert "201" in post_op["responses"]

    async def test_get_logged_date_required(self, test_settings):
        app = create_app(settings=test_settings)
        schema = app.openapi()
        get_op = schema["paths"]["/api/v1/nutrition-logs"]["get"]
        params = get_op.get("parameters", [])
        logged_date_params = [p for p in params if p["name"] == "logged_date"]
        assert len(logged_date_params) >= 1
        assert logged_date_params[0]["required"] is True

    async def test_get_logged_date_format(self, test_settings):
        app = create_app(settings=test_settings)
        schema = app.openapi()
        get_op = schema["paths"]["/api/v1/nutrition-logs"]["get"]
        params = get_op.get("parameters", [])
        logged_date_params = [p for p in params if p["name"] == "logged_date"]
        assert logged_date_params[0]["schema"]["format"] == "date"

    async def test_delete_entry_id_required(self, test_settings):
        app = create_app(settings=test_settings)
        schema = app.openapi()
        delete_op = schema["paths"]["/api/v1/nutrition-logs/{entry_id}"]["delete"]
        params = delete_op.get("parameters", [])
        entry_id_params = [p for p in params if p["name"] == "entry_id"]
        assert len(entry_id_params) >= 1

    async def test_all_endpoints_use_bearer_auth(self, test_settings):
        app = create_app(settings=test_settings)
        schema = app.openapi()
        paths_to_check = [
            ("/api/v1/nutrition-logs", "post"),
            ("/api/v1/nutrition-logs", "get"),
            ("/api/v1/nutrition-logs/summary", "get"),
            ("/api/v1/nutrition-logs/{entry_id}", "delete"),
        ]
        for path, method in paths_to_check:
            op = schema["paths"][path][method]
            sec = op.get("security", [])
            assert any("BearerAuth" in s for s in sec), f"{method} {path} missing BearerAuth"

    async def test_exactly_one_bearer_scheme(self, test_settings):
        app = create_app(settings=test_settings)
        schema = app.openapi()
        schemes = schema.get("components", {}).get("securitySchemes", {})
        bearer_count = sum(1 for v in schemes.values() if v.get("scheme") == "bearer")
        assert bearer_count == 1

    async def test_bearer_type_http(self, test_settings):
        app = create_app(settings=test_settings)
        schema = app.openapi()
        schemes = schema.get("components", {}).get("securitySchemes", {})
        bearer = schemes.get("BearerAuth", {})
        assert bearer.get("type") == "http"
        assert bearer.get("scheme") == "bearer"

    async def test_no_user_id_parameter(self, test_settings):
        app = create_app(settings=test_settings)
        schema = app.openapi()
        # Check that user_id doesn't appear as a parameter in nutrition-logs paths
        nutrition_logs_paths = {k: v for k, v in schema["paths"].items() if "nutrition-logs" in k}
        for path, methods in nutrition_logs_paths.items():
            for method, details in methods.items():
                params = details.get("parameters", [])
                param_names = [p["name"] for p in params]
                assert "user_id" not in param_names, f"{method} {path} has user_id param"

    async def test_no_aggregation_route(self, test_settings):
        app = create_app(settings=test_settings)
        schema = app.openapi()
        paths = list(schema["paths"].keys())
        aggreg_paths = [p for p in paths if "aggregat" in p.lower()]
        assert len(aggreg_paths) == 0

    async def test_summary_path_exists_in_nutrition_logs(self, test_settings):
        app = create_app(settings=test_settings)
        schema = app.openapi()
        found = [p for p in schema["paths"] if "nutrition-logs" in p and "summary" in p.lower()]
        assert len(found) == 1
        assert "/api/v1/nutrition-logs/summary" in found

    async def test_no_put_patch_under_nutrition_logs(self, test_settings):
        app = create_app(settings=test_settings)
        schema = app.openapi()
        for path, methods in schema["paths"].items():
            if "nutrition-logs" in path:
                assert "put" not in methods, f"Unexpected PUT at {path}"
                assert "patch" not in methods, f"Unexpected PATCH at {path}"


# ===========================================================================
# R. Existing Route Regression
# ===========================================================================


class TestExistingRouteRegression:
    async def test_root_exists(self, app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            response = await c.get("/")
        assert response.status_code == 200

    async def test_health_still_public(self, app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            response = await c.get("/api/v1/health")
        assert response.status_code == 200

    async def test_register_still_registered(self, app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            response = await c.post("/api/v1/auth/register", json={})
        assert response.status_code != 404

    async def test_login_still_registered(self, app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            response = await c.post("/api/v1/auth/login", json={})
        assert response.status_code != 404

    async def test_auth_me_still_protected(self, app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            response = await c.get("/api/v1/auth/me")
        assert response.status_code == 401

    async def test_nutrition_profile_post_exists(self, app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            response = await c.post("/api/v1/nutrition-profile", json={})
        assert response.status_code != 404

    async def test_nutrition_profile_get_exists(self, app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            response = await c.get("/api/v1/nutrition-profile")
        assert response.status_code != 404

    async def test_nutrition_profile_calculations_exists(self, app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            response = await c.get("/api/v1/nutrition-profile/calculations")
        assert response.status_code != 404

    async def test_nutrition_profile_summary_exists(self, app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            response = await c.get("/api/v1/nutrition-profile/summary")
        assert response.status_code != 404

    async def test_app_factory_two_instances(self, test_settings):
        app1 = create_app(settings=test_settings)
        app2 = create_app(settings=test_settings)
        assert app1 is not app2
