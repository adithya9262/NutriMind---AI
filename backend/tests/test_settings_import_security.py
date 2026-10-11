from __future__ import annotations

import json
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.settings import import_data


def _session() -> AsyncMock:
    session = AsyncMock(spec=AsyncSession)
    result = MagicMock()
    result.scalars.return_value.one_or_none.return_value = None
    result.scalars.return_value.first.return_value = None
    session.execute = AsyncMock(return_value=result)
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session


def _upload(filename: str, content: bytes) -> MagicMock:
    upload = MagicMock(filename=filename)
    upload.read = AsyncMock(return_value=content)
    return upload


@pytest.mark.asyncio
async def test_simple_csv_import_uses_first_row_for_header_detection():
    session = _session()
    upload = _upload("weights.csv", b"2026-10-10,70.5 kg\n")

    response = await import_data(
        file=upload,
        session=session,
        current_user=MagicMock(id=uuid.uuid4()),
    )

    assert response["success"] is True
    assert response["imported"]["body_weights"] == 1
    session.add.assert_called_once()
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_invalid_goal_error_does_not_echo_health_record_or_exception():
    session = _session()
    sensitive_title = "private health goal"
    sensitive_type = "private-medical-category"
    upload = _upload(
        "backup.json",
        json.dumps({"goals": [{"title": sensitive_title, "goal_type": sensitive_type}]}).encode(
            "utf-8"
        ),
    )

    response = await import_data(
        file=upload,
        session=session,
        current_user=MagicMock(id=uuid.uuid4()),
    )

    assert response["success"] is True
    assert response["errors"] == [{"type": "goal", "reason": "Invalid or unavailable record."}]
    assert sensitive_title not in json.dumps(response)
    assert sensitive_type not in json.dumps(response)
