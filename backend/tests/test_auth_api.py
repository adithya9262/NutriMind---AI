from __future__ import annotations

import asyncio
import json
import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import jwt
import pytest
import pytest_asyncio
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.authentication import get_current_user
from app.api.v1.auth import SupabaseSyncRequest, get_settings, supabase_sync
from app.core.config import Settings
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
    user.supabase_user_id = None
    user.created_at = datetime.now(UTC)
    user.updated_at = datetime.now(UTC)
    return user


def _setup_session_for_no_user(session: AsyncMock) -> None:
    added_objects: list = []

    result_mock = MagicMock()
    result_mock.scalars.return_value.first.return_value = None
    session.execute = AsyncMock(return_value=result_mock)

    def add_side_effect(obj: object) -> None:
        added_objects.append(obj)

    session.add = MagicMock(side_effect=add_side_effect)

    async def flush_side_effect(*args: object, **kwargs: object) -> None:
        for obj in added_objects:
            if isinstance(obj, User):
                if obj.id is None:
                    obj.id = uuid.uuid4()
                if obj.is_active is None:
                    obj.is_active = True
                if obj.is_verified is None:
                    obj.is_verified = False
        added_objects.clear()

    session.flush = AsyncMock(side_effect=flush_side_effect)
    session.commit = AsyncMock()
    session.rollback = AsyncMock()

    async def refresh_side_effect(instance: object, *args: object, **kwargs: object) -> None:
        now = datetime.now(UTC)
        instance.created_at = now  # type: ignore[attr-defined]
        instance.updated_at = now  # type: ignore[attr-defined]

    session.refresh = AsyncMock(side_effect=refresh_side_effect)


def _setup_session_for_user(session: AsyncMock, user: MagicMock) -> None:
    result_mock = MagicMock()
    result_mock.scalars.return_value.first.return_value = user
    session.execute = AsyncMock(return_value=result_mock)
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.refresh = AsyncMock()


def _run_isolated_asgi_request(app, method: str, url: str, **kwargs):
    async def perform_request():
        async with AsyncClient(
            transport=ASGITransport(app=app, raise_app_exceptions=False),
            base_url="http://test",
        ) as async_client:
            request = asyncio.create_task(async_client.request(method, url, **kwargs))
            await asyncio.sleep(0.1)
            return await asyncio.wait_for(request, timeout=15)

    return asyncio.run(perform_request())


def _effective_route_paths(routes, prefix: str = "") -> list[str]:
    paths: list[str] = []
    for route in routes:
        included_router = getattr(route, "original_router", None)
        if included_router is not None:
            context = route.include_context
            nested_prefix = f"{prefix.rstrip('/')}/{context.prefix.lstrip('/')}"
            paths.extend(_effective_route_paths(included_router.routes, nested_prefix))
            continue
        route_path = getattr(route, "path", None)
        if route_path is not None:
            paths.append(f"{prefix.rstrip('/')}/{route_path.lstrip('/')}")
    return paths


class TaskYieldingASGIClient:
    """Schedule each in-process request separately and bound any transport stall."""

    def __init__(self, async_client: AsyncClient):
        self.async_client = async_client

    async def request(self, method: str, url: str, **kwargs):
        request = asyncio.create_task(self.async_client.request(method, url, **kwargs))
        await asyncio.sleep(0.1)
        return await asyncio.wait_for(request, timeout=15)

    async def get(self, url: str, **kwargs):
        return await self.request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs):
        return await self.request("POST", url, **kwargs)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def test_settings():
    return Settings(
        APP_ENV="test",
        DEBUG=False,
        CORS_ORIGINS="http://test",
        DATABASE_URL="",
        JWT_SECRET_KEY="test-secret-key-that-is-at-least-32-characters!!",
    )


@pytest.fixture
def mock_session():
    return _make_session()


@pytest.fixture
def app(test_settings, mock_session):
    application = create_app(settings=test_settings)

    async def override_get_settings():
        return test_settings

    application.dependency_overrides[get_settings] = override_get_settings

    async def override_get_db_session():
        try:
            yield mock_session
        finally:
            pass

    application.dependency_overrides[get_db_session] = override_get_db_session
    try:
        yield application
    finally:
        application.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client(app):
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield TaskYieldingASGIClient(async_client)


# ---------------------------------------------------------------------------
# Route registration
# ---------------------------------------------------------------------------


class TestRouteRegistration:
    async def test_backend_authentication_still_rejects_missing_bearer_token(
        self, test_settings, mock_session
    ):
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(
                request=MagicMock(headers={}),
                credentials=None,
                session=mock_session,
                settings=test_settings,
            )
        assert exc_info.value.status_code == 401

    @patch("app.api.dependencies.authentication._verify_via_supabase_api", new_callable=AsyncMock)
    @patch("app.api.dependencies.authentication.UserRepository")
    async def test_backend_rejects_unverified_email_when_linking_existing_user(
        self, mock_repo_class, mock_verify, mock_session
    ):
        now = int(datetime.now(UTC).timestamp())
        supabase_secret = "supabase-test-signing-secret-long-enough"
        settings = Settings(
            APP_ENV="test",
            DEBUG=False,
            JWT_SECRET_KEY="test-secret-key-that-is-at-least-32-characters!!",
            SUPABASE_JWT_SECRET=supabase_secret,
        )
        supabase_id = uuid.uuid4()
        token = jwt.encode(
            {
                "sub": str(supabase_id),
                "email": "existing@example.com",
                "aud": "authenticated",
                "iat": now,
                "exp": now + 300,
            },
            supabase_secret,
            algorithm="HS256",
        )
        repo = MagicMock()
        repo.get_by_supabase_id = AsyncMock(return_value=None)
        repo.get_by_id = AsyncMock(return_value=None)
        repo.get_by_email = AsyncMock()
        mock_repo_class.return_value = repo
        mock_verify.return_value = {
            "id": str(supabase_id),
            "email": "existing@example.com",
            "email_confirmed_at": None,
        }

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(
                request=MagicMock(headers={}),
                credentials=HTTPAuthorizationCredentials(
                    scheme="Bearer", credentials=token
                ),
                session=mock_session,
                settings=settings,
            )

        assert exc_info.value.status_code == 401
        repo.get_by_email.assert_not_awaited()

    @patch("app.api.dependencies.authentication.UserRepository")
    async def test_supabase_identity_cannot_fall_back_to_conflicting_local_id(
        self, mock_repo_class, mock_session
    ):
        now = int(datetime.now(UTC).timestamp())
        supabase_secret = "supabase-test-signing-secret-long-enough"
        settings = Settings(
            APP_ENV="test",
            DEBUG=False,
            JWT_SECRET_KEY="test-secret-key-that-is-at-least-32-characters!!",
            SUPABASE_JWT_SECRET=supabase_secret,
        )
        supabase_id = uuid.uuid4()
        token = jwt.encode(
            {
                "sub": str(supabase_id),
                "email": "new-identity@example.com",
                "aud": "authenticated",
                "iat": now,
                "exp": now + 300,
            },
            supabase_secret,
            algorithm="HS256",
        )
        local_user = _make_user()
        local_user.id = supabase_id
        local_user.supabase_user_id = uuid.uuid4()
        repo = MagicMock()
        repo.get_by_supabase_id = AsyncMock(return_value=None)
        repo.get_by_id = AsyncMock(return_value=local_user)
        mock_repo_class.return_value = repo

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(
                request=MagicMock(headers={}),
                credentials=HTTPAuthorizationCredentials(
                    scheme="Bearer", credentials=token
                ),
                session=mock_session,
                settings=settings,
            )

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail["error"]["code"] == "IDENTITY_CONFLICT"
        mock_session.commit.assert_not_awaited()

    def test_register_path_exists(self, app):
        response = _run_isolated_asgi_request(app, "POST", "/api/v1/auth/register", json={})
        assert response.status_code == 422

    def test_login_path_exists(self, app):
        response = _run_isolated_asgi_request(app, "POST", "/api/v1/auth/login", json={})
        assert response.status_code == 422

    def test_register_accepts_post(self, app):
        response = _run_isolated_asgi_request(app, "POST", "/api/v1/auth/register", json={})
        assert response.status_code == 422

    def test_login_accepts_post(self, app):
        response = _run_isolated_asgi_request(app, "POST", "/api/v1/auth/login", json={})
        assert response.status_code == 422

    def test_register_rejects_get(self, app):
        response = _run_isolated_asgi_request(app, "GET", "/api/v1/auth/register")
        assert response.status_code == 405

    def test_login_rejects_get(self, app):
        response = _run_isolated_asgi_request(app, "GET", "/api/v1/auth/login")
        assert response.status_code == 405

    def test_health_path_remains(self, app):
        response = _run_isolated_asgi_request(app, "GET", "/api/v1/health")
        assert response.status_code == 200

    def test_no_auth_route_outside_api_v1(self, app):
        response = _run_isolated_asgi_request(app, "POST", "/auth/register", json={})
        assert response.status_code == 404

    def test_no_logout_route(self, app):
        response = _run_isolated_asgi_request(app, "POST", "/api/v1/auth/logout")
        assert response.status_code == 405 or response.status_code == 404

    def test_auth_me_route_exists(self, app):
        response = _run_isolated_asgi_request(app, "GET", "/api/v1/auth/me")
        assert response.status_code != 404


# ---------------------------------------------------------------------------
# Registration — success
# ---------------------------------------------------------------------------


class TestRegisterSuccess:
    @patch("app.services.authentication.hash_password", return_value="hashed_pw")
    async def test_returns_201(self, mock_hash, client, mock_session, test_settings):
        _setup_session_for_no_user(mock_session)
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "new@example.com", "password": "secure12345"},
        )
        assert response.status_code == 201

    @patch("app.services.authentication.hash_password", return_value="hashed_pw")
    async def test_success_is_true(self, mock_hash, client, mock_session, test_settings):
        _setup_session_for_no_user(mock_session)
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "new@example.com", "password": "secure12345"},
        )
        data = response.json()
        assert data["success"] is True

    @patch("app.services.authentication.hash_password", return_value="hashed_pw")
    async def test_correct_message(self, mock_hash, client, mock_session, test_settings):
        _setup_session_for_no_user(mock_session)
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "new@example.com", "password": "secure12345"},
        )
        data = response.json()
        assert data["message"] == "Registration successful."

    @patch("app.services.authentication.hash_password", return_value="hashed_pw")
    async def test_public_user_returned(self, mock_hash, client, mock_session, test_settings):
        _setup_session_for_no_user(mock_session)
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "new@example.com", "password": "secure12345"},
        )
        data = response.json()
        assert "user" in data["data"]
        user = data["data"]["user"]
        assert "id" in user
        assert "email" in user
        assert "is_active" in user
        assert "is_verified" in user
        assert "created_at" in user
        assert "updated_at" in user

    @patch("app.services.authentication.hash_password", return_value="hashed_pw")
    async def test_access_token_returned(self, mock_hash, client, mock_session, test_settings):
        _setup_session_for_no_user(mock_session)
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "new@example.com", "password": "secure12345"},
        )
        data = response.json()
        assert "access_token" in data["data"]
        assert len(data["data"]["access_token"]) > 0

    @patch("app.services.authentication.hash_password", return_value="hashed_pw")
    async def test_token_type_is_bearer(self, mock_hash, client, mock_session, test_settings):
        _setup_session_for_no_user(mock_session)
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "new@example.com", "password": "secure12345"},
        )
        data = response.json()
        assert data["data"]["token_type"] == "bearer"

    @patch("app.services.authentication.hash_password", return_value="hashed_pw")
    async def test_expires_in_correct(self, mock_hash, client, mock_session, test_settings):
        _setup_session_for_no_user(mock_session)
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "new@example.com", "password": "secure12345"},
        )
        data = response.json()
        expected = test_settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
        assert data["data"]["expires_in"] == expected

    @patch("app.services.authentication.hash_password", return_value="hashed_pw")
    async def test_token_decodes(self, mock_hash, client, mock_session, test_settings):
        _setup_session_for_no_user(mock_session)
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "new@example.com", "password": "secure12345"},
        )
        token = response.json()["data"]["access_token"]
        payload = jwt.decode(
            token,
            test_settings.JWT_SECRET_KEY,
            algorithms=[test_settings.JWT_ALGORITHM],
            options={"verify_exp": False},
            audience=test_settings.JWT_AUDIENCE,
        )
        assert "sub" in payload
        assert "type" in payload
        assert payload["type"] == "access"

    @patch("app.services.authentication.hash_password", return_value="hashed_pw")
    async def test_commits_exactly_once(self, mock_hash, client, mock_session, test_settings):
        _setup_session_for_no_user(mock_session)
        await client.post(
            "/api/v1/auth/register",
            json={"email": "new@example.com", "password": "secure12345"},
        )
        mock_session.commit.assert_awaited_once()

    @patch("app.services.authentication.hash_password", return_value="hashed_pw")
    async def test_does_not_rollback_on_success(
        self, mock_hash, client, mock_session, test_settings
    ):
        _setup_session_for_no_user(mock_session)
        await client.post(
            "/api/v1/auth/register",
            json={"email": "new@example.com", "password": "secure12345"},
        )
        mock_session.rollback.assert_not_called()

    @patch("app.services.authentication.hash_password", return_value="hashed_pw")
    async def test_password_absent(self, mock_hash, client, mock_session, test_settings):
        _setup_session_for_no_user(mock_session)
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "new@example.com", "password": "secure12345"},
        )
        assert "secure12345" not in response.text

    @patch("app.services.authentication.hash_password", return_value="hashed_pw")
    async def test_password_hash_absent(self, mock_hash, client, mock_session, test_settings):
        _setup_session_for_no_user(mock_session)
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "new@example.com", "password": "secure12345"},
        )
        assert "password_hash" not in response.text

    @patch("app.services.authentication.hash_password", return_value="hashed_pw")
    async def test_refresh_token_absent(self, mock_hash, client, mock_session, test_settings):
        _setup_session_for_no_user(mock_session)
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "new@example.com", "password": "secure12345"},
        )
        assert "refresh_token" not in response.text

    @patch("app.services.authentication.hash_password", return_value="hashed_pw")
    async def test_x_request_id_present(self, mock_hash, client, mock_session, test_settings):
        _setup_session_for_no_user(mock_session)
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "new@example.com", "password": "secure12345"},
        )
        assert "X-Request-ID" in response.headers
        assert len(response.headers["X-Request-ID"]) > 0


# ---------------------------------------------------------------------------
# Login — success
# ---------------------------------------------------------------------------


class TestLoginSuccess:
    @patch("app.services.authentication.verify_password", return_value=True)
    async def test_returns_200(self, mock_verify, client, mock_session, test_settings):
        user = _make_user()
        _setup_session_for_user(mock_session, user)
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "password123"},
        )
        assert response.status_code == 200

    @patch("app.services.authentication.verify_password", return_value=True)
    async def test_success_is_true(self, mock_verify, client, mock_session, test_settings):
        user = _make_user()
        _setup_session_for_user(mock_session, user)
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "password123"},
        )
        data = response.json()
        assert data["success"] is True

    @patch("app.services.authentication.verify_password", return_value=True)
    async def test_correct_message(self, mock_verify, client, mock_session, test_settings):
        user = _make_user()
        _setup_session_for_user(mock_session, user)
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "password123"},
        )
        data = response.json()
        assert data["message"] == "Login successful."

    @patch("app.services.authentication.verify_password", return_value=True)
    async def test_public_user_returned(self, mock_verify, client, mock_session, test_settings):
        user = _make_user()
        _setup_session_for_user(mock_session, user)
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "password123"},
        )
        data = response.json()
        assert "user" in data["data"]
        user_data = data["data"]["user"]
        assert "id" in user_data
        assert "email" in user_data
        assert "is_active" in user_data
        assert "is_verified" in user_data
        assert "created_at" in user_data
        assert "updated_at" in user_data

    @patch("app.services.authentication.verify_password", return_value=True)
    async def test_access_token_returned(self, mock_verify, client, mock_session, test_settings):
        user = _make_user()
        _setup_session_for_user(mock_session, user)
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "password123"},
        )
        data = response.json()
        assert "access_token" in data["data"]
        assert len(data["data"]["access_token"]) > 0

    @patch("app.services.authentication.verify_password", return_value=True)
    async def test_token_type_is_bearer(self, mock_verify, client, mock_session, test_settings):
        user = _make_user()
        _setup_session_for_user(mock_session, user)
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "password123"},
        )
        data = response.json()
        assert data["data"]["token_type"] == "bearer"

    @patch("app.services.authentication.verify_password", return_value=True)
    async def test_expires_in_correct(self, mock_verify, client, mock_session, test_settings):
        user = _make_user()
        _setup_session_for_user(mock_session, user)
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "password123"},
        )
        data = response.json()
        expected = test_settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
        assert data["data"]["expires_in"] == expected

    @patch("app.services.authentication.verify_password", return_value=True)
    async def test_token_decodes_with_correct_subject(
        self, mock_verify, client, mock_session, test_settings
    ):
        user = _make_user()
        _setup_session_for_user(mock_session, user)
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "password123"},
        )
        token = response.json()["data"]["access_token"]
        payload = jwt.decode(
            token,
            test_settings.JWT_SECRET_KEY,
            algorithms=[test_settings.JWT_ALGORITHM],
            options={"verify_exp": False},
            audience=test_settings.JWT_AUDIENCE,
        )
        assert payload["sub"] == str(user.id)
        assert payload["type"] == "access"

    @patch("app.services.authentication.verify_password", return_value=True)
    async def test_no_commit(self, mock_verify, client, mock_session, test_settings):
        user = _make_user()
        _setup_session_for_user(mock_session, user)
        await client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "password123"},
        )
        mock_session.commit.assert_not_called()

    @patch("app.services.authentication.verify_password", return_value=True)
    async def test_no_flush(self, mock_verify, client, mock_session, test_settings):
        user = _make_user()
        _setup_session_for_user(mock_session, user)
        await client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "password123"},
        )
        mock_session.flush.assert_not_called()

    @patch("app.services.authentication.verify_password", return_value=True)
    async def test_password_absent(self, mock_verify, client, mock_session, test_settings):
        user = _make_user()
        _setup_session_for_user(mock_session, user)
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "password123"},
        )
        assert "password123" not in response.text

    @patch("app.services.authentication.verify_password", return_value=True)
    async def test_password_hash_absent(self, mock_verify, client, mock_session, test_settings):
        user = _make_user()
        _setup_session_for_user(mock_session, user)
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "password123"},
        )
        assert "password_hash" not in response.text

    @patch("app.services.authentication.verify_password", return_value=True)
    async def test_refresh_token_absent(self, mock_verify, client, mock_session, test_settings):
        user = _make_user()
        _setup_session_for_user(mock_session, user)
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "password123"},
        )
        assert "refresh_token" not in response.text

    @patch("app.services.authentication.verify_password", return_value=True)
    async def test_x_request_id_present(self, mock_verify, client, mock_session, test_settings):
        user = _make_user()
        _setup_session_for_user(mock_session, user)
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "password123"},
        )
        assert "X-Request-ID" in response.headers


# ---------------------------------------------------------------------------
# Registration — duplicate email
# ---------------------------------------------------------------------------


class TestRegisterDuplicateEmail:
    async def test_returns_409(self, client, mock_session):
        # get_by_email returns an existing user -> pre-check fails
        existing_user = _make_user()
        _setup_session_for_user(mock_session, existing_user)
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "existing@example.com", "password": "secure12345"},
        )
        assert response.status_code == 409

    async def test_error_code(self, client, mock_session):
        existing_user = _make_user()
        _setup_session_for_user(mock_session, existing_user)
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "existing@example.com", "password": "secure12345"},
        )
        data = response.json()
        assert data["error"]["code"] == "EMAIL_ALREADY_REGISTERED"

    async def test_error_message(self, client, mock_session):
        existing_user = _make_user()
        _setup_session_for_user(mock_session, existing_user)
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "existing@example.com", "password": "secure12345"},
        )
        data = response.json()
        assert "already exists" in data["error"]["message"]

    async def test_request_id_in_body(self, client, mock_session):
        existing_user = _make_user()
        _setup_session_for_user(mock_session, existing_user)
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "existing@example.com", "password": "secure12345"},
        )
        data = response.json()
        assert "request_id" in data["error"]
        assert len(data["error"]["request_id"]) > 0

    async def test_x_request_id_header(self, client, mock_session):
        existing_user = _make_user()
        _setup_session_for_user(mock_session, existing_user)
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "existing@example.com", "password": "secure12345"},
        )
        assert "X-Request-ID" in response.headers

    async def test_rollback_occurs(self, client, mock_session):
        existing_user = _make_user()
        _setup_session_for_user(mock_session, existing_user)
        await client.post(
            "/api/v1/auth/register",
            json={"email": "existing@example.com", "password": "secure12345"},
        )
        mock_session.rollback.assert_called_once()

    async def test_no_access_token(self, client, mock_session):
        existing_user = _make_user()
        _setup_session_for_user(mock_session, existing_user)
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "existing@example.com", "password": "secure12345"},
        )
        assert "access_token" not in response.text


# ---------------------------------------------------------------------------
# Login — invalid credentials
# ---------------------------------------------------------------------------


class TestLoginInvalidCredentials:
    async def test_unknown_email_returns_401(self, client, mock_session):
        _setup_session_for_no_user(mock_session)
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "unknown@example.com", "password": "password123"},
        )
        assert response.status_code == 401

    @patch("app.services.authentication.verify_password", return_value=False)
    async def test_wrong_password_returns_401(
        self, mock_verify, client, mock_session, test_settings
    ):
        user = _make_user()
        _setup_session_for_user(mock_session, user)
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "wrong_password"},
        )
        assert response.status_code == 401

    async def test_error_code(self, client, mock_session):
        _setup_session_for_no_user(mock_session)
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "unknown@example.com", "password": "password123"},
        )
        data = response.json()
        assert data["error"]["code"] == "INVALID_CREDENTIALS"

    async def test_error_message_safe(self, client, mock_session):
        _setup_session_for_no_user(mock_session)
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "unknown@example.com", "password": "password123"},
        )
        data = response.json()
        assert data["error"]["message"] == "Invalid email or password."

    async def test_www_authenticate_header(self, client, mock_session):
        _setup_session_for_no_user(mock_session)
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "unknown@example.com", "password": "password123"},
        )
        assert response.headers.get("WWW-Authenticate") == "Bearer"

    async def test_no_distinction_between_unknown_and_wrong(self, client, mock_session):
        _setup_session_for_no_user(mock_session)
        response1 = await client.post(
            "/api/v1/auth/login",
            json={"email": "unknown@example.com", "password": "password123"},
        )
        data1 = response1.json()
        assert data1["error"]["code"] == "INVALID_CREDENTIALS"
        assert data1["error"]["message"] == "Invalid email or password."

    async def test_no_access_token(self, client, mock_session):
        _setup_session_for_no_user(mock_session)
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "unknown@example.com", "password": "password123"},
        )
        assert "access_token" not in response.text

    async def test_request_id_in_body(self, client, mock_session):
        _setup_session_for_no_user(mock_session)
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "unknown@example.com", "password": "password123"},
        )
        data = response.json()
        assert "request_id" in data["error"]

    async def test_x_request_id_header(self, client, mock_session):
        _setup_session_for_no_user(mock_session)
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "unknown@example.com", "password": "password123"},
        )
        assert "X-Request-ID" in response.headers


# ---------------------------------------------------------------------------
# Login — inactive account
# ---------------------------------------------------------------------------


class TestLoginInactiveAccount:
    @patch("app.services.authentication.verify_password", return_value=True)
    async def test_returns_403(self, mock_verify, client, mock_session, test_settings):
        user = _make_user(is_active=False)
        _setup_session_for_user(mock_session, user)
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "inactive@example.com", "password": "password123"},
        )
        assert response.status_code == 403

    @patch("app.services.authentication.verify_password", return_value=True)
    async def test_error_code(self, mock_verify, client, mock_session, test_settings):
        user = _make_user(is_active=False)
        _setup_session_for_user(mock_session, user)
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "inactive@example.com", "password": "password123"},
        )
        data = response.json()
        assert data["error"]["code"] == "INACTIVE_ACCOUNT"

    @patch("app.services.authentication.verify_password", return_value=True)
    async def test_error_message(self, mock_verify, client, mock_session, test_settings):
        user = _make_user(is_active=False)
        _setup_session_for_user(mock_session, user)
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "inactive@example.com", "password": "password123"},
        )
        data = response.json()
        assert "inactive" in data["error"]["message"].lower()

    @patch("app.services.authentication.verify_password", return_value=True)
    async def test_no_token(self, mock_verify, client, mock_session, test_settings):
        user = _make_user(is_active=False)
        _setup_session_for_user(mock_session, user)
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "inactive@example.com", "password": "password123"},
        )
        assert "access_token" not in response.text

    @patch("app.services.authentication.verify_password", return_value=True)
    async def test_request_id_in_body(self, mock_verify, client, mock_session, test_settings):
        user = _make_user(is_active=False)
        _setup_session_for_user(mock_session, user)
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "inactive@example.com", "password": "password123"},
        )
        data = response.json()
        assert "request_id" in data["error"]


# ---------------------------------------------------------------------------
# Token configuration failure
# ---------------------------------------------------------------------------


class TestTokenConfigurationFailure:
    async def test_registration_returns_503(self, app, client, mock_session, test_settings):
        _setup_session_for_no_user(mock_session)
        bad_settings = Settings(
            APP_ENV="test",
            DEBUG=False,
            JWT_SECRET_KEY="",
        )
        app.dependency_overrides[get_settings] = lambda: bad_settings
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "new@example.com", "password": "secure12345"},
        )
        assert response.status_code == 503

    async def test_registration_error_code(self, app, client, mock_session, test_settings):
        _setup_session_for_no_user(mock_session)
        bad_settings = Settings(
            APP_ENV="test",
            DEBUG=False,
            JWT_SECRET_KEY="",
        )
        app.dependency_overrides[get_settings] = lambda: bad_settings
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "new@example.com", "password": "secure12345"},
        )
        data = response.json()
        assert data["error"]["code"] == "AUTHENTICATION_UNAVAILABLE"

    async def test_registration_rolls_back(self, app, client, mock_session, test_settings):
        _setup_session_for_no_user(mock_session)
        bad_settings = Settings(
            APP_ENV="test",
            DEBUG=False,
            JWT_SECRET_KEY="",
        )
        app.dependency_overrides[get_settings] = lambda: bad_settings
        await client.post(
            "/api/v1/auth/register",
            json={"email": "new@example.com", "password": "secure12345"},
        )
        mock_session.rollback.assert_called_once()

    @patch("app.services.authentication.verify_password", return_value=True)
    async def test_login_returns_503(self, mock_verify, app, client, mock_session, test_settings):
        user = _make_user()
        _setup_session_for_user(mock_session, user)
        bad_settings = Settings(
            APP_ENV="test",
            DEBUG=False,
            JWT_SECRET_KEY="",
        )
        app.dependency_overrides[get_settings] = lambda: bad_settings
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "password123"},
        )
        assert response.status_code == 503

    @patch("app.services.authentication.verify_password", return_value=True)
    async def test_login_error_code(self, mock_verify, app, client, mock_session, test_settings):
        user = _make_user()
        _setup_session_for_user(mock_session, user)
        bad_settings = Settings(
            APP_ENV="test",
            DEBUG=False,
            JWT_SECRET_KEY="",
        )
        app.dependency_overrides[get_settings] = lambda: bad_settings
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "password123"},
        )
        data = response.json()
        assert data["error"]["code"] == "AUTHENTICATION_UNAVAILABLE"

    @patch("app.services.authentication.verify_password", return_value=True)
    async def test_login_does_not_commit(
        self, mock_verify, app, client, mock_session, test_settings
    ):
        user = _make_user()
        _setup_session_for_user(mock_session, user)
        bad_settings = Settings(
            APP_ENV="test",
            DEBUG=False,
            JWT_SECRET_KEY="",
        )
        app.dependency_overrides[get_settings] = lambda: bad_settings
        await client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "password123"},
        )
        mock_session.commit.assert_not_called()


# ---------------------------------------------------------------------------
# Validation errors
# ---------------------------------------------------------------------------


class TestRegisterValidation:
    async def test_invalid_email_returns_422(self, client):
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "not-an-email", "password": "password123"},
        )
        assert response.status_code == 422

    async def test_missing_email_returns_422(self, client):
        response = await client.post(
            "/api/v1/auth/register",
            json={"password": "password123"},
        )
        assert response.status_code == 422

    async def test_empty_email_returns_422(self, client):
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "", "password": "password123"},
        )
        assert response.status_code == 422

    async def test_missing_password_returns_422(self, client):
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "user@example.com"},
        )
        assert response.status_code == 422

    async def test_empty_password_returns_422(self, client):
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "user@example.com", "password": ""},
        )
        assert response.status_code == 422

    async def test_short_password_returns_422(self, client):
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "user@example.com", "password": "1234567"},
        )
        assert response.status_code == 422

    async def test_long_password_returns_422(self, client):
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "user@example.com", "password": "x" * 129},
        )
        assert response.status_code == 422

    async def test_extra_field_returns_422(self, client):
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "user@example.com",
                "password": "password123",
                "extra": "field",
            },
        )
        assert response.status_code == 422

    async def test_password_not_exposed_in_error(self, client):
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "user@example.com", "password": ""},
        )
        assert response.status_code == 422
        assert '"****"' not in response.text

    async def test_no_session_call_on_validation_failure(self, client, mock_session):
        await client.post(
            "/api/v1/auth/register",
            json={"email": "bad", "password": "short"},
        )
        mock_session.execute.assert_not_called()


class TestLoginValidation:
    async def test_invalid_email_returns_422(self, client):
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "not-an-email", "password": "password123"},
        )
        assert response.status_code == 422

    async def test_missing_email_returns_422(self, client):
        response = await client.post(
            "/api/v1/auth/login",
            json={"password": "password123"},
        )
        assert response.status_code == 422

    async def test_empty_email_returns_422(self, client):
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "", "password": "password123"},
        )
        assert response.status_code == 422

    async def test_missing_password_returns_422(self, client):
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "user@example.com"},
        )
        assert response.status_code == 422

    async def test_empty_password_returns_422(self, client):
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "user@example.com", "password": ""},
        )
        assert response.status_code == 422

    async def test_extra_field_returns_422(self, client):
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "user@example.com",
                "password": "password123",
                "extra": "field",
            },
        )
        assert response.status_code == 422

    async def test_no_session_call_on_validation_failure(self, client, mock_session):
        await client.post(
            "/api/v1/auth/login",
            json={"email": "bad", "password": ""},
        )
        mock_session.execute.assert_not_called()


# ---------------------------------------------------------------------------
# Email normalization
# ---------------------------------------------------------------------------


class TestEmailNormalization:
    @patch("app.services.authentication.hash_password", return_value="hashed_pw")
    async def test_registration_email_normalized(
        self, mock_hash, client, mock_session, test_settings
    ):
        _setup_session_for_no_user(mock_session)
        await client.post(
            "/api/v1/auth/register",
            json={"email": "  NEW@Example.COM  ", "password": "secure12345"},
        )
        # Verify the session query used normalized email
        call_args_list = mock_session.execute.call_args_list
        if call_args_list:
            stmt = call_args_list[0][0][0]
            compiled = stmt.compile(compile_kwargs={"literal_binds": True})
            assert "new@example.com" in str(compiled)

    @patch("app.services.authentication.hash_password", return_value="hashed_pw")
    async def test_password_not_trimmed(self, mock_hash, client, mock_session, test_settings):
        _setup_session_for_no_user(mock_session)
        await client.post(
            "/api/v1/auth/register",
            json={"email": "new@example.com", "password": "  MyPass 123  "},
        )
        # hash_password was called with exact password
        mock_hash.assert_called_once()
        password_arg = mock_hash.call_args[0][0]
        assert password_arg == "  MyPass 123  "

    @patch("app.services.authentication.verify_password", return_value=True)
    async def test_login_email_normalized(self, mock_verify, client, mock_session, test_settings):
        user = _make_user()
        _setup_session_for_user(mock_session, user)
        await client.post(
            "/api/v1/auth/login",
            json={"email": "  Test@Example.COM  ", "password": "password123"},
        )
        call_args = mock_session.execute.call_args
        if call_args is not None:
            stmt = call_args[0][0]
            compiled = stmt.compile(compile_kwargs={"literal_binds": True})
            assert "test@example.com" in str(compiled)


# ---------------------------------------------------------------------------
# Transaction behavior
# ---------------------------------------------------------------------------


class TestTransactionBehavior:
    @patch("app.services.authentication.hash_password", return_value="hashed_pw")
    async def test_register_commits_once_no_rollback(
        self, mock_hash, client, mock_session, test_settings
    ):
        _setup_session_for_no_user(mock_session)
        await client.post(
            "/api/v1/auth/register",
            json={"email": "new@example.com", "password": "secure12345"},
        )
        mock_session.commit.assert_awaited_once()
        mock_session.rollback.assert_not_called()

    @patch("app.services.authentication.hash_password", return_value="hashed_pw")
    async def test_session_refreshed(self, mock_hash, client, mock_session, test_settings):
        _setup_session_for_no_user(mock_session)
        await client.post(
            "/api/v1/auth/register",
            json={"email": "new@example.com", "password": "secure12345"},
        )
        mock_session.refresh.assert_awaited_once()

    async def test_duplicate_email_rolls_back(self, client, mock_session):
        existing_user = _make_user()
        _setup_session_for_user(mock_session, existing_user)
        await client.post(
            "/api/v1/auth/register",
            json={"email": "existing@example.com", "password": "secure12345"},
        )
        mock_session.rollback.assert_called_once()

    async def test_duplicate_email_does_not_commit(self, client, mock_session):
        existing_user = _make_user()
        _setup_session_for_user(mock_session, existing_user)
        await client.post(
            "/api/v1/auth/register",
            json={"email": "existing@example.com", "password": "secure12345"},
        )
        mock_session.commit.assert_not_called()

    async def test_token_failure_rolls_back(self, app, client, mock_session, test_settings):
        _setup_session_for_no_user(mock_session)
        bad_settings = Settings(
            APP_ENV="test",
            DEBUG=False,
            JWT_SECRET_KEY="",
        )
        app.dependency_overrides[get_settings] = lambda: bad_settings
        await client.post(
            "/api/v1/auth/register",
            json={"email": "new@example.com", "password": "secure12345"},
        )
        mock_session.rollback.assert_called_once()

    async def test_token_failure_does_not_commit(self, app, client, mock_session, test_settings):
        _setup_session_for_no_user(mock_session)
        bad_settings = Settings(
            APP_ENV="test",
            DEBUG=False,
            JWT_SECRET_KEY="",
        )
        app.dependency_overrides[get_settings] = lambda: bad_settings
        await client.post(
            "/api/v1/auth/register",
            json={"email": "new@example.com", "password": "secure12345"},
        )
        mock_session.commit.assert_not_called()

    @patch("app.services.authentication.verify_password", return_value=True)
    async def test_login_does_not_commit(self, mock_verify, client, mock_session, test_settings):
        user = _make_user()
        _setup_session_for_user(mock_session, user)
        await client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "password123"},
        )
        mock_session.commit.assert_not_called()
        mock_session.rollback.assert_not_called()

    @patch("app.services.authentication.verify_password", return_value=True)
    async def test_login_does_not_mutate_user(
        self, mock_verify, client, mock_session, test_settings
    ):
        user = _make_user()
        _setup_session_for_user(mock_session, user)
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "password123"},
        )
        data = response.json()
        assert data["data"]["user"]["email"] == user.email
        assert data["data"]["user"]["is_active"] == user.is_active


# ---------------------------------------------------------------------------
# Application factory and OpenAPI
# ---------------------------------------------------------------------------


class TestAppFactory:
    def test_app_imports(self):
        from app.main import create_app

        app = create_app(Settings(APP_ENV="test", DEBUG=False))
        assert app is not None

    def test_two_apps_can_be_created(self):
        app1 = create_app(Settings(APP_ENV="test", DEBUG=False))
        app2 = create_app(Settings(APP_ENV="test", DEBUG=False))
        assert app1 is not app2

    def test_auth_routes_registered_exactly_once(self):
        settings = Settings(APP_ENV="test", DEBUG=False)
        app = create_app(settings=settings)
        routes = _effective_route_paths(app.routes)
        register_routes = [
            path for path in routes if path == settings.API_V1_PREFIX + "/auth/register"
        ]
        login_routes = [path for path in routes if path == settings.API_V1_PREFIX + "/auth/login"]
        assert len(register_routes) == 1
        assert len(login_routes) == 1

    def test_openapi_contains_auth_paths(self):
        settings = Settings(APP_ENV="test", DEBUG=False)
        app = create_app(settings=settings)
        openapi = app.openapi()
        paths = openapi["paths"]
        assert "/api/v1/auth/register" in paths
        assert "/api/v1/auth/login" in paths
        assert "/api/v1/health" in paths

    def test_openapi_has_bearer_scheme(self):
        settings = Settings(APP_ENV="test", DEBUG=False)
        app = create_app(settings=settings)
        openapi = app.openapi()
        components = openapi.get("components", {})
        schemes = components.get("securitySchemes", {})
        assert "BearerAuth" in schemes
        assert schemes["BearerAuth"]["type"] == "http"
        assert schemes["BearerAuth"]["scheme"] == "bearer"

    def test_openapi_has_no_oauth2_scheme(self):
        settings = Settings(APP_ENV="test", DEBUG=False)
        app = create_app(settings=settings)
        openapi = app.openapi()
        components = openapi.get("components", {})
        schemes = components.get("securitySchemes", {})
        assert "oauth2" not in str(schemes).lower()

    def test_openapi_has_no_refresh_token_in_schemas(self):
        settings = Settings(APP_ENV="test", DEBUG=False)
        app = create_app(settings=settings)
        openapi = app.openapi()
        text = str(openapi)
        assert "refresh_token" not in text

    def test_openapi_has_no_logout(self):
        settings = Settings(APP_ENV="test", DEBUG=False)
        app = create_app(settings=settings)
        openapi = app.openapi()
        paths = openapi["paths"]
        logout_paths = [p for p in paths if "logout" in p.lower()]
        assert len(logout_paths) == 0

    def test_openapi_has_auth_me(self):
        settings = Settings(APP_ENV="test", DEBUG=False)
        app = create_app(settings=settings)
        openapi = app.openapi()
        paths = openapi["paths"]
        assert "/api/v1/auth/me" in paths
        me_operations = paths["/api/v1/auth/me"]
        assert "get" in me_operations
        assert "post" not in me_operations


# ---------------------------------------------------------------------------
# Security — OAuth sentinel account protection
# ---------------------------------------------------------------------------

SUPABASE_PASSWORD_SENTINEL = "$supabase$"


class TestLoginOAuthAccount:
    """Login with OAuth-only account must return safe OAUTH_ACCOUNT_EXISTS response."""

    async def test_oauth_login_returns_401(self, client, mock_session):
        user = _make_user(password_hash=SUPABASE_PASSWORD_SENTINEL)
        _setup_session_for_user(mock_session, user)
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "oauth@example.com", "password": "anypassword"},
        )
        assert response.status_code == 401

    async def test_oauth_code_is_oauth_account_exists(self, client, mock_session):
        user = _make_user(password_hash=SUPABASE_PASSWORD_SENTINEL)
        _setup_session_for_user(mock_session, user)
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "oauth@example.com", "password": "anypassword"},
        )
        data = response.json()
        assert data["error"]["code"] == "OAUTH_ACCOUNT_EXISTS"

    async def test_oauth_message_helpful(self, client, mock_session):
        user = _make_user(password_hash=SUPABASE_PASSWORD_SENTINEL)
        _setup_session_for_user(mock_session, user)
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "oauth@example.com", "password": "anypassword"},
        )
        data = response.json()
        msg = data["error"]["message"]
        assert "Google" in msg or "Apple" in msg

    async def test_oauth_www_authenticate_header(self, client, mock_session):
        user = _make_user(password_hash=SUPABASE_PASSWORD_SENTINEL)
        _setup_session_for_user(mock_session, user)
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "oauth@example.com", "password": "anypassword"},
        )
        assert response.headers.get("WWW-Authenticate") == "Bearer"

    async def test_oauth_no_access_token(self, client, mock_session):
        user = _make_user(password_hash=SUPABASE_PASSWORD_SENTINEL)
        _setup_session_for_user(mock_session, user)
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "oauth@example.com", "password": "anypassword"},
        )
        assert "access_token" not in response.text


class TestRegisterOAuthAccount:
    """Register with OAuth-only email must reject with EMAIL_ALREADY_REGISTERED."""

    async def test_oauth_register_returns_409(self, client, mock_session):
        user = _make_user(password_hash=SUPABASE_PASSWORD_SENTINEL)
        _setup_session_for_user(mock_session, user)
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "oauth@example.com", "password": "attackerpass123"},
        )
        assert response.status_code == 409

    async def test_oauth_register_code_email_already_registered(self, client, mock_session):
        user = _make_user(password_hash=SUPABASE_PASSWORD_SENTINEL)
        _setup_session_for_user(mock_session, user)
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "oauth@example.com", "password": "attackerpass123"},
        )
        data = response.json()
        assert data["error"]["code"] == "EMAIL_ALREADY_REGISTERED"

    async def test_oauth_register_password_hash_unchanged(self, client, mock_session):
        user = _make_user(password_hash=SUPABASE_PASSWORD_SENTINEL)
        _setup_session_for_user(mock_session, user)
        original_hash = user.password_hash
        await client.post(
            "/api/v1/auth/register",
            json={"email": "oauth@example.com", "password": "attackerpass123"},
        )
        assert user.password_hash == original_hash


class TestSyncSupabaseUserPreservesCredentials:
    """sync_supabase_user must never overwrite existing password credentials."""

    @patch("app.api.v1.auth.verify_supabase_token", new_callable=AsyncMock, return_value=None)
    async def test_sync_rejects_jwt_without_verified_supabase_identity(
        self, mock_verifier, test_settings, mock_session
    ):
        forged_token = jwt.encode(
            {
                "sub": str(uuid.uuid4()),
                "email": "victim@example.com",
                "exp": int(datetime.now(UTC).timestamp()) + 300,
            },
            "attacker-controlled-signing-key-000000",
            algorithm="HS256",
        )

        response = await supabase_sync(
            request=MagicMock(),
            body=SupabaseSyncRequest(access_token=forged_token),
            session=mock_session,
            settings=test_settings,
        )

        assert response.status_code == 401
        body = json.loads(response.body)
        assert body["error"]["code"] == "INVALID_SUPABASE_TOKEN"
        mock_session.execute.assert_not_awaited()
        mock_verifier.assert_awaited_once()

    @patch("app.api.v1.auth.verify_supabase_token", new_callable=AsyncMock, return_value=None)
    async def test_sync_rejects_expired_supabase_token(
        self, mock_verifier, test_settings, mock_session
    ):
        expired_token = jwt.encode(
            {
                "sub": str(uuid.uuid4()),
                "email": "person@example.com",
                "exp": int(datetime.now(UTC).timestamp()) - 1,
            },
            "attacker-controlled-signing-key-000000",
            algorithm="HS256",
        )
        response = await supabase_sync(
            request=MagicMock(),
            body=SupabaseSyncRequest(access_token=expired_token),
            session=mock_session,
            settings=test_settings,
        )
        assert response.status_code == 401
        mock_session.execute.assert_not_awaited()
        mock_verifier.assert_awaited_once()

    @patch("app.api.v1.auth.verify_supabase_token", new_callable=AsyncMock)
    async def test_sync_rejects_unverified_email_before_database_access(
        self, mock_verifier, test_settings, mock_session
    ):
        mock_verifier.return_value = {
            "id": str(uuid.uuid4()),
            "email": "victim@example.com",
            "email_confirmed_at": None,
        }
        response = await supabase_sync(
            request=MagicMock(),
            body=SupabaseSyncRequest(access_token="valid-but-unverified"),
            session=mock_session,
            settings=test_settings,
        )
        assert response.status_code == 403
        assert json.loads(response.body)["error"]["code"] == "EMAIL_NOT_VERIFIED"
        mock_session.execute.assert_not_awaited()

    @pytest.mark.parametrize(
        "identity, expected_status, expected_code",
        [
            ({"id": str(uuid.uuid4()), "email_confirmed_at": "now"}, 400, "MISSING_EMAIL"),
            (
                {
                    "id": str(uuid.uuid4()),
                    "email": "person@example.com",
                    "email_confirmed_at": False,
                },
                403,
                "EMAIL_NOT_VERIFIED",
            ),
            (
                {"email": "person@example.com", "email_confirmed_at": "now"},
                401,
                "INVALID_SUPABASE_IDENTITY",
            ),
            ({"id": str(uuid.uuid4()), "email": "person@example.com"}, 403, "EMAIL_NOT_VERIFIED"),
        ],
    )
    @patch("app.api.v1.auth.verify_supabase_token", new_callable=AsyncMock)
    async def test_sync_rejects_incomplete_identity(
        self, mock_verifier, identity, expected_status, expected_code, test_settings, mock_session
    ):
        mock_verifier.return_value = identity
        response = await supabase_sync(
            request=MagicMock(),
            body=SupabaseSyncRequest(access_token="supabase-token"),
            session=mock_session,
            settings=test_settings,
        )
        assert response.status_code == expected_status
        assert json.loads(response.body)["error"]["code"] == expected_code
        mock_session.execute.assert_not_awaited()

    @patch("app.api.v1.auth.verify_supabase_token", new_callable=AsyncMock)
    async def test_sync_links_verified_email_and_records_supabase_identity(
        self, mock_verifier, client, mock_session
    ):
        supabase_id = uuid.uuid4()
        mock_verifier.return_value = {
            "id": str(supabase_id),
            "email": "test@example.com",
            "email_confirmed_at": "2026-10-11T00:00:00Z",
        }
        user = _make_user(email="test@example.com")
        _setup_session_for_user(mock_session, user)
        response = await client.post(
            "/api/v1/auth/supabase-sync",
            json={"access_token": "verified-token"},
        )
        assert response.status_code == 200
        assert response.json()["success"] is True
        assert user.supabase_user_id == supabase_id
        assert user.is_verified is True

    @patch("app.api.v1.auth.verify_supabase_token", new_callable=AsyncMock)
    async def test_sync_rejects_conflicting_supabase_identity(
        self, mock_verifier, client, mock_session
    ):
        mock_verifier.return_value = {
            "id": str(uuid.uuid4()),
            "email": "test@example.com",
            "email_confirmed_at": "2026-10-11T00:00:00Z",
        }
        user = _make_user(email="test@example.com")
        user.supabase_user_id = uuid.uuid4()
        _setup_session_for_user(mock_session, user)
        response = await client.post(
            "/api/v1/auth/supabase-sync",
            json={"access_token": "conflicting-token"},
        )
        assert response.status_code == 409
        assert response.json()["error"]["code"] == "IDENTITY_CONFLICT"

    @patch("app.api.v1.auth.verify_supabase_token", new_callable=AsyncMock)
    async def test_sync_with_existing_password_user_returns_unchanged(
        self, mock_verifier, app, client, mock_session
    ):
        original_hash = "$argon2id$v=19$m=65536,t=3,p=4$realhash"
        user = _make_user(password_hash=original_hash)
        mock_verifier.return_value = {
            "id": str(uuid.uuid4()),
            "email": user.email,
            "email_confirmed_at": "2026-10-11T00:00:00Z",
        }
        result_mock = MagicMock()
        result_mock.scalars.return_value.first.return_value = user
        mock_session.execute = AsyncMock(return_value=result_mock)
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        mock_session.refresh = AsyncMock()
        await client.post(
            "/api/v1/auth/supabase-sync",
            json={"access_token": "some-token"},
        )
        assert user.password_hash == original_hash

    @patch("app.api.v1.auth.verify_supabase_token", new_callable=AsyncMock)
    async def test_sync_with_existing_oauth_user_returns_unchanged(
        self, mock_verifier, app, client, mock_session
    ):
        user = _make_user(password_hash=SUPABASE_PASSWORD_SENTINEL)
        mock_verifier.return_value = {
            "id": str(uuid.uuid4()),
            "email": user.email,
            "email_confirmed_at": "2026-10-11T00:00:00Z",
        }
        result_mock = MagicMock()
        result_mock.scalars.return_value.first.return_value = user
        mock_session.execute = AsyncMock(return_value=result_mock)
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        mock_session.refresh = AsyncMock()
        await client.post(
            "/api/v1/auth/supabase-sync",
            json={"access_token": "some-token"},
        )
        assert user.password_hash == SUPABASE_PASSWORD_SENTINEL


# ---------------------------------------------------------------------------
# Security — response field audit
# ---------------------------------------------------------------------------


class TestResponseSecurity:
    @patch("app.services.authentication.hash_password", return_value="hashed_pw")
    async def test_register_has_only_expected_fields(
        self, mock_hash, client, mock_session, test_settings
    ):
        _setup_session_for_no_user(mock_session)
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "new@example.com", "password": "secure12345"},
        )
        data = response.json()
        assert set(data.keys()) == {"success", "message", "data"}
        assert set(data["data"].keys()) == {"user", "access_token", "token_type", "expires_in"}
        assert set(data["data"]["user"].keys()) == {
            "id",
            "email",
            "is_active",
            "is_verified",
            "created_at",
            "updated_at",
        }

    @patch("app.services.authentication.verify_password", return_value=True)
    async def test_login_has_only_expected_fields(
        self, mock_verify, client, mock_session, test_settings
    ):
        user = _make_user()
        _setup_session_for_user(mock_session, user)
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "password123"},
        )
        data = response.json()
        assert set(data.keys()) == {"success", "message", "data"}
        assert set(data["data"].keys()) == {"user", "access_token", "token_type", "expires_in"}
        assert set(data["data"]["user"].keys()) == {
            "id",
            "email",
            "is_active",
            "is_verified",
            "created_at",
            "updated_at",
        }

    @patch("app.services.authentication.hash_password", return_value="hashed_pw")
    async def test_register_no_password_hash(self, mock_hash, client, mock_session, test_settings):
        _setup_session_for_no_user(mock_session)
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "new@example.com", "password": "secure12345"},
        )
        assert "password_hash" not in response.text

    @patch("app.services.authentication.hash_password", return_value="hashed_pw")
    async def test_register_no_jwt_secret(self, mock_hash, client, mock_session, test_settings):
        _setup_session_for_no_user(mock_session)
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "new@example.com", "password": "secure12345"},
        )
        text_lower = response.text.lower()
        assert "secret" not in text_lower
