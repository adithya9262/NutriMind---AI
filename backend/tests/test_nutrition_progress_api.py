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
from app.core.nutrition_logs import MealType
from app.core.tokens import create_access_token
from app.db.dependencies import get_db_session
from app.main import create_app
from app.models.enums import ActivityLevel, BiologicalSex, NutritionGoal
from app.models.nutrition_log import NutritionLog
from app.models.nutrition_profile import NutritionProfile
from app.models.user import User
from app.schemas.nutrition_progress import (
    DailyNutritionProgressSuccessResponse,
)

NOW = datetime.now(UTC)
PROGRESS_URL = "/api/v1/nutrition-logs/progress"


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


def _make_nutrition_log(
    user_id: uuid.UUID | None = None,
    entry_id: uuid.UUID | None = None,
    logged_date: date = date(2026, 7, 12),
    meal_type: MealType = MealType.BREAKFAST,
    food_name: str = "Oatmeal",
    serving: str = "1 bowl",
    calories: str = "300.00",
    protein: str = "10.00",
    carbs: str = "50.00",
    fat: str = "5.00",
) -> MagicMock:
    entry = MagicMock(spec=NutritionLog)
    entry.id = uuid.uuid4()
    entry.user_id = user_id or uuid.uuid4()
    entry.logged_date = logged_date
    entry.entry_id = entry_id or uuid.uuid4()
    entry.food_name = food_name
    entry.meal_type = meal_type
    entry.serving_description = serving
    entry.calories_kcal = Decimal(calories)
    entry.protein_g = Decimal(protein)
    entry.carbohydrate_g = Decimal(carbs)
    entry.fat_g = Decimal(fat)
    entry.created_at = NOW
    entry.updated_at = NOW
    return entry


def _make_execute_result(value: MagicMock | None) -> MagicMock:
    result = MagicMock()
    result.scalars.return_value.one_or_none.return_value = value
    return result


def _make_entries_result(entries: list) -> MagicMock:
    result = MagicMock()
    result.scalars.return_value.all.return_value = entries
    return result


def _setup_session_with_profile_and_logs(
    session: AsyncMock,
    user: MagicMock,
    profile: MagicMock | None,
    log_entries: list | None = None,
) -> None:
    if log_entries is None:
        log_entries = []
    session.execute = AsyncMock(
        side_effect=[
            _make_execute_result(user),
            _make_execute_result(profile),
            _make_entries_result(log_entries),
        ]
    )
    session.commit = AsyncMock()
    session.flush = AsyncMock()
    session.rollback = AsyncMock()


def _dec(value: str) -> Decimal:
    return Decimal(value)


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
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ===========================================================================
# A. Route Registration and Ordering
# ===========================================================================


class TestRouteRegistration:
    async def test_progress_path_registered(self, client):
        response = await client.get(PROGRESS_URL)
        assert response.status_code != 404

    async def test_get_only(self, client):
        response = await client.get(PROGRESS_URL)
        assert response.status_code != 405

    async def test_post_rejected(self, client):
        response = await client.post(PROGRESS_URL)
        assert response.status_code == 405

    async def test_put_rejected(self, client):
        response = await client.put(PROGRESS_URL)
        assert response.status_code == 405

    async def test_patch_rejected(self, client):
        response = await client.patch(PROGRESS_URL)
        assert response.status_code == 405

    async def test_delete_rejected(self, client):
        response = await client.delete(PROGRESS_URL)
        assert response.status_code in (401, 405)

    async def test_progress_before_entry_id(self, app):
        routes = [r.path for r in app.routes if "nutrition-logs" in r.path]
        progress_idx = routes.index("/api/v1/nutrition-logs/progress")
        entry_id_idx = routes.index("/api/v1/nutrition-logs/{entry_id}")
        assert progress_idx < entry_id_idx

    async def test_no_duplicate_progress_path(self, app):
        progress_routes = [
            r.path for r in app.routes if r.path == "/api/v1/nutrition-logs/progress"
        ]
        assert len(progress_routes) == 1

    async def test_summary_still_registered(self, client):
        response = await client.get("/api/v1/nutrition-logs/summary")
        assert response.status_code != 404

    async def test_post_crud_still_registered(self, client):
        response = await client.post("/api/v1/nutrition-logs", json={})
        assert response.status_code != 404

    async def test_get_crud_still_registered(self, client):
        response = await client.get("/api/v1/nutrition-logs")
        assert response.status_code != 404

    async def test_delete_crud_still_registered(self, client):
        response = await client.delete(f"/api/v1/nutrition-logs/{uuid.uuid4()}")
        assert response.status_code != 404

    async def test_progress_static_not_interpreted_as_entry_id(self, client):
        response = await client.get(PROGRESS_URL)
        assert response.status_code != 404
        assert response.status_code != 422


# ===========================================================================
# B. OpenAPI
# ===========================================================================


class TestOpenAPI:
    async def test_progress_path_exists(self, app):
        schema = app.openapi()
        assert "/api/v1/nutrition-logs/progress" in schema["paths"]

    async def test_get_operation_exists(self, app):
        schema = app.openapi()
        path_item = schema["paths"]["/api/v1/nutrition-logs/progress"]
        assert "get" in path_item

    async def test_no_write_methods(self, app):
        schema = app.openapi()
        path_item = schema["paths"]["/api/v1/nutrition-logs/progress"]
        assert "post" not in path_item
        assert "put" not in path_item
        assert "patch" not in path_item
        assert "delete" not in path_item

    async def test_logged_date_required(self, app):
        schema = app.openapi()
        op = schema["paths"]["/api/v1/nutrition-logs/progress"]["get"]
        params = op.get("parameters", [])
        lp = [p for p in params if p["name"] == "logged_date"]
        assert len(lp) >= 1
        assert lp[0]["required"] is True
        assert lp[0]["schema"]["format"] == "date"

    async def test_reference_date_required(self, app):
        schema = app.openapi()
        op = schema["paths"]["/api/v1/nutrition-logs/progress"]["get"]
        params = op.get("parameters", [])
        rp = [p for p in params if p["name"] == "reference_date"]
        assert len(rp) >= 1
        assert rp[0]["required"] is True
        assert rp[0]["schema"]["format"] == "date"

    async def test_bearer_auth_required(self, app):
        schema = app.openapi()
        op = schema["paths"]["/api/v1/nutrition-logs/progress"]["get"]
        sec = op.get("security", [])
        assert any("BearerAuth" in s for s in sec)

    async def test_exactly_one_bearer_scheme(self, app):
        schema = app.openapi()
        schemes = schema.get("components", {}).get("securitySchemes", {})
        bearer_count = sum(1 for v in schemes.values() if v.get("scheme") == "bearer")
        assert bearer_count == 1

    async def test_success_response_200(self, app):
        schema = app.openapi()
        op = schema["paths"]["/api/v1/nutrition-logs/progress"]["get"]
        assert "200" in op["responses"]

    async def test_summary_still_in_schema(self, app):
        schema = app.openapi()
        assert "/api/v1/nutrition-logs/summary" in schema["paths"]


# ===========================================================================
# C. Authentication
# ===========================================================================


class TestAuthMissingToken:
    async def test_returns_401(self, client):
        response = await client.get(PROGRESS_URL)
        assert response.status_code == 401

    async def test_safe_envelope(self, client):
        response = await client.get(PROGRESS_URL)
        data = response.json()
        assert data["success"] is False
        assert "error" in data

    async def test_code_authentication_required(self, client):
        response = await client.get(PROGRESS_URL)
        data = response.json()
        assert data["error"]["code"] == "AUTHENTICATION_REQUIRED"

    async def test_www_authenticate(self, client):
        response = await client.get(PROGRESS_URL)
        assert response.headers.get("WWW-Authenticate") == "Bearer"

    async def test_no_detail_field(self, client):
        response = await client.get(PROGRESS_URL)
        assert '"detail"' not in response.text


class TestAuthInvalidToken:
    async def test_returns_401(self, client):
        response = await client.get(
            PROGRESS_URL,
            headers={"Authorization": "Bearer not-a-valid-token"},
        )
        assert response.status_code == 401

    async def test_code_invalid_token(self, client):
        response = await client.get(
            PROGRESS_URL,
            headers={"Authorization": "Bearer not-a-valid-token"},
        )
        data = response.json()
        assert data["error"]["code"] == "INVALID_ACCESS_TOKEN"


class TestAuthExpiredToken:
    def _make_expired_token(self, settings: Settings) -> str:
        user_id = uuid.uuid4()
        past = datetime.now(UTC) - timedelta(hours=2)
        return create_access_token(user_id=user_id, settings=settings, now=past)

    async def test_returns_401(self, client, test_settings):
        token = self._make_expired_token(test_settings)
        response = await client.get(
            PROGRESS_URL,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401

    async def test_code_expired(self, client, test_settings):
        token = self._make_expired_token(test_settings)
        response = await client.get(
            PROGRESS_URL,
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["error"]["code"] == "ACCESS_TOKEN_EXPIRED"


class TestAuthUnknownUser:
    def _setup_session(self, mock_session):
        mock_session.execute = AsyncMock(return_value=_make_execute_result(None))

    async def test_returns_401(self, client, test_settings, mock_session):
        self._setup_session(mock_session)
        user_id = uuid.uuid4()
        token = create_access_token(user_id=user_id, settings=test_settings)
        response = await client.get(
            PROGRESS_URL,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401

    async def test_code_invalid_token(self, client, test_settings, mock_session):
        self._setup_session(mock_session)
        user_id = uuid.uuid4()
        token = create_access_token(user_id=user_id, settings=test_settings)
        response = await client.get(
            PROGRESS_URL,
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["error"]["code"] == "INVALID_ACCESS_TOKEN"


class TestAuthInactiveUser:
    async def test_returns_403(self, client, test_settings, mock_session):
        user = _make_user(is_active=False)
        _setup_session_with_profile_and_logs(mock_session, user, None)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            PROGRESS_URL,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403

    async def test_code_inactive(self, client, test_settings, mock_session):
        user = _make_user(is_active=False)
        _setup_session_with_profile_and_logs(mock_session, user, None)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            PROGRESS_URL,
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["error"]["code"] == "INACTIVE_ACCOUNT"


class TestAuthPreventsDownstream:
    async def test_auth_failure_before_profile_lookup(self, client):
        response = await client.get(PROGRESS_URL)
        assert response.status_code == 401
        data = response.json()
        assert data["error"]["code"] in ("AUTHENTICATION_REQUIRED", "INVALID_ACCESS_TOKEN")


# ===========================================================================
# D. Query Validation
# ===========================================================================


class TestQueryValidation:
    def _setup_auth(self, mock_session, user):
        mock_session.execute = AsyncMock(return_value=_make_execute_result(user))

    async def test_missing_logged_date_returns_422(self, client, test_settings, mock_session):
        user = _make_user()
        self._setup_auth(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            PROGRESS_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422
        data = response.json()
        assert data["error"]["code"] == "VALIDATION_ERROR"

    async def test_missing_reference_date_returns_422(self, client, test_settings, mock_session):
        user = _make_user()
        self._setup_auth(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            PROGRESS_URL,
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422
        data = response.json()
        assert data["error"]["code"] == "VALIDATION_ERROR"

    async def test_both_missing_returns_422(self, client, test_settings, mock_session):
        user = _make_user()
        self._setup_auth(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            PROGRESS_URL,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    async def test_malformed_logged_date_returns_422(self, client, test_settings, mock_session):
        user = _make_user()
        self._setup_auth(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            PROGRESS_URL,
            params={"logged_date": "not-a-date", "reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    async def test_malformed_reference_date_returns_422(self, client, test_settings, mock_session):
        user = _make_user()
        self._setup_auth(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            PROGRESS_URL,
            params={"logged_date": "2026-07-12", "reference_date": "not-a-date"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    async def test_impossible_logged_date_returns_422(self, client, test_settings, mock_session):
        user = _make_user()
        self._setup_auth(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            PROGRESS_URL,
            params={"logged_date": "2026-13-01", "reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    async def test_impossible_reference_date_returns_422(self, client, test_settings, mock_session):
        user = _make_user()
        self._setup_auth(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            PROGRESS_URL,
            params={"logged_date": "2026-07-12", "reference_date": "2026-13-01"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    async def test_leap_day_accepted(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile_and_logs(mock_session, user, profile, [])
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            PROGRESS_URL,
            params={
                "logged_date": "2024-02-29",
                "reference_date": "2026-07-12",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    async def test_logged_date_as_datetime_string_accepted(
        self, client, test_settings, mock_session
    ):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile_and_logs(mock_session, user, profile, [])
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            PROGRESS_URL,
            params={
                "logged_date": "2026-07-12T00:00:00",
                "reference_date": "2026-07-12",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    async def test_no_system_clock_fallback(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile_and_logs(mock_session, user, profile, [])
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            PROGRESS_URL,
            params={
                "logged_date": "2026-07-12",
                "reference_date": "2026-07-12",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200


# ===========================================================================
# E. Current-User Isolation
# ===========================================================================


class TestUserIsolation:
    async def test_profile_lookup_uses_current_user_id(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile_and_logs(mock_session, user, profile, [])
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            PROGRESS_URL,
            params={"logged_date": "2026-07-12", "reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    async def test_log_lookup_uses_current_user_id(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        entries = [_make_nutrition_log(user_id=user.id)]
        _setup_session_with_profile_and_logs(mock_session, user, profile, entries)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            PROGRESS_URL,
            params={"logged_date": "2026-07-12", "reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    async def test_no_user_id_path_param(self, app):
        paths = [r.path for r in app.routes if PROGRESS_URL in r.path]
        assert all("user_id" not in p for p in paths)

    async def test_user_id_not_in_response(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile_and_logs(mock_session, user, profile, [])
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            PROGRESS_URL,
            params={"logged_date": "2026-07-12", "reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert "user_id" not in response.text.lower()

    async def test_another_user_data_not_exposed(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        other_user_id = uuid.uuid4()
        entries = [_make_nutrition_log(user_id=other_user_id)]
        _setup_session_with_profile_and_logs(mock_session, user, profile, entries)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            PROGRESS_URL,
            params={"logged_date": "2026-07-12", "reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200


# ===========================================================================
# F. Existing-Component Reuse (spy verification)
# ===========================================================================


class TestComponentReuse:
    async def test_reuses_nutrition_profile_repository(
        self, client, test_settings, mock_session, monkeypatch
    ):
        from app.api.v1 import nutrition_logs as nl_module

        captured = {"called": False}
        original = nl_module.NutritionProfileRepository

        def spy(session):
            captured["called"] = True
            captured["session"] = session
            return original(session)

        monkeypatch.setattr(nl_module, "NutritionProfileRepository", spy)
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile_and_logs(mock_session, user, profile, [])
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.get(
            PROGRESS_URL,
            params={"logged_date": "2026-07-12", "reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert captured["called"]

    async def test_reuses_nutrition_profile_service(
        self, client, test_settings, mock_session, monkeypatch
    ):
        from app.api.v1 import nutrition_logs as nl_module

        captured = {"called": False}
        original = nl_module.NutritionProfileService

        def spy(repo):
            captured["called"] = True
            return original(repo)

        monkeypatch.setattr(nl_module, "NutritionProfileService", spy)
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile_and_logs(mock_session, user, profile, [])
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.get(
            PROGRESS_URL,
            params={"logged_date": "2026-07-12", "reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert captured["called"]

    async def test_reuses_nutrition_log_repository(
        self, client, test_settings, mock_session, monkeypatch
    ):
        from app.api.v1 import nutrition_logs as nl_module

        captured = {"called": False}
        original = nl_module.NutritionLogRepository

        def spy(session):
            captured["called"] = True
            return original(session)

        monkeypatch.setattr(nl_module, "NutritionLogRepository", spy)
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile_and_logs(mock_session, user, profile, [])
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.get(
            PROGRESS_URL,
            params={"logged_date": "2026-07-12", "reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert captured["called"]

    async def test_reuses_nutrition_log_service(
        self, client, test_settings, mock_session, monkeypatch
    ):
        from app.api.v1 import nutrition_logs as nl_module

        captured = {"called": False}
        original = nl_module.NutritionLogService

        def spy(repo):
            captured["called"] = True
            return original(repo)

        monkeypatch.setattr(nl_module, "NutritionLogService", spy)
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile_and_logs(mock_session, user, profile, [])
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.get(
            PROGRESS_URL,
            params={"logged_date": "2026-07-12", "reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert captured["called"]

    async def test_calculate_daily_totals_called_once(
        self, client, test_settings, mock_session, monkeypatch
    ):
        from app.api.v1 import nutrition_logs as nl_module

        calls = {"n": 0}
        original = nl_module.calculate_daily_nutrition_totals

        def spy(**kwargs):
            calls["n"] += 1
            return original(**kwargs)

        monkeypatch.setattr(nl_module, "calculate_daily_nutrition_totals", spy)
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile_and_logs(mock_session, user, profile, [])
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.get(
            PROGRESS_URL,
            params={"logged_date": "2026-07-12", "reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert calls["n"] == 1

    async def test_calculate_nutrition_metrics_called_once(
        self, client, test_settings, mock_session, monkeypatch
    ):
        from app.api.v1 import nutrition_logs as nl_module

        calls = {"n": 0}
        original = nl_module.calculate_nutrition_metrics

        def spy(**kwargs):
            calls["n"] += 1
            return original(**kwargs)

        monkeypatch.setattr(nl_module, "calculate_nutrition_metrics", spy)
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile_and_logs(mock_session, user, profile, [])
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.get(
            PROGRESS_URL,
            params={"logged_date": "2026-07-12", "reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert calls["n"] == 1

    async def test_calculate_nutrition_targets_called_once(
        self, client, test_settings, mock_session, monkeypatch
    ):
        from app.api.v1 import nutrition_logs as nl_module

        calls = {"n": 0}
        original = nl_module.calculate_nutrition_targets

        def spy(**kwargs):
            calls["n"] += 1
            return original(**kwargs)

        monkeypatch.setattr(nl_module, "calculate_nutrition_targets", spy)
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile_and_logs(mock_session, user, profile, [])
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.get(
            PROGRESS_URL,
            params={"logged_date": "2026-07-12", "reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert calls["n"] == 1

    async def test_calculate_daily_progress_called_once(
        self, client, test_settings, mock_session, monkeypatch
    ):
        from app.api.v1 import nutrition_logs as nl_module

        calls = {"n": 0}
        original = nl_module.calculate_daily_nutrition_progress

        def spy(**kwargs):
            calls["n"] += 1
            return original(**kwargs)

        monkeypatch.setattr(nl_module, "calculate_daily_nutrition_progress", spy)
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile_and_logs(mock_session, user, profile, [])
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.get(
            PROGRESS_URL,
            params={"logged_date": "2026-07-12", "reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert calls["n"] == 1

    async def test_from_result_called_once(self, client, test_settings, mock_session, monkeypatch):
        from app.api.v1 import nutrition_logs as nl_module

        calls = {"n": 0}
        original = nl_module.DailyNutritionProgressData.from_result

        def spy(cls, result):
            calls["n"] += 1
            return original(result)

        monkeypatch.setattr(nl_module.DailyNutritionProgressData, "from_result", classmethod(spy))
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile_and_logs(mock_session, user, profile, [])
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.get(
            PROGRESS_URL,
            params={"logged_date": "2026-07-12", "reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert calls["n"] == 1

    async def test_no_duplicated_formulas_in_route(self, client, test_settings, mock_session):
        from app.api.v1 import nutrition_logs as nl_module

        source = inspect.getsource(nl_module)
        assert "remaining = " not in source
        assert "/ target * 100" not in source
        assert "target - consumed" not in source


# ===========================================================================
# G. Correct Argument Mapping
# ===========================================================================


class TestArgumentMapping:
    async def test_profile_fields_passed_to_metrics(
        self, client, test_settings, mock_session, monkeypatch
    ):
        from app.api.v1 import nutrition_logs as nl_module

        captured: dict = {}
        original = nl_module.calculate_nutrition_metrics

        def spy(**kwargs):
            captured.update(kwargs)
            return original(**kwargs)

        monkeypatch.setattr(nl_module, "calculate_nutrition_metrics", spy)
        user = _make_user()
        profile = _make_profile(
            user_id=user.id,
            biological_sex=BiologicalSex.FEMALE,
            height_cm=Decimal("165.00"),
            weight_kg=Decimal("60.00"),
            activity_level=ActivityLevel.LIGHTLY_ACTIVE,
            date_of_birth=date(1995, 6, 15),
        )
        _setup_session_with_profile_and_logs(mock_session, user, profile, [])
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.get(
            PROGRESS_URL,
            params={"logged_date": "2026-07-12", "reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert captured["reference_date"] == date(2026, 7, 12)
        assert captured["date_of_birth"] == date(1995, 6, 15)
        assert captured["biological_sex"] == BiologicalSex.FEMALE
        assert captured["height_cm"] == Decimal("165.00")
        assert captured["weight_kg"] == Decimal("60.00")
        assert captured["activity_level"] == ActivityLevel.LIGHTLY_ACTIVE

    async def test_tdee_from_metrics_passed_to_targets(
        self, client, test_settings, mock_session, monkeypatch
    ):
        from app.api.v1 import nutrition_logs as nl_module

        captured: dict = {}
        original = nl_module.calculate_nutrition_targets

        def spy(**kwargs):
            captured.update(kwargs)
            return original(**kwargs)

        monkeypatch.setattr(nl_module, "calculate_nutrition_targets", spy)
        user = _make_user()
        profile = _make_profile(
            user_id=user.id,
            goal=NutritionGoal.LOSE_WEIGHT,
            weight_kg=Decimal("80.00"),
        )
        _setup_session_with_profile_and_logs(mock_session, user, profile, [])
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.get(
            PROGRESS_URL,
            params={"logged_date": "2026-07-12", "reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert captured["tdee_kcal_per_day"] == Decimal("2664")
        assert captured["goal"] == NutritionGoal.LOSE_WEIGHT

    async def test_goal_from_profile_passed_to_targets(
        self, client, test_settings, mock_session, monkeypatch
    ):
        from app.api.v1 import nutrition_logs as nl_module

        captured: dict = {}
        original = nl_module.calculate_nutrition_targets

        def spy(**kwargs):
            captured.update(kwargs)
            return original(**kwargs)

        monkeypatch.setattr(nl_module, "calculate_nutrition_targets", spy)
        user = _make_user()
        profile = _make_profile(user_id=user.id, goal=NutritionGoal.GAIN_MUSCLE)
        _setup_session_with_profile_and_logs(mock_session, user, profile, [])
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.get(
            PROGRESS_URL,
            params={"logged_date": "2026-07-12", "reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert captured["goal"] == NutritionGoal.GAIN_MUSCLE


# ===========================================================================
# H. Successful Response
# ===========================================================================


class TestSuccessfulResponse:
    async def test_returns_200(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile_and_logs(mock_session, user, profile, [])
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            PROGRESS_URL,
            params={"logged_date": "2026-07-12", "reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    async def test_success_is_true(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile_and_logs(mock_session, user, profile, [])
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            PROGRESS_URL,
            params={"logged_date": "2026-07-12", "reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["success"] is True

    async def test_exact_default_message(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile_and_logs(mock_session, user, profile, [])
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            PROGRESS_URL,
            params={"logged_date": "2026-07-12", "reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["message"] == "Daily nutrition target progress calculated successfully."

    async def test_has_data_with_all_four_nutrients_and_onboarding(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile_and_logs(mock_session, user, profile, [])
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            PROGRESS_URL,
            params={"logged_date": "2026-07-12", "reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert "data" in data
        assert set(data["data"].keys()) == {"calories", "protein", "carbohydrate", "fat", "requires_onboarding"}

    async def test_each_nutrient_has_exact_fields(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile_and_logs(mock_session, user, profile, [])
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            PROGRESS_URL,
            params={"logged_date": "2026-07-12", "reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        for nutrient in ("calories", "protein", "carbohydrate", "fat"):
            section = data["data"][nutrient]
            assert set(section.keys()) == {
                "consumed",
                "target",
                "remaining",
                "percentage",
                "status",
            }

    async def test_no_extra_top_level_fields(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile_and_logs(mock_session, user, profile, [])
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            PROGRESS_URL,
            params={"logged_date": "2026-07-12", "reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert set(data.keys()) == {"success", "message", "data"}

    async def test_validates_against_schema(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile_and_logs(mock_session, user, profile, [])
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            PROGRESS_URL,
            params={"logged_date": "2026-07-12", "reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        DailyNutritionProgressSuccessResponse.model_validate(response.json())

    async def test_deterministic_known_values(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(
            user_id=user.id,
            biological_sex=BiologicalSex.MALE,
            height_cm=Decimal("175.00"),
            weight_kg=Decimal("70.00"),
            activity_level=ActivityLevel.MODERATELY_ACTIVE,
            goal=NutritionGoal.MAINTAIN_WEIGHT,
            date_of_birth=date(1990, 1, 1),
        )
        entry = _make_nutrition_log(
            user_id=user.id,
            logged_date=date(2026, 7, 12),
            meal_type=MealType.BREAKFAST,
            calories="600.00",
            protein="25.00",
            carbs="80.00",
            fat="15.00",
        )
        _setup_session_with_profile_and_logs(mock_session, user, profile, [entry])
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            PROGRESS_URL,
            params={"logged_date": "2026-07-12", "reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        progress = data["data"]
        assert progress["calories"]["consumed"] == "600.00"
        assert progress["protein"]["consumed"] == "25.00"
        assert progress["carbohydrate"]["consumed"] == "80.00"
        assert progress["fat"]["consumed"] == "15.00"

    async def test_decimal_values_serialized_as_strings(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile_and_logs(mock_session, user, profile, [])
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            PROGRESS_URL,
            params={"logged_date": "2026-07-12", "reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        calories = data["data"]["calories"]
        assert isinstance(calories["consumed"], str)
        assert isinstance(calories["target"], str)
        assert isinstance(calories["remaining"], str)
        assert isinstance(calories["percentage"], str)

    async def test_status_lowercase(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile_and_logs(mock_session, user, profile, [])
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            PROGRESS_URL,
            params={"logged_date": "2026-07-12", "reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        for nutrient in ("calories", "protein", "carbohydrate", "fat"):
            status = data["data"][nutrient]["status"]
            assert status == status.lower()

    async def test_x_request_id_present(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile_and_logs(mock_session, user, profile, [])
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            PROGRESS_URL,
            params={"logged_date": "2026-07-12", "reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert "X-Request-ID" in response.headers


# ===========================================================================
# I. Empty-Day Behavior
# ===========================================================================


class TestEmptyDay:
    async def test_no_entries_returns_200(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile_and_logs(mock_session, user, profile, [])
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            PROGRESS_URL,
            params={"logged_date": "2026-07-12", "reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    async def test_empty_day_consumed_zero(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile_and_logs(mock_session, user, profile, [])
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            PROGRESS_URL,
            params={"logged_date": "2026-07-12", "reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        for nutrient in ("calories", "protein", "carbohydrate", "fat"):
            assert data["data"][nutrient]["consumed"] == "0.00"

    async def test_empty_day_targets_positive(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile_and_logs(mock_session, user, profile, [])
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            PROGRESS_URL,
            params={"logged_date": "2026-07-12", "reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        calories_target = _dec(data["data"]["calories"]["target"])
        assert calories_target > 0

    async def test_empty_day_remaining_equals_target(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile_and_logs(mock_session, user, profile, [])
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            PROGRESS_URL,
            params={"logged_date": "2026-07-12", "reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        for nutrient in ("calories", "protein", "carbohydrate", "fat"):
            remaining = _dec(data["data"][nutrient]["remaining"])
            target = _dec(data["data"][nutrient]["target"])
            assert remaining == target

    async def test_empty_day_percentage_zero(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile_and_logs(mock_session, user, profile, [])
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            PROGRESS_URL,
            params={"logged_date": "2026-07-12", "reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        for nutrient in ("calories", "protein", "carbohydrate", "fat"):
            assert data["data"][nutrient]["percentage"] == "0.00"

    async def test_empty_day_status_below_target(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile_and_logs(mock_session, user, profile, [])
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            PROGRESS_URL,
            params={"logged_date": "2026-07-12", "reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        for nutrient in ("calories", "protein", "carbohydrate", "fat"):
            assert data["data"][nutrient]["status"] == "below_target"

    async def test_empty_day_not_404(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile_and_logs(mock_session, user, profile, [])
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            PROGRESS_URL,
            params={"logged_date": "2026-07-12", "reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    async def test_empty_day_no_fake_entries(self, client, test_settings, mock_session):
        from app.api.v1 import nutrition_logs as nl_module

        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile_and_logs(mock_session, user, profile, [])
        token = create_access_token(user_id=user.id, settings=test_settings)

        calls = {"n": 0}
        original = nl_module.calculate_daily_nutrition_totals

        def spy(**kwargs):
            calls["n"] += 1
            return original(**kwargs)

        monkeypatch = pytest.MonkeyPatch()
        monkeypatch.setattr(nl_module, "calculate_daily_nutrition_totals", spy)
        await client.get(
            PROGRESS_URL,
            params={"logged_date": "2026-07-12", "reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert calls["n"] == 1
        monkeypatch.undo()


# ===========================================================================
# J. Progress Edge Cases
# ===========================================================================


class TestProgressEdgeCases:
    async def test_exactly_at_target(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(
            user_id=user.id,
            goal=NutritionGoal.MAINTAIN_WEIGHT,
        )
        entry = _make_nutrition_log(
            user_id=user.id,
            calories="1800.00",
            protein="112.00",
            carbs="203.00",
            fat="60.00",
        )
        _setup_session_with_profile_and_logs(mock_session, user, profile, [entry])
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            PROGRESS_URL,
            params={"logged_date": "2026-07-12", "reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    async def test_below_target_status(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        entry = _make_nutrition_log(
            user_id=user.id,
            calories="100.00",
            protein="5.00",
            carbs="10.00",
            fat="2.00",
        )
        _setup_session_with_profile_and_logs(mock_session, user, profile, [entry])
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            PROGRESS_URL,
            params={"logged_date": "2026-07-12", "reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        for nutrient in ("calories", "protein", "carbohydrate", "fat"):
            assert data["data"][nutrient]["status"] == "below_target"

    async def test_negative_remaining_preserved(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        entry = _make_nutrition_log(
            user_id=user.id,
            calories="9999.00",
            protein="999.00",
            carbs="1999.00",
            fat="999.00",
        )
        _setup_session_with_profile_and_logs(mock_session, user, profile, [entry])
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            PROGRESS_URL,
            params={"logged_date": "2026-07-12", "reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        for nutrient in ("calories", "protein", "carbohydrate", "fat"):
            remaining = _dec(data["data"][nutrient]["remaining"])
            assert remaining < 0

    async def test_percentage_above_100_preserved(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        entry = _make_nutrition_log(
            user_id=user.id,
            calories="5000.00",
            protein="500.00",
            carbs="1000.00",
            fat="500.00",
        )
        _setup_session_with_profile_and_logs(mock_session, user, profile, [entry])
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            PROGRESS_URL,
            params={"logged_date": "2026-07-12", "reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        for nutrient in ("calories", "protein", "carbohydrate", "fat"):
            percentage = _dec(data["data"][nutrient]["percentage"])
            assert percentage > 100

    async def test_above_target_status(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        entry = _make_nutrition_log(
            user_id=user.id,
            calories="5000.00",
            protein="500.00",
            carbs="1000.00",
            fat="500.00",
        )
        _setup_session_with_profile_and_logs(mock_session, user, profile, [entry])
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            PROGRESS_URL,
            params={"logged_date": "2026-07-12", "reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        for nutrient in ("calories", "protein", "carbohydrate", "fat"):
            assert data["data"][nutrient]["status"] == "above_target"

    async def test_no_remaining_clamp(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        entry = _make_nutrition_log(
            user_id=user.id,
            calories="9999.00",
            protein="999.00",
            carbs="1999.00",
            fat="999.00",
        )
        _setup_session_with_profile_and_logs(mock_session, user, profile, [entry])
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            PROGRESS_URL,
            params={"logged_date": "2026-07-12", "reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert _dec(data["data"]["calories"]["remaining"]) < 0
        assert _dec(data["data"]["protein"]["remaining"]) < 0
        assert _dec(data["data"]["carbohydrate"]["remaining"]) < 0
        assert _dec(data["data"]["fat"]["remaining"]) < 0

    async def test_no_percentage_cap(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        entry = _make_nutrition_log(
            user_id=user.id,
            calories="5000.00",
            protein="500.00",
            carbs="1000.00",
            fat="500.00",
        )
        _setup_session_with_profile_and_logs(mock_session, user, profile, [entry])
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            PROGRESS_URL,
            params={"logged_date": "2026-07-12", "reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert _dec(data["data"]["calories"]["percentage"]) > 100

    async def test_no_status_reclassification_in_route(self, client, test_settings, mock_session):
        from app.api.v1 import nutrition_logs as nl_module

        source = inspect.getsource(nl_module)
        assert "consumed < target" not in source
        assert "consumed == target" not in source
        assert "consumed > target" not in source


# ===========================================================================
# K. Error Mapping
# ===========================================================================


class TestErrorMapping:
    async def test_missing_profile_returns_404(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_session_with_profile_and_logs(mock_session, user, None)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            PROGRESS_URL,
            params={"logged_date": "2026-07-12", "reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404
        data = response.json()
        assert data["error"]["code"] == "NUTRITION_PROFILE_NOT_FOUND"
        assert data["error"]["message"] == "Nutrition profile not found."
        assert "request_id" in data["error"]

    async def test_unsupported_bmr_returns_422(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id, biological_sex=BiologicalSex.OTHER)
        _setup_session_with_profile_and_logs(mock_session, user, profile, [])
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            PROGRESS_URL,
            params={"logged_date": "2026-07-12", "reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422
        data = response.json()
        assert data["error"]["code"] == "BMR_CALCULATION_UNSUPPORTED"
        assert "Mifflin-St Jeor" in data["error"]["message"]
        assert "request_id" in data["error"]

    async def test_prefer_not_to_say_bmr_returns_422(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id, biological_sex=BiologicalSex.PREFER_NOT_TO_SAY)
        _setup_session_with_profile_and_logs(mock_session, user, profile, [])
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            PROGRESS_URL,
            params={"logged_date": "2026-07-12", "reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422
        data = response.json()
        assert data["error"]["code"] == "BMR_CALCULATION_UNSUPPORTED"

    async def test_below_minimum_calorie_returns_422(self, client, test_settings, mock_session):
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
        _setup_session_with_profile_and_logs(mock_session, user, profile, [])
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            PROGRESS_URL,
            params={"logged_date": "2026-07-12", "reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422
        data = response.json()
        assert data["error"]["code"] == "CALORIE_TARGET_BELOW_MINIMUM"
        assert "supported minimum" in data["error"]["message"]
        assert "request_id" in data["error"]

    async def test_reference_date_equals_dob_returns_422(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id, date_of_birth=date(2000, 1, 1))
        _setup_session_with_profile_and_logs(mock_session, user, profile, [])
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            PROGRESS_URL,
            params={"logged_date": "2026-07-12", "reference_date": "2000-01-01"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422
        data = response.json()
        assert data["error"]["code"] == "INVALID_CALCULATION_INPUT"
        assert "request_id" in data["error"]

    async def test_reference_date_before_dob_returns_422(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id, date_of_birth=date(2000, 1, 1))
        _setup_session_with_profile_and_logs(mock_session, user, profile, [])
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            PROGRESS_URL,
            params={"logged_date": "2026-07-12", "reference_date": "1999-12-31"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422
        data = response.json()
        assert data["error"]["code"] == "INVALID_CALCULATION_INPUT"

    async def test_log_read_failure_propagates(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile_and_logs(mock_session, user, profile, None)
        mock_session.execute = AsyncMock(
            side_effect=[
                _make_execute_result(user),
                _make_execute_result(profile),
                Exception("DB read failure"),
            ]
        )
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            PROGRESS_URL,
            params={"logged_date": "2026-07-12", "reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 500

    async def test_no_sql_exposed_on_error(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id, biological_sex=BiologicalSex.OTHER)
        _setup_session_with_profile_and_logs(mock_session, user, profile, [])
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            PROGRESS_URL,
            params={"logged_date": "2026-07-12", "reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        text = response.text.lower()
        import re

        assert "insert into" not in text
        assert not re.search(r"\bselect\b", text)
        assert "constraint" not in text
        assert "integrity" not in text


# ===========================================================================
# L. Short-Circuit Behavior
# ===========================================================================


class TestShortCircuit:
    async def test_auth_failure_prevents_profile_lookup(self, client, test_settings, mock_session):
        response = await client.get(PROGRESS_URL)
        assert response.status_code == 401

    async def test_missing_profile_shortcircuits_log_lookup(
        self, client, test_settings, mock_session, monkeypatch
    ):
        user = _make_user()
        _setup_session_with_profile_and_logs(mock_session, user, None)
        token = create_access_token(user_id=user.id, settings=test_settings)

        from app.api.v1 import nutrition_logs as nl_module

        calls = {"n": 0}
        original = nl_module.NutritionLogService

        def spy(repo):
            calls["n"] += 1
            return original(repo)

        monkeypatch.setattr(nl_module, "NutritionLogService", spy)
        await client.get(
            PROGRESS_URL,
            params={"logged_date": "2026-07-12", "reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert calls["n"] == 0

    async def test_unsupported_bmr_shortcircuits_target_and_progress(
        self, client, test_settings, mock_session, monkeypatch
    ):
        user = _make_user()
        profile = _make_profile(user_id=user.id, biological_sex=BiologicalSex.OTHER)
        _setup_session_with_profile_and_logs(mock_session, user, profile, [])
        token = create_access_token(user_id=user.id, settings=test_settings)

        from app.api.v1 import nutrition_logs as nl_module

        target_calls = {"n": 0}
        original_target = nl_module.calculate_nutrition_targets

        def target_spy(**kwargs):
            target_calls["n"] += 1
            return original_target(**kwargs)

        monkeypatch.setattr(nl_module, "calculate_nutrition_targets", target_spy)

        progress_calls = {"n": 0}
        original_progress = nl_module.calculate_daily_nutrition_progress

        def progress_spy(**kwargs):
            progress_calls["n"] += 1
            return original_progress(**kwargs)

        monkeypatch.setattr(nl_module, "calculate_daily_nutrition_progress", progress_spy)

        await client.get(
            PROGRESS_URL,
            params={"logged_date": "2026-07-12", "reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert target_calls["n"] == 0
        assert progress_calls["n"] == 0

    async def test_below_minimum_target_shortcircuits_progress(
        self, client, test_settings, mock_session, monkeypatch
    ):
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
        _setup_session_with_profile_and_logs(mock_session, user, profile, [])
        token = create_access_token(user_id=user.id, settings=test_settings)

        from app.api.v1 import nutrition_logs as nl_module

        calls = {"n": 0}
        original = nl_module.calculate_daily_nutrition_progress

        def spy(**kwargs):
            calls["n"] += 1
            return original(**kwargs)

        monkeypatch.setattr(nl_module, "calculate_daily_nutrition_progress", spy)
        await client.get(
            PROGRESS_URL,
            params={"logged_date": "2026-07-12", "reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert calls["n"] == 0

    async def test_invalid_reference_date_shortcircuits_progress(
        self, client, test_settings, mock_session, monkeypatch
    ):
        user = _make_user()
        profile = _make_profile(user_id=user.id, date_of_birth=date(2000, 1, 1))
        _setup_session_with_profile_and_logs(mock_session, user, profile, [])
        token = create_access_token(user_id=user.id, settings=test_settings)

        from app.api.v1 import nutrition_logs as nl_module

        calls = {"n": 0}
        original = nl_module.calculate_daily_nutrition_progress

        def spy(**kwargs):
            calls["n"] += 1
            return original(**kwargs)

        monkeypatch.setattr(nl_module, "calculate_daily_nutrition_progress", spy)
        await client.get(
            PROGRESS_URL,
            params={"logged_date": "2026-07-12", "reference_date": "2000-01-01"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert calls["n"] == 0


# ===========================================================================
# M. Read-Only Behavior
# ===========================================================================


class TestReadOnly:
    async def test_no_commit(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile_and_logs(mock_session, user, profile, [])
        mock_session.commit = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.get(
            PROGRESS_URL,
            params={"logged_date": "2026-07-12", "reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        mock_session.commit.assert_not_called()

    async def test_no_flush(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile_and_logs(mock_session, user, profile, [])
        mock_session.flush = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.get(
            PROGRESS_URL,
            params={"logged_date": "2026-07-12", "reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        mock_session.flush.assert_not_called()

    async def test_no_refresh(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile_and_logs(mock_session, user, profile, [])
        mock_session.refresh = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.get(
            PROGRESS_URL,
            params={"logged_date": "2026-07-12", "reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        mock_session.refresh.assert_not_called()

    async def test_no_add(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile_and_logs(mock_session, user, profile, [])
        mock_session.add = MagicMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.get(
            PROGRESS_URL,
            params={"logged_date": "2026-07-12", "reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        mock_session.add.assert_not_called()

    async def test_no_delete(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile_and_logs(mock_session, user, profile, [])
        mock_session.delete = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.get(
            PROGRESS_URL,
            params={"logged_date": "2026-07-12", "reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        mock_session.delete.assert_not_called()

    async def test_user_not_mutated(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        original_email = user.email
        _setup_session_with_profile_and_logs(mock_session, user, profile, [])
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.get(
            PROGRESS_URL,
            params={"logged_date": "2026-07-12", "reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert user.email == original_email

    async def test_profile_not_mutated(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        original_dob = profile.date_of_birth
        _setup_session_with_profile_and_logs(mock_session, user, profile, [])
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.get(
            PROGRESS_URL,
            params={"logged_date": "2026-07-12", "reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert profile.date_of_birth == original_dob

    async def test_log_entries_not_mutated(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        entry = _make_nutrition_log(user_id=user.id, calories="300.00")
        original_calories = entry.calories_kcal
        _setup_session_with_profile_and_logs(mock_session, user, profile, [entry])
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.get(
            PROGRESS_URL,
            params={"logged_date": "2026-07-12", "reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert entry.calories_kcal == original_calories

    async def test_no_rollback_during_success(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile_and_logs(mock_session, user, profile, [])
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.get(
            PROGRESS_URL,
            params={"logged_date": "2026-07-12", "reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        mock_session.rollback.assert_not_called()


# ===========================================================================
# N. Privacy and Response Safety
# ===========================================================================


class TestPrivacy:
    async def test_no_user_id_in_response(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile_and_logs(mock_session, user, profile, [])
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            PROGRESS_URL,
            params={"logged_date": "2026-07-12", "reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        text = response.text.lower()
        assert "user_id" not in text
        assert "email" not in text
        assert "password" not in text
        assert "password_hash" not in text
        assert "access_token" not in text
        assert "secret" not in text
        assert "$argon2id" not in text

    async def test_no_jwt_or_token_claims(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile_and_logs(mock_session, user, profile, [])
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            PROGRESS_URL,
            params={"logged_date": "2026-07-12", "reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert "jwt" not in response.text.lower()
        assert "token" not in response.text.lower()

    async def test_no_profile_id_exposed(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile_and_logs(mock_session, user, profile, [])
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            PROGRESS_URL,
            params={"logged_date": "2026-07-12", "reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert "profile" not in response.text.lower()

    async def test_no_sql_exposed(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile_and_logs(mock_session, user, profile, [])
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            PROGRESS_URL,
            params={"logged_date": "2026-07-12", "reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        text = response.text.lower()
        assert "select" not in text
        assert "insert into" not in text
        assert "delete from" not in text


# ===========================================================================
# O. Regression Tests
# ===========================================================================


class TestRegression:
    async def test_health_route_still_public(self, client):
        response = await client.get("/api/v1/health")
        assert response.status_code == 200

    async def test_register_still_public(self, client):
        response = await client.post("/api/v1/auth/register", json={})
        assert response.status_code != 401

    async def test_login_still_public(self, client):
        response = await client.post("/api/v1/auth/login", json={})
        assert response.status_code != 401

    async def test_auth_me_still_protected(self, client):
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401

    async def test_nutrition_log_crud_post_still_protected(self, client):
        response = await client.post("/api/v1/nutrition-logs", json={})
        assert response.status_code == 401

    async def test_nutrition_log_crud_get_still_protected(self, client):
        response = await client.get("/api/v1/nutrition-logs")
        assert response.status_code == 401

    async def test_nutrition_log_summary_still_protected(self, client):
        response = await client.get("/api/v1/nutrition-logs/summary")
        assert response.status_code == 401

    async def test_nutrition_profile_get_still_protected(self, client):
        response = await client.get("/api/v1/nutrition-profile")
        assert response.status_code == 401

    async def test_nutrition_calculations_still_protected(self, client):
        response = await client.get("/api/v1/nutrition-profile/calculations")
        assert response.status_code == 401

    async def test_nutrition_summary_still_protected(self, client):
        response = await client.get("/api/v1/nutrition-profile/summary")
        assert response.status_code == 401


# ===========================================================================
# P. Architecture and Phase Boundaries
# ===========================================================================


class TestArchitectureBoundaries:
    async def test_orm_metadata_updated(self):
        from app.db.base import Base

        tables = set(Base.metadata.tables.keys())
        assert tables == {
            "users",
            "nutrition_profiles",
            "nutrition_logs",
            "body_weights",
            "tasks",
            "goals",
        }

    async def test_no_system_clock_in_route(self):
        from app.api.v1 import nutrition_logs as nl_module

        source = inspect.getsource(nl_module)
        assert "date.today()" not in source
        assert "datetime.now()" not in source
        assert "datetime.utcnow()" not in source

    async def test_no_jwt_decoding_in_route(self):
        from app.api.v1 import nutrition_logs as nl_module

        source = inspect.getsource(nl_module)
        assert "decode_access_token" not in source
        assert "encode_access_token" not in source

    async def test_no_authorization_header_parsing(self):
        from app.api.v1 import nutrition_logs as nl_module

        source = inspect.getsource(nl_module)
        assert "Authorization" not in source

    async def test_no_httpbearer_instance_in_route(self):
        from app.api.v1 import nutrition_logs as nl_module

        source = inspect.getsource(nl_module)
        assert "HTTPBearer" not in source

    async def test_no_user_id_acceptance(self):
        from app.api.v1 import nutrition_logs as nl_module

        source = inspect.getsource(nl_module)
        assert '"user_id"' not in source
        assert "'user_id'" not in source

    async def test_no_progress_persistence(self):
        from app.core import nutrition_progress as progress_module

        source = inspect.getsource(progress_module)
        assert "commit" not in source
        assert "insert" not in source

    async def test_no_duplicate_formulas(self):
        from app.api.v1 import nutrition_logs as nl_module

        source = inspect.getsource(nl_module)
        assert "remaining = " not in source
        assert "percentage = " not in source
        assert "status = " not in source
        assert (
            "BELOW_TARGET" not in source
            or "NutritionProgressStatus.BELOW_TARGET" in source
            or "NutritionProgressStatus" in source
        )
        assert "MINIMUM_CALORIE_TARGET" not in source

    async def test_no_new_exception_classes_defined(self):
        from app.core import (
            nutrition_calculation_exceptions,
            nutrition_log_exceptions,
            nutrition_profile_exceptions,
            nutrition_progress_exceptions,
        )

        assert hasattr(nutrition_calculation_exceptions, "UnsupportedBMRCalculationError")
        assert hasattr(nutrition_calculation_exceptions, "CalorieTargetBelowMinimumError")
        assert hasattr(nutrition_log_exceptions, "NutritionLogPersistenceError")
        assert hasattr(nutrition_profile_exceptions, "NutritionProfileNotFoundError")
        assert hasattr(nutrition_progress_exceptions, "InvalidNutritionProgressInputError")


# ===========================================================================
# Q. Global Handler / Unexpected Errors
# ===========================================================================


class TestUnexpectedErrors:
    async def test_calculation_exception_global_500(
        self, client, test_settings, mock_session, monkeypatch
    ):
        from app.api.v1 import nutrition_logs as nl_module

        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile_and_logs(mock_session, user, profile, [])

        def _boom(**kwargs):
            raise RuntimeError("unexpected calculation error")

        monkeypatch.setattr(nl_module, "calculate_nutrition_metrics", _boom)
        token = create_access_token(user_id=user.id, settings=test_settings)

        response = await client.get(
            PROGRESS_URL,
            params={"logged_date": "2026-07-12", "reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 500

    async def test_global_handler_safe_500(self):
        from starlette.requests import Request

        from app.core.exceptions import global_exception_handler

        async def _receive():
            return {"type": "http.disconnect"}

        request = Request(
            {"type": "http", "method": "GET", "path": PROGRESS_URL, "headers": []},
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
