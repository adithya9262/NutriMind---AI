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
from app.schemas.nutrition_summaries import (
    EXPECTED_NUTRITION_SUMMARY_CODES,
    EXPECTED_NUTRITION_SUMMARY_ITEM_COUNT,
    NutritionSummarySuccessResponse,
    NutritionSummaryTone,
)

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


SUMMARY_URL = "/api/v1/nutrition-profile/summary"


# ===========================================================================
# PART 1 — Route registration
# ===========================================================================


class TestRouteRegistration:
    async def test_summary_route_exists(self, client):
        response = await client.get(SUMMARY_URL, params={"reference_date": "2026-07-12"})
        assert response.status_code != 404

    async def test_summary_accepts_get(self, client):
        response = await client.get(SUMMARY_URL, params={"reference_date": "2026-07-12"})
        assert response.status_code != 405

    async def test_post_rejected(self, client):
        response = await client.post(SUMMARY_URL, params={"reference_date": "2026-07-12"})
        assert response.status_code == 405

    async def test_patch_rejected(self, client):
        response = await client.patch(SUMMARY_URL, params={"reference_date": "2026-07-12"})
        assert response.status_code == 405

    async def test_delete_rejected(self, client):
        response = await client.delete(SUMMARY_URL, params={"reference_date": "2026-07-12"})
        assert response.status_code == 405

    async def test_put_rejected(self, client):
        response = await client.put(SUMMARY_URL, params={"reference_date": "2026-07-12"})
        assert response.status_code == 405

    async def test_no_duplicate_summary_route(self, app):
        paths = [r.path for r in app.routes if "nutrition-profile/summary" in r.path]
        assert paths.count("/api/v1/nutrition-profile/summary") == 1

    async def test_calculations_route_still_registered(self, app):
        paths = [r.path for r in app.routes if "nutrition-profile" in r.path]
        assert "/api/v1/nutrition-profile/calculations" in paths

    async def test_profile_routes_still_registered(self, app):
        methods: set[str] = set()
        for r in app.routes:
            if getattr(r, "path", None) == "/api/v1/nutrition-profile":
                methods.update(m.upper() for m in r.methods)
        assert "GET" in methods
        assert "POST" in methods
        assert "PATCH" in methods

    async def test_summary_has_only_get(self, app):
        route = next(r for r in app.routes if r.path == "/api/v1/nutrition-profile/summary")
        methods = {m.upper() for m in route.methods}
        assert "GET" in methods
        assert "POST" not in methods
        assert "PATCH" not in methods
        assert "DELETE" not in methods


# ===========================================================================
# PART 2 — OpenAPI
# ===========================================================================


class TestOpenAPI:
    async def test_summary_path_exists(self, app):
        spec = app.openapi()
        assert "/api/v1/nutrition-profile/summary" in spec["paths"]

    async def test_get_operation_exists(self, app):
        spec = app.openapi()
        op = spec["paths"]["/api/v1/nutrition-profile/summary"]
        assert "get" in op

    async def test_bearer_auth_required(self, app):
        spec = app.openapi()
        op = spec["paths"]["/api/v1/nutrition-profile/summary"]["get"]
        assert "security" in op
        assert any("BearerAuth" in s for s in op["security"])

    async def test_exactly_one_bearer_scheme(self, app):
        spec = app.openapi()
        schemes = spec["components"]["securitySchemes"]
        assert list(schemes.keys()) == ["BearerAuth"]

    async def test_reference_date_present(self, app):
        spec = app.openapi()
        op = spec["paths"]["/api/v1/nutrition-profile/summary"]["get"]
        params = op.get("parameters", [])
        ref_params = [p for p in params if p["name"] == "reference_date"]
        assert ref_params

    async def test_reference_date_required(self, app):
        spec = app.openapi()
        op = spec["paths"]["/api/v1/nutrition-profile/summary"]["get"]
        params = op.get("parameters", [])
        ref_params = [p for p in params if p["name"] == "reference_date"]
        assert ref_params[0]["required"] is True

    async def test_reference_date_query_param(self, app):
        spec = app.openapi()
        op = spec["paths"]["/api/v1/nutrition-profile/summary"]["get"]
        params = op.get("parameters", [])
        ref_params = [p for p in params if p["name"] == "reference_date"]
        assert ref_params[0]["in"] == "query"

    async def test_reference_date_date_format(self, app):
        spec = app.openapi()
        op = spec["paths"]["/api/v1/nutrition-profile/summary"]["get"]
        params = op.get("parameters", [])
        ref_params = [p for p in params if p["name"] == "reference_date"]
        assert ref_params[0]["schema"]["type"] == "string"
        assert ref_params[0]["schema"]["format"] == "date"

    async def test_no_request_body(self, app):
        spec = app.openapi()
        op = spec["paths"]["/api/v1/nutrition-profile/summary"]["get"]
        assert "requestBody" not in op

    async def test_public_routes_remain_public(self, app):
        spec = app.openapi()
        assert "security" not in spec["paths"]["/api/v1/auth/register"]["post"]
        assert "security" not in spec["paths"]["/api/v1/auth/login"]["post"]
        assert "security" not in spec["paths"]["/api/v1/health"]["get"]


# ===========================================================================
# PART 3 — Authentication
# ===========================================================================


class TestAuthMissingToken:
    async def test_returns_401(self, client):
        response = await client.get(SUMMARY_URL, params={"reference_date": "2026-07-12"})
        assert response.status_code == 401

    async def test_safe_envelope(self, client):
        response = await client.get(SUMMARY_URL, params={"reference_date": "2026-07-12"})
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "AUTHENTICATION_REQUIRED"
        assert "request_id" in data["error"]

    async def test_www_authenticate(self, client):
        response = await client.get(SUMMARY_URL, params={"reference_date": "2026-07-12"})
        assert response.headers.get("WWW-Authenticate") == "Bearer"

    async def test_no_detail_field(self, client):
        response = await client.get(SUMMARY_URL, params={"reference_date": "2026-07-12"})
        assert '"detail"' not in response.text


class TestAuthEmptyBearer:
    async def test_empty_token_401(self, client):
        response = await client.get(
            SUMMARY_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": "Bearer "},
        )
        assert response.status_code == 401

    async def test_whitespace_only_401(self, client):
        response = await client.get(
            SUMMARY_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": "Bearer    "},
        )
        assert response.status_code == 401


class TestAuthWrongScheme:
    async def test_basic_scheme_401(self, client):
        response = await client.get(
            SUMMARY_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": "Basic abcdef"},
        )
        assert response.status_code == 401


class TestAuthInvalidToken:
    async def test_returns_401(self, client):
        response = await client.get(
            SUMMARY_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": "Bearer not-a-valid-token"},
        )
        assert response.status_code == 401

    async def test_code_invalid_token(self, client):
        response = await client.get(
            SUMMARY_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": "Bearer not-a-valid-token"},
        )
        assert response.json()["error"]["code"] == "INVALID_ACCESS_TOKEN"


class TestAuthExpiredToken:
    def _make_expired_token(self, settings: Settings) -> str:
        past = datetime.now(UTC) - timedelta(hours=2)
        return create_access_token(user_id=uuid.uuid4(), settings=settings, now=past)

    async def test_returns_401(self, client, test_settings):
        token = self._make_expired_token(test_settings)
        response = await client.get(
            SUMMARY_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401

    async def test_code_expired(self, client, test_settings):
        token = self._make_expired_token(test_settings)
        response = await client.get(
            SUMMARY_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.json()["error"]["code"] == "ACCESS_TOKEN_EXPIRED"


class TestAuthUnknownUser:
    async def test_returns_401(self, client, test_settings, mock_session):
        _setup_session_with_profile(mock_session, None, None)
        token = create_access_token(user_id=uuid.uuid4(), settings=test_settings)
        response = await client.get(
            SUMMARY_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401

    async def test_profile_lookup_not_called(self, client, test_settings, mock_session):
        _setup_session_with_profile(mock_session, None, None)
        token = create_access_token(user_id=uuid.uuid4(), settings=test_settings)
        await client.get(
            SUMMARY_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        mock_session.execute.assert_awaited_once()


class TestAuthInactiveUser:
    async def test_returns_403(self, client, test_settings, mock_session):
        user = _make_user(is_active=False)
        _setup_session_with_profile(mock_session, user, None)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            SUMMARY_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403

    async def test_code_inactive(self, client, test_settings, mock_session):
        user = _make_user(is_active=False)
        _setup_session_with_profile(mock_session, user, None)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            SUMMARY_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.json()["error"]["code"] == "INACTIVE_ACCOUNT"

    async def test_profile_lookup_not_called(self, client, test_settings, mock_session):
        user = _make_user(is_active=False)
        _setup_session_with_profile(mock_session, user, None)
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.get(
            SUMMARY_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        mock_session.execute.assert_awaited_once()


class TestAuthValidUserReachesEndpoint:
    async def test_reaches_endpoint(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            SUMMARY_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code not in (401, 403)


# ===========================================================================
# PART 4 — reference_date validation
# ===========================================================================


class TestReferenceDateValidation:
    async def test_missing_returns_422(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            SUMMARY_URL,
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
            SUMMARY_URL,
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
            SUMMARY_URL,
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
            SUMMARY_URL,
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
            SUMMARY_URL,
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
            SUMMARY_URL,
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
            SUMMARY_URL,
            params={"reference_date": "2026-07-12T10:00:00"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    async def test_leap_day_parsed(self, client, test_settings, mock_session, monkeypatch):
        user = _make_user()
        profile = _make_profile(user_id=user.id, date_of_birth=date(2000, 2, 29))
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)

        from app.api.v1 import nutrition_profile as np_module

        captured: dict = {}
        original = np_module.calculate_nutrition_metrics

        def spy(**kwargs):
            captured.update(kwargs)
            return original(**kwargs)

        monkeypatch.setattr(np_module, "calculate_nutrition_metrics", spy)
        response = await client.get(
            SUMMARY_URL,
            params={"reference_date": "2024-02-29"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert captured["reference_date"] == date(2024, 2, 29)

    async def test_no_default_date_used(self, client, test_settings, mock_session, monkeypatch):
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
            SUMMARY_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert captured.get("reference_date") == date(2026, 7, 12)
        assert captured["reference_date"] != date(1900, 1, 1)


# ===========================================================================
# PART 5 — User isolation
# ===========================================================================


class TestUserIsolation:
    async def test_lookup_uses_current_user_id(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            SUMMARY_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert mock_session.execute.await_count == 2

    async def test_no_user_id_query_param(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        other_id = uuid.uuid4()
        response = await client.get(
            SUMMARY_URL,
            params={"reference_date": "2026-07-12", "user_id": str(other_id)},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert profile.user_id == user.id

    async def test_no_body_user_id_accepted(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            SUMMARY_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert profile.user_id == user.id

    async def test_token_string_not_used_for_lookup(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            SUMMARY_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert profile.user_id == user.id


# ===========================================================================
# PART 6 — Repository / service reuse
# ===========================================================================


class TestRepositoryServiceReuse:
    async def test_uses_existing_repository(self, client, test_settings, mock_session, monkeypatch):
        from app.api.v1 import nutrition_profile as np_module

        captured: dict = {}
        original = np_module.NutritionProfileRepository

        def spy(session):
            captured["session"] = session
            return original(session)

        monkeypatch.setattr(np_module, "NutritionProfileRepository", spy)
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.get(
            SUMMARY_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert "session" in captured
        assert captured["session"] is mock_session

    async def test_uses_existing_service(self, client, test_settings, mock_session, monkeypatch):
        from app.api.v1 import nutrition_profile as np_module

        captured: dict = {}
        original = np_module.NutritionProfileService

        def spy(repo):
            captured["repo"] = repo
            return original(repo)

        monkeypatch.setattr(np_module, "NutritionProfileService", spy)
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.get(
            SUMMARY_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert "repo" in captured

    async def test_missing_profile_returns_200_incomplete(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_session_for_create(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            SUMMARY_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"] is None
        assert "incomplete" in data["message"].lower()

    async def test_no_direct_orm_query(self, client, test_settings, mock_session):
        from app.api.v1 import nutrition_profile as np_module

        source = inspect.getsource(np_module)
        assert "select(" not in source
        assert "session.execute" not in source


# ===========================================================================
# PART 7 — Calculation orchestration
# ===========================================================================


class TestCalculationOrchestration:
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
            SUMMARY_URL,
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
            SUMMARY_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert calls["n"] == 1

    async def test_metrics_args(self, client, test_settings, mock_session, monkeypatch):
        user = _make_user()
        profile = _make_profile(
            user_id=user.id,
            biological_sex=BiologicalSex.FEMALE,
            height_cm=Decimal("165.00"),
            weight_kg=Decimal("60.00"),
            activity_level=ActivityLevel.LIGHTLY_ACTIVE,
            date_of_birth=date(1995, 6, 15),
        )
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
            SUMMARY_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert captured["reference_date"] == date(2026, 7, 12)
        assert captured["date_of_birth"] == date(1995, 6, 15)
        assert captured["biological_sex"] == BiologicalSex.FEMALE
        assert captured["height_cm"] == Decimal("165.00")
        assert captured["weight_kg"] == Decimal("60.00")
        assert captured["activity_level"] == ActivityLevel.LIGHTLY_ACTIVE

    async def test_targets_args(self, client, test_settings, mock_session, monkeypatch):
        user = _make_user()
        profile = _make_profile(
            user_id=user.id,
            goal=NutritionGoal.LOSE_WEIGHT,
            weight_kg=Decimal("80.00"),
        )
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)

        from app.api.v1 import nutrition_profile as np_module

        captured: dict = {}
        original = np_module.calculate_nutrition_targets

        def spy(**kwargs):
            captured.update(kwargs)
            return original(**kwargs)

        monkeypatch.setattr(np_module, "calculate_nutrition_targets", spy)
        await client.get(
            SUMMARY_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert captured["tdee_kcal_per_day"] == Decimal("2664")
        assert captured["goal"] == NutritionGoal.LOSE_WEIGHT

    async def test_no_formula_logic(self, client, test_settings, mock_session):
        from app.api.v1 import nutrition_profile as np_module

        source = inspect.getsource(np_module)
        assert "ACTIVITY_MULTIPLIERS" not in source
        assert "CALORIE_ADJUSTMENTS" not in source
        assert "MACRO_DISTRIBUTIONS" not in source
        assert "6.25 * height_cm" not in source


# ===========================================================================
# PART 8 — Summary orchestration
# ===========================================================================


class TestSummaryOrchestration:
    async def test_build_called_once(self, client, test_settings, mock_session, monkeypatch):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)

        from app.api.v1 import nutrition_profile as np_module

        calls = {"n": 0}
        original = np_module.build_nutrition_summary

        def spy(*, metrics, targets, goal):
            calls["n"] += 1
            return original(metrics=metrics, targets=targets, goal=goal)

        monkeypatch.setattr(np_module, "build_nutrition_summary", spy)
        await client.get(
            SUMMARY_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert calls["n"] == 1

    async def test_build_args(self, client, test_settings, mock_session, monkeypatch):
        user = _make_user()
        profile = _make_profile(user_id=user.id, goal=NutritionGoal.GAIN_MUSCLE)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)

        from app.api.v1 import nutrition_profile as np_module

        captured: dict = {}
        original = np_module.build_nutrition_summary

        def spy(*, metrics, targets, goal):
            captured["metrics"] = metrics
            captured["targets"] = targets
            captured["goal"] = goal
            return original(metrics=metrics, targets=targets, goal=goal)

        monkeypatch.setattr(np_module, "build_nutrition_summary", spy)
        await client.get(
            SUMMARY_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        from app.core.nutrition_calculations import (
            NutritionCalculationResult,
            NutritionTargetResult,
        )

        assert isinstance(captured["metrics"], NutritionCalculationResult)
        assert isinstance(captured["targets"], NutritionTargetResult)
        assert captured["goal"] == NutritionGoal.GAIN_MUSCLE

    async def test_from_result_called_once(self, client, test_settings, mock_session, monkeypatch):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)

        from app.api.v1 import nutrition_profile as np_module

        calls = {"n": 0}
        original = np_module.NutritionSummaryData.from_result

        def spy(cls, result):
            calls["n"] += 1
            return original(result)

        monkeypatch.setattr(np_module.NutritionSummaryData, "from_result", classmethod(spy))
        await client.get(
            SUMMARY_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert calls["n"] == 1

    async def test_domain_result_not_mutated(
        self, client, test_settings, mock_session, monkeypatch
    ):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)

        from app.api.v1 import nutrition_profile as np_module

        captured_result = {}
        original = np_module.build_nutrition_summary

        def spy(*, metrics, targets, goal):
            captured_result["result"] = original(metrics=metrics, targets=targets, goal=goal)
            return captured_result["result"]

        monkeypatch.setattr(np_module, "build_nutrition_summary", spy)
        await client.get(
            SUMMARY_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        result = captured_result["result"]
        codes = [item.code for item in result.items]
        assert codes == list(EXPECTED_NUTRITION_SUMMARY_CODES)


# ===========================================================================
# PART 9 — Success response
# ===========================================================================


class TestSuccessResponse:
    async def test_returns_200(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            SUMMARY_URL,
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
            SUMMARY_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Nutrition summary generated successfully."
        assert "overview" in data["data"]
        assert "items" in data["data"]

    async def test_only_overview_and_items(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            SUMMARY_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert set(data.keys()) == {"success", "message", "data"}
        assert set(data["data"].keys()) == {"overview", "items"}

    async def test_exactly_six_items(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            SUMMARY_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        items = response.json()["data"]["items"]
        assert len(items) == EXPECTED_NUTRITION_SUMMARY_ITEM_COUNT

    async def test_codes_in_order(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            SUMMARY_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        items = response.json()["data"]["items"]
        codes = [item["code"] for item in items]
        assert codes == list(EXPECTED_NUTRITION_SUMMARY_CODES)

    async def test_no_duplicate_codes(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            SUMMARY_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        items = response.json()["data"]["items"]
        codes = [item["code"] for item in items]
        assert len(set(codes)) == len(codes)

    async def test_tones_lowercase_strings(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            SUMMARY_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        items = response.json()["data"]["items"]
        for item in items:
            assert item["tone"] in ("informational", "caution")

    async def test_tone_values_match_domain(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            SUMMARY_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        items = response.json()["data"]["items"]
        expected_tones = {
            "BMI_SCREENING_CONTEXT": NutritionSummaryTone.INFORMATIONAL.value,
            "DAILY_ENERGY_ESTIMATE": NutritionSummaryTone.INFORMATIONAL.value,
            "CALORIE_TARGET_CONTEXT": NutritionSummaryTone.INFORMATIONAL.value,
            "MACRONUTRIENT_TARGET_CONTEXT": NutritionSummaryTone.INFORMATIONAL.value,
            "GOAL_CONTEXT": NutritionSummaryTone.INFORMATIONAL.value,
            "GENERAL_ESTIMATE_LIMITATION": NutritionSummaryTone.CAUTION.value,
        }
        for item in items:
            assert item["tone"] == expected_tones[item["code"]]

    async def test_items_have_required_fields(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            SUMMARY_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        items = response.json()["data"]["items"]
        for item in items:
            assert set(item.keys()) == {"code", "title", "message", "tone"}

    async def test_no_sensitive_data(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            SUMMARY_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        text = response.text.lower()
        assert "password" not in text
        assert "password_hash" not in text
        assert "access_token" not in text
        assert "secret" not in text
        assert "$argon2id" not in text
        assert "jwt" not in text
        assert str(user.id) not in text

    async def test_validates_against_schema(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            SUMMARY_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        NutritionSummarySuccessResponse.model_validate(response.json())
        assert response.json()["success"] is True

    async def test_x_request_id_present(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            SUMMARY_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert "X-Request-ID" in response.headers


# ===========================================================================
# PART 10 — Domain errors
# ===========================================================================


class TestUnsupportedBMR:
    async def test_other_returns_422(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id, biological_sex=BiologicalSex.OTHER)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            SUMMARY_URL,
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
            SUMMARY_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.json()["error"]["code"] == "BMR_CALCULATION_UNSUPPORTED"
        assert "request_id" in response.json()["error"]

    async def test_prefer_not_to_say_same(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id, biological_sex=BiologicalSex.PREFER_NOT_TO_SAY)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            SUMMARY_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.json()["error"]["code"] == "BMR_CALCULATION_UNSUPPORTED"

    async def test_no_target_after_bmr_failure(
        self, client, test_settings, mock_session, monkeypatch
    ):
        user = _make_user()
        profile = _make_profile(user_id=user.id, biological_sex=BiologicalSex.OTHER)
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
            SUMMARY_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert calls["n"] == 0

    async def test_no_summary_after_bmr_failure(
        self, client, test_settings, mock_session, monkeypatch
    ):
        user = _make_user()
        profile = _make_profile(user_id=user.id, biological_sex=BiologicalSex.OTHER)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)

        from app.api.v1 import nutrition_profile as np_module

        calls = {"n": 0}
        original = np_module.build_nutrition_summary

        def spy(*, metrics, targets, goal):
            calls["n"] += 1
            return original(metrics=metrics, targets=targets, goal=goal)

        monkeypatch.setattr(np_module, "build_nutrition_summary", spy)
        await client.get(
            SUMMARY_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert calls["n"] == 0


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
            SUMMARY_URL,
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
            SUMMARY_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.json()["error"]["code"] == "CALORIE_TARGET_BELOW_MINIMUM"

    async def test_no_summary_after_target_failure(
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
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)

        from app.api.v1 import nutrition_profile as np_module

        calls = {"n": 0}
        original = np_module.build_nutrition_summary

        def spy(*, metrics, targets, goal):
            calls["n"] += 1
            return original(metrics=metrics, targets=targets, goal=goal)

        monkeypatch.setattr(np_module, "build_nutrition_summary", spy)
        await client.get(
            SUMMARY_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert calls["n"] == 0


class TestInvalidAgeReference:
    async def test_reference_equals_dob_returns_422(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id, date_of_birth=date(2000, 1, 1))
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            SUMMARY_URL,
            params={"reference_date": "2000-01-01"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "INVALID_CALCULATION_INPUT"

    async def test_reference_before_dob_returns_422(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id, date_of_birth=date(2000, 1, 1))
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            SUMMARY_URL,
            params={"reference_date": "1999-12-31"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "INVALID_CALCULATION_INPUT"

    async def test_no_data_returned(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id, date_of_birth=date(2000, 1, 1))
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            SUMMARY_URL,
            params={"reference_date": "2000-01-01"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert "data" not in response.json()


# ===========================================================================
# PART 11 — Unexpected errors
# ===========================================================================


class TestUnexpectedErrors:
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
                SUMMARY_URL,
                params={"reference_date": "2026-07-12"},
                headers={"Authorization": f"Bearer {token}"},
            )

    async def test_summary_builder_error_propagates(
        self, client, test_settings, mock_session, monkeypatch
    ):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)

        from app.api.v1 import nutrition_profile as np_module

        def _boom(*, metrics, targets, goal):
            raise RuntimeError("summary boom")

        monkeypatch.setattr(np_module, "build_nutrition_summary", _boom)
        with pytest.raises(RuntimeError):
            await client.get(
                SUMMARY_URL,
                params={"reference_date": "2026-07-12"},
                headers={"Authorization": f"Bearer {token}"},
            )

    async def test_global_handler_safe_500(self):
        from starlette.requests import Request

        from app.core.exceptions import global_exception_handler

        async def _receive():
            return {"type": "http.disconnect"}

        request = Request(
            {"type": "http", "method": "GET", "path": SUMMARY_URL, "headers": []},
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
# PART 12 — Read-only
# ===========================================================================


class TestReadOnly:
    async def test_no_commit(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.get(
            SUMMARY_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        mock_session.commit.assert_not_called()

    async def test_no_flush(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.get(
            SUMMARY_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        mock_session.flush.assert_not_called()

    async def test_no_refresh(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.get(
            SUMMARY_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        mock_session.refresh.assert_not_called()

    async def test_no_add(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        mock_session.add = MagicMock()
        await client.get(
            SUMMARY_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        mock_session.add.assert_not_called()

    async def test_no_add_all(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        mock_session.add_all = MagicMock()
        await client.get(
            SUMMARY_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        mock_session.add_all.assert_not_called()

    async def test_no_delete(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        mock_session.delete = MagicMock()
        await client.get(
            SUMMARY_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        mock_session.delete.assert_not_called()

    async def test_no_merge(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        mock_session.merge = MagicMock()
        await client.get(
            SUMMARY_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        mock_session.merge.assert_not_called()

    async def test_user_unchanged(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        original_email = user.email
        await client.get(
            SUMMARY_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert user.email == original_email

    async def test_profile_unchanged(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        original_dob = profile.date_of_birth
        original_goal = profile.goal
        await client.get(
            SUMMARY_URL,
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert profile.date_of_birth == original_dob
        assert profile.goal == original_goal


# ===========================================================================
# PART 13 — Regression (existing routes)
# ===========================================================================


class TestRegression:
    async def test_calculations_behavior_unchanged(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/nutrition-profile/calculations",
            params={"reference_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert "metrics" in response.json()["data"]
        assert "targets" in response.json()["data"]

    async def test_profile_get_unchanged(self, client, test_settings, mock_session):
        user = _make_user()
        profile = _make_profile(user_id=user.id)
        _setup_session_with_profile(mock_session, user, profile)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/nutrition-profile",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert "profile" in response.json()["data"]

    async def test_profile_post_unchanged(self, client, test_settings, mock_session):
        user = _make_user()
        _setup_session_for_create(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/nutrition-profile",
            json={
                "date_of_birth": "1990-01-01",
                "biological_sex": "male",
                "height_cm": "175.00",
                "weight_kg": "70.00",
                "activity_level": "moderately_active",
                "goal": "maintain_weight",
                "target_weight_kg": None,
                "dietary_preference": None,
                "allergies": [],
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 201

    async def test_profile_patch_unchanged(self, client, test_settings, mock_session):
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

    async def test_register_unchanged(self, client):
        response = await client.post("/api/v1/auth/register", json={})
        assert response.status_code != 401

    async def test_login_unchanged(self, client):
        response = await client.post("/api/v1/auth/login", json={})
        assert response.status_code != 401

    async def test_auth_me_unchanged(self, client):
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401

    async def test_health_unchanged(self, client):
        response = await client.get("/api/v1/health")
        assert response.status_code != 401

    async def test_validation_envelope_unchanged(self, client):
        response = await client.get(SUMMARY_URL)
        assert response.status_code == 401
        assert response.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"

    async def test_bearer_scheme_not_duplicated(self, app):
        spec = app.openapi()
        schemes = spec["components"]["securitySchemes"]
        assert list(schemes.keys()) == ["BearerAuth"]
