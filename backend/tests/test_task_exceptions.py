from __future__ import annotations

import importlib.util

import pytest

from app.core.task_exceptions import (
    InvalidTaskError,
    TaskAlreadyCompletedError,
    TaskError,
    TaskNotCompletedError,
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
    "datetime",
    "date",
    "uuid",
    "database",
}

EXPECTED_INVALID = "Task data is invalid."
EXPECTED_ALREADY = "Task is already completed."
EXPECTED_NOT = "Task is not completed."


# ===========================================================================
# A. Exception hierarchy
# ===========================================================================


class TestExceptionHierarchy:
    def test_base_inherits_exception(self):
        assert issubclass(TaskError, Exception)

    def test_invalid_inherits_base(self):
        assert issubclass(InvalidTaskError, TaskError)

    def test_already_inherits_base(self):
        assert issubclass(TaskAlreadyCompletedError, TaskError)

    def test_not_inherits_base(self):
        assert issubclass(TaskNotCompletedError, TaskError)

    def test_all_inherit_exception(self):
        for cls in (InvalidTaskError, TaskAlreadyCompletedError, TaskNotCompletedError):
            assert issubclass(cls, Exception)

    def test_base_is_distinct(self):
        assert TaskError is not InvalidTaskError
        assert TaskError is not TaskAlreadyCompletedError
        assert TaskError is not TaskNotCompletedError

    def test_can_be_caught_as_base(self):
        with pytest.raises(TaskError):
            raise InvalidTaskError()
        with pytest.raises(TaskError):
            raise TaskAlreadyCompletedError()
        with pytest.raises(TaskError):
            raise TaskNotCompletedError()

    def test_can_be_caught_as_exception(self):
        with pytest.raises(Exception):
            raise InvalidTaskError()


# ===========================================================================
# B. Exact messages
# ===========================================================================


class TestExceptionMessages:
    def test_invalid_exact_message(self):
        assert str(InvalidTaskError()) == EXPECTED_INVALID

    def test_already_exact_message(self):
        assert str(TaskAlreadyCompletedError()) == EXPECTED_ALREADY

    def test_not_exact_message(self):
        assert str(TaskNotCompletedError()) == EXPECTED_NOT

    def test_message_stable_args(self):
        assert InvalidTaskError().args[0] == EXPECTED_INVALID
        assert TaskAlreadyCompletedError().args[0] == EXPECTED_ALREADY
        assert TaskNotCompletedError().args[0] == EXPECTED_NOT

    def test_default_message_attribute(self):
        assert InvalidTaskError.default_message == EXPECTED_INVALID
        assert TaskAlreadyCompletedError.default_message == EXPECTED_ALREADY
        assert TaskNotCompletedError.default_message == EXPECTED_NOT

    def test_custom_message(self):
        assert str(InvalidTaskError("custom")) == "custom"

    def test_no_raw_value_leak(self):
        for err in (
            InvalidTaskError(),
            TaskAlreadyCompletedError(),
            TaskNotCompletedError(),
        ):
            text = str(err)
            assert "UUID" not in text
            assert "datetime" not in text
            assert "\n" not in text

    def test_base_has_no_specific_message(self):
        assert str(TaskError()) not in (EXPECTED_INVALID, EXPECTED_ALREADY, EXPECTED_NOT)


# ===========================================================================
# C. Framework / database independence
# ===========================================================================


class TestExceptionFrameworkIndependence:
    def test_no_prohibited_imports(self):
        spec = importlib.util.find_spec("app.core.task_exceptions")
        assert spec is not None
        with open(spec.origin, encoding="utf-8") as fh:
            text = fh.read().lower()
        for token in _PROHIBITED:
            assert token not in text, f"Prohibited import token: {token}"

    def test_only_stdlib_and_base(self):
        spec = importlib.util.find_spec("app.core.task_exceptions")
        assert spec is not None
        with open(spec.origin, encoding="utf-8") as fh:
            source = fh.read()
        for line in source.splitlines():
            stripped = line.strip()
            if stripped.startswith("import ") or stripped.startswith("from "):
                assert stripped in ("from __future__ import annotations",)
