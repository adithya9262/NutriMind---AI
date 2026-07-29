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
from app.core.nutrition_logs import MealType
from app.core.tokens import create_access_token
from app.db.dependencies import get_db_session
from app.main import create_app
from app.models.nutrition_log import NutritionLog
from app.models.user import User

NOW = datetime.now(UTC)
TEST_LOGGED_DATE = date(2026, 7, 12)
TEST_ZERO_DEC = Decimal("0.00")


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


def _make_execute_result(value: MagicMock | None | list) -> MagicMock:
    result = MagicMock()
    if isinstance(value, list):
        result.scalars.return_value.all.return_value = value
    else:
        result.scalars.return_value.one_or_none.return_value = value
    return result


def _make_entries_result(entries: list) -> MagicMock:
    result = MagicMock()
    result.scalars.return_value.all.return_value = entries
    return result


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
# A. Route Registration and Ordering
# ===========================================================================


class TestRouteRegistration:
    async def test_summary_path_registered(self, client):
        response = await client.get("/api/v1/nutrition-logs/summary")
        assert response.status_code != 404

    async def test_summary_before_entry_id(self, app):
        routes = [r.path for r in app.routes if "nutrition-logs" in r.path]
        summary_idx = routes.index("/api/v1/nutrition-logs/summary")
        entry_id_idx = routes.index("/api/v1/nutrition-logs/{entry_id}")
        assert summary_idx < entry_id_idx

    async def test_static_summary_not_interpreted_as_entry_id(self, client):
        response = await client.get("/api/v1/nutrition-logs/summary")
        assert response.status_code != 404
        assert response.status_code != 422

    async def test_delete_entry_id_remains(self, client):
        response = await client.delete(f"/api/v1/nutrition-logs/{uuid.uuid4()}")
        assert response.status_code != 404

    async def test_post_still_registered(self, client):
        response = await client.post("/api/v1/nutrition-logs", json={})
        assert response.status_code != 404

    async def test_get_collection_still_registered(self, client):
        response = await client.get("/api/v1/nutrition-logs")
        assert response.status_code != 404

    async def test_no_duplicate_summary_path(self, app):
        summary_routes = [r.path for r in app.routes if r.path == "/api/v1/nutrition-logs/summary"]
        assert len(summary_routes) == 1


# ===========================================================================
# B. OpenAPI Contract
# ===========================================================================


class TestOpenAPI:
    async def test_summary_path_in_schema(self, test_settings):
        app = create_app(settings=test_settings)
        schema = app.openapi()
        assert "/api/v1/nutrition-logs/summary" in schema["paths"]

    async def test_summary_method_get(self, test_settings):
        app = create_app(settings=test_settings)
        schema = app.openapi()
        assert "get" in schema["paths"]["/api/v1/nutrition-logs/summary"]

    async def test_logged_date_required(self, test_settings):
        app = create_app(settings=test_settings)
        schema = app.openapi()
        op = schema["paths"]["/api/v1/nutrition-logs/summary"]["get"]
        params = op.get("parameters", [])
        logged_date_params = [p for p in params if p["name"] == "logged_date"]
        assert len(logged_date_params) >= 1
        assert logged_date_params[0]["required"] is True

    async def test_logged_date_format_date(self, test_settings):
        app = create_app(settings=test_settings)
        schema = app.openapi()
        op = schema["paths"]["/api/v1/nutrition-logs/summary"]["get"]
        params = op.get("parameters", [])
        logged_date_params = [p for p in params if p["name"] == "logged_date"]
        assert logged_date_params[0]["schema"]["format"] == "date"

    async def test_bearer_auth_required(self, test_settings):
        app = create_app(settings=test_settings)
        schema = app.openapi()
        op = schema["paths"]["/api/v1/nutrition-logs/summary"]["get"]
        sec = op.get("security", [])
        assert any("BearerAuth" in s for s in sec)

    async def test_200_typed_response(self, test_settings):
        app = create_app(settings=test_settings)
        schema = app.openapi()
        op = schema["paths"]["/api/v1/nutrition-logs/summary"]["get"]
        assert "200" in op["responses"]

    async def test_exactly_one_bearer_scheme(self, test_settings):
        app = create_app(settings=test_settings)
        schema = app.openapi()
        schemes = schema.get("components", {}).get("securitySchemes", {})
        bearer_count = sum(1 for v in schemes.values() if v.get("scheme") == "bearer")
        assert bearer_count == 1

    async def test_no_put_patch_post_aggregation(self, test_settings):
        app = create_app(settings=test_settings)
        schema = app.openapi()
        for path, methods in schema["paths"].items():
            if "nutrition-logs" in path and "summary" in path:
                assert "put" not in methods
                assert "patch" not in methods
                assert "post" not in methods
                assert "delete" not in methods

    async def test_no_user_id_param(self, test_settings):
        app = create_app(settings=test_settings)
        schema = app.openapi()
        op = schema["paths"]["/api/v1/nutrition-logs/summary"]["get"]
        params = op.get("parameters", [])
        param_names = [p["name"] for p in params]
        assert "user_id" not in param_names

    async def test_existing_crud_paths_still_present(self, test_settings):
        app = create_app(settings=test_settings)
        schema = app.openapi()
        assert "/api/v1/nutrition-logs" in schema["paths"]
        assert "/api/v1/nutrition-logs/{entry_id}" in schema["paths"]

    async def test_summary_not_under_nutrition_profile(self, test_settings):
        app = create_app(settings=test_settings)
        schema = app.openapi()
        for path in schema["paths"]:
            if "nutrition-profile" in path and "summary" in path:
                break
        else:
            pytest.fail("Expected nutrition-profile/summary to exist")


# ===========================================================================
# C. Authentication Failures
# ===========================================================================


class TestAuthMissingToken:
    async def test_returns_401(self, client):
        response = await client.get(
            "/api/v1/nutrition-logs/summary",
            params={"logged_date": "2026-07-12"},
        )
        assert response.status_code == 401

    async def test_safe_envelope(self, client):
        response = await client.get(
            "/api/v1/nutrition-logs/summary",
            params={"logged_date": "2026-07-12"},
        )
        data = response.json()
        assert data["success"] is False
        assert "error" in data

    async def test_code_authentication_required(self, client):
        response = await client.get(
            "/api/v1/nutrition-logs/summary",
            params={"logged_date": "2026-07-12"},
        )
        data = response.json()
        assert data["error"]["code"] == "AUTHENTICATION_REQUIRED"

    async def test_www_authenticate(self, client):
        response = await client.get(
            "/api/v1/nutrition-logs/summary",
            params={"logged_date": "2026-07-12"},
        )
        assert response.headers.get("WWW-Authenticate") == "Bearer"

    async def test_no_detail_field(self, client):
        response = await client.get(
            "/api/v1/nutrition-logs/summary",
            params={"logged_date": "2026-07-12"},
        )
        assert '"detail"' not in response.text

    async def test_bearer_prefix_missing(self, client):
        response = await client.get(
            "/api/v1/nutrition-logs/summary",
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": "token123"},
        )
        assert response.status_code == 401


class TestAuthInvalidToken:
    async def test_returns_401(self, client):
        response = await client.get(
            "/api/v1/nutrition-logs/summary",
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": "Bearer not-a-valid-token"},
        )
        assert response.status_code == 401

    async def test_code_invalid_token(self, client):
        response = await client.get(
            "/api/v1/nutrition-logs/summary",
            params={"logged_date": "2026-07-12"},
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
            "/api/v1/nutrition-logs/summary",
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401

    async def test_code_expired(self, client, test_settings):
        token = self._make_expired_token(test_settings)
        response = await client.get(
            "/api/v1/nutrition-logs/summary",
            params={"logged_date": "2026-07-12"},
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
            "/api/v1/nutrition-logs/summary",
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401

    async def test_code_invalid_token(self, client, test_settings, mock_session):
        self._setup_session(mock_session)
        user_id = uuid.uuid4()
        token = create_access_token(user_id=user_id, settings=test_settings)
        response = await client.get(
            "/api/v1/nutrition-logs/summary",
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["error"]["code"] == "INVALID_ACCESS_TOKEN"


class TestAuthInactiveUser:
    def _setup_session(self, mock_session, user):
        mock_session.execute = AsyncMock(return_value=_make_execute_result(user))

    async def test_returns_403(self, client, test_settings, mock_session):
        user = _make_user(is_active=False)
        self._setup_session(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/nutrition-logs/summary",
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403

    async def test_code_inactive(self, client, test_settings, mock_session):
        user = _make_user(is_active=False)
        self._setup_session(mock_session, user)
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/nutrition-logs/summary",
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["error"]["code"] == "INACTIVE_ACCOUNT"


class TestAuthNotCalledBeforeService:
    async def test_auth_fails_before_service(self, client):
        response = await client.get(
            "/api/v1/nutrition-logs/summary",
            params={"logged_date": "2026-07-12"},
        )
        assert response.status_code == 401


# ===========================================================================
# D. Current-User Ownership Isolation
# ===========================================================================


class TestUserIsolation:
    async def test_no_user_id_query_param(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute = AsyncMock(return_value=_make_execute_result(user))
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/nutrition-logs/summary",
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert "user_id" not in response.text.lower()

    async def test_extra_user_id_ignored(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute = AsyncMock(return_value=_make_execute_result(user))
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/nutrition-logs/summary",
            params={"logged_date": "2026-07-12", "user_id": str(uuid.uuid4())},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code != 422  # extra params are ignored

    async def test_own_entries_only(self, client, test_settings, mock_session):
        user = _make_user()
        entries = [_make_nutrition_log(user_id=user.id)]
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            _make_entries_result(entries),
        ]
        mock_session.commit = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/nutrition-logs/summary",
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200


# ===========================================================================
# E. logged_date Validation
# ===========================================================================


class TestLoggedDateValidation:
    async def test_missing_returns_422(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute = AsyncMock(return_value=_make_execute_result(user))
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/nutrition-logs/summary",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    async def test_missing_validation_envelope(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute = AsyncMock(return_value=_make_execute_result(user))
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/nutrition-logs/summary",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["error"]["code"] == "VALIDATION_ERROR"

    async def test_malformed_date_returns_422(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute = AsyncMock(return_value=_make_execute_result(user))
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/nutrition-logs/summary",
            params={"logged_date": "not-a-date"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    async def test_impossible_date_returns_422(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute = AsyncMock(return_value=_make_execute_result(user))
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/nutrition-logs/summary",
            params={"logged_date": "2026-13-01"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    async def test_datetime_string_accepted_by_fastapi(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            _make_entries_result([]),
        ]
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/nutrition-logs/summary",
            params={"logged_date": "2026-07-12T00:00:00"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    async def test_valid_iso_date_accepted(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            _make_entries_result([]),
        ]
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/nutrition-logs/summary",
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    async def test_leap_date_accepted(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            _make_entries_result([]),
        ]
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/nutrition-logs/summary",
            params={"logged_date": "2024-02-29"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    async def test_past_date_accepted(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            _make_entries_result([]),
        ]
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/nutrition-logs/summary",
            params={"logged_date": "2020-01-01"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200


# ===========================================================================
# F. Repository Construction and Reuse
# ===========================================================================


class TestRepositoryReuse:
    async def test_repository_constructed_with_session(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            _make_entries_result([]),
        ]
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.get(
            "/api/v1/nutrition-logs/summary",
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        mock_session.execute.assert_called()


# ===========================================================================
# G. Service Construction and Reuse
# ===========================================================================


class TestServiceReuse:
    async def test_service_list_called_with_correct_args(self, client, test_settings, mock_session):
        user = _make_user()
        entry = _make_nutrition_log(user_id=user.id)
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            _make_entries_result([entry]),
        ]
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/nutrition-logs/summary",
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200


# ===========================================================================
# H. Empty-Day Summary
# ===========================================================================


class TestEmptyDaySummary:
    async def test_empty_day_returns_200(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            _make_entries_result([]),
        ]
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/nutrition-logs/summary",
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    async def test_empty_day_success_true(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            _make_entries_result([]),
        ]
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/nutrition-logs/summary",
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["success"] is True

    async def test_empty_day_message(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            _make_entries_result([]),
        ]
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/nutrition-logs/summary",
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["message"] == "Daily nutrition log summarized successfully."

    async def test_empty_day_entry_count(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            _make_entries_result([]),
        ]
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/nutrition-logs/summary",
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["data"]["entry_count"] == 0

    async def test_empty_day_zero_totals(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            _make_entries_result([]),
        ]
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/nutrition-logs/summary",
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        totals = data["data"]["totals"]
        assert totals["calories_kcal"] == "0.00"
        assert totals["protein_g"] == "0.00"
        assert totals["carbohydrate_g"] == "0.00"
        assert totals["fat_g"] == "0.00"

    async def test_empty_day_four_meals(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            _make_entries_result([]),
        ]
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/nutrition-logs/summary",
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert len(data["data"]["meals"]) == 4

    async def test_empty_day_each_meal_zero(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            _make_entries_result([]),
        ]
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/nutrition-logs/summary",
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        for meal in data["data"]["meals"]:
            assert meal["entry_count"] == 0
            assert meal["totals"]["calories_kcal"] == "0.00"

    async def test_empty_day_requested_date_preserved(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            _make_entries_result([]),
        ]
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/nutrition-logs/summary",
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    async def test_empty_day_no_write(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            _make_entries_result([]),
        ]
        mock_session.commit = AsyncMock()
        mock_session.flush = AsyncMock()
        mock_session.add = MagicMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.get(
            "/api/v1/nutrition-logs/summary",
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        mock_session.commit.assert_not_called()
        mock_session.flush.assert_not_called()
        mock_session.add.assert_not_called()


# ===========================================================================
# I. One-Entry Summary
# ===========================================================================


class TestOneEntrySummary:
    async def test_one_entry_returns_200(self, client, test_settings, mock_session):
        user = _make_user()
        entry = _make_nutrition_log(
            user_id=user.id,
            meal_type=MealType.BREAKFAST,
            calories="300.00",
            protein="10.00",
            carbs="50.00",
            fat="5.00",
        )
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            _make_entries_result([entry]),
        ]
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/nutrition-logs/summary",
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    async def test_one_entry_success_true(self, client, test_settings, mock_session):
        user = _make_user()
        entry = _make_nutrition_log(user_id=user.id, meal_type=MealType.BREAKFAST)
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            _make_entries_result([entry]),
        ]
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/nutrition-logs/summary",
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["success"] is True

    async def test_one_entry_entry_count(self, client, test_settings, mock_session):
        user = _make_user()
        entry = _make_nutrition_log(user_id=user.id, meal_type=MealType.BREAKFAST)
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            _make_entries_result([entry]),
        ]
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/nutrition-logs/summary",
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["data"]["entry_count"] == 1

    async def test_one_entry_breakfast_totals(self, client, test_settings, mock_session):
        user = _make_user()
        entry = _make_nutrition_log(
            user_id=user.id,
            meal_type=MealType.BREAKFAST,
            calories="300.00",
            protein="10.00",
            carbs="50.00",
            fat="5.00",
        )
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            _make_entries_result([entry]),
        ]
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/nutrition-logs/summary",
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        totals = data["data"]["totals"]
        assert totals["calories_kcal"] == "300.00"
        assert totals["protein_g"] == "10.00"
        assert totals["carbohydrate_g"] == "50.00"
        assert totals["fat_g"] == "5.00"

    async def test_one_entry_meal_has_one_entry(self, client, test_settings, mock_session):
        user = _make_user()
        entry = _make_nutrition_log(user_id=user.id, meal_type=MealType.BREAKFAST)
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            _make_entries_result([entry]),
        ]
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/nutrition-logs/summary",
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        meals = data["data"]["meals"]
        assert meals[0]["entry_count"] == 1
        assert meals[1]["entry_count"] == 0
        assert meals[2]["entry_count"] == 0
        assert meals[3]["entry_count"] == 0

    async def test_one_entry_breakfast_meal_totals(self, client, test_settings, mock_session):
        user = _make_user()
        entry = _make_nutrition_log(
            user_id=user.id,
            meal_type=MealType.BREAKFAST,
            calories="300.00",
            protein="10.00",
            carbs="50.00",
            fat="5.00",
        )
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            _make_entries_result([entry]),
        ]
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/nutrition-logs/summary",
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        meal_totals = data["data"]["meals"][0]["totals"]
        assert meal_totals["calories_kcal"] == "300.00"
        assert meal_totals["protein_g"] == "10.00"
        assert meal_totals["carbohydrate_g"] == "50.00"
        assert meal_totals["fat_g"] == "5.00"


# ===========================================================================
# J. Multi-Entry Summary
# ===========================================================================


class TestMultiEntrySummary:
    async def test_two_entries_one_meal(self, client, test_settings, mock_session):
        user = _make_user()
        e1 = _make_nutrition_log(
            user_id=user.id,
            meal_type=MealType.BREAKFAST,
            calories="300.00",
            protein="10.00",
            carbs="50.00",
            fat="5.00",
        )
        e2 = _make_nutrition_log(
            user_id=user.id,
            meal_type=MealType.BREAKFAST,
            calories="200.00",
            protein="8.00",
            carbs="30.00",
            fat="3.00",
        )
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            _make_entries_result([e1, e2]),
        ]
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/nutrition-logs/summary",
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["data"]["entry_count"] == 2
        assert data["data"]["meals"][0]["entry_count"] == 2
        assert data["data"]["totals"]["calories_kcal"] == "500.00"
        assert data["data"]["totals"]["protein_g"] == "18.00"
        assert data["data"]["totals"]["carbohydrate_g"] == "80.00"
        assert data["data"]["totals"]["fat_g"] == "8.00"

    async def test_multiple_entries_same_meal_correct_meal_totals(
        self, client, test_settings, mock_session
    ):
        user = _make_user()
        e1 = _make_nutrition_log(
            user_id=user.id,
            meal_type=MealType.BREAKFAST,
            calories="300.00",
            protein="10.00",
            carbs="50.00",
            fat="5.00",
        )
        e2 = _make_nutrition_log(
            user_id=user.id,
            meal_type=MealType.BREAKFAST,
            calories="200.00",
            protein="8.00",
            carbs="30.00",
            fat="3.00",
        )
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            _make_entries_result([e1, e2]),
        ]
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/nutrition-logs/summary",
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        meal_totals = data["data"]["meals"][0]["totals"]
        assert meal_totals["calories_kcal"] == "500.00"
        assert meal_totals["protein_g"] == "18.00"
        assert meal_totals["carbohydrate_g"] == "80.00"
        assert meal_totals["fat_g"] == "8.00"


# ===========================================================================
# K. Multi-Meal Summary
# ===========================================================================


class TestMultiMealSummary:
    async def test_entries_across_all_meals(self, client, test_settings, mock_session):
        user = _make_user()
        breakfast = _make_nutrition_log(
            user_id=user.id,
            meal_type=MealType.BREAKFAST,
            calories="300.00",
            protein="10.00",
            carbs="50.00",
            fat="5.00",
        )
        lunch = _make_nutrition_log(
            user_id=user.id,
            meal_type=MealType.LUNCH,
            calories="500.00",
            protein="20.00",
            carbs="60.00",
            fat="15.00",
        )
        dinner = _make_nutrition_log(
            user_id=user.id,
            meal_type=MealType.DINNER,
            calories="700.00",
            protein="30.00",
            carbs="80.00",
            fat="20.00",
        )
        snack = _make_nutrition_log(
            user_id=user.id,
            meal_type=MealType.SNACK,
            calories="200.00",
            protein="5.00",
            carbs="25.00",
            fat="8.00",
        )
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            _make_entries_result([breakfast, lunch, dinner, snack]),
        ]
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/nutrition-logs/summary",
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["data"]["entry_count"] == 4
        totals = data["data"]["totals"]
        assert totals["calories_kcal"] == "1700.00"
        assert totals["protein_g"] == "65.00"
        assert totals["carbohydrate_g"] == "215.00"
        assert totals["fat_g"] == "48.00"

    async def test_per_meal_totals_correct(self, client, test_settings, mock_session):
        user = _make_user()
        breakfast = _make_nutrition_log(
            user_id=user.id,
            meal_type=MealType.BREAKFAST,
            calories="300.00",
        )
        lunch = _make_nutrition_log(
            user_id=user.id,
            meal_type=MealType.LUNCH,
            calories="500.00",
        )
        dinner = _make_nutrition_log(
            user_id=user.id,
            meal_type=MealType.DINNER,
            calories="700.00",
        )
        snack = _make_nutrition_log(
            user_id=user.id,
            meal_type=MealType.SNACK,
            calories="200.00",
        )
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            _make_entries_result([breakfast, lunch, dinner, snack]),
        ]
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/nutrition-logs/summary",
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        meals = data["data"]["meals"]
        assert meals[0]["totals"]["calories_kcal"] == "300.00"
        assert meals[1]["totals"]["calories_kcal"] == "500.00"
        assert meals[2]["totals"]["calories_kcal"] == "700.00"
        assert meals[3]["totals"]["calories_kcal"] == "200.00"


# ===========================================================================
# L. Deterministic Meal Ordering
# ===========================================================================


class TestDeterministicMealOrder:
    async def test_meals_in_correct_order(self, client, test_settings, mock_session):
        user = _make_user()
        entries = [
            _make_nutrition_log(user_id=user.id, meal_type=MealType.SNACK),
            _make_nutrition_log(user_id=user.id, meal_type=MealType.DINNER),
            _make_nutrition_log(user_id=user.id, meal_type=MealType.LUNCH),
            _make_nutrition_log(user_id=user.id, meal_type=MealType.BREAKFAST),
        ]
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            _make_entries_result(entries),
        ]
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/nutrition-logs/summary",
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        meals = data["data"]["meals"]
        assert meals[0]["meal_type"] == "breakfast"
        assert meals[1]["meal_type"] == "lunch"
        assert meals[2]["meal_type"] == "dinner"
        assert meals[3]["meal_type"] == "snack"


# ===========================================================================
# M. Decimal Preservation
# ===========================================================================


class TestDecimalPreservation:
    async def test_decimal_values_serialized_as_strings(self, client, test_settings, mock_session):
        user = _make_user()
        entry = _make_nutrition_log(
            user_id=user.id,
            meal_type=MealType.BREAKFAST,
            calories="300.50",
            protein="10.12",
            carbs="50.78",
            fat="5.99",
        )
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            _make_entries_result([entry]),
        ]
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/nutrition-logs/summary",
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        totals = data["data"]["totals"]
        assert isinstance(totals["calories_kcal"], str)
        assert totals["calories_kcal"] == "300.50"

    async def test_two_decimal_precision(self, client, test_settings, mock_session):
        user = _make_user()
        entry = _make_nutrition_log(
            user_id=user.id,
            meal_type=MealType.BREAKFAST,
            calories="100.555",
        )
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            _make_entries_result([entry]),
        ]
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/nutrition-logs/summary",
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["data"]["totals"]["calories_kcal"] == "100.56"


# ===========================================================================
# N. MealType Serialization
# ===========================================================================


class TestMealTypeSerialization:
    async def test_meal_type_lowercase(self, client, test_settings, mock_session):
        user = _make_user()
        entry = _make_nutrition_log(user_id=user.id, meal_type=MealType.BREAKFAST)
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            _make_entries_result([entry]),
        ]
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/nutrition-logs/summary",
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["data"]["meals"][0]["meal_type"] == "breakfast"

    async def test_all_meal_types_lowercase(self, client, test_settings, mock_session):
        user = _make_user()
        entries = [
            _make_nutrition_log(user_id=user.id, meal_type=MealType.BREAKFAST),
            _make_nutrition_log(user_id=user.id, meal_type=MealType.LUNCH),
            _make_nutrition_log(user_id=user.id, meal_type=MealType.DINNER),
            _make_nutrition_log(user_id=user.id, meal_type=MealType.SNACK),
        ]
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            _make_entries_result(entries),
        ]
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/nutrition-logs/summary",
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        for meal in data["data"]["meals"]:
            assert meal["meal_type"] == meal["meal_type"].lower()


# ===========================================================================
# O. Read-Only Session Behavior
# ===========================================================================


class TestReadOnly:
    async def test_no_commit(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            _make_entries_result([]),
        ]
        mock_session.commit = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.get(
            "/api/v1/nutrition-logs/summary",
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        mock_session.commit.assert_not_called()

    async def test_no_flush(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            _make_entries_result([]),
        ]
        mock_session.flush = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.get(
            "/api/v1/nutrition-logs/summary",
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        mock_session.flush.assert_not_called()

    async def test_no_refresh(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            _make_entries_result([]),
        ]
        mock_session.refresh = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.get(
            "/api/v1/nutrition-logs/summary",
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        mock_session.refresh.assert_not_called()

    async def test_no_add(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            _make_entries_result([]),
        ]
        mock_session.add = MagicMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.get(
            "/api/v1/nutrition-logs/summary",
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        mock_session.add.assert_not_called()

    async def test_no_delete(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            _make_entries_result([]),
        ]
        mock_session.delete = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.get(
            "/api/v1/nutrition-logs/summary",
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        mock_session.delete.assert_not_called()

    async def test_no_rollback_during_success(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            _make_entries_result([]),
        ]
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.get(
            "/api/v1/nutrition-logs/summary",
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        mock_session.rollback.assert_not_called()


# ===========================================================================
# P. No Source-Object Mutation
# ===========================================================================


class TestNoMutation:
    async def test_orm_objects_not_mutated(self, client, test_settings, mock_session):
        user = _make_user()
        entry = _make_nutrition_log(user_id=user.id, meal_type=MealType.BREAKFAST)
        original_food = entry.food_name
        original_calories = entry.calories_kcal
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            _make_entries_result([entry]),
        ]
        token = create_access_token(user_id=user.id, settings=test_settings)
        await client.get(
            "/api/v1/nutrition-logs/summary",
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert entry.food_name == original_food
        assert entry.calories_kcal == original_calories


# ===========================================================================
# Q. Unexpected Error Handling
# ===========================================================================


class TestUnexpectedRepositoryError:
    async def test_repository_error_returns_500(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            RuntimeError("repo failure"),
        ]
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/nutrition-logs/summary",
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 500

    async def test_global_envelope(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            RuntimeError("repo failure"),
        ]
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/nutrition-logs/summary",
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["error"]["code"] == "INTERNAL_SERVER_ERROR"

    async def test_safe_message(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            RuntimeError("repo failure"),
        ]
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/nutrition-logs/summary",
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert data["error"]["message"] == "An unexpected error occurred."

    async def test_no_raw_exception(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            RuntimeError("repo failure"),
        ]
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/nutrition-logs/summary",
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert "repo failure" not in response.text.lower()
        assert "RuntimeError" not in response.text

    async def test_request_id_in_body(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            RuntimeError("repo failure"),
        ]
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/nutrition-logs/summary",
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert "request_id" in data["error"]

    async def test_x_request_id_header(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            RuntimeError("repo failure"),
        ]
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/nutrition-logs/summary",
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert "X-Request-ID" in response.headers

    async def test_no_sql_exposed(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            RuntimeError("repo failure"),
        ]
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/nutrition-logs/summary",
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        text = response.text.lower()
        assert "select" not in text
        assert "insert" not in text


# ===========================================================================
# R. X-Request-ID
# ===========================================================================


class TestRequestID:
    async def test_x_request_id_header_on_success(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            _make_entries_result([]),
        ]
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/nutrition-logs/summary",
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert "X-Request-ID" in response.headers

    async def test_x_request_id_header_on_error(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            RuntimeError("fail"),
        ]
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/nutrition-logs/summary",
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert "X-Request-ID" in response.headers


# ===========================================================================
# S. No User ID or Password in Response
# ===========================================================================


class TestPrivacy:
    async def test_no_user_id_exposed(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            _make_entries_result([]),
        ]
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/nutrition-logs/summary",
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert "user_id" not in response.text.lower()

    async def test_no_password_exposed(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            _make_entries_result([]),
        ]
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/nutrition-logs/summary",
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert "password" not in response.text.lower()

    async def test_no_entry_id_exposed_in_totals(self, client, test_settings, mock_session):
        user = _make_user()
        entry = _make_nutrition_log(user_id=user.id)
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            _make_entries_result([entry]),
        ]
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/nutrition-logs/summary",
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert "entry_id" not in data["data"]
        assert "entry_id" not in data["data"]["totals"]
        for meal in data["data"]["meals"]:
            assert "entry_id" not in meal

    async def test_no_food_names_in_summary(self, client, test_settings, mock_session):
        user = _make_user()
        entry = _make_nutrition_log(user_id=user.id)
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            _make_entries_result([entry]),
        ]
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/nutrition-logs/summary",
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert "food_name" not in data["data"]
        for meal in data["data"]["meals"]:
            assert "food_name" not in meal
            assert "serving_description" not in meal


# ===========================================================================
# T. Deterministic Ordering with Different Input Orders
# ===========================================================================


class TestDeterministicInputOrder:
    async def test_different_entry_order_same_summary(self, client, test_settings, mock_session):
        user = _make_user()

        def make(calories: str) -> MagicMock:
            return _make_nutrition_log(
                user_id=user.id,
                meal_type=MealType.BREAKFAST,
                calories=calories,
            )

        entries_abc = [make("100"), make("200"), make("300")]
        entries_cba = [make("300"), make("200"), make("100")]

        # First call
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            _make_entries_result(entries_abc),
        ]
        token = create_access_token(user_id=user.id, settings=test_settings)
        response1 = await client.get(
            "/api/v1/nutrition-logs/summary",
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data1 = response1.json()

        # Second call with different DB order
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            _make_entries_result(entries_cba),
        ]
        response2 = await client.get(
            "/api/v1/nutrition-logs/summary",
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data2 = response2.json()

        assert data1["data"]["totals"] == data2["data"]["totals"]
        assert data1["data"]["entry_count"] == data2["data"]["entry_count"]


# ===========================================================================
# U. Existing CRUD Route Regression
# ===========================================================================


class TestExistingRouteRegression:
    async def test_post_still_works(self, app, test_settings, mock_session):
        user = _make_user()
        mock_session.execute = AsyncMock(return_value=_make_execute_result(user))
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()
        mock_session.commit = AsyncMock()
        async with AsyncClient(
            transport=ASGITransport(app=app, raise_app_exceptions=False),
            base_url="http://test",
        ) as c:
            token = create_access_token(user_id=user.id, settings=test_settings)
            response = await c.post(
                "/api/v1/nutrition-logs",
                json={
                    "entry_id": str(uuid.uuid4()),
                    "food_name": "Test",
                    "meal_type": "breakfast",
                    "serving_description": "1 serving",
                    "calories_kcal": "100",
                    "protein_g": "10",
                    "carbohydrate_g": "10",
                    "fat_g": "5",
                },
                params={"logged_date": "2026-07-12"},
                headers={"Authorization": f"Bearer {token}"},
            )
            assert response.status_code != 404

    async def test_get_list_still_works(self, app, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            _make_entries_result([]),
        ]
        async with AsyncClient(
            transport=ASGITransport(app=app, raise_app_exceptions=False),
            base_url="http://test",
        ) as c:
            token = create_access_token(user_id=user.id, settings=test_settings)
            response = await c.get(
                "/api/v1/nutrition-logs",
                params={"logged_date": "2026-07-12"},
                headers={"Authorization": f"Bearer {token}"},
            )
            assert response.status_code == 200

    async def test_delete_still_works(self, app, test_settings, mock_session):
        user = _make_user()
        entry = _make_nutrition_log(user_id=user.id)
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            _make_execute_result(entry),
        ]
        mock_session.delete = AsyncMock()
        mock_session.flush = AsyncMock()
        mock_session.commit = AsyncMock()
        async with AsyncClient(
            transport=ASGITransport(app=app, raise_app_exceptions=False),
            base_url="http://test",
        ) as c:
            token = create_access_token(user_id=user.id, settings=test_settings)
            response = await c.delete(
                f"/api/v1/nutrition-logs/{entry.entry_id}",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert response.status_code != 404


# ===========================================================================
# V. Phase-Boundary Checks
# ===========================================================================


class TestPhaseBoundary:
    async def test_no_put_summary(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute = AsyncMock(return_value=_make_execute_result(user))
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.put(
            "/api/v1/nutrition-logs/summary",
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 405

    async def test_no_patch_summary(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute = AsyncMock(return_value=_make_execute_result(user))
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.patch(
            "/api/v1/nutrition-logs/summary",
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 405

    async def test_no_delete_summary(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute = AsyncMock(return_value=_make_execute_result(user))
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.delete(
            "/api/v1/nutrition-logs/summary",
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    async def test_no_post_summary(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute = AsyncMock(return_value=_make_execute_result(user))
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.post(
            "/api/v1/nutrition-logs/summary",
            json={},
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 405

    async def test_no_aggregation_route(self, app):
        aggreg_paths = [
            r.path
            for r in app.routes
            if "nutrition-logs" in r.path and "aggregat" in r.path.lower()
        ]
        assert len(aggreg_paths) == 0

    async def test_no_target_comparison(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            _make_entries_result([]),
        ]
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/nutrition-logs/summary",
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        assert "remaining_calories" not in data
        assert "calorie_target" not in data
        assert "adherence" not in data
        assert "score" not in data
        assert "progress" not in response.text.lower()

    async def test_no_health_score(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            _make_entries_result([]),
        ]
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/nutrition-logs/summary",
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert "health" not in response.text.lower()

    async def test_x_request_id_on_success(self, client, test_settings, mock_session):
        user = _make_user()
        mock_session.execute.side_effect = [
            _make_execute_result(user),
            _make_entries_result([]),
        ]
        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/nutrition-logs/summary",
            params={"logged_date": "2026-07-12"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert "X-Request-ID" in response.headers
