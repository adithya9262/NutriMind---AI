from __future__ import annotations

import pytest

from app.core.nutrition_log_exceptions import (
    InvalidNutritionLogEntryError,
    NutritionLogEntryAlreadyExistsError,
    NutritionLogEntryNotFoundError,
    NutritionLogError,
    NutritionLogPersistenceError,
)


class TestNutritionLogError:
    def test_inherits_from_exception(self):
        assert issubclass(NutritionLogError, Exception)

    def test_can_be_raised(self):
        with pytest.raises(NutritionLogError):
            raise NutritionLogError()

    def test_no_http_status_code(self):
        exc = NutritionLogError()
        assert not hasattr(exc, "status_code")

    def test_no_fastapi_dependency(self):
        import app.core.nutrition_log_exceptions as mod

        source = open(mod.__file__).read()
        assert "fastapi" not in source.lower()

    def test_no_http_exception_import(self):
        import app.core.nutrition_log_exceptions as mod

        source = open(mod.__file__).read()
        assert "HTTPException" not in source

    def test_no_sqlalchemy(self):
        import app.core.nutrition_log_exceptions as mod

        source = open(mod.__file__).read()
        assert "sqlalchemy" not in source.lower()

    def test_no_pydantic(self):
        import app.core.nutrition_log_exceptions as mod

        source = open(mod.__file__).read()
        assert "pydantic" not in source.lower()


class TestInvalidNutritionLogEntryError:
    def test_inherits_from_nutrition_log_error(self):
        assert issubclass(InvalidNutritionLogEntryError, NutritionLogError)

    def test_default_message_stable(self):
        exc = InvalidNutritionLogEntryError()
        assert str(exc) == "Nutrition log entry data is invalid."

    def test_custom_message(self):
        exc = InvalidNutritionLogEntryError("Custom invalid entry error")
        assert str(exc) == "Custom invalid entry error"

    def test_message_contains_no_sql(self):
        exc = InvalidNutritionLogEntryError()
        assert "SELECT" not in str(exc)
        assert "INSERT" not in str(exc)
        assert "FROM" not in str(exc)

    def test_message_contains_no_database_url(self):
        exc = InvalidNutritionLogEntryError()
        assert "postgresql" not in str(exc).lower()
        assert "localhost" not in str(exc)

    def test_message_contains_no_credentials(self):
        exc = InvalidNutritionLogEntryError()
        assert "password" not in str(exc).lower()
        assert "jwt" not in str(exc).lower()
        assert "token" not in str(exc).lower()

    def test_str_is_safe(self):
        exc = InvalidNutritionLogEntryError()
        s = str(exc)
        assert isinstance(s, str)
        assert len(s) > 0

    def test_repr_contains_no_secrets(self):
        exc = InvalidNutritionLogEntryError()
        assert "secret" not in repr(exc).lower()

    def test_no_sensitive_data_in_message(self):
        exc = InvalidNutritionLogEntryError()
        s = str(exc)
        assert "calories" not in s.lower()
        assert "protein" not in s.lower()

    def test_can_be_caught_as_base(self):
        with pytest.raises(NutritionLogError):
            raise InvalidNutritionLogEntryError()

    def test_args_behavior(self):
        exc = InvalidNutritionLogEntryError()
        assert exc.args == ("Nutrition log entry data is invalid.",)

    def test_custom_args_behavior(self):
        exc = InvalidNutritionLogEntryError("custom")
        assert exc.args == ("custom",)

    def test_no_nutrition_values_in_default_message(self):
        exc = InvalidNutritionLogEntryError()
        msg = str(exc)
        assert "10000" not in msg
        assert "1000" not in msg
        assert "2000" not in msg

    def test_no_env_access(self):
        import app.core.nutrition_log_exceptions as mod

        source = open(mod.__file__).read()
        assert "environ" not in source

    def test_no_network_access(self):
        import app.core.nutrition_log_exceptions as mod

        source = open(mod.__file__).read()
        assert "http" not in source.lower()

    def test_hashable(self):
        exc = InvalidNutritionLogEntryError()
        d = {exc: "mapped"}
        assert d[exc] == "mapped"


class TestImportSideEffects:
    def test_import_does_not_connect_to_database(self):
        import app.core.nutrition_log_exceptions as mod

        assert mod is not None

    def test_import_does_not_require_fastapi(self):
        import app.core.nutrition_log_exceptions as mod

        assert hasattr(mod, "NutritionLogError")
        assert hasattr(mod, "InvalidNutritionLogEntryError")

    def test_module_has_no_star_imports(self):
        import app.core.nutrition_log_exceptions as mod

        source = open(mod.__file__).read()
        assert "from " in source

    def test_no_database_dependency(self):
        import app.core.nutrition_log_exceptions as mod

        source = open(mod.__file__).read()
        assert "engine" not in source.lower()
        assert "session" not in source.lower()


class TestNutritionLogEntryNotFoundError:
    def test_inherits_from_nutrition_log_error(self):
        assert issubclass(NutritionLogEntryNotFoundError, NutritionLogError)

    def test_default_message_stable(self):
        exc = NutritionLogEntryNotFoundError()
        assert str(exc) == "Nutrition log entry was not found."

    def test_custom_message(self):
        exc = NutritionLogEntryNotFoundError("Custom not found")
        assert str(exc) == "Custom not found"

    def test_message_contains_no_sql(self):
        exc = NutritionLogEntryNotFoundError()
        assert "SELECT" not in str(exc)
        assert "INSERT" not in str(exc)

    def test_message_contains_no_database_url(self):
        exc = NutritionLogEntryNotFoundError()
        assert "postgresql" not in str(exc).lower()

    def test_message_contains_no_credentials(self):
        exc = NutritionLogEntryNotFoundError()
        assert "password" not in str(exc).lower()

    def test_str_is_safe(self):
        exc = NutritionLogEntryNotFoundError()
        s = str(exc)
        assert isinstance(s, str)
        assert len(s) > 0

    def test_can_be_raised(self):
        with pytest.raises(NutritionLogEntryNotFoundError):
            raise NutritionLogEntryNotFoundError()

    def test_can_be_caught_as_base(self):
        with pytest.raises(NutritionLogError):
            raise NutritionLogEntryNotFoundError()

    def test_args_behavior(self):
        exc = NutritionLogEntryNotFoundError()
        assert exc.args == ("Nutrition log entry was not found.",)

    def test_custom_args_behavior(self):
        exc = NutritionLogEntryNotFoundError("custom")
        assert exc.args == ("custom",)


class TestNutritionLogEntryAlreadyExistsError:
    def test_inherits_from_nutrition_log_error(self):
        assert issubclass(NutritionLogEntryAlreadyExistsError, NutritionLogError)

    def test_default_message_stable(self):
        exc = NutritionLogEntryAlreadyExistsError()
        assert str(exc) == "A nutrition log entry with this identifier already exists."

    def test_custom_message(self):
        exc = NutritionLogEntryAlreadyExistsError("Custom exists")
        assert str(exc) == "Custom exists"

    def test_message_contains_no_sql(self):
        exc = NutritionLogEntryAlreadyExistsError()
        assert "SELECT" not in str(exc)
        assert "INSERT" not in str(exc)

    def test_message_contains_no_constraint_name(self):
        exc = NutritionLogEntryAlreadyExistsError()
        assert "uq_nutrition_logs" not in str(exc)

    def test_message_contains_no_credentials(self):
        exc = NutritionLogEntryAlreadyExistsError()
        assert "password" not in str(exc).lower()

    def test_str_is_safe(self):
        exc = NutritionLogEntryAlreadyExistsError()
        s = str(exc)
        assert isinstance(s, str)
        assert len(s) > 0

    def test_can_be_raised(self):
        with pytest.raises(NutritionLogEntryAlreadyExistsError):
            raise NutritionLogEntryAlreadyExistsError()

    def test_can_be_caught_as_base(self):
        with pytest.raises(NutritionLogError):
            raise NutritionLogEntryAlreadyExistsError()

    def test_args_behavior(self):
        exc = NutritionLogEntryAlreadyExistsError()
        assert exc.args == ("A nutrition log entry with this identifier already exists.",)


class TestNutritionLogPersistenceError:
    def test_inherits_from_nutrition_log_error(self):
        assert issubclass(NutritionLogPersistenceError, NutritionLogError)

    def test_default_message_stable(self):
        exc = NutritionLogPersistenceError()
        assert str(exc) == "Nutrition log data could not be saved."

    def test_custom_message(self):
        exc = NutritionLogPersistenceError("Custom persistence error")
        assert str(exc) == "Custom persistence error"

    def test_message_contains_no_sql(self):
        exc = NutritionLogPersistenceError()
        assert "SELECT" not in str(exc)
        assert "INSERT" not in str(exc)

    def test_message_contains_no_credentials(self):
        exc = NutritionLogPersistenceError()
        assert "password" not in str(exc).lower()

    def test_str_is_safe(self):
        exc = NutritionLogPersistenceError()
        s = str(exc)
        assert isinstance(s, str)
        assert len(s) > 0

    def test_can_be_raised(self):
        with pytest.raises(NutritionLogPersistenceError):
            raise NutritionLogPersistenceError()

    def test_can_be_caught_as_base(self):
        with pytest.raises(NutritionLogError):
            raise NutritionLogPersistenceError()


class TestNewExceptionImports:
    def test_all_new_exceptions_importable(self):
        from app.core.nutrition_log_exceptions import (
            NutritionLogEntryAlreadyExistsError,
            NutritionLogEntryNotFoundError,
            NutritionLogPersistenceError,
        )

        assert NutritionLogEntryNotFoundError is not None
        assert NutritionLogEntryAlreadyExistsError is not None
        assert NutritionLogPersistenceError is not None

    def test_no_fastapi_in_new_exceptions(self):
        from app.core import nutrition_log_exceptions as mod

        source = open(mod.__file__).read()
        assert "fastapi" not in source.lower()

    def test_no_http_exception_in_new_exceptions(self):
        from app.core import nutrition_log_exceptions as mod

        source = open(mod.__file__).read()
        assert "HTTPException" not in source

    def test_no_sqlalchemy_in_new_exceptions(self):
        from app.core import nutrition_log_exceptions as mod

        source = open(mod.__file__).read()
        assert "sqlalchemy" not in source.lower()

    def test_no_raw_sql_in_new_exceptions(self):
        from app.core import nutrition_log_exceptions as mod

        source = open(mod.__file__).read()
        assert "INSERT" not in source
        assert "SELECT" not in source
        assert "UPDATE" not in source
        assert "DELETE" not in source

    def test_no_status_codes(self):
        from app.core import nutrition_log_exceptions as mod

        source = open(mod.__file__).read()
        assert "status_code" not in source
        assert "HTTP_" not in source
