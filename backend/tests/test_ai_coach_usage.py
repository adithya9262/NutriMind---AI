from __future__ import annotations

from datetime import UTC, date, datetime

from app.api.v1 import ai_coach


def test_usage_day_is_derived_from_utc(monkeypatch):
    class FixedDateTime:
        @classmethod
        def now(cls, tz=None):
            assert tz is UTC
            return datetime(2026, 10, 10, 23, 30, tzinfo=UTC)

    monkeypatch.setattr(ai_coach, "datetime", FixedDateTime)

    assert ai_coach._today_utc() == date(2026, 10, 10)
