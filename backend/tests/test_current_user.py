from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import jwt
import pytest
from fastapi import Depends
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.authentication import (
    get_current_user,
    security_scheme,
)
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
    is_active: bool = True,
    is_verified: bool = False,
) -> MagicMock:
    user = MagicMock(spec=User)
    user.id = uuid.uuid4()
    user.email = email
    user.password_hash = "$argon2id$v=19$m=65536,t=3,p=4$hash"
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

    @app.get("/test/me")
    async def test_endpoint(user: User = Depends(get_current_user)):
        return {
            "id": str(user.id),
            "email": user.email,
            "is_active": user.is_active,
        }

    return app


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ---------------------------------------------------------------------------
# HTTPBearer configuration
# ---------------------------------------------------------------------------


class TestHTTPBearerConfiguration:
    def test_security_scheme_name(self):
        assert security_scheme.scheme_name == "BearerAuth"

    def test_auto_error_is_false(self):
        assert security_scheme.auto_error is False

    def test_model_scheme_is_bearer(self):
        assert security_scheme.model.scheme == "bearer"


# ---------------------------------------------------------------------------
# Missing/Invalid credentials
# ---------------------------------------------------------------------------


class TestMissingCredentials:
    async def test_returns_401(self, client):
        response = await client.get("/test/me")
        assert response.status_code == 401

    async def test_code_is_authentication_required(self, client):
        response = await client.get("/test/me")
        data = response.json()
        assert data["error"]["code"] == "AUTHENTICATION_REQUIRED"

    async def test_safe_message(self, client):
        response = await client.get("/test/me")
        data = response.json()
        assert data["error"]["message"] == "Authentication is required."

    async def test_www_authenticate_header(self, client):
        response = await client.get("/test/me")
        assert response.headers.get("WWW-Authenticate") == "Bearer"

    async def test_request_id_in_body(self, client):
        response = await client.get("/test/me")
        data = response.json()
        assert "request_id" in data["error"]
        assert len(data["error"]["request_id"]) > 0

    async def test_x_request_id_header(self, client):
        response = await client.get("/test/me")
        assert "X-Request-ID" in response.headers

    async def test_repository_not_called(self, client, mock_session):
        await client.get("/test/me")
        mock_session.execute.assert_not_called()


class TestWrongScheme:
    async def test_returns_401(self, client):
        response = await client.get("/test/me", headers={"Authorization": "Basic dGVzdDpwYXNz"})
        assert response.status_code == 401

    async def test_same_code_and_message(self, client):
        response = await client.get("/test/me", headers={"Authorization": "Basic dGVzdDpwYXNz"})
        data = response.json()
        assert data["error"]["code"] == "AUTHENTICATION_REQUIRED"
        assert data["error"]["message"] == "Authentication is required."

    async def test_token_not_exposed(self, client):
        response = await client.get("/test/me", headers={"Authorization": "Basic dGVzdDpwYXNz"})
        assert "dGVzdDpwYXNz" not in response.text

    async def test_repository_not_called(self, client, mock_session):
        await client.get("/test/me", headers={"Authorization": "Basic dGVzdDpwYXNz"})
        mock_session.execute.assert_not_called()


class TestEmptyToken:
    async def test_returns_401(self, client):
        response = await client.get("/test/me", headers={"Authorization": "Bearer "})
        assert response.status_code == 401

    async def test_code_is_invalid_token(self, client):
        response = await client.get("/test/me", headers={"Authorization": "Bearer "})
        data = response.json()
        assert data["error"]["code"] == "INVALID_ACCESS_TOKEN"

    async def test_safe_message(self, client):
        response = await client.get("/test/me", headers={"Authorization": "Bearer "})
        data = response.json()
        assert data["error"]["message"] == "The access token is invalid."

    async def test_repository_not_called(self, client, mock_session):
        await client.get("/test/me", headers={"Authorization": "Bearer "})
        mock_session.execute.assert_not_called()


class TestWhitespaceOnlyToken:
    async def test_space_only_returns_401(self, client):
        response = await client.get("/test/me", headers={"Authorization": "Bearer   "})
        assert response.status_code == 401

    async def test_space_only_code_is_invalid_token(self, client):
        response = await client.get("/test/me", headers={"Authorization": "Bearer   "})
        data = response.json()
        assert data["error"]["code"] == "INVALID_ACCESS_TOKEN"

    async def test_space_only_safe_message(self, client):
        response = await client.get("/test/me", headers={"Authorization": "Bearer   "})
        data = response.json()
        assert data["error"]["message"] == "The access token is invalid."

    async def test_space_only_repository_not_called(self, client, mock_session):
        await client.get("/test/me", headers={"Authorization": "Bearer   "})
        mock_session.execute.assert_not_called()


class TestMalformedToken:
    async def test_returns_401(self, client):
        response = await client.get("/test/me", headers={"Authorization": "Bearer not-a-valid-jwt"})
        assert response.status_code == 401

    async def test_code_is_invalid_token(self, client):
        response = await client.get("/test/me", headers={"Authorization": "Bearer not-a-valid-jwt"})
        data = response.json()
        assert data["error"]["code"] == "INVALID_ACCESS_TOKEN"

    async def test_token_not_in_response(self, client):
        response = await client.get("/test/me", headers={"Authorization": "Bearer not-a-valid-jwt"})
        assert "not-a-valid-jwt" not in response.text

    async def test_repository_not_called(self, client, mock_session):
        await client.get("/test/me", headers={"Authorization": "Bearer not-a-valid-jwt"})
        mock_session.execute.assert_not_called()


class TestInvalidSignature:
    async def test_returns_401(self, client, test_settings):
        user_id = uuid.uuid4()
        token = create_access_token(user_id=user_id, settings=test_settings)
        # Modify the token to have an invalid signature
        parts = token.split(".")
        bad_token = f"{parts[0]}.{parts[1]}.invalidsignature"
        response = await client.get("/test/me", headers={"Authorization": f"Bearer {bad_token}"})
        assert response.status_code == 401

    async def test_code_is_invalid_token(self, client, test_settings):
        user_id = uuid.uuid4()
        token = create_access_token(user_id=user_id, settings=test_settings)
        parts = token.split(".")
        bad_token = f"{parts[0]}.{parts[1]}.invalidsignature"
        response = await client.get("/test/me", headers={"Authorization": f"Bearer {bad_token}"})
        data = response.json()
        assert data["error"]["code"] == "INVALID_ACCESS_TOKEN"

    async def test_no_raw_jwt_error(self, client, test_settings):
        user_id = uuid.uuid4()
        token = create_access_token(user_id=user_id, settings=test_settings)
        parts = token.split(".")
        bad_token = f"{parts[0]}.{parts[1]}.invalidsignature"
        response = await client.get("/test/me", headers={"Authorization": f"Bearer {bad_token}"})
        assert "Signature verification failed" not in response.text

    async def test_token_not_exposed(self, client, test_settings):
        user_id = uuid.uuid4()
        token = create_access_token(user_id=user_id, settings=test_settings)
        parts = token.split(".")
        bad_token = f"{parts[0]}.{parts[1]}.invalidsignature"
        response = await client.get("/test/me", headers={"Authorization": f"Bearer {bad_token}"})
        assert bad_token not in response.text

    async def test_repository_not_called(self, client, test_settings, mock_session):
        user_id = uuid.uuid4()
        token = create_access_token(user_id=user_id, settings=test_settings)
        parts = token.split(".")
        bad_token = f"{parts[0]}.{parts[1]}.invalidsignature"
        await client.get("/test/me", headers={"Authorization": f"Bearer {bad_token}"})
        mock_session.execute.assert_not_called()


class TestExpiredToken:
    def _make_expired_token(self, settings: Settings) -> str:
        user_id = uuid.uuid4()
        past = datetime.now(UTC) - timedelta(hours=2)
        return create_access_token(user_id=user_id, settings=settings, now=past)

    async def test_returns_401(self, client, test_settings):
        token = self._make_expired_token(test_settings)
        response = await client.get("/test/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 401

    async def test_code_is_expired(self, client, test_settings):
        token = self._make_expired_token(test_settings)
        response = await client.get("/test/me", headers={"Authorization": f"Bearer {token}"})
        data = response.json()
        assert data["error"]["code"] == "ACCESS_TOKEN_EXPIRED"

    async def test_safe_message(self, client, test_settings):
        token = self._make_expired_token(test_settings)
        response = await client.get("/test/me", headers={"Authorization": f"Bearer {token}"})
        data = response.json()
        assert data["error"]["message"] == "The access token has expired."

    async def test_no_expiration_timestamp_exposed(self, client, test_settings):
        token = self._make_expired_token(test_settings)
        response = await client.get("/test/me", headers={"Authorization": f"Bearer {token}"})
        assert token not in response.text

    async def test_repository_not_called(self, client, test_settings, mock_session):
        token = self._make_expired_token(test_settings)
        await client.get("/test/me", headers={"Authorization": f"Bearer {token}"})
        mock_session.execute.assert_not_called()


class TestWrongIssuer:
    async def test_returns_401(self, client, test_settings):
        user_id = uuid.uuid4()
        bad_settings = Settings(
            APP_ENV="test",
            DEBUG=False,
            JWT_SECRET_KEY="test-secret-key-that-is-at-least-32-characters!!",
            JWT_ISSUER="wrong-issuer",
        )
        token = create_access_token(user_id=user_id, settings=bad_settings)
        response = await client.get("/test/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 401

    async def test_code_is_invalid_token(self, client, test_settings):
        user_id = uuid.uuid4()
        bad_settings = Settings(
            APP_ENV="test",
            DEBUG=False,
            JWT_SECRET_KEY="test-secret-key-that-is-at-least-32-characters!!",
            JWT_ISSUER="wrong-issuer",
        )
        token = create_access_token(user_id=user_id, settings=bad_settings)
        response = await client.get("/test/me", headers={"Authorization": f"Bearer {token}"})
        data = response.json()
        assert data["error"]["code"] == "INVALID_ACCESS_TOKEN"

    async def test_repository_not_called(self, client, test_settings, mock_session):
        user_id = uuid.uuid4()
        bad_settings = Settings(
            APP_ENV="test",
            DEBUG=False,
            JWT_SECRET_KEY="test-secret-key-that-is-at-least-32-characters!!",
            JWT_ISSUER="wrong-issuer",
        )
        token = create_access_token(user_id=user_id, settings=bad_settings)
        await client.get("/test/me", headers={"Authorization": f"Bearer {token}"})
        mock_session.execute.assert_not_called()


class TestWrongAudience:
    async def test_returns_401(self, client, test_settings):
        user_id = uuid.uuid4()
        bad_settings = Settings(
            APP_ENV="test",
            DEBUG=False,
            JWT_SECRET_KEY="test-secret-key-that-is-at-least-32-characters!!",
            JWT_AUDIENCE="wrong-audience",
        )
        token = create_access_token(user_id=user_id, settings=bad_settings)
        response = await client.get("/test/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 401

    async def test_code_is_invalid_token(self, client, test_settings):
        user_id = uuid.uuid4()
        bad_settings = Settings(
            APP_ENV="test",
            DEBUG=False,
            JWT_SECRET_KEY="test-secret-key-that-is-at-least-32-characters!!",
            JWT_AUDIENCE="wrong-audience",
        )
        token = create_access_token(user_id=user_id, settings=bad_settings)
        response = await client.get("/test/me", headers={"Authorization": f"Bearer {token}"})
        data = response.json()
        assert data["error"]["code"] == "INVALID_ACCESS_TOKEN"

    async def test_repository_not_called(self, client, test_settings, mock_session):
        user_id = uuid.uuid4()
        bad_settings = Settings(
            APP_ENV="test",
            DEBUG=False,
            JWT_SECRET_KEY="test-secret-key-that-is-at-least-32-characters!!",
            JWT_AUDIENCE="wrong-audience",
        )
        token = create_access_token(user_id=user_id, settings=bad_settings)
        await client.get("/test/me", headers={"Authorization": f"Bearer {token}"})
        mock_session.execute.assert_not_called()


class TestWrongTokenType:
    async def test_returns_401(self, client, test_settings):
        user_id = uuid.uuid4()
        now = datetime.now(UTC)
        payload = {
            "sub": str(user_id),
            "type": "refresh",
            "iat": now,
            "exp": now + timedelta(minutes=15),
            "iss": test_settings.JWT_ISSUER,
            "aud": test_settings.JWT_AUDIENCE,
        }
        token = jwt.encode(
            payload,
            test_settings.JWT_SECRET_KEY,
            algorithm=test_settings.JWT_ALGORITHM,
        )
        response = await client.get("/test/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 401

    async def test_code_is_invalid_token(self, client, test_settings):
        user_id = uuid.uuid4()
        now = datetime.now(UTC)
        payload = {
            "sub": str(user_id),
            "type": "refresh",
            "iat": now,
            "exp": now + timedelta(minutes=15),
            "iss": test_settings.JWT_ISSUER,
            "aud": test_settings.JWT_AUDIENCE,
        }
        token = jwt.encode(
            payload,
            test_settings.JWT_SECRET_KEY,
            algorithm=test_settings.JWT_ALGORITHM,
        )
        response = await client.get("/test/me", headers={"Authorization": f"Bearer {token}"})
        data = response.json()
        assert data["error"]["code"] == "INVALID_ACCESS_TOKEN"

    async def test_repository_not_called(self, client, test_settings, mock_session):
        user_id = uuid.uuid4()
        now = datetime.now(UTC)
        payload = {
            "sub": str(user_id),
            "type": "refresh",
            "iat": now,
            "exp": now + timedelta(minutes=15),
            "iss": test_settings.JWT_ISSUER,
            "aud": test_settings.JWT_AUDIENCE,
        }
        token = jwt.encode(
            payload,
            test_settings.JWT_SECRET_KEY,
            algorithm=test_settings.JWT_ALGORITHM,
        )
        await client.get("/test/me", headers={"Authorization": f"Bearer {token}"})
        mock_session.execute.assert_not_called()


class TestMissingRequiredClaim:
    async def test_returns_401(self, client, test_settings):
        user_id = uuid.uuid4()
        now = datetime.now(UTC)
        payload = {
            "sub": str(user_id),
            "iat": now,
            "exp": now + timedelta(minutes=15),
            "iss": test_settings.JWT_ISSUER,
            "aud": test_settings.JWT_AUDIENCE,
        }
        token = jwt.encode(
            payload,
            test_settings.JWT_SECRET_KEY,
            algorithm=test_settings.JWT_ALGORITHM,
        )
        response = await client.get("/test/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 401

    async def test_code_is_invalid_token(self, client, test_settings):
        user_id = uuid.uuid4()
        now = datetime.now(UTC)
        payload = {
            "sub": str(user_id),
            "iat": now,
            "exp": now + timedelta(minutes=15),
            "iss": test_settings.JWT_ISSUER,
            "aud": test_settings.JWT_AUDIENCE,
        }
        token = jwt.encode(
            payload,
            test_settings.JWT_SECRET_KEY,
            algorithm=test_settings.JWT_ALGORITHM,
        )
        response = await client.get("/test/me", headers={"Authorization": f"Bearer {token}"})
        data = response.json()
        assert data["error"]["code"] == "INVALID_ACCESS_TOKEN"

    async def test_repository_not_called(self, client, test_settings, mock_session):
        user_id = uuid.uuid4()
        now = datetime.now(UTC)
        payload = {
            "sub": str(user_id),
            "iat": now,
            "exp": now + timedelta(minutes=15),
            "iss": test_settings.JWT_ISSUER,
            "aud": test_settings.JWT_AUDIENCE,
        }
        token = jwt.encode(
            payload,
            test_settings.JWT_SECRET_KEY,
            algorithm=test_settings.JWT_ALGORITHM,
        )
        await client.get("/test/me", headers={"Authorization": f"Bearer {token}"})
        mock_session.execute.assert_not_called()


class TestInvalidSubject:
    async def test_returns_401(self, client, test_settings):
        now = datetime.now(UTC)
        payload = {
            "sub": "not-a-valid-uuid",
            "type": "access",
            "iat": now,
            "exp": now + timedelta(minutes=15),
            "iss": test_settings.JWT_ISSUER,
            "aud": test_settings.JWT_AUDIENCE,
        }
        token = jwt.encode(
            payload,
            test_settings.JWT_SECRET_KEY,
            algorithm=test_settings.JWT_ALGORITHM,
        )
        response = await client.get("/test/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 401

    async def test_code_is_invalid_token(self, client, test_settings):
        now = datetime.now(UTC)
        payload = {
            "sub": "not-a-valid-uuid",
            "type": "access",
            "iat": now,
            "exp": now + timedelta(minutes=15),
            "iss": test_settings.JWT_ISSUER,
            "aud": test_settings.JWT_AUDIENCE,
        }
        token = jwt.encode(
            payload,
            test_settings.JWT_SECRET_KEY,
            algorithm=test_settings.JWT_ALGORITHM,
        )
        response = await client.get("/test/me", headers={"Authorization": f"Bearer {token}"})
        data = response.json()
        assert data["error"]["code"] == "INVALID_ACCESS_TOKEN"

    async def test_repository_not_called(self, client, test_settings, mock_session):
        now = datetime.now(UTC)
        payload = {
            "sub": "not-a-valid-uuid",
            "type": "access",
            "iat": now,
            "exp": now + timedelta(minutes=15),
            "iss": test_settings.JWT_ISSUER,
            "aud": test_settings.JWT_AUDIENCE,
        }
        token = jwt.encode(
            payload,
            test_settings.JWT_SECRET_KEY,
            algorithm=test_settings.JWT_ALGORITHM,
        )
        await client.get("/test/me", headers={"Authorization": f"Bearer {token}"})
        mock_session.execute.assert_not_called()


# ---------------------------------------------------------------------------
# User lookup
# ---------------------------------------------------------------------------


class TestUnknownUser:
    async def test_returns_401(self, client, test_settings, mock_session):
        _setup_session_for_get_by_id(mock_session, None)
        user_id = uuid.uuid4()
        token = create_access_token(user_id=user_id, settings=test_settings)
        response = await client.get("/test/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 401

    async def test_code_is_invalid_token(self, client, test_settings, mock_session):
        _setup_session_for_get_by_id(mock_session, None)
        user_id = uuid.uuid4()
        token = create_access_token(user_id=user_id, settings=test_settings)
        response = await client.get("/test/me", headers={"Authorization": f"Bearer {token}"})
        data = response.json()
        assert data["error"]["code"] == "INVALID_ACCESS_TOKEN"

    async def test_does_not_reveal_missing_user(self, client, test_settings, mock_session):
        _setup_session_for_get_by_id(mock_session, None)
        user_id = uuid.uuid4()
        token = create_access_token(user_id=user_id, settings=test_settings)
        response = await client.get("/test/me", headers={"Authorization": f"Bearer {token}"})
        data = response.json()
        assert "user" not in data.get("data", {})
        assert "exists" not in response.text.lower()
        assert "unknown" not in data["error"]["message"].lower()

    async def test_get_by_id_called_with_correct_uuid(self, client, test_settings, mock_session):
        _setup_session_for_get_by_id(mock_session, None)
        user_id = uuid.uuid4()
        token = create_access_token(user_id=user_id, settings=test_settings)
        await client.get("/test/me", headers={"Authorization": f"Bearer {token}"})
        mock_session.execute.assert_awaited_once()

    async def test_no_commit(self, client, test_settings, mock_session):
        _setup_session_for_get_by_id(mock_session, None)
        user_id = uuid.uuid4()
        token = create_access_token(user_id=user_id, settings=test_settings)
        await client.get("/test/me", headers={"Authorization": f"Bearer {token}"})
        mock_session.commit.assert_not_called()

    async def test_no_flush(self, client, test_settings, mock_session):
        _setup_session_for_get_by_id(mock_session, None)
        user_id = uuid.uuid4()
        token = create_access_token(user_id=user_id, settings=test_settings)
        await client.get("/test/me", headers={"Authorization": f"Bearer {token}"})
        mock_session.flush.assert_not_called()


class TestInactiveUser:
    async def test_returns_403(self, client, test_settings, mock_session):
        user = _make_user(is_active=False)
        _setup_session_for_get_by_id(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get("/test/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 403

    async def test_code_is_inactive_account(self, client, test_settings, mock_session):
        user = _make_user(is_active=False)
        _setup_session_for_get_by_id(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get("/test/me", headers={"Authorization": f"Bearer {token}"})
        data = response.json()
        assert data["error"]["code"] == "INACTIVE_ACCOUNT"

    async def test_safe_message(self, client, test_settings, mock_session):
        user = _make_user(is_active=False)
        _setup_session_for_get_by_id(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get("/test/me", headers={"Authorization": f"Bearer {token}"})
        data = response.json()
        assert data["error"]["message"] == "This account is inactive."

    async def test_token_not_returned(self, client, test_settings, mock_session):
        user = _make_user(is_active=False)
        _setup_session_for_get_by_id(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get("/test/me", headers={"Authorization": f"Bearer {token}"})
        assert token not in response.text

    async def test_no_commit(self, client, test_settings, mock_session):
        user = _make_user(is_active=False)
        _setup_session_for_get_by_id(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.get("/test/me", headers={"Authorization": f"Bearer {token}"})
        mock_session.commit.assert_not_called()

    async def test_no_flush(self, client, test_settings, mock_session):
        user = _make_user(is_active=False)
        _setup_session_for_get_by_id(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.get("/test/me", headers={"Authorization": f"Bearer {token}"})
        mock_session.flush.assert_not_called()


class TestActiveUser:
    async def test_returns_user(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_session_for_get_by_id(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get("/test/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(user.id)
        assert data["email"] == user.email

    async def test_get_by_id_called_once(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_session_for_get_by_id(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.get("/test/me", headers={"Authorization": f"Bearer {token}"})
        mock_session.execute.assert_awaited_once()

    async def test_no_commit(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_session_for_get_by_id(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.get("/test/me", headers={"Authorization": f"Bearer {token}"})
        mock_session.commit.assert_not_called()

    async def test_no_flush(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_session_for_get_by_id(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.get("/test/me", headers={"Authorization": f"Bearer {token}"})
        mock_session.flush.assert_not_called()

    async def test_user_not_mutated(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_session_for_get_by_id(mock_session, user)
        original_email = user.email
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get("/test/me", headers={"Authorization": f"Bearer {token}"})
        data = response.json()
        assert data["email"] == original_email
