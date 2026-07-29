"""Phase 5C — final audit: focused cross-layer invariants for the body-weight trend module.

These tests cover cross-layer invariants that are NOT already protected by the
dedicated unit/API test files (test_body_weight_trends.py,
test_body_weight_trend_schemas.py, test_body_weight_trend_api.py,
test_body_weight_trend_exceptions.py, test_phase_5b_final_audit.py,
test_migrations.py).  The intent is to freeze the trend feature, not to
duplicate existing coverage.

The tests are read-only and never connect to a real database.
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.authentication import get_settings as deps_get_settings
from app.core.body_weight_trends import BodyWeightTrendResult, calculate_body_weight_trend
from app.core.config import Settings
from app.core.tokens import create_access_token
from app.db.dependencies import get_db_session
from app.main import create_app
from app.models.body_weight import BodyWeight
from app.models.user import User
from app.schemas.body_weight_trends import BodyWeightTrendData
from app.services.body_weight import BodyWeightService

NOW = datetime.now(UTC)

EXPECTED_TREND_FIELDS = [
    "observation_count",
    "first_logged_date",
    "latest_logged_date",
    "starting_weight_kg",
    "latest_weight_kg",
    "absolute_change_kg",
    "percentage_change",
    "direction",
    "requires_onboarding",
]


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
    *,
    user_id: uuid.UUID | None = None,
    entry_id: uuid.UUID | None = None,
    logged_date: date | None = None,
    weight_kg: Decimal | None = None,
) -> MagicMock:
    entry = MagicMock(spec=BodyWeight)
    entry.id = uuid.uuid4()
    entry.user_id = user_id or uuid.uuid4()
    entry.entry_id = entry_id or uuid.uuid4()
    entry.logged_date = logged_date or date(2026, 7, 1)
    entry.weight_kg = weight_kg or Decimal("70.00")
    entry.created_at = NOW
    entry.updated_at = NOW
    return entry


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def test_settings() -> Settings:
    return Settings(
        APP_ENV="test",
        DEBUG=False,
        CORS_ORIGINS="http://test",
        JWT_SECRET_KEY="test-secret-key-that-is-at-least-32-characters!!",
    )


@pytest.fixture
def mock_session() -> AsyncMock:
    return _make_session()


@pytest.fixture
def app(test_settings: Settings, mock_session: AsyncMock):
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
# A. Cross-layer field alignment (domain result <-> schema)
# ===========================================================================


class TestTrendDomainSchemaFieldAlignment:
    """The public trend schema must mirror the domain result exactly.

    If a field is added to one side but not the other, the trend response
    would silently drift from the calculated domain value.
    """

    def test_field_names_match(self):
        domain_fields = set(BodyWeightTrendResult.__dataclass_fields__)
        schema_fields = set(BodyWeightTrendData.model_fields)
        # Schema may add UI-only fields (e.g. requires_onboarding) on top of domain.
        assert domain_fields.issubset(schema_fields)

    def test_field_names_are_exact_and_complete(self):
        domain_fields = list(BodyWeightTrendResult.__dataclass_fields__)
        # Domain fields — requires_onboarding lives only on schema (UI signal)
        assert domain_fields == EXPECTED_TREND_FIELDS[:-1]

    def test_field_order_matches(self):
        domain_fields = list(BodyWeightTrendResult.__dataclass_fields__)
        schema_fields = list(BodyWeightTrendData.model_fields)
        # Domain canonical order must be preserved at start of schema field list.
        assert domain_fields == EXPECTED_TREND_FIELDS[:-1]  # without requires_onboarding
        # Schema adds requires_onboarding at end.
        assert schema_fields[:-1] == EXPECTED_TREND_FIELDS[:-1]

    def test_direction_enum_is_reused_not_duplicated(self):
        from app.core.body_weight_trends import BodyWeightTrendDirection

        annotation = BodyWeightTrendData.model_fields["direction"].annotation
        assert annotation is BodyWeightTrendDirection

    def test_decimal_fields_remain_decimal_in_python(self):
        for field in (
            "starting_weight_kg",
            "latest_weight_kg",
            "absolute_change_kg",
            "percentage_change",
        ):
            annotation = BodyWeightTrendData.model_fields[field].annotation
            assert annotation is Decimal


# ===========================================================================
# B. Exact API orchestration (one call each, user-scoped)
# ===========================================================================


class TestTrendApiOrchestration:
    """The endpoint must invoke the existing pipeline exactly once each and
    never recompute or duplicate logic locally.
    """

    async def test_exact_orchestration(
        self,
        client,
        test_settings,
        mock_session,
        monkeypatch,
    ):
        user = _make_user()
        entries = [
            _make_body_weight(logged_date=date(2026, 7, 1), weight_kg=Decimal("75.00")),
            _make_body_weight(
                logged_date=date(2026, 7, 12),
                weight_kg=Decimal("73.50"),
                entry_id=uuid.uuid4(),
            ),
        ]

        auth_result = MagicMock()
        auth_result.scalars.return_value.one_or_none.return_value = user
        mock_session.execute = AsyncMock(return_value=auth_result)
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()

        calls = {"calc": 0, "from_result": 0, "list_history_user_id": None}
        real_calc = calculate_body_weight_trend
        real_from = BodyWeightTrendData.from_result

        def spy_calc(**kwargs):
            calls["calc"] += 1
            return real_calc(**kwargs)

        def spy_from(result):
            calls["from_result"] += 1
            return real_from(result)

        async def spy_list_history(self, *, user_id):
            calls["list_history_user_id"] = user_id
            return entries

        monkeypatch.setattr("app.api.v1.body_weights.calculate_body_weight_trend", spy_calc)
        monkeypatch.setattr(BodyWeightTrendData, "from_result", spy_from)
        monkeypatch.setattr(BodyWeightService, "list_history", spy_list_history)

        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/body-weights/trend",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        assert calls["calc"] == 1, "calculate_body_weight_trend must be called exactly once"
        assert calls["from_result"] == 1, (
            "BodyWeightTrendData.from_result must be called exactly once"
        )
        assert calls["list_history_user_id"] == user.id, "list_history must use current_user.id"
        data = response.json()["data"]
        assert data["observation_count"] == 2
        assert data["starting_weight_kg"] == "75.00"
        assert data["absolute_change_kg"] == "-1.50"
        assert data["direction"] == "decreased"

    async def test_insufficient_history_does_not_convert(
        self,
        client,
        test_settings,
        mock_session,
        monkeypatch,
    ):
        user = _make_user()
        auth_result = MagicMock()
        auth_result.scalars.return_value.one_or_none.return_value = user
        mock_session.execute = AsyncMock(return_value=auth_result)

        state = {"from_result_called": False}

        def spy_from(result):
            state["from_result_called"] = True
            return BodyWeightTrendData.from_result(result)

        async def spy_list_history(self, *, user_id):
            return []

        monkeypatch.setattr(BodyWeightTrendData, "from_result", spy_from)
        monkeypatch.setattr(BodyWeightService, "list_history", spy_list_history)

        token = create_access_token(user_id=user.id, settings=test_settings)
        response = await client.get(
            "/api/v1/body-weights/trend",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        assert state["from_result_called"] is False
        assert response.json()["data"]["requires_onboarding"] is True
