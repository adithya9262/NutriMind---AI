from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
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
from app.models.user import User

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_session() -> AsyncMock:
    return AsyncMock(spec=AsyncSession)


def _make_user(
    email: str = "test@example.com",
    password_hash: str = "$argon2id$v=19$m=65536,t=3,p=4$hash",
    is_active: bool = True,
    is_verified: bool = False,
) -> MagicMock:
    user = MagicMock(spec=User)
    user.id = uuid.uuid4()
    user.email = email
    user.password_hash = password_hash
    user.is_active = is_active
    user.is_verified = is_verified
    user.created_at = datetime.now(UTC)
    user.updated_at = datetime.now(UTC)
    return user


def _setup_session_for_get_by_id(
    session: AsyncMock,
    user: MagicMock | None,
) -> None:
    result_mock = MagicMock()
    result_mock.scalars.return_value.one_or_none.return_value = user
    session.execute = AsyncMock(return_value=result_mock)
    session.commit = AsyncMock()
    session.flush = AsyncMock()
    session.rollback = AsyncMock()


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
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ---------------------------------------------------------------------------
# Route registration
# ---------------------------------------------------------------------------


class TestRouteRegistration:
    async def test_auth_me_path_exists(self, client):
        response = await client.get("/api/v1/auth/me")
        assert response.status_code != 404

    async def test_auth_me_accepts_get(self, client):
        response = await client.get("/api/v1/auth/me")
        assert response.status_code != 405

    async def test_auth_me_rejects_post(self, client):
        response = await client.post("/api/v1/auth/me")
        assert response.status_code == 405

    async def test_register_still_exists(self, client):
        response = await client.post("/api/v1/auth/register", json={})
        assert response.status_code != 404

    async def test_login_still_exists(self, client):
        response = await client.post("/api/v1/auth/login", json={})
        assert response.status_code != 404

    async def test_health_still_public(self, client):
        transport = ASGITransport(app=create_app(Settings(APP_ENV="test", DEBUG=False)))
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            response = await c.get("/api/v1/health")
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# Success
# ---------------------------------------------------------------------------


class TestAuthMeSuccess:
    async def test_returns_200(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_session_for_get_by_id(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    async def test_success_is_true(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_session_for_get_by_id(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["success"] is True

    async def test_correct_message(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_session_for_get_by_id(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["message"] == "Current user retrieved successfully."

    async def test_public_user_returned(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_session_for_get_by_id(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert "data" in data
        user_data = data["data"]
        assert user_data["id"] == str(user.id)
        assert user_data["email"] == user.email
        assert user_data["is_active"] is True
        assert user_data["is_verified"] is False
        assert "created_at" in user_data
        assert "updated_at" in user_data

    async def test_public_user_fields_only(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_session_for_get_by_id(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        user_keys = set(data["data"].keys())
        assert user_keys == {"id", "email", "is_active", "is_verified", "created_at", "updated_at"}

    async def test_no_password(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_session_for_get_by_id(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert "password" not in response.text

    async def test_no_password_hash(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_session_for_get_by_id(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert "password_hash" not in response.text

    async def test_no_access_token(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_session_for_get_by_id(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert "access_token" not in response.text

    async def test_no_refresh_token(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_session_for_get_by_id(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert "refresh_token" not in response.text

    async def test_no_jwt_claims(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_session_for_get_by_id(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        text_lower = response.text.lower()
        assert "sub" not in text_lower
        assert "iss" not in text_lower
        assert "aud" not in text_lower

    async def test_no_jwt_secret(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_session_for_get_by_id(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert "secret" not in response.text.lower()

    async def test_no_nutrition_profile(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_session_for_get_by_id(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert "nutrition" not in response.text.lower()

    async def test_no_role_or_permissions(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_session_for_get_by_id(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        text_lower = response.text.lower()
        assert "role" not in text_lower
        assert "permission" not in text_lower

    async def test_x_request_id_present(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_session_for_get_by_id(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert "X-Request-ID" in response.headers

    async def test_no_commit(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_session_for_get_by_id(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        mock_session.commit.assert_not_called()

    async def test_no_flush(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_session_for_get_by_id(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        mock_session.flush.assert_not_called()

    async def test_user_not_mutated(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_session_for_get_by_id(mock_session, user)
        original_email = user.email
        original_active = user.is_active
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert user.email == original_email
        assert user.is_active == original_active


# ---------------------------------------------------------------------------
# Missing authorization
# ---------------------------------------------------------------------------


class TestAuthMeMissingAuth:
    async def test_returns_401(self, client):
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401

    async def test_code_is_authentication_required(self, client):
        response = await client.get("/api/v1/auth/me")
        data = response.json()
        assert data["error"]["code"] == "AUTHENTICATION_REQUIRED"

    async def test_safe_message(self, client):
        response = await client.get("/api/v1/auth/me")
        data = response.json()
        assert data["error"]["message"] == "Authentication is required."

    async def test_www_authenticate_header(self, client):
        response = await client.get("/api/v1/auth/me")
        assert response.headers.get("WWW-Authenticate") == "Bearer"

    async def test_request_id_present(self, client):
        response = await client.get("/api/v1/auth/me")
        data = response.json()
        assert "request_id" in data["error"]
        assert "X-Request-ID" in response.headers


# ---------------------------------------------------------------------------
# Invalid token
# ---------------------------------------------------------------------------


class TestAuthMeInvalidToken:
    async def test_returns_401(self, client):
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer not-a-valid-token"},
        )
        assert response.status_code == 401

    async def test_code_is_invalid_token(self, client):
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer not-a-valid-token"},
        )
        data = response.json()
        assert data["error"]["code"] == "INVALID_ACCESS_TOKEN"

    async def test_safe_message(self, client):
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer not-a-valid-token"},
        )
        data = response.json()
        assert data["error"]["message"] == "The access token is invalid."

    async def test_token_not_in_response(self, client):
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer not-a-valid-token"},
        )
        assert "not-a-valid-token" not in response.text


# ---------------------------------------------------------------------------
# Expired token
# ---------------------------------------------------------------------------


class TestAuthMeExpiredToken:
    def _make_expired_token(self, settings: Settings) -> str:
        user_id = uuid.uuid4()
        past = datetime.now(UTC) - timedelta(hours=2)
        return create_access_token(user_id=user_id, settings=settings, now=past)

    async def test_returns_401(self, client, test_settings):
        token = self._make_expired_token(test_settings)
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401

    async def test_code_is_expired(self, client, test_settings):
        token = self._make_expired_token(test_settings)
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["error"]["code"] == "ACCESS_TOKEN_EXPIRED"

    async def test_safe_message(self, client, test_settings):
        token = self._make_expired_token(test_settings)
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["error"]["message"] == "The access token has expired."


# ---------------------------------------------------------------------------
# Unknown user
# ---------------------------------------------------------------------------


class TestAuthMeUnknownUser:
    async def test_returns_401(self, client, test_settings, mock_session):
        _setup_session_for_get_by_id(mock_session, None)
        user_id = uuid.uuid4()
        token = create_access_token(user_id=user_id, settings=test_settings)
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401

    async def test_code_is_invalid_token(self, client, test_settings, mock_session):
        _setup_session_for_get_by_id(mock_session, None)
        user_id = uuid.uuid4()
        token = create_access_token(user_id=user_id, settings=test_settings)
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["error"]["code"] == "INVALID_ACCESS_TOKEN"

    async def test_does_not_reveal_user_absence(self, client, test_settings, mock_session):
        _setup_session_for_get_by_id(mock_session, None)
        user_id = uuid.uuid4()
        token = create_access_token(user_id=user_id, settings=test_settings)
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert "exists" not in data["error"]["message"].lower()
        assert "found" not in data["error"]["message"].lower()


# ---------------------------------------------------------------------------
# Inactive user
# ---------------------------------------------------------------------------


class TestAuthMeInactiveUser:
    async def test_returns_403(self, client, test_settings, mock_session):
        user = _make_user(is_active=False)
        _setup_session_for_get_by_id(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403

    async def test_code_is_inactive_account(self, client, test_settings, mock_session):
        user = _make_user(is_active=False)
        _setup_session_for_get_by_id(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["error"]["code"] == "INACTIVE_ACCOUNT"

    async def test_safe_message(self, client, test_settings, mock_session):
        user = _make_user(is_active=False)
        _setup_session_for_get_by_id(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["error"]["message"] == "This account is inactive."
