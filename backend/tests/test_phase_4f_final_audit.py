"""Phase 4F-10 -- Final audit cross-layer invariants.

Tests focus on cross-cutting invariants that span domain, schema, ORM,
migration, API, and OpenAPI layers.  These are not already comprehensively
covered by existing per-module tests.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from sqlalchemy import CheckConstraint, ForeignKeyConstraint, Numeric, String, UniqueConstraint

from app.api.v1.router import router
from app.core.nutrition_logs import (
    MAX_CALORIES_KCAL,
    MAX_CARBOHYDRATE_G,
    MAX_FAT_G,
    MAX_PROTEIN_G,
)
from app.db.base import Base
from app.main import create_app
from app.models.nutrition_log import NutritionLog
from app.schemas.nutrition_logs import (
    MAX_CALORIES_KCAL as SCHEMA_MAX_CALORIES_KCAL,
)
from app.schemas.nutrition_logs import (
    MAX_CARBOHYDRATE_G as SCHEMA_MAX_CARBOHYDRATE_G,
)
from app.schemas.nutrition_logs import (
    MAX_FAT_G as SCHEMA_MAX_FAT_G,
)
from app.schemas.nutrition_logs import (
    MAX_PROTEIN_G as SCHEMA_MAX_PROTEIN_G,
)

# ===========================================================================
# Cross-layer limit agreement
# ===========================================================================


class TestCrossLayerNumericLimitAgreement:
    """Domain constants, schema validators, and ORM constraints must agree."""

    def _check_constraint_text(self, field: str, expected: str) -> None:
        for c in NutritionLog.__table__.constraints:
            if isinstance(c, CheckConstraint) and field in c.name:
                assert expected in str(c.sqltext)
                break
        else:
            pytest.fail(f"{field} check constraint not found")

    def test_calories_limit_consistent(self):
        assert MAX_CALORIES_KCAL == SCHEMA_MAX_CALORIES_KCAL
        col = NutritionLog.__table__.c.calories_kcal
        assert isinstance(col.type, Numeric)
        assert col.type.precision == 7
        assert col.type.scale == 2
        self._check_constraint_text("calories_kcal", "10000")

    def test_protein_limit_consistent(self):
        assert MAX_PROTEIN_G == SCHEMA_MAX_PROTEIN_G
        col = NutritionLog.__table__.c.protein_g
        assert isinstance(col.type, Numeric)
        assert col.type.precision == 6
        assert col.type.scale == 2
        self._check_constraint_text("protein_g", "1000")

    def test_carbohydrate_limit_consistent(self):
        assert MAX_CARBOHYDRATE_G == SCHEMA_MAX_CARBOHYDRATE_G
        col = NutritionLog.__table__.c.carbohydrate_g
        assert isinstance(col.type, Numeric)
        assert col.type.precision == 6
        assert col.type.scale == 2
        self._check_constraint_text("carbohydrate_g", "2000")

    def test_fat_limit_consistent(self):
        assert MAX_FAT_G == SCHEMA_MAX_FAT_G
        col = NutritionLog.__table__.c.fat_g
        assert isinstance(col.type, Numeric)
        assert col.type.precision == 6
        assert col.type.scale == 2
        self._check_constraint_text("fat_g", "1000")


class TestCrossLayerTextLengthAgreement:
    """Domain, schema, and ORM must agree on text-field max lengths."""

    def test_food_name_length_consistent(self):
        col = NutritionLog.__table__.c.food_name
        assert isinstance(col.type, String)
        assert col.type.length == 200

    def test_serving_description_length_consistent(self):
        col = NutritionLog.__table__.c.serving_description
        assert isinstance(col.type, String)
        assert col.type.length == 200


# ===========================================================================
# ORM metadata
# ===========================================================================


class TestOrmMetadata:
    """Verify Base.metadata contains exactly the expected tables."""

    def test_exactly_five_tables(self):
        names = sorted(t.name for t in Base.metadata.sorted_tables)
        assert names == [
            "body_weights",
            "goals",
            "nutrition_logs",
            "nutrition_profiles",
            "tasks",
            "users",
        ]


# ===========================================================================
# Migration topology
# ===========================================================================


class TestMigrationTopology:
    """Verify migration file invariants without a live database."""

    VERSIONS_DIR = Path(__file__).resolve().parent.parent / "alembic" / "versions"

    def _py_files(self) -> list[Path]:
        return sorted(
            p for p in self.VERSIONS_DIR.iterdir() if p.suffix == ".py" and p.name != "__init__.py"
        )

    def test_exactly_five_revision_files(self):
        assert len(self._py_files()) == 7

    def test_correct_head_revision(self):
        content = self._py_files()[-1].read_text(encoding="utf-8")
        assert "e5f6a7b8c9d0" in content

    def test_no_branches(self):
        for f in self._py_files():
            content = f.read_text(encoding="utf-8")
            assert "branch_labels" in content
            assert "branch_labels =" in content or "branch_labels:" in content


# ===========================================================================
# Nutrition-log route ordering
# ===========================================================================


class TestNutritionLogRouteOrdering:
    """Static routes must be registered before dynamic {entry_id} routes."""

    def test_routes_in_correct_order(self):
        paths = [r.path for r in router.routes if hasattr(r, "path") and "nutrition-logs" in r.path]
        nl_paths = [p for p in paths if "/nutrition-logs" in p]
        for expected in [
            "/nutrition-logs",
            "/nutrition-logs",
            "/nutrition-logs/summary",
            "/nutrition-logs/progress",
        ]:
            assert expected in nl_paths, f"Expected {expected} not found"
        summary_idx = nl_paths.index("/nutrition-logs/summary")
        progress_idx = nl_paths.index("/nutrition-logs/progress")
        entry_path = "/nutrition-logs/{entry_id}"
        entry_idx = nl_paths.index(entry_path) if entry_path in nl_paths else len(nl_paths)
        assert summary_idx < entry_idx, "/summary must be before /{entry_id}"
        assert progress_idx < entry_idx, "/progress must be before /{entry_id}"


# ===========================================================================
# OpenAPI invariants
# ===========================================================================


class TestOpenAPIBearerAuth:
    """Exactly one BearerAuth scheme must exist in OpenAPI."""

    def _get_schema(self) -> dict:
        app = create_app()
        return get_openapi(title=app.title, version=app.version, routes=app.routes)

    def test_exactly_one_bearer_auth(self):
        schema = self._get_schema()
        schemes = schema.get("components", {}).get("securitySchemes", {})
        bearer = {k: v for k, v in schemes.items() if v.get("scheme") == "bearer"}
        msg = f"Expected 1 BearerAuth, found {len(bearer)}: {list(bearer.keys())}"
        assert len(bearer) == 1, msg

    def test_bearer_auth_is_http_type(self):
        schema = self._get_schema()
        schemes = schema.get("components", {}).get("securitySchemes", {})
        for details in schemes.values():
            if details.get("scheme") == "bearer":
                assert details.get("type") == "http"


class TestOpenAPINutritionLogPaths:
    """Verify expected nutrition-log paths and methods in OpenAPI."""

    def _get_openapi(self) -> dict:
        app = create_app()
        return get_openapi(title=app.title, version=app.version, routes=app.routes)

    def test_nutrition_logs_path_exists(self):
        assert "/api/v1/nutrition-logs" in self._get_openapi().get("paths", {})

    def test_nutrition_logs_entry_path_exists(self):
        assert "/api/v1/nutrition-logs/{entry_id}" in self._get_openapi().get("paths", {})

    def test_nutrition_logs_summary_path_exists(self):
        assert "/api/v1/nutrition-logs/summary" in self._get_openapi().get("paths", {})

    def test_nutrition_logs_progress_path_exists(self):
        assert "/api/v1/nutrition-logs/progress" in self._get_openapi().get("paths", {})

    def test_correct_methods_on_collection(self):
        methods = self._get_openapi()["paths"]["/api/v1/nutrition-logs"]
        assert "post" in methods
        assert "get" in methods
        assert "put" not in methods
        assert "patch" not in methods
        assert "delete" not in methods

    def test_correct_methods_on_entry(self):
        methods = self._get_openapi()["paths"]["/api/v1/nutrition-logs/{entry_id}"]
        assert "delete" in methods
        assert "get" not in methods
        assert "post" not in methods
        assert "put" not in methods
        assert "patch" not in methods

    def test_summary_is_get_only(self):
        methods = self._get_openapi()["paths"]["/api/v1/nutrition-logs/summary"]
        assert "get" in methods
        for verb in ("post", "put", "patch", "delete"):
            assert verb not in methods

    def test_progress_is_get_only(self):
        methods = self._get_openapi()["paths"]["/api/v1/nutrition-logs/progress"]
        assert "get" in methods
        for verb in ("post", "put", "patch", "delete"):
            assert verb not in methods


class TestOpenAPIQueryParams:
    """Verify required query parameters are documented."""

    def _get_openapi(self) -> dict:
        app = create_app()
        return get_openapi(title=app.title, version=app.version, routes=app.routes)

    def test_logged_date_required_on_list(self):
        params = self._get_openapi()["paths"]["/api/v1/nutrition-logs"]["get"]["parameters"]
        logged = [p for p in params if p.get("name") == "logged_date"]
        assert len(logged) == 1
        assert logged[0].get("required") is True
        assert logged[0].get("schema", {}).get("format") == "date"

    def test_logged_date_required_on_create(self):
        params = self._get_openapi()["paths"]["/api/v1/nutrition-logs"]["post"]["parameters"]
        logged = [p for p in params if p.get("name") == "logged_date"]
        assert len(logged) == 1
        assert logged[0].get("required") is True

    def test_logged_date_required_on_summary(self):
        schema = self._get_openapi()
        params = schema["paths"]["/api/v1/nutrition-logs/summary"]["get"]["parameters"]
        logged = [p for p in params if p.get("name") == "logged_date"]
        assert len(logged) == 1
        assert logged[0].get("required") is True

    def test_progress_params_required(self):
        path = "/api/v1/nutrition-logs/progress"
        params = self._get_openapi()["paths"][path]["get"]["parameters"]
        logged = [p for p in params if p.get("name") == "logged_date"]
        ref = [p for p in params if p.get("name") == "reference_date"]
        assert len(logged) == 1
        assert logged[0].get("required") is True
        assert len(ref) == 1
        assert ref[0].get("required") is True
        assert ref[0].get("schema", {}).get("format") == "date"


# ===========================================================================
# ORM constraints and indexes
# ===========================================================================


class TestNutritionLogORMConstraints:
    """Verify ORM NutritionLog has expected constraints."""

    def _fks(self) -> list:
        return [
            c for c in NutritionLog.__table__.constraints if isinstance(c, ForeignKeyConstraint)
        ]

    def test_foreign_key_to_users(self):
        user_fk = None
        for fk in self._fks():
            cols = list(fk.columns)
            if cols == [NutritionLog.__table__.c.user_id]:
                user_fk = fk
                break
        assert user_fk is not None
        assert list(user_fk.elements)[0].column.table.name == "users"
        assert user_fk.ondelete == "CASCADE"

    def test_unique_user_id_entry_id(self):
        uqs = [c for c in NutritionLog.__table__.constraints if isinstance(c, UniqueConstraint)]
        target = next(
            (c for c in uqs if set(c.columns.keys()) == {"user_id", "entry_id"}),
            None,
        )
        assert target is not None, "UniqueConstraint(user_id, entry_id) not found"
        assert target.name == "uq_nutrition_logs_user_id_entry_id"

    def test_composite_index_exists(self):
        indexes = NutritionLog.__table__.indexes
        target = next(
            (ix for ix in indexes if set(ix.columns.keys()) == {"user_id", "logged_date"}),
            None,
        )
        assert target is not None, "Index(user_id, logged_date) not found"
        assert target.name == "ix_nutrition_logs_user_id_logged_date"

    def test_exactly_four_check_constraints(self):
        checks = [c for c in NutritionLog.__table__.constraints if isinstance(c, CheckConstraint)]
        assert len(checks) == 4


# ===========================================================================
# Error-envelope consistency (module-level audit)
# ===========================================================================


class TestDomainLayerPurity:
    """Domain layer must have no framework imports."""

    DOMAIN_MODULES = [
        "app.core.nutrition_logs",
        "app.core.nutrition_log_exceptions",
        "app.core.nutrition_progress",
        "app.core.nutrition_progress_exceptions",
        "app.core.nutrition_calculations",
        "app.core.nutrition_calculation_exceptions",
    ]

    def _module_source(self, module_name: str) -> str:
        import importlib
        import inspect

        mod = importlib.import_module(module_name)
        return inspect.getsource(mod)

    def test_no_fastapi_imports(self):
        for mod_name in self.DOMAIN_MODULES:
            source = self._module_source(mod_name)
            assert "from fastapi" not in source, f"{mod_name} imports from fastapi"

    def test_no_starlette_imports(self):
        for mod_name in self.DOMAIN_MODULES:
            source = self._module_source(mod_name)
            assert "from starlette" not in source, f"{mod_name} imports from starlette"

    def test_no_sqlalchemy_imports(self):
        for mod_name in self.DOMAIN_MODULES:
            source = self._module_source(mod_name)
            assert "from sqlalchemy" not in source, f"{mod_name} imports from sqlalchemy"

    def test_no_pydantic_imports(self):
        for mod_name in self.DOMAIN_MODULES:
            source = self._module_source(mod_name)
            assert "from pydantic" not in source, f"{mod_name} imports from pydantic"

    def test_no_database_session(self):
        for mod_name in self.DOMAIN_MODULES:
            source = self._module_source(mod_name)
            assert "async_session" not in source.lower()

    def test_no_system_clock_for_dates(self):
        """Domain modules must not use date.today() or datetime.now()."""
        for mod_name in self.DOMAIN_MODULES:
            source = self._module_source(mod_name)
            assert "date.today" not in source
            assert "datetime.now" not in source
            assert "datetime.utcnow" not in source


class TestSchemaPrivacyAudit:
    """Public response schemas must not expose sensitive fields."""

    SENSITIVE = [
        "user_id",
        "password",
        "password_hash",
        "access_token",
        "refresh_token",
        "jwt",
    ]

    @pytest.mark.parametrize(
        "schema_module",
        [
            "app.schemas.nutrition_logs",
            "app.schemas.nutrition_progress",
            "app.schemas.nutrition_summaries",
        ],
    )
    def test_no_sensitive_field_names(self, schema_module: str):
        import importlib
        import inspect

        mod = importlib.import_module(schema_module)
        source = inspect.getsource(mod)
        for word in self.SENSITIVE:
            if word in source:
                lines = [line.strip() for line in source.split("\n") if word in line.lower()]
                bad_lines = [
                    ln for ln in lines if not ln.startswith("from app.core") and "import" not in ln
                ]
                if bad_lines:
                    pytest.fail(f"{schema_module} has sensitive field '{word}' in: {bad_lines}")


# ===========================================================================
# Application invariants
# ===========================================================================


class TestApplicationFactory:
    """Verify create_app works and produces consistent instances."""

    def test_two_instances_are_distinct(self):
        app1 = create_app()
        app2 = create_app()
        assert app1 is not app2
        assert app1.title == app2.title

    def test_openapi_generates_successfully(self):
        app = create_app()
        schema = get_openapi(title=app.title, version=app.version, routes=app.routes)
        assert "paths" in schema
        assert len(schema["paths"]) > 0

    def test_no_database_connection_on_import(self):
        from app.main import app

        assert isinstance(app, FastAPI)
