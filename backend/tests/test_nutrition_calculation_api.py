from __future__ import annotations

import inspect
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


def _make_profile(
    user_id: uuid.UUID | None = None,
    *,
    biological_sex: BiologicalSex = BiologicalSex.MALE,
    height_cm: Decimal = Decimal("175.00"),
    weight_kg: Decimal = Decimal("70.00"),
    activity_level: ActivityLevel = ActivityLevel.MODERATELY_ACTIVE,
    goal: NutritionGoal = NutritionGoal.MAINTAIN_WEIGHT,
    date_of_birth: date = date(1990, 1, 1),
) -> MagicMock:
    profile = MagicMock(spec=NutritionProfile)
    profile.id = uuid.uuid4()
    profile.user_id = user_id or uuid.uuid4()
    profile.date_of_birth = date_of_birth
    profile.biological_sex = biological_sex
    profile.height_cm = height_cm
    profile.weight_kg = weight_kg
    profile.activity_level = activity_level
    profile.goal = goal
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
    result = MagicMock()
    result.scalars.return_value.one_or_none.return_value = value
    return result


def _setup_session_with_profile(
    session: AsyncMock,
    user: MagicMock,
    profile: MagicMock | None,
) -> None:
    session.execute = AsyncMock(
        side_effect=[
            _make_execute_result(user),  # auth user lookup
            _make_execute_result(profile),  # profile lookup
        ]
    )
    session.commit = AsyncMock()
    session.flush = AsyncMock()
    session.rollback = AsyncMock()


def _setup_session_for_create(session: AsyncMock, user: MagicMock) -> None:
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


def _setup_session_with_profile_side_effect(
    session: AsyncMock,
    user: MagicMock,
    profile_side_effect,
) -> None:
    state = {"n": 0}

    def _side_effect(*args, **kwargs):
        state["n"] += 1
        if state["n"] == 1:
            return _make_execute_result(user)
        if callable(profile_side_effect):
            return profile_side_effect()
        return profile_side_effect

    session.execute = AsyncMock(side_effect=_side_effect)
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
    application = create_app(settings=test_settings)
    application.dependency_overrides[deps_get_settings] = lambda: test_settings

    async def override_get_db_session():
        try:
            yield mock_session
        finally:
            pass

    application.dependency_overrides[get_db_session] = override_get_db_session
    return application


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


CALC_URL = "/api/v1/nutrition-profile/calculations"


# ===========================================================================
# PART 1 — Route registration
# ===========================================================================


class TestRouteRegistration:
    async def test_get_route_exists(self, client):
        response = await client.get(CALC_URL, params={"reference_date": "2026-07-12"})
        assert response.status_code != 404

    async def test_get_accepts_get(self, client):
        response = await client.get(CALC_URL, params={"reference_date": "2026-07-12"})
        assert response.status_code != 405

    async def test_post_rejected(self, client):
        response = await client.post(CALC_URL, params={"reference_date": "2026-07-12"})
        assert response.status_code == 405

    async def test_patch_rejected(self, client):
        response = await client.patch(CALC_URL, params={"reference_date": "2026-07-12"})
        assert response.status_code == 405

    async def test_delete_rejected(self, client):
        response = await client.delete(CALC_URL, params={"reference_date": "2026-07-12"})
        assert response.status_code == 405

    async def test_put_rejected(self, client):
        response = await client.put(CALC_URL, params={"reference_date": "2026-07-12"})
        assert response.status_code == 405

    async def test_static_route_not_shadowed(self, client):
        response = await client.get(CALC_URL, params={"reference_date": "2026-07-12"})
        assert response.status_code != 404

    async def test_health_route_still_public(self, client):
        response = await client.get("/api/v1/health")
        assert response.status_code != 401

    async def test_register_still_public(self, client):
        response = await client.post("/api/v1/auth/register", json={})
        assert response.status_code != 401

    async def test_login_still_public(self, client):
        response = await client.post("/api/v1/auth/login", json={})
        assert response.status_code != 401

    async def test_auth_me_still_protected(self, client):
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401

    async def test_profile_get_still_protected(self, client):
        response = await client.get("/api/v1/nutrition-profile")
        assert response.status_code == 401

    async def test_existing_routes_preserved(self, app):
        paths = [r.path for r in app.routes if "nutrition-profile" in r.path]
        assert paths.count("/api/v1/nutrition-profile") == 3
        assert "/api/v1/nutrition-profile/calculations" in paths

    async def test_calculations_route_has_get(self, app):
        route = next(
            r
            for r in app.routes
            if getattr(r, "path", None) == "/api/v1/nutrition-profile/calculations"
        )
        methods = {m.upper() for m in route.methods}
        assert "GET" in methods
        assert "POST" not in methods
        assert "PATCH" not in methods
        assert "DELETE" not in methods


# ===========================================================================
# PART 2 — Authentication
# ===========================================================================


class TestAuthMissingToken:
    async def test_returns_401(self, client):
        response = await client.get(CALC_URL, params={"reference_date": "2026-07-12"})
        assert response.status_code == 401

    async def test_safe_envelope(self, client):
        response = await client.get(CALC_URL, params={"reference_date": "2026-07-12"})
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "AUTHENTICATION_REQUIRED"
        assert "request_id" in data["error"]

    async def test_www_authenticate(self, client):
        response = await client.get(CALC_URL, params={"reference_date": "2026-07-12"})
        assert response.headers.get("WWW-Authenticate") == "Bearer"

    async def test_no_detail_field(self, client):
        response = await client.get(CALC_URL, params={"reference_date": "2026-07-12"})
        assert '"detail"' not in response.text


class TestAuthEmptyBearer:
    async def test_empty_token_401(self, client):
        response = await client.get(
            CALC_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": "Bearer "},
        )
        assert response.status_code == 401

    async def test_whitespace_only_401(self, client):
        response = await client.get(
            CALC_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": "Bearer    "},
        )
        assert response.status_code == 401


class TestAuthWrongScheme:
    async def test_basic_scheme_401(self, client):
        response = await client.get(
            CALC_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": "Basic abcdef"},
        )
        assert response.status_code == 401


class TestAuthInvalidToken:
    async def test_returns_401(self, client):
        response = await client.get(
            CALC_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": "Bearer not-a-valid-token"},
        )
        assert response.status_code == 401

    async def test_code_invalid_token(self, client):
        response = await client.get(
            CALC_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": "Bearer not-a-valid-token"},
        )
        data = response.json()
        assert data["error"]["code"] == "INVALID_ACCESS_TOKEN"


class TestAuthExpiredToken:
    def _make_expired_token(self, settings: Settings) -> str:
        past = datetime.now(UTC) - timedelta(hours=2)
        return create_access_token(user_id=uuid.uuid4(), settings=settings, now=past)

    async def test_returns_401(self, client, test_settings):
        token = self._make_expired_token(test_settings)
        response = await client.get(
            CALC_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401

    async def test_code_expired(self, client, test_settings):
        token = self._make_expired_token(test_settings)
        response = await client.get(
            CALC_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.json()["error"]["code"] == "ACCESS_TOKEN_EXPIRED"


class TestAuthUnknownUser:
    async def test_returns_401(self, client, test_settings, mock_session):
        _setup_session_with_profile(mock_session, None, None)
        token = create_access_token(user_id=uuid.uuid4(), settings=test_settings)
        response = await client.get(
            CALC_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401


class TestAuthInactiveUser:
    async def test_returns_403(self, client, test_settings, mock_session):
        user = _make_user(is_active=False)
        _setup_session_with_profile(mock_session, user, None)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            CALC_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403

    async def test_code_inactive(self, client, test_settings, mock_session):
        user = _make_user(is_active=False)
        _setup_session_with_profile(mock_session, user, None)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            CALC_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.json()["error"]["code"] == "INACTIVE_ACCOUNT"


class TestAuthValidUserReachesEndpoint:
    async def test_reaches_endpoint(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            CALC_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code not in (401, 403)


# ===========================================================================
# PART 3 — reference_date validation
# ===========================================================================


class TestReferenceDateValidation:
    async def test_missing_returns_422(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            CALC_URL,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422
        data = response.json()
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert "request_id" in data["error"]

    async def test_valid_iso_accepted(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            CALC_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    async def test_malformed_date_rejected(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            CALC_URL,
            params={"reference_date": "not-a-date"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    async def test_impossible_date_rejected(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            CALC_URL,
            params={"reference_date": "2026-02-30"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    async def test_invalid_month_rejected(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            CALC_URL,
            params={"reference_date": "2026-13-01"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    async def test_invalid_day_rejected(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            CALC_URL,
            params={"reference_date": "2026-04-31"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    async def test_datetime_string_rejected(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            CALC_URL,
            params={"reference_date": "2026-07-12T10:00:00"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    async def test_deterministic_for_same_input(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        r1 = await client.get(
            CALC_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        profile2 = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile2)
        r2 = await client.get(
            CALC_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r1.json()["data"] == r2.json()["data"]

    async def test_different_dates_different_age(self, client, test_settings, mock_session):
        user = _make_user()
        token = create_access_token(user_id=user.id, settings=test_settings)

        profile_young = _make_profile(user_id=user.id, date_of_birth=date(2000, 1, 1))
        _setup_session_with_profile(mock_session, user, profile_young)
        r_young = await client.get(
            CALC_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r_young.json()["data"]["metrics"]["age_years"] == 26

        profile_old = _make_profile(user_id=user.id, date_of_birth=date(1990, 1, 1))
        _setup_session_with_profile(mock_session, user, profile_old)
        r_old = await client.get(
            CALC_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r_old.json()["data"]["metrics"]["age_years"] == 36


# ===========================================================================
# PART 4 — Profile lookup
# ===========================================================================


class TestProfileLookup:
    async def test_uses_authenticated_user_id(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            CALC_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    async def test_missing_profile_returns_200_incomplete(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_session_for_create(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            CALC_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"] is None
        assert "incomplete" in data["message"].lower()

    async def test_repository_called_once(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.get(
            CALC_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert mock_session.execute.await_count == 2

    async def test_no_commit(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.get(
            CALC_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        mock_session.commit.assert_not_called()
        mock_session.flush.assert_not_called()
        mock_session.refresh.assert_not_called()

    async def test_no_sql_exposed(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            CALC_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        text = response.text.lower()
        assert "insert into" not in text
        assert "select" not in text


# ===========================================================================
# PART 5 — Successful calculation
# ===========================================================================


class TestSuccessfulCalculation:
    async def test_returns_200(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            CALC_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    async def test_success_envelope(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            CALC_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Nutrition calculations completed successfully."
        assert "metrics" in data["data"]
        assert "targets" in data["data"]

    async def test_metrics_values(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            CALC_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        metrics = response.json()["data"]["metrics"]
        assert metrics["age_years"] == 36
        assert metrics["bmi"] == "22.86"
        assert metrics["bmi_category"] == "healthy_weight"
        assert metrics["bmr_kcal_per_day"] == "1619"
        assert metrics["tdee_kcal_per_day"] == "2509"

    async def test_targets_values(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            CALC_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        targets = response.json()["data"]["targets"]
        assert targets["calorie_target_kcal_per_day"] == "2509"
        assert targets["protein_g_per_day"] == "157"
        assert targets["carbohydrate_g_per_day"] == "282"
        assert targets["fat_g_per_day"] == "84"

    async def test_decimal_not_float(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            CALC_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert isinstance(data["data"]["metrics"]["bmr_kcal_per_day"], str)
        assert isinstance(data["data"]["metrics"]["bmi"], str)
        assert ":1619" not in response.text
        assert ':"1619"' in response.text

    async def test_enum_lowercase(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            CALC_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.json()["data"]["metrics"]["bmi_category"] == "healthy_weight"

    async def test_no_sensitive_data(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            CALC_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        text = response.text.lower()
        assert "password" not in text
        assert "password_hash" not in text
        assert "access_token" not in text
        assert "secret" not in text
        assert "$argon2id" not in text

    async def test_no_profile_object_in_response(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            CALC_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert "profile" not in data["data"]
        assert "user" not in data["data"]

    async def test_x_request_id_present(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            CALC_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert "X-Request-ID" in response.headers


# ===========================================================================
# PART 6 — Domain function reuse (spy verification)
# ===========================================================================


class TestDomainFunctionReuse:
    async def test_metrics_called_once(self, client, test_settings, mock_session, monkeypatch):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)

        from app.api.v1 import nutrition_profile as np_module

        calls = {"n": 0}
        original = np_module.calculate_nutrition_metrics

        def spy(**kwargs):
            calls["n"] += 1
            return original(**kwargs)

        monkeypatch.setattr(np_module, "calculate_nutrition_metrics", spy)
        await client.get(
            CALC_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert calls["n"] == 1

    async def test_targets_called_once(self, client, test_settings, mock_session, monkeypatch):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)

        from app.api.v1 import nutrition_profile as np_module

        calls = {"n": 0}
        original = np_module.calculate_nutrition_targets

        def spy(**kwargs):
            calls["n"] += 1
            return original(**kwargs)

        monkeypatch.setattr(np_module, "calculate_nutrition_targets", spy)
        await client.get(
            CALC_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert calls["n"] == 1

    async def test_reference_date_passed(self, client, test_settings, mock_session, monkeypatch):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)

        from app.api.v1 import nutrition_profile as np_module

        captured: dict = {}
        original = np_module.calculate_nutrition_metrics

        def spy(**kwargs):
            captured.update(kwargs)
            return original(**kwargs)

        monkeypatch.setattr(np_module, "calculate_nutrition_metrics", spy)
        await client.get(
            CALC_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert captured["reference_date"] == date(2026, 7, 12)
        assert captured["date_of_birth"] == date(1990, 1, 1)
        assert captured["biological_sex"] == BiologicalSex.MALE
        assert captured["height_cm"] == Decimal("175.00")
        assert captured["weight_kg"] == Decimal("70.00")
        assert captured["activity_level"] == ActivityLevel.MODERATELY_ACTIVE

    async def test_profile_not_mutated(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        original_dob = profile.date_of_birth
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.get(
            CALC_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert profile.date_of_birth == original_dob


# ===========================================================================
# PART 7 — Unsupported BMR
# ===========================================================================


class TestUnsupportedBMR:
    async def test_other_returns_422(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id, biological_sex=BiologicalSex.OTHER)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            CALC_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    async def test_other_error_code(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id, biological_sex=BiologicalSex.OTHER)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            CALC_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["error"]["code"] == "BMR_CALCULATION_UNSUPPORTED"
        assert "request_id" in data["error"]

    async def test_other_safe_message(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id, biological_sex=BiologicalSex.OTHER)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            CALC_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        msg = response.json()["error"]["message"]
        assert "Mifflin-St Jeor" in msg

    async def test_prefer_not_to_say_same_contract(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id, biological_sex=BiologicalSex.PREFER_NOT_TO_SAY)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            CALC_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["error"]["code"] == "BMR_CALCULATION_UNSUPPORTED"

    async def test_no_target_calc_after_bmr_failure(
        self, client, test_settings, mock_session, monkeypatch
    ):
        user = _make_user()
        profile = _make_profile(user_id=user.id, biological_sex=BiologicalSex.OTHER)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)

        from app.api.v1 import nutrition_profile as np_module

        calls = {"n": 0}
        original = np_module.calculate_nutrition_targets

        async def spy(**kwargs):
            calls["n"] += 1
            return await original(**kwargs)

        monkeypatch.setattr(np_module, "calculate_nutrition_targets", spy)
        await client.get(
            CALC_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert calls["n"] == 0

    async def test_no_persistence(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id, biological_sex=BiologicalSex.OTHER)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.get(
            CALC_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        mock_session.commit.assert_not_called()
        mock_session.add.assert_not_called()


# ===========================================================================
# PART 8 — Below minimum calorie target
# ===========================================================================


class TestBelowMinimumCalorie:
    async def test_returns_422(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(
            user_id=user.id,
            biological_sex=BiologicalSex.FEMALE,
            height_cm=Decimal("50.00"),
            weight_kg=Decimal("10.00"),
            activity_level=ActivityLevel.SEDENTARY,
            goal=NutritionGoal.MAINTAIN_WEIGHT,
            date_of_birth=date(2000, 1, 1),
        )
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            CALC_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    async def test_error_code(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(
            user_id=user.id,
            biological_sex=BiologicalSex.FEMALE,
            height_cm=Decimal("50.00"),
            weight_kg=Decimal("10.00"),
            activity_level=ActivityLevel.SEDENTARY,
            goal=NutritionGoal.MAINTAIN_WEIGHT,
            date_of_birth=date(2000, 1, 1),
        )
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            CALC_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["error"]["code"] == "CALORIE_TARGET_BELOW_MINIMUM"
        assert "request_id" in data["error"]

    async def test_safe_message(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(
            user_id=user.id,
            biological_sex=BiologicalSex.FEMALE,
            height_cm=Decimal("50.00"),
            weight_kg=Decimal("10.00"),
            activity_level=ActivityLevel.SEDENTARY,
            goal=NutritionGoal.MAINTAIN_WEIGHT,
            date_of_birth=date(2000, 1, 1),
        )
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            CALC_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert "supported minimum" in response.json()["error"]["message"]

    async def test_no_success_response(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(
            user_id=user.id,
            biological_sex=BiologicalSex.FEMALE,
            height_cm=Decimal("50.00"),
            weight_kg=Decimal("10.00"),
            activity_level=ActivityLevel.SEDENTARY,
            goal=NutritionGoal.MAINTAIN_WEIGHT,
            date_of_birth=date(2000, 1, 1),
        )
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            CALC_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.json()["success"] is False

    async def test_no_persistence(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(
            user_id=user.id,
            biological_sex=BiologicalSex.FEMALE,
            height_cm=Decimal("50.00"),
            weight_kg=Decimal("10.00"),
            activity_level=ActivityLevel.SEDENTARY,
            goal=NutritionGoal.MAINTAIN_WEIGHT,
            date_of_birth=date(2000, 1, 1),
        )
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.get(
            CALC_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        mock_session.commit.assert_not_called()


# ===========================================================================
# PART 9 — Invalid age / reference date relative to DOB
# ===========================================================================


class TestInvalidAgeReference:
    async def test_reference_equals_dob_returns_422(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id, date_of_birth=date(2000, 1, 1))
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            CALC_URL,
            params={"reference_date": "2000-01-01"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "INVALID_CALCULATION_INPUT"
        assert "request_id" in response.json()["error"]

    async def test_reference_before_dob_returns_422(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id, date_of_birth=date(2000, 1, 1))
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            CALC_URL,
            params={"reference_date": "1999-12-31"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "INVALID_CALCULATION_INPUT"

    async def test_no_result_returned(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id, date_of_birth=date(2000, 1, 1))
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            CALC_URL,
            params={"reference_date": "2000-01-01"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert "data" not in response.json()


# ===========================================================================
# PART 10 — Unexpected errors
# ===========================================================================


class TestUnexpectedErrors:
    async def test_repository_error_propagates(self, client, test_settings, mock_session):
        user = _make_user()
        token = create_access_token(user_id=user.id, settings=test_settings)

        def _raise():
            raise RuntimeError("db exploded")

        _setup_session_with_profile_side_effect(mock_session, user, _raise)
        with pytest.raises(RuntimeError):
            await client.get(
                CALC_URL,
                params={"reference_date": "2026-07-12"},
                headers={"Authorization": f"Bearer {token}"},
            )

    async def test_calculation_error_propagates(
        self, client, test_settings, mock_session, monkeypatch
    ):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)

        from app.api.v1 import nutrition_profile as np_module

        def _boom(**kwargs):
            raise RuntimeError("calc boom")

        monkeypatch.setattr(np_module, "calculate_nutrition_metrics", _boom)
        with pytest.raises(RuntimeError):
            await client.get(
                CALC_URL,
                params={"reference_date": "2026-07-12"},
                headers={"Authorization": f"Bearer {token}"},
            )

    async def test_global_handler_safe_500(self):
        from starlette.requests import Request

        from app.core.exceptions import global_exception_handler

        async def _receive():
            return {"type": "http.disconnect"}

        request = Request(
            {"type": "http", "method": "GET", "path": CALC_URL, "headers": []},
            receive=_receive,
        )
        response = await global_exception_handler(request, RuntimeError("boom details"))
        assert response.status_code == 500
        import json

        data = json.loads(response.body)
        assert data["success"] is False
        assert data["error"]["code"] == "INTERNAL_SERVER_ERROR"
        assert data["error"]["message"] == "An unexpected error occurred."
        assert "boom details" not in response.body.decode()
        assert "X-Request-ID" in response.headers


# ===========================================================================
# PART 11 — Response schema validation
# ===========================================================================


class TestResponseSchema:
    async def test_validates_against_schema(self, client, test_settings, mock_session):
        from app.schemas.nutrition_calculations import CalculatedNutritionSuccessResponse

        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            CALC_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        CalculatedNutritionSuccessResponse.model_validate(response.json())
        assert response.json()["success"] is True

    async def test_no_extra_fields(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            CALC_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert set(data.keys()) == {"success", "message", "data"}


# ===========================================================================
# PART 12 — OpenAPI
# ===========================================================================


class TestOpenAPI:
    async def test_calculation_path_exists(self, app):
        spec = app.openapi()
        assert "/api/v1/nutrition-profile/calculations" in spec["paths"]

    async def test_get_operation_exists(self, app):
        spec = app.openapi()
        path_item = spec["paths"]["/api/v1/nutrition-profile/calculations"]
        assert "get" in path_item

    async def test_no_post_operation(self, app):
        spec = app.openapi()
        path_item = spec["paths"]["/api/v1/nutrition-profile/calculations"]
        assert "post" not in path_item
        assert "patch" not in path_item
        assert "delete" not in path_item

    async def test_required_reference_date_param(self, app):
        spec = app.openapi()
        op = spec["paths"]["/api/v1/nutrition-profile/calculations"]["get"]
        params = op.get("parameters", [])
        ref_params = [p for p in params if p["name"] == "reference_date"]
        assert ref_params
        assert ref_params[0]["required"] is True
        assert ref_params[0]["schema"]["type"] == "string"
        assert ref_params[0]["schema"]["format"] == "date"

    async def test_bearer_auth_protects(self, app):
        spec = app.openapi()
        op = spec["paths"]["/api/v1/nutrition-profile/calculations"]["get"]
        assert "security" in op
        assert any("BearerAuth" in s for s in op["security"])

    async def test_exactly_one_bearer_scheme(self, app):
        spec = app.openapi()
        schemes = spec["components"]["securitySchemes"]
        assert list(schemes.keys()) == ["BearerAuth"]

    async def test_response_schema_references_success(self, app):
        spec = app.openapi()
        op = spec["paths"]["/api/v1/nutrition-profile/calculations"]["get"]
        assert "200" in op["responses"]

    async def test_register_remains_public(self, app):
        spec = app.openapi()
        assert "security" not in spec["paths"]["/api/v1/auth/register"]["post"]

    async def test_login_remains_public(self, app):
        spec = app.openapi()
        assert "security" not in spec["paths"]["/api/v1/auth/login"]["post"]

    async def test_health_remains_public(self, app):
        spec = app.openapi()
        assert "security" not in spec["paths"]["/api/v1/health"]["get"]

    async def test_auth_me_remains_protected(self, app):
        spec = app.openapi()
        op = spec["paths"]["/api/v1/auth/me"]["get"]
        assert "security" in op

    async def test_profile_routes_unchanged(self, app):
        spec = app.openapi()
        for method in ("get", "post", "patch"):
            assert method in spec["paths"]["/api/v1/nutrition-profile"]


# ===========================================================================
# PART 13 — Source boundary audit (static analysis)
# ===========================================================================


class TestSourceBoundaries:
    def test_router_has_no_bmi_formula(self):
        from app.api.v1 import nutrition_profile as np_module

        source = inspect.getsource(np_module)
        assert "weight_kg /" not in source
        assert "(height_m" not in source

    def test_router_has_no_bmr_formula(self):
        from app.api.v1 import nutrition_profile as np_module

        source = inspect.getsource(np_module)
        assert "6.25 * height_cm" not in source

    def test_router_has_no_tdee_multiplier(self):
        from app.api.v1 import nutrition_profile as np_module

        source = inspect.getsource(np_module)
        assert "ACTIVITY_MULTIPLIERS" not in source

    def test_router_has_no_calorie_adjustment(self):
        from app.api.v1 import nutrition_profile as np_module

        source = inspect.getsource(np_module)
        assert "CALORIE_ADJUSTMENTS" not in source

    def test_router_has_no_macro_distribution(self):
        from app.api.v1 import nutrition_profile as np_module

        source = inspect.getsource(np_module)
        assert "MACRO_DISTRIBUTIONS" not in source

    def test_router_uses_no_system_clock(self):
        from app.api.v1 import nutrition_profile as np_module

        source = inspect.getsource(np_module)
        assert "date.today()" not in source
        assert "datetime.now()" not in source

    def test_router_does_not_import_jwt(self):
        from app.api.v1 import nutrition_profile as np_module

        source = inspect.getsource(np_module)
        assert "import jwt" not in source
        assert "decode_access_token" not in source

    def test_router_does_not_create_session(self):
        from app.api.v1 import nutrition_profile as np_module

        source = inspect.getsource(np_module)
        assert "create_async_engine" not in source
        assert "AsyncSession(" not in source

    def test_router_has_no_persistence_calls(self):
        from app.api.v1 import nutrition_profile as np_module

        source = inspect.getsource(np_module.get_nutrition_calculations)
        for token in ("session.commit", "session.flush", "session.refresh", "create_all"):
            assert token not in source

    def test_router_has_no_env_access(self):
        from app.api.v1 import nutrition_profile as np_module

        source = inspect.getsource(np_module)
        assert "os.environ" not in source

    def test_router_has_no_ai_integration(self):
        from app.api.v1 import nutrition_profile as np_module

        source = inspect.getsource(np_module)
        for token in ("usda", "groq", "openai"):
            assert token.lower() not in source.lower()
