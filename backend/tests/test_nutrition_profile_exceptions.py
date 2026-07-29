from __future__ import annotations

import pytest

from app.core.nutrition_profile_exceptions import (
    NutritionProfileAlreadyExistsError,
    NutritionProfileError,
    NutritionProfileNotFoundError,
    NutritionProfilePersistenceError,
)


class TestNutritionProfileError:
    def test_inherits_from_exception(self):
        assert issubclass(NutritionProfileError, Exception)

    def test_can_be_raised(self):
        with pytest.raises(NutritionProfileError):
            raise NutritionProfileError()

    def test_no_http_status_code(self):
        exc = NutritionProfileError()
        assert not hasattr(exc, "status_code")

    def test_no_fastapi_dependency(self):
        import app.core.nutrition_profile_exceptions

        source = open(app.core.nutrition_profile_exceptions.__file__).read()
        assert "fastapi" not in source.lower()

    def test_no_http_exception_import(self):
        import app.core.nutrition_profile_exceptions

        source = open(app.core.nutrition_profile_exceptions.__file__).read()
        assert "HTTPException" not in source


class TestNutritionProfileNotFoundError:
    def test_inherits_from_nutrition_profile_error(self):
        assert issubclass(NutritionProfileNotFoundError, NutritionProfileError)

    def test_default_message_stable(self):
        exc = NutritionProfileNotFoundError()
        assert str(exc) == "Nutrition profile not found."

    def test_custom_message(self):
        exc = NutritionProfileNotFoundError("Custom not found")
        assert str(exc) == "Custom not found"

    def test_message_contains_no_sql(self):
        exc = NutritionProfileNotFoundError()
        assert "SELECT" not in str(exc)
        assert "INSERT" not in str(exc)
        assert "FROM" not in str(exc)

    def test_message_contains_no_database_url(self):
        exc = NutritionProfileNotFoundError()
        assert "postgresql" not in str(exc).lower()
        assert "localhost" not in str(exc)

    def test_message_contains_no_constraint_name(self):
        exc = NutritionProfileNotFoundError()
        assert "uq_nutrition_profiles_user_id" not in str(exc)
        assert "constraint" not in str(exc).lower()

    def test_message_contains_no_credentials(self):
        exc = NutritionProfileNotFoundError()
        assert "password" not in str(exc).lower()
        assert "jwt" not in str(exc).lower()
        assert "token" not in str(exc).lower()

    def test_str_is_safe(self):
        exc = NutritionProfileNotFoundError()
        s = str(exc)
        assert isinstance(s, str)
        assert len(s) > 0

    def test_repr_contains_no_secrets(self):
        exc = NutritionProfileNotFoundError()
        assert "secret" not in repr(exc).lower()


class TestNutritionProfileAlreadyExistsError:
    def test_inherits_from_nutrition_profile_error(self):
        assert issubclass(NutritionProfileAlreadyExistsError, NutritionProfileError)

    def test_default_message_stable(self):
        exc = NutritionProfileAlreadyExistsError()
        assert str(exc) == "A nutrition profile already exists for this user."

    def test_custom_message(self):
        exc = NutritionProfileAlreadyExistsError("Custom exists")
        assert str(exc) == "Custom exists"

    def test_message_contains_no_sql(self):
        exc = NutritionProfileAlreadyExistsError()
        assert "SELECT" not in str(exc)
        assert "INSERT" not in str(exc)

    def test_message_contains_no_constraint_name(self):
        exc = NutritionProfileAlreadyExistsError()
        assert "uq_nutrition_profiles_user_id" not in str(exc)
        assert "constraint" not in str(exc).lower()

    def test_message_contains_no_raw_database_error(self):
        exc = NutritionProfileAlreadyExistsError()
        assert "IntegrityError" not in str(exc)

    def test_message_contains_no_database_details(self):
        exc = NutritionProfileAlreadyExistsError()
        assert "pgcode" not in str(exc).lower()
        assert "psycopg" not in str(exc).lower()
        assert "asyncpg" not in str(exc).lower()

    def test_message_contains_no_user_email(self):
        exc = NutritionProfileAlreadyExistsError()
        assert "@" not in str(exc)

    def test_message_contains_no_credentials(self):
        exc = NutritionProfileAlreadyExistsError()
        assert "password" not in str(exc).lower()
        assert "token" not in str(exc).lower()

    def test_str_is_safe(self):
        exc = NutritionProfileAlreadyExistsError()
        s = str(exc)
        assert isinstance(s, str)
        assert len(s) > 0


class TestNutritionProfilePersistenceError:
    def test_inherits_from_nutrition_profile_error(self):
        assert issubclass(NutritionProfilePersistenceError, NutritionProfileError)

    def test_default_message_stable(self):
        exc = NutritionProfilePersistenceError()
        assert str(exc) == "Unable to save the nutrition profile."

    def test_custom_message(self):
        exc = NutritionProfilePersistenceError("Custom persistence")
        assert str(exc) == "Custom persistence"

    def test_message_contains_no_raw_error(self):
        exc = NutritionProfilePersistenceError()
        assert "IntegrityError" not in str(exc)
        assert "DatabaseError" not in str(exc)

    def test_message_contains_no_constraint_name(self):
        exc = NutritionProfilePersistenceError()
        assert "uq_" not in str(exc)
        assert "constraint" not in str(exc).lower()

    def test_message_contains_no_credentials(self):
        exc = NutritionProfilePersistenceError()
        assert "password" not in str(exc).lower()
        assert "token" not in str(exc).lower()

    def test_str_is_safe(self):
        exc = NutritionProfilePersistenceError()
        s = str(exc)
        assert isinstance(s, str)
        assert len(s) > 0


class TestImportSideEffects:
    def test_import_does_not_connect_to_database(self):
        import app.core.nutrition_profile_exceptions

        assert app.core.nutrition_profile_exceptions is not None

    def test_import_does_not_require_fastapi(self):
        import app.core.nutrition_profile_exceptions

        assert hasattr(app.core.nutrition_profile_exceptions, "NutritionProfileError")

    def test_import_works_without_database_url(self):
        import app.core.nutrition_profile_exceptions

        assert hasattr(
            app.core.nutrition_profile_exceptions,
            "NutritionProfileNotFoundError",
        )
        assert hasattr(
            app.core.nutrition_profile_exceptions,
            "NutritionProfileAlreadyExistsError",
        )
        assert hasattr(
            app.core.nutrition_profile_exceptions,
            "NutritionProfilePersistenceError",
        )

    def test_exceptions_are_hashable(self):
        exc = NutritionProfileNotFoundError()
        d = {exc: "mapped"}
        assert d[exc] == "mapped"
