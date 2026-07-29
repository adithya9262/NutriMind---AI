from __future__ import annotations

import pytest

from app.core.nutrition_calculation_exceptions import (
    NutritionCalculationError,
    UnsupportedBMRCalculationError,
)


class TestNutritionCalculationError:
    def test_inherits_from_exception(self):
        assert issubclass(NutritionCalculationError, Exception)

    def test_can_be_raised(self):
        with pytest.raises(NutritionCalculationError):
            raise NutritionCalculationError()

    def test_no_http_status_code(self):
        exc = NutritionCalculationError()
        assert not hasattr(exc, "status_code")

    def test_no_fastapi_dependency(self):
        import app.core.nutrition_calculation_exceptions as mod

        source = open(mod.__file__).read()
        assert "fastapi" not in source.lower()

    def test_no_http_exception_import(self):
        import app.core.nutrition_calculation_exceptions as mod

        source = open(mod.__file__).read()
        assert "HTTPException" not in source


class TestUnsupportedBMRCalculationError:
    def test_inherits_from_nutrition_calculation_error(self):
        assert issubclass(UnsupportedBMRCalculationError, NutritionCalculationError)

    def test_default_message_stable(self):
        exc = UnsupportedBMRCalculationError()
        expected = (
            "BMR cannot be calculated with the selected biological-sex option "
            "using the Mifflin-St Jeor equation."
        )
        assert str(exc) == expected

    def test_custom_message(self):
        exc = UnsupportedBMRCalculationError("Custom BMR error")
        assert str(exc) == "Custom BMR error"

    def test_message_contains_no_sql(self):
        exc = UnsupportedBMRCalculationError()
        assert "SELECT" not in str(exc)
        assert "INSERT" not in str(exc)
        assert "FROM" not in str(exc)

    def test_message_contains_no_database_url(self):
        exc = UnsupportedBMRCalculationError()
        assert "postgresql" not in str(exc).lower()
        assert "localhost" not in str(exc)

    def test_message_contains_no_credentials(self):
        exc = UnsupportedBMRCalculationError()
        assert "password" not in str(exc).lower()
        assert "jwt" not in str(exc).lower()
        assert "token" not in str(exc).lower()

    def test_str_is_safe(self):
        exc = UnsupportedBMRCalculationError()
        s = str(exc)
        assert isinstance(s, str)
        assert len(s) > 0

    def test_repr_contains_no_secrets(self):
        exc = UnsupportedBMRCalculationError()
        assert "secret" not in repr(exc).lower()

    def test_no_sensitive_data_in_message(self):
        exc = UnsupportedBMRCalculationError()
        s = str(exc)
        assert "male" not in s.lower() or "male" in s.lower()
        assert "female" not in s.lower() or "female" in s.lower()

    def test_can_be_caught_as_base(self):
        with pytest.raises(NutritionCalculationError):
            raise UnsupportedBMRCalculationError()


class TestImportSideEffects:
    def test_import_does_not_connect_to_database(self):
        import app.core.nutrition_calculation_exceptions as mod

        assert mod is not None

    def test_import_does_not_require_fastapi(self):
        import app.core.nutrition_calculation_exceptions as mod

        assert hasattr(mod, "NutritionCalculationError")
        assert hasattr(mod, "UnsupportedBMRCalculationError")

    def test_exceptions_are_hashable(self):
        exc = UnsupportedBMRCalculationError()
        d = {exc: "mapped"}
        assert d[exc] == "mapped"

    def test_module_has_no_star_imports(self):
        import app.core.nutrition_calculation_exceptions as mod

        source = open(mod.__file__).read()
        assert "from " in source
