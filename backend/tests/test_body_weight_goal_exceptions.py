from __future__ import annotations

import importlib.util

import pytest

from app.core.body_weight_goal_exceptions import (
    BodyWeightGoalError,
    InvalidBodyWeightGoalProgressError,
)

EXPECTED_MESSAGE = (
    "Body-weight goal progress requires a starting weight that differs from the target weight."
)

_PROHIBITED = {
    "fastapi",
    "starlette",
    "pydantic",
    "sqlalchemy",
    "alembic",
    "http",
    "os",
    "requests",
    "httpx",
    "urllib",
}


# ===========================================================================
# A. Exception hierarchy
# ===========================================================================


class TestExceptionHierarchy:
    def test_base_inherits_exception(self):
        assert issubclass(BodyWeightGoalError, Exception)

    def test_leaf_inherits_base(self):
        assert issubclass(InvalidBodyWeightGoalProgressError, BodyWeightGoalError)

    def test_leaf_inherits_exception(self):
        assert issubclass(InvalidBodyWeightGoalProgressError, Exception)

    def test_base_is_not_leaf(self):
        assert BodyWeightGoalError is not InvalidBodyWeightGoalProgressError

    def test_can_be_caught_as_base(self):
        with pytest.raises(BodyWeightGoalError):
            raise InvalidBodyWeightGoalProgressError()

    def test_can_be_caught_as_exception(self):
        with pytest.raises(Exception):
            raise InvalidBodyWeightGoalProgressError()


class TestExceptionMessage:
    def test_exact_default_message(self):
        assert str(InvalidBodyWeightGoalProgressError()) == EXPECTED_MESSAGE

    def test_message_is_stable(self):
        assert InvalidBodyWeightGoalProgressError().args[0] == EXPECTED_MESSAGE

    def test_no_raw_value_leak(self):
        err = InvalidBodyWeightGoalProgressError()
        assert "100" not in str(err)
        assert "80" not in str(err)
        assert "Decimal" not in str(err)

    def test_base_has_safe_default(self):
        assert str(BodyWeightGoalError()) != EXPECTED_MESSAGE
        assert "Decimal" in str(BodyWeightGoalError())


class TestExceptionFrameworkIndependence:
    def test_no_prohibited_imports(self):
        source = importlib.util.find_spec("app.core.body_weight_goal_exceptions")
        assert source is not None
        with open(source.origin, encoding="utf-8") as fh:
            text = fh.read().lower()
        for token in _PROHIBITED:
            assert token not in text, f"Prohibited import token: {token}"
