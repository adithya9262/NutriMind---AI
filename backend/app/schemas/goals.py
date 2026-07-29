from __future__ import annotations

import uuid
from collections.abc import Iterable
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator

from app.models.enums import GoalStatus, GoalType

# ---------------------------------------------------------------------------
# GoalCreate  (input schema)
# ---------------------------------------------------------------------------


class GoalCreate(BaseModel):
    goal_type: GoalType
    title: str
    description: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    weekly_target: Decimal | None = None
    target_calories: int | None = None
    target_protein_g: int | None = None
    target_carbs_g: int | None = None
    target_fats_g: int | None = None
    target_water_ml: int | None = None

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    @field_validator("title", mode="before")
    @classmethod
    def validate_title(cls, v: object) -> str:
        if isinstance(v, bool) or not isinstance(v, str):
            raise ValueError("title must be a string")
        if "\0" in v:
            raise ValueError("title must not contain null bytes")
        for ch in v:
            if ord(ch) < 32 and ch not in ("\t", "\n", "\r"):
                raise ValueError("title must not contain control characters")
        normalized = v.strip()
        if not normalized:
            raise ValueError("title must not be empty or whitespace-only")
        if len(normalized) > 200:
            raise ValueError("title must not exceed 200 characters")
        return normalized

    @field_validator("description", mode="before")
    @classmethod
    def validate_description(cls, v: object) -> str | None:
        if v is None:
            return None
        if isinstance(v, bool) or not isinstance(v, str):
            raise ValueError("description must be a string or None")
        if "\0" in v:
            raise ValueError("description must not contain null bytes")
        for ch in v:
            if ord(ch) < 32 and ch not in ("\t", "\n", "\r"):
                raise ValueError("description must not contain control characters")
        normalized = v.strip()
        if not normalized:
            return None
        if len(normalized) > 2000:
            raise ValueError("description must not exceed 2000 characters")
        return normalized

    @field_validator("start_date", mode="before")
    @classmethod
    def validate_start_date(cls, v: object) -> date | None:
        if v is None or v == "":
            return None
        if isinstance(v, datetime):
            raise ValueError("start_date must be a date, not a datetime")
        if isinstance(v, date):
            return v
        if isinstance(v, str):
            try:
                return date.fromisoformat(v)
            except ValueError:
                raise ValueError("start_date must be a valid date in YYYY-MM-DD format")
        raise ValueError("start_date must be a date instance or ISO format string")

    @field_validator("end_date", mode="before")
    @classmethod
    def validate_end_date(cls, v: object) -> date | None:
        if v is None or v == "":
            return None
        if isinstance(v, datetime):
            raise ValueError("end_date must be a date, not a datetime")
        if isinstance(v, date):
            return v
        if isinstance(v, str):
            try:
                return date.fromisoformat(v)
            except ValueError:
                raise ValueError("end_date must be a valid date in YYYY-MM-DD format")
        raise ValueError("end_date must be a date instance or ISO format string")

    @field_validator("weekly_target", mode="before")
    @classmethod
    def validate_weekly_target(cls, v: object) -> Decimal | None:
        if v is None:
            return None
        try:
            d = Decimal(str(v))
        except Exception:
            raise ValueError("weekly_target must be a valid decimal number")
        if not d.is_finite():
            raise ValueError("weekly_target must be a finite number")
        return d


# ---------------------------------------------------------------------------
# GoalUpdate  (input schema for PATCH)
# ---------------------------------------------------------------------------


class GoalUpdate(BaseModel):
    goal_type: GoalType | None = None
    title: str | None = None
    description: str | None = None
    status: GoalStatus | None = None
    start_date: date | None = None
    end_date: date | None = None
    weekly_target: Decimal | None = None
    target_calories: int | None = None
    target_protein_g: int | None = None
    target_carbs_g: int | None = None
    target_fats_g: int | None = None
    target_water_ml: int | None = None
    progress_percentage: Decimal | None = None

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    @field_validator("title", mode="before")
    @classmethod
    def validate_title(cls, v: object) -> str | None:
        if v is None:
            return None
        if isinstance(v, bool) or not isinstance(v, str):
            raise ValueError("title must be a string")
        if "\0" in v:
            raise ValueError("title must not contain null bytes")
        for ch in v:
            if ord(ch) < 32 and ch not in ("\t", "\n", "\r"):
                raise ValueError("title must not contain control characters")
        normalized = v.strip()
        if not normalized:
            raise ValueError("title must not be empty or whitespace-only")
        if len(normalized) > 200:
            raise ValueError("title must not exceed 200 characters")
        return normalized

    @field_validator("description", mode="before")
    @classmethod
    def validate_description(cls, v: object) -> str | None:
        if v is None:
            return None
        if isinstance(v, bool) or not isinstance(v, str):
            raise ValueError("description must be a string or None")
        if "\0" in v:
            raise ValueError("description must not contain null bytes")
        for ch in v:
            if ord(ch) < 32 and ch not in ("\t", "\n", "\r"):
                raise ValueError("description must not contain control characters")
        normalized = v.strip()
        if not normalized:
            return None
        if len(normalized) > 2000:
            raise ValueError("description must not exceed 2000 characters")
        return normalized

    @field_validator("weekly_target", mode="before")
    @classmethod
    def validate_weekly_target(cls, v: object) -> Decimal | None:
        if v is None:
            return None
        try:
            d = Decimal(str(v))
        except Exception:
            raise ValueError("weekly_target must be a valid decimal number")
        if not d.is_finite():
            raise ValueError("weekly_target must be a finite number")
        return d

    @field_validator("progress_percentage", mode="before")
    @classmethod
    def validate_progress_percentage(cls, v: object) -> Decimal | None:
        if v is None:
            return None
        try:
            d = Decimal(str(v))
        except Exception:
            raise ValueError("progress_percentage must be a valid decimal number")
        if not d.is_finite():
            raise ValueError("progress_percentage must be a finite number")
        if d < Decimal("0") or d > Decimal("100"):
            raise ValueError("progress_percentage must be between 0 and 100")
        return d


# ---------------------------------------------------------------------------
# GoalData  (public response schema)
# ---------------------------------------------------------------------------


class GoalData(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    goal_type: GoalType
    title: str
    description: str | None
    status: GoalStatus
    start_date: date | None
    end_date: date | None
    weekly_target: Decimal | None
    target_calories: int | None
    target_protein_g: int | None
    target_carbs_g: int | None
    target_fats_g: int | None
    target_water_ml: int | None
    progress_percentage: Decimal | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        from_attributes=True,
    )

    @field_validator("created_at", "updated_at", mode="before")
    @classmethod
    def validate_timezone_aware(cls, v: object) -> object:
        if v is None:
            return v
        if isinstance(v, datetime):
            if v.tzinfo is None:
                raise ValueError("Timestamp must be timezone-aware")
            return v
        if isinstance(v, str):
            try:
                dt = datetime.fromisoformat(v)
            except ValueError:
                raise ValueError("Invalid timestamp format")
            if dt.tzinfo is None:
                raise ValueError("Timestamp must be timezone-aware")
        return v

    @classmethod
    def from_orm_model(cls, goal: object) -> GoalData:
        if not hasattr(goal, "id"):
            raise TypeError("goal must have an id attribute")
        return cls(
            id=goal.id,
            user_id=goal.user_id,
            goal_type=goal.goal_type,
            title=goal.title,
            description=goal.description,
            status=goal.status,
            start_date=goal.start_date,
            end_date=goal.end_date,
            weekly_target=goal.weekly_target,
            target_calories=goal.target_calories,
            target_protein_g=goal.target_protein_g,
            target_carbs_g=goal.target_carbs_g,
            target_fats_g=goal.target_fats_g,
            target_water_ml=goal.target_water_ml,
            progress_percentage=goal.progress_percentage,
            created_at=goal.created_at,
            updated_at=goal.updated_at,
        )


# ---------------------------------------------------------------------------
# GoalListData  (collection response schema)
# ---------------------------------------------------------------------------


class GoalListData(BaseModel):
    goals: tuple[GoalData, ...]

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    @classmethod
    def from_domain(cls, goals: Iterable[object]) -> GoalListData:
        materialized = tuple(GoalData.from_orm_model(g) for g in goals)
        return cls(goals=materialized)


# ---------------------------------------------------------------------------
# Success response schemas
# ---------------------------------------------------------------------------


class GoalSuccessResponse(BaseModel):
    success: Literal[True] = True
    message: str = "Goal created successfully."
    data: GoalData

    model_config = ConfigDict(extra="forbid")


class GoalListSuccessResponse(BaseModel):
    success: Literal[True] = True
    message: str = "Goals retrieved successfully."
    data: GoalListData

    model_config = ConfigDict(extra="forbid")


class GoalDeleteSuccessResponse(BaseModel):
    success: Literal[True] = True
    message: str = "Goal deleted successfully."

    model_config = ConfigDict(extra="forbid")


__all__ = [
    "GoalCreate",
    "GoalData",
    "GoalDeleteSuccessResponse",
    "GoalListData",
    "GoalListSuccessResponse",
    "GoalSuccessResponse",
    "GoalUpdate",
]
