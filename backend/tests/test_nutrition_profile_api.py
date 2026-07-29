from __future__ import annotations

import json
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
from app.models.enums import ActivityLevel, BiologicalSex, NutritionGoal
from app.models.nutrition_profile import NutritionProfile
from app.models.user import User

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

NOW = datetime.now(UTC)


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


def _make_profile(user_id: uuid.UUID | None = None) -> MagicMock:
    profile = MagicMock(spec=NutritionProfile)
    profile.id = uuid.uuid4()
    profile.user_id = user_id or uuid.uuid4()
    profile.date_of_birth = date(1990, 1, 1)
    profile.biological_sex = BiologicalSex.MALE
    profile.height_cm = Decimal("175.00")
    profile.weight_kg = Decimal("70.00")
    profile.activity_level = ActivityLevel.MODERATELY_ACTIVE
    profile.goal = NutritionGoal.MAINTAIN_WEIGHT
    profile.target_weight_kg = None
    profile.dietary_preference = None
    profile.allergies = []
    profile.full_name = None
    profile.phone = None
    profile.avatar_url = None
    profile.fitness_goal = None
    profile.medical_conditions = []
    profile.water_goal_ml = None
    profile.sleep_goal_hours = None
    profile.daily_calorie_goal = None
    profile.daily_protein_goal_g = None
    profile.daily_carb_goal_g = None
    profile.daily_fat_goal_g = None
    profile.created_at = NOW
    profile.updated_at = NOW
    return profile


def _make_execute_result(value: MagicMock | None) -> MagicMock:
    """Create a mock that mimics session.execute() returning a scalars chain."""
    result = MagicMock()
    result.scalars.return_value.one_or_none.return_value = value
    return result


def _setup_session_auth_only(session: AsyncMock, user: MagicMock | None) -> None:
    """Set up session so get_current_user (first execute) returns the user."""
    session.execute = AsyncMock(return_value=_make_execute_result(user))
    session.commit = AsyncMock()
    session.flush = AsyncMock()
    session.rollback = AsyncMock()


def _setup_session_with_profile(
    session: AsyncMock,
    user: MagicMock,
    profile: MagicMock | None,
) -> None:
    """Set up session so:
    1st execute (get_current_user) returns user,
    2nd execute (profile lookup) returns profile.
    """
    session.execute = AsyncMock(
        side_effect=[
            _make_execute_result(user),
            _make_execute_result(profile),
        ]
    )
    session.commit = AsyncMock()
    session.flush = AsyncMock()
    session.rollback = AsyncMock()


def _setup_session_for_create(
    session: AsyncMock,
    user: MagicMock,
) -> None:
    """Set up session for successful create: user lookup returns user,
    profile lookup returns None, then add/flush/commit/refresh are used."""
    session.execute = AsyncMock(
        side_effect=[
            _make_execute_result(user),  # auth user lookup
            _make_execute_result(None),  # get_or_create lookup
            _make_execute_result(None),  # create_profile lookup
            _make_execute_result(None),  # extra
        ]
    )
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()

    async def _refresh_side_effect(obj, *args, **kwargs):
        if obj.id is None:
            obj.id = uuid.uuid4()
        obj.created_at = NOW
        obj.updated_at = NOW

    session.refresh = AsyncMock(side_effect=_refresh_side_effect)
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
# Valid profile data
# ---------------------------------------------------------------------------

_VALID_CREATE = {
    "date_of_birth": "1990-01-01",
    "biological_sex": "male",
    "height_cm": "175.00",
    "weight_kg": "70.00",
    "activity_level": "moderately_active",
    "goal": "maintain_weight",
    "target_weight_kg": None,
    "dietary_preference": None,
    "allergies": [],
}

_VALID_UPDATE = {
    "date_of_birth": "1995-06-15",
    "biological_sex": "female",
    "height_cm": "165.00",
    "weight_kg": "60.00",
    "activity_level": "lightly_active",
    "goal": "lose_weight",
    "dietary_preference": "vegan",
    "allergies": ["peanuts"],
}

# ===========================================================================
# PART 1 — Route Registration
# ===========================================================================


class TestRouteRegistration:
    async def test_post_route_exists(self, client):
        response = await client.post("/api/v1/nutrition-profile", json=_VALID_CREATE)
        assert response.status_code != 404

    async def test_get_route_exists(self, client):
        response = await client.get("/api/v1/nutrition-profile")
        assert response.status_code != 404

    async def test_patch_route_exists(self, client):
        response = await client.patch("/api/v1/nutrition-profile", json={})
        assert response.status_code != 404

    async def test_post_accepts_post(self, client):
        response = await client.post("/api/v1/nutrition-profile", json=_VALID_CREATE)
        assert response.status_code != 405

    async def test_get_accepts_get(self, client):
        response = await client.get("/api/v1/nutrition-profile")
        assert response.status_code != 405

    async def test_patch_accepts_patch(self, client):
        response = await client.patch("/api/v1/nutrition-profile", json={})
        assert response.status_code != 405

    async def test_get_rejects_put(self, client):
        response = await client.put("/api/v1/nutrition-profile")
        assert response.status_code == 405

    async def test_post_rejects_put(self, client):
        response = await client.put("/api/v1/nutrition-profile", json=_VALID_CREATE)
        assert response.status_code == 405

    async def test_patch_rejects_put(self, client):
        response = await client.put("/api/v1/nutrition-profile", json=_VALID_UPDATE)
        assert response.status_code == 405

    async def test_get_rejects_delete(self, client):
        response = await client.delete("/api/v1/nutrition-profile")
        assert response.status_code == 405

    async def test_post_rejects_delete(self, client):
        response = await client.delete("/api/v1/nutrition-profile")
        assert response.status_code == 405

    async def test_patch_rejects_delete(self, client):
        response = await client.delete("/api/v1/nutrition-profile")
        assert response.status_code == 405

    async def test_no_user_id_route(self, client):
        response = await client.get("/api/v1/nutrition-profile/me")
        assert response.status_code == 404

    async def test_no_profile_id_route(self, client):
        some_id = str(uuid.uuid4())
        response = await client.get(f"/api/v1/nutrition-profile/{some_id}")
        assert response.status_code == 404

    async def test_no_users_user_id_route(self, client):
        some_id = str(uuid.uuid4())
        response = await client.get(f"/api/v1/users/{some_id}/nutrition-profile")
        assert response.status_code == 404

    async def test_no_profiles_route(self, client):
        response = await client.get("/api/v1/profiles")
        assert response.status_code == 404

    async def test_no_duplicate_routes(self, app):
        paths = [r.path for r in app.routes if "nutrition-profile" in r.path]
        assert paths.count("/api/v1/nutrition-profile") == 3
        assert "/api/v1/nutrition-profile/calculations" in paths


# ===========================================================================
# PART 2 — Authentication (POST, GET, PATCH)
# ===========================================================================


class TestAuthMissingHeader:
    async def test_post_returns_401(self, client):
        response = await client.post("/api/v1/nutrition-profile", json=_VALID_CREATE)
        assert response.status_code == 401

    async def test_get_returns_401(self, client):
        response = await client.get("/api/v1/nutrition-profile")
        assert response.status_code == 401

    async def test_patch_returns_401(self, client):
        response = await client.patch("/api/v1/nutrition-profile", json={})
        assert response.status_code == 401

    async def test_post_safe_envelope(self, client):
        response = await client.post("/api/v1/nutrition-profile", json=_VALID_CREATE)
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "AUTHENTICATION_REQUIRED"
        assert data["error"]["message"] == "Authentication is required."
        assert "request_id" in data["error"]

    async def test_get_safe_envelope(self, client):
        response = await client.get("/api/v1/nutrition-profile")
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "AUTHENTICATION_REQUIRED"

    async def test_patch_safe_envelope(self, client):
        response = await client.patch("/api/v1/nutrition-profile", json={})
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "AUTHENTICATION_REQUIRED"

    async def test_post_www_authenticate(self, client):
        response = await client.post("/api/v1/nutrition-profile", json=_VALID_CREATE)
        assert response.headers.get("WWW-Authenticate") == "Bearer"

    async def test_get_www_authenticate(self, client):
        response = await client.get("/api/v1/nutrition-profile")
        assert response.headers.get("WWW-Authenticate") == "Bearer"

    async def test_patch_www_authenticate(self, client):
        response = await client.patch("/api/v1/nutrition-profile", json={})
        assert response.headers.get("WWW-Authenticate") == "Bearer"

    async def test_post_no_detail_field(self, client):
        response = await client.post("/api/v1/nutrition-profile", json=_VALID_CREATE)
        assert '"detail"' not in response.text

    async def test_get_no_detail_field(self, client):
        response = await client.get("/api/v1/nutrition-profile")
        assert '"detail"' not in response.text

    async def test_patch_no_detail_field(self, client):
        response = await client.patch("/api/v1/nutrition-profile", json={})
        assert '"detail"' not in response.text

    async def test_post_bearer_prefix_missing(self, client):
        response = await client.post(
            "/api/v1/nutrition-profile",
            json=_VALID_CREATE,
            headers={"Authorization": "token123"},
        )
        assert response.status_code == 401

    async def test_get_bearer_prefix_missing(self, client):
        response = await client.get(
            "/api/v1/nutrition-profile",
            headers={"Authorization": "token123"},
        )
        assert response.status_code == 401

    async def test_patch_bearer_prefix_missing(self, client):
        response = await client.patch(
            "/api/v1/nutrition-profile",
            json={},
            headers={"Authorization": "token123"},
        )
        assert response.status_code == 401


class TestAuthInvalidToken:
    async def test_post_returns_401(self, client):
        response = await client.post(
            "/api/v1/nutrition-profile",
            json=_VALID_CREATE,
            headers={"Authorization": "Bearer not-a-valid-token"},
        )
        assert response.status_code == 401

    async def test_get_returns_401(self, client):
        response = await client.get(
            "/api/v1/nutrition-profile",
            headers={"Authorization": "Bearer not-a-valid-token"},
        )
        assert response.status_code == 401

    async def test_patch_returns_401(self, client):
        response = await client.patch(
            "/api/v1/nutrition-profile",
            json={},
            headers={"Authorization": "Bearer not-a-valid-token"},
        )
        assert response.status_code == 401

    async def test_post_code_invalid_token(self, client):
        response = await client.post(
            "/api/v1/nutrition-profile",
            json=_VALID_CREATE,
            headers={"Authorization": "Bearer not-a-valid-token"},
        )
        data = response.json()
        assert data["error"]["code"] == "INVALID_ACCESS_TOKEN"

    async def test_get_code_invalid_token(self, client):
        response = await client.get(
            "/api/v1/nutrition-profile",
            headers={"Authorization": "Bearer not-a-valid-token"},
        )
        data = response.json()
        assert data["error"]["code"] == "INVALID_ACCESS_TOKEN"

    async def test_patch_code_invalid_token(self, client):
        response = await client.patch(
            "/api/v1/nutrition-profile",
            json={},
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
            "/api/v1/nutrition-profile",
            json=_VALID_CREATE,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401

    async def test_get_returns_401(self, client, test_settings):
        token = self._make_expired_token(test_settings)
        response = await client.get(
            "/api/v1/nutrition-profile",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401

    async def test_patch_returns_401(self, client, test_settings):
        token = self._make_expired_token(test_settings)
        response = await client.patch(
            "/api/v1/nutrition-profile",
            json={},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401

    async def test_post_code_expired(self, client, test_settings):
        token = self._make_expired_token(test_settings)
        response = await client.post(
            "/api/v1/nutrition-profile",
            json=_VALID_CREATE,
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["error"]["code"] == "ACCESS_TOKEN_EXPIRED"


class TestAuthUnknownUser:
    async def test_post_returns_401(self, client, test_settings, mock_session):
        _setup_session_auth_only(mock_session, None)
        user_id = uuid.uuid4()
        token = create_access_token(user_id=user_id, settings=test_settings)
        response = await client.post(
            "/api/v1/nutrition-profile",
            json=_VALID_CREATE,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401

    async def test_get_returns_401(self, client, test_settings, mock_session):
        _setup_session_auth_only(mock_session, None)
        user_id = uuid.uuid4()
        token = create_access_token(user_id=user_id, settings=test_settings)
        response = await client.get(
            "/api/v1/nutrition-profile",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401

    async def test_patch_returns_401(self, client, test_settings, mock_session):
        _setup_session_auth_only(mock_session, None)
        user_id = uuid.uuid4()
        token = create_access_token(user_id=user_id, settings=test_settings)
        response = await client.patch(
            "/api/v1/nutrition-profile",
            json={},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401


class TestAuthInactiveUser:
    async def test_post_returns_403(self, client, test_settings, mock_session):
        user = _make_user(is_active=False)
        _setup_session_auth_only(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/nutrition-profile",
            json=_VALID_CREATE,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403

    async def test_get_returns_403(self, client, test_settings, mock_session):
        user = _make_user(is_active=False)
        _setup_session_auth_only(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/nutrition-profile",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403

    async def test_patch_returns_403(self, client, test_settings, mock_session):
        user = _make_user(is_active=False)
        _setup_session_auth_only(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.patch(
            "/api/v1/nutrition-profile",
            json={},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403

    async def test_post_code_inactive(self, client, test_settings, mock_session):
        user = _make_user(is_active=False)
        _setup_session_auth_only(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/nutrition-profile",
            json=_VALID_CREATE,
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["error"]["code"] == "INACTIVE_ACCOUNT"


class TestAuthValidUserReachesEndpoint:
    async def test_post_reaches_endpoint(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_session_for_create(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/nutrition-profile",
            json=_VALID_CREATE,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code not in (401, 403)

    async def test_get_reaches_endpoint(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/nutrition-profile",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code not in (401, 403)

    async def test_patch_reaches_endpoint(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.patch(
            "/api/v1/nutrition-profile",
            json={"weight_kg": "75.00"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code not in (401, 403)


# ===========================================================================
# PART 3 — POST: Create profile
# ===========================================================================


class TestPostSuccess:
    async def test_returns_201(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_session_for_create(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/nutrition-profile",
            json=_VALID_CREATE,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 201

    async def test_success_envelope(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_session_for_create(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/nutrition-profile",
            json=_VALID_CREATE,
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["success"] is True
        assert "message" in data
        assert "data" in data
        assert "profile" in data["data"]

    async def test_public_fields_returned(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_session_for_create(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/nutrition-profile",
            json=_VALID_CREATE,
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        profile = data["data"]["profile"]
        assert "id" in profile
        assert "user_id" in profile
        assert "date_of_birth" in profile
        assert "biological_sex" in profile
        assert "height_cm" in profile
        assert "weight_kg" in profile
        assert "activity_level" in profile
        assert "goal" in profile
        assert "created_at" in profile
        assert "updated_at" in profile

    async def test_user_id_is_current_user(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_session_for_create(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/nutrition-profile",
            json=_VALID_CREATE,
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["data"]["profile"]["user_id"] == str(user.id)

    async def test_commits_exactly_once(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_session_for_create(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.post(
            "/api/v1/nutrition-profile",
            json=_VALID_CREATE,
            headers={"Authorization": f"Bearer {token}"},
        )
        mock_session.commit.assert_awaited_once()

    async def test_refresh_called(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_session_for_create(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.post(
            "/api/v1/nutrition-profile",
            json=_VALID_CREATE,
            headers={"Authorization": f"Bearer {token}"},
        )
        mock_session.refresh.assert_awaited()

    async def test_no_password_hash_exposed(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_session_for_create(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/nutrition-profile",
            json=_VALID_CREATE,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert "password_hash" not in response.text.lower()

    async def test_no_token_exposed(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_session_for_create(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/nutrition-profile",
            json=_VALID_CREATE,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert "access_token" not in response.text.lower()

    async def test_no_sql_exposed(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_session_for_create(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/nutrition-profile",
            json=_VALID_CREATE,
            headers={"Authorization": f"Bearer {token}"},
        )
        text = response.text.lower()
        assert "insert into" not in text
        assert "select" not in text
        assert "sql" not in text

    async def test_x_request_id_present(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_session_for_create(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/nutrition-profile",
            json=_VALID_CREATE,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert "X-Request-ID" in response.headers


class TestPostDuplicate:
    async def test_returns_409(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/nutrition-profile",
            json=_VALID_CREATE,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 409

    async def test_duplicate_error_code(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/nutrition-profile",
            json=_VALID_CREATE,
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["error"]["code"] == "NUTRITION_PROFILE_ALREADY_EXISTS"

    async def test_duplicate_safe_message(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/nutrition-profile",
            json=_VALID_CREATE,
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["error"]["message"] == "A nutrition profile already exists for this user."

    async def test_duplicate_rolls_back(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.post(
            "/api/v1/nutrition-profile",
            json=_VALID_CREATE,
            headers={"Authorization": f"Bearer {token}"},
        )
        mock_session.rollback.assert_called()

    async def test_duplicate_no_commit(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.post(
            "/api/v1/nutrition-profile",
            json=_VALID_CREATE,
            headers={"Authorization": f"Bearer {token}"},
        )
        mock_session.commit.assert_not_called()

    async def test_duplicate_no_sql_exposed(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/nutrition-profile",
            json=_VALID_CREATE,
            headers={"Authorization": f"Bearer {token}"},
        )
        text = response.text.lower()
        assert "constraint" not in text
        assert "integrity" not in text
        assert "insert" not in text


class TestPostPersistenceFailure:
    async def test_commit_failure_returns_503(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_session_for_create(mock_session, user)
        mock_session.commit = AsyncMock(side_effect=Exception("DB commit failed"))
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/nutrition-profile",
            json=_VALID_CREATE,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 503

    async def test_commit_failure_code(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_session_for_create(mock_session, user)
        mock_session.commit = AsyncMock(side_effect=Exception("DB commit failed"))
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/nutrition-profile",
            json=_VALID_CREATE,
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["error"]["code"] == "NUTRITION_PROFILE_UNAVAILABLE"

    async def test_commit_failure_safe_message(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_session_for_create(mock_session, user)
        mock_session.commit = AsyncMock(side_effect=Exception("DB commit failed"))
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/nutrition-profile",
            json=_VALID_CREATE,
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert "DB commit failed" not in response.text
        assert "Unable to save" in data["error"]["message"]

    async def test_commit_failure_rolls_back(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_session_for_create(mock_session, user)
        mock_session.commit = AsyncMock(side_effect=Exception("DB commit failed"))
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.post(
            "/api/v1/nutrition-profile",
            json=_VALID_CREATE,
            headers={"Authorization": f"Bearer {token}"},
        )
        mock_session.rollback.assert_called()

    async def test_refresh_failure_handled(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_session_for_create(mock_session, user)
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock(side_effect=Exception("refresh failed"))
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/nutrition-profile",
            json=_VALID_CREATE,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 503

    async def test_no_raw_exception_in_response(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_session_for_create(mock_session, user)
        mock_session.commit = AsyncMock(side_effect=Exception("hidden error"))
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/nutrition-profile",
            json=_VALID_CREATE,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert "hidden error" not in response.text


# ===========================================================================
# PART 4 — GET: Retrieve profile
# ===========================================================================


class TestGetSuccess:
    async def test_returns_200(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/nutrition-profile",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    async def test_success_envelope(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/nutrition-profile",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["success"] is True
        assert data["data"]["profile"]["user_id"] == str(user.id)

    async def test_does_not_commit(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.get(
            "/api/v1/nutrition-profile",
            headers={"Authorization": f"Bearer {token}"},
        )
        mock_session.commit.assert_not_called()

    async def test_does_not_flush(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.get(
            "/api/v1/nutrition-profile",
            headers={"Authorization": f"Bearer {token}"},
        )
        mock_session.flush.assert_not_called()

    async def test_does_not_mutate_profile(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        original_email = user.email
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.get(
            "/api/v1/nutrition-profile",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert user.email == original_email

    async def test_uses_current_user_id(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/nutrition-profile",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["data"]["profile"]["user_id"] == str(user.id)


class TestGetAutoProvision:
    async def test_returns_200(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_session_for_create(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/nutrition-profile",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    async def test_auto_provision_success_envelope(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_session_for_create(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/nutrition-profile",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["success"] is True
        assert "profile" in data["data"]
        assert data["data"]["profile"]["user_id"] == str(user.id)

    async def test_auto_provision_commits(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_session_for_create(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.get(
            "/api/v1/nutrition-profile",
            headers={"Authorization": f"Bearer {token}"},
        )
        mock_session.commit.assert_awaited_once()

    async def test_auto_provision_refreshes(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_session_for_create(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.get(
            "/api/v1/nutrition-profile",
            headers={"Authorization": f"Bearer {token}"},
        )
        mock_session.refresh.assert_awaited()


# ===========================================================================
# PART 5 — PATCH: Update profile
# ===========================================================================


class TestPatchSuccess:
    async def test_returns_200(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.patch(
            "/api/v1/nutrition-profile",
            json={"weight_kg": "75.00"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    async def test_success_envelope(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.patch(
            "/api/v1/nutrition-profile",
            json={"weight_kg": "75.00"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "profile" in data["data"]

    async def test_uses_current_user_id(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.patch(
            "/api/v1/nutrition-profile",
            json={"weight_kg": "75.00"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["data"]["profile"]["user_id"] == str(user.id)

    async def test_commits_exactly_once(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.patch(
            "/api/v1/nutrition-profile",
            json={"weight_kg": "75.00"},
            headers={"Authorization": f"Bearer {token}"},
        )
        mock_session.commit.assert_awaited_once()

    async def test_single_field_update(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.patch(
            "/api/v1/nutrition-profile",
            json={"weight_kg": "75.00"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    async def test_multi_field_update(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.patch(
            "/api/v1/nutrition-profile",
            json=_VALID_UPDATE,
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["success"] is True

    async def test_empty_object_noop(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.patch(
            "/api/v1/nutrition-profile",
            json={},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    async def test_empty_allergies_clear(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.patch(
            "/api/v1/nutrition-profile",
            json={"allergies": []},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    async def test_no_password_exposed(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.patch(
            "/api/v1/nutrition-profile",
            json={"weight_kg": "75.00"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert "password" not in response.text.lower()

    async def test_x_request_id_present(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.patch(
            "/api/v1/nutrition-profile",
            json={"weight_kg": "75.00"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert "X-Request-ID" in response.headers


class TestPatchNotFound:
    async def test_returns_404(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_session_with_profile(mock_session, user, None)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.patch(
            "/api/v1/nutrition-profile",
            json={"weight_kg": "75.00"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404

    async def test_not_found_code(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_session_with_profile(mock_session, user, None)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.patch(
            "/api/v1/nutrition-profile",
            json={"weight_kg": "75.00"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["error"]["code"] == "NUTRITION_PROFILE_NOT_FOUND"

    async def test_not_found_safe_message(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_session_with_profile(mock_session, user, None)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.patch(
            "/api/v1/nutrition-profile",
            json={"weight_kg": "75.00"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["error"]["message"] == "Nutrition profile not found."

    async def test_not_found_x_request_id(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_session_with_profile(mock_session, user, None)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.patch(
            "/api/v1/nutrition-profile",
            json={"weight_kg": "75.00"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert "request_id" in data["error"]


class TestPatchPersistenceFailure:
    async def test_commit_failure_returns_503(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        mock_session.commit = AsyncMock(side_effect=Exception("commit error"))
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.patch(
            "/api/v1/nutrition-profile",
            json={"weight_kg": "75.00"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 503

    async def test_commit_failure_code(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        mock_session.commit = AsyncMock(side_effect=Exception("commit error"))
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.patch(
            "/api/v1/nutrition-profile",
            json={"weight_kg": "75.00"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["error"]["code"] == "NUTRITION_PROFILE_UNAVAILABLE"

    async def test_commit_failure_safe_message(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        mock_session.commit = AsyncMock(side_effect=Exception("commit error"))
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.patch(
            "/api/v1/nutrition-profile",
            json={"weight_kg": "75.00"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert "Unable to save" in response.text

    async def test_commit_failure_rolls_back(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        mock_session.commit = AsyncMock(side_effect=Exception("commit error"))
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.patch(
            "/api/v1/nutrition-profile",
            json={"weight_kg": "75.00"},
            headers={"Authorization": f"Bearer {token}"},
        )
        mock_session.rollback.assert_called()

    async def test_no_raw_exception(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        mock_session.commit = AsyncMock(side_effect=Exception("hidden error"))
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.patch(
            "/api/v1/nutrition-profile",
            json={"weight_kg": "75.00"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert "hidden error" not in response.text


# ===========================================================================
# PART 6 — Ownership / IDOR Protection
# ===========================================================================


class TestOwnershipProtection:
    async def test_user_id_in_body_rejected(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_session_for_create(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        payload = dict(_VALID_CREATE)
        payload["user_id"] = str(uuid.uuid4())
        response = await client.post(
            "/api/v1/nutrition-profile",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    async def test_id_in_body_rejected(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_session_for_create(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        payload = dict(_VALID_CREATE)
        payload["id"] = str(uuid.uuid4())
        response = await client.post(
            "/api/v1/nutrition-profile",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    async def test_created_at_in_body_rejected(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_session_for_create(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        payload = dict(_VALID_CREATE)
        payload["created_at"] = "2024-01-01T00:00:00Z"
        response = await client.post(
            "/api/v1/nutrition-profile",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    async def test_updated_at_in_body_rejected(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_session_for_create(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        payload = dict(_VALID_CREATE)
        payload["updated_at"] = "2024-01-01T00:00:00Z"
        response = await client.post(
            "/api/v1/nutrition-profile",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    async def test_bmi_in_body_rejected(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_session_for_create(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        payload = dict(_VALID_CREATE)
        payload["bmi"] = 22.5
        response = await client.post(
            "/api/v1/nutrition-profile",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    async def test_calorie_target_in_body_rejected(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_session_for_create(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        payload = dict(_VALID_CREATE)
        payload["calorie_target"] = 2000
        response = await client.post(
            "/api/v1/nutrition-profile",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    async def test_password_injection_rejected(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_session_for_create(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        payload = dict(_VALID_CREATE)
        payload["password"] = "secret"
        response = await client.post(
            "/api/v1/nutrition-profile",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    async def test_password_hash_injection_rejected(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_session_for_create(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        payload = dict(_VALID_CREATE)
        payload["password_hash"] = "hash"
        response = await client.post(
            "/api/v1/nutrition-profile",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    async def test_access_token_injection_rejected(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_session_for_create(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        payload = dict(_VALID_CREATE)
        payload["access_token"] = "some-token"
        response = await client.post(
            "/api/v1/nutrition-profile",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    async def test_user_id_in_update_body_rejected(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        payload = {"weight_kg": "80.00", "user_id": str(uuid.uuid4())}
        response = await client.patch(
            "/api/v1/nutrition-profile",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    async def test_id_in_update_rejected(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        payload = {"weight_kg": "80.00", "id": str(uuid.uuid4())}
        response = await client.patch(
            "/api/v1/nutrition-profile",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    async def test_bmi_in_update_rejected(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        payload = {"weight_kg": "80.00", "bmi": 22.5}
        response = await client.patch(
            "/api/v1/nutrition-profile",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422


# ===========================================================================
# PART 7 — Validation
# ===========================================================================


class TestValidation:
    async def test_height_below_minimum(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_session_for_create(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        payload = dict(_VALID_CREATE)
        payload["height_cm"] = "10.00"
        response = await client.post(
            "/api/v1/nutrition-profile",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    async def test_height_above_maximum(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_session_for_create(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        payload = dict(_VALID_CREATE)
        payload["height_cm"] = "350.00"
        response = await client.post(
            "/api/v1/nutrition-profile",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    async def test_height_excessive_decimals(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_session_for_create(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        payload = dict(_VALID_CREATE)
        payload["height_cm"] = "175.123"
        response = await client.post(
            "/api/v1/nutrition-profile",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    async def test_weight_below_minimum(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_session_for_create(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        payload = dict(_VALID_CREATE)
        payload["weight_kg"] = "5.00"
        response = await client.post(
            "/api/v1/nutrition-profile",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    async def test_weight_above_maximum(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_session_for_create(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        payload = dict(_VALID_CREATE)
        payload["weight_kg"] = "800.00"
        response = await client.post(
            "/api/v1/nutrition-profile",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    async def test_invalid_date_of_birth(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_session_for_create(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        payload = dict(_VALID_CREATE)
        payload["date_of_birth"] = "not-a-date"
        response = await client.post(
            "/api/v1/nutrition-profile",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    async def test_today_date_of_birth(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_session_for_create(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        payload = dict(_VALID_CREATE)
        payload["date_of_birth"] = date.today().isoformat()
        response = await client.post(
            "/api/v1/nutrition-profile",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    async def test_future_date_of_birth(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_session_for_create(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        payload = dict(_VALID_CREATE)
        payload["date_of_birth"] = "2099-01-01"
        response = await client.post(
            "/api/v1/nutrition-profile",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    async def test_invalid_enum_value(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_session_for_create(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        payload = dict(_VALID_CREATE)
        payload["biological_sex"] = "invalid"
        response = await client.post(
            "/api/v1/nutrition-profile",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    async def test_too_many_allergies(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_session_for_create(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        payload = dict(_VALID_CREATE)
        payload["allergies"] = [f"allergy_{i}" for i in range(51)]
        response = await client.post(
            "/api/v1/nutrition-profile",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    async def test_allergy_too_long(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_session_for_create(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        payload = dict(_VALID_CREATE)
        payload["allergies"] = ["a" * 101]
        response = await client.post(
            "/api/v1/nutrition-profile",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    async def test_null_byte_in_allergy(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_session_for_create(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        payload = dict(_VALID_CREATE)
        payload["allergies"] = ["bad\x00allergy"]
        response = await client.post(
            "/api/v1/nutrition-profile",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    async def test_null_for_required_field_create(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_session_for_create(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        payload = dict(_VALID_CREATE)
        payload["date_of_birth"] = None
        response = await client.post(
            "/api/v1/nutrition-profile",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 201

    async def test_null_for_required_field_update(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        payload = {
            "date_of_birth": None,
            "biological_sex": "male",
            "height_cm": "175.00",
            "weight_kg": "70.00",
            "activity_level": "moderately_active",
            "goal": "maintain_weight",
        }
        response = await client.patch(
            "/api/v1/nutrition-profile",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    async def test_null_allergies_rejected_update(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.patch(
            "/api/v1/nutrition-profile",
            json={"allergies": None},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    async def test_validation_uses_safe_envelope(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_session_for_create(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        payload = dict(_VALID_CREATE)
        payload["height_cm"] = "10.00"
        response = await client.post(
            "/api/v1/nutrition-profile",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert data["error"]["message"] == "Request validation failed."
        assert "request_id" in data["error"]

    async def test_validation_strips_input(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_session_for_create(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        payload = dict(_VALID_CREATE)
        payload["height_cm"] = "10.00"
        response = await client.post(
            "/api/v1/nutrition-profile",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        body = json.loads(response.text)
        if "details" in body["error"]:
            for detail in body["error"]["details"]:
                assert "input" not in detail


# ===========================================================================
# PART 8 — Error Envelope
# ===========================================================================


class TestErrorEnvelope:
    async def test_success_is_false(self, client, test_settings, mock_session):
        response = await client.get("/api/v1/nutrition-profile")
        data = response.json()
        assert data["success"] is False

    async def test_error_code_exists(self, client, test_settings, mock_session):
        response = await client.get("/api/v1/nutrition-profile")
        data = response.json()
        assert "code" in data["error"]

    async def test_error_message_exists(self, client, test_settings, mock_session):
        response = await client.get("/api/v1/nutrition-profile")
        data = response.json()
        assert "message" in data["error"]

    async def test_request_id_in_error(self, client, test_settings, mock_session):
        response = await client.get("/api/v1/nutrition-profile")
        data = response.json()
        assert "request_id" in data["error"]
        assert "X-Request-ID" in response.headers

    async def test_no_detail_wrapper(self, client, test_settings, mock_session):
        response = await client.get("/api/v1/nutrition-profile")
        assert '"detail"' not in response.text

    async def test_no_stack_trace(self, client, test_settings, mock_session):
        response = await client.get("/api/v1/nutrition-profile")
        assert "Traceback" not in response.text
        assert "File" not in response.text

    async def test_no_sql_in_error(self, client, test_settings, mock_session):
        response = await client.get("/api/v1/nutrition-profile")
        text = response.text.lower()
        assert "select" not in text
        assert "from" not in text
        assert "insert" not in text


# ===========================================================================
# PART 9 — OpenAPI / Schema verification
# ===========================================================================


class TestOpenAPI:
    async def test_nutrition_profile_operations_in_schema(self, test_settings):
        app = create_app(settings=test_settings)
        schema = app.openapi()
        paths = schema["paths"]
        assert "/api/v1/nutrition-profile" in paths
        assert "post" in paths["/api/v1/nutrition-profile"]
        assert "get" in paths["/api/v1/nutrition-profile"]
        assert "patch" in paths["/api/v1/nutrition-profile"]

    async def test_all_routes_require_bearer_auth(self, test_settings):
        app = create_app(settings=test_settings)
        schema = app.openapi()
        path = schema["paths"]["/api/v1/nutrition-profile"]
        for method in ("post", "get", "patch"):
            sec = path[method].get("security", [])
            assert any("BearerAuth" in s for s in sec), f"{method} missing BearerAuth"

    async def test_no_duplicate_bearer_scheme(self, test_settings):
        app = create_app(settings=test_settings)
        schema = app.openapi()
        schemes = schema.get("components", {}).get("securitySchemes", {})
        bearer_count = sum(1 for v in schemes.values() if v.get("scheme") == "bearer")
        assert bearer_count == 1

    async def test_request_schema_documented(self, test_settings):
        app = create_app(settings=test_settings)
        schema = app.openapi()
        post_op = schema["paths"]["/api/v1/nutrition-profile"]["post"]
        assert "requestBody" in post_op

    async def test_response_schema_documented(self, test_settings):
        app = create_app(settings=test_settings)
        schema = app.openapi()
        get_op = schema["paths"]["/api/v1/nutrition-profile"]["get"]
        assert "200" in get_op["responses"]

    async def test_existing_health_public(self, test_settings):
        app = create_app(settings=test_settings)
        schema = app.openapi()
        health_path = schema["paths"]["/api/v1/health"]
        assert "get" in health_path
        sec = health_path["get"].get("security", [])
        assert not any("BearerAuth" in s for s in sec)

    async def test_existing_auth_me_protected(self, test_settings):
        app = create_app(settings=test_settings)
        schema = app.openapi()
        auth_me_path = schema["paths"]["/api/v1/auth/me"]
        assert "get" in auth_me_path
        sec = auth_me_path["get"].get("security", [])
        assert any("BearerAuth" in s for s in sec)


# ===========================================================================
# PART 10 — Regression
# ===========================================================================


class TestRegression:
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

    async def test_app_factory_two_instances(self, test_settings):
        app1 = create_app(settings=test_settings)
        app2 = create_app(settings=test_settings)
        assert app1 is not app2
