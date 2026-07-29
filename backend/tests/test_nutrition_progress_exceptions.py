from __future__ import annotations

from app.core.nutrition_progress_exceptions import (
    InvalidNutritionProgressInputError,
    NutritionProgressError,
)


class TestNutritionProgressExceptions:
    def test_base_exception(self):
        assert issubclass(NutritionProgressError, Exception)

    def test_invalid_input_inherits(self):
        assert issubclass(InvalidNutritionProgressInputError, NutritionProgressError)

    def test_default_message_stable(self):
        exc = InvalidNutritionProgressInputError()
        assert str(exc) == "Nutrition progress input is invalid."

    def test_no_fastapi_dependency(self):
        import inspect

        import app.core.nutrition_progress_exceptions as mod

        source = inspect.getsource(mod)
        assert "fastapi" not in source.lower()

    def test_no_http_status_code(self):
        exc = InvalidNutritionProgressInputError()
        assert not hasattr(exc, "status_code")

    def test_no_internal_values_exposed(self):
        exc = InvalidNutritionProgressInputError()
        s = str(exc)
        assert "Decimal" not in s
        assert "NaN" not in s
