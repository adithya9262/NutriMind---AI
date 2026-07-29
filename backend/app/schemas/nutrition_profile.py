from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.enums import (
    ActivityLevel,
    BiologicalSex,
    DietaryPreference,
    FitnessGoal,
    NutritionGoal,
)

# ---------------------------------------------------------------------------
# Allergy normalization
# ---------------------------------------------------------------------------


def normalize_allergies(allergies: object) -> list[str]:
    if not isinstance(allergies, list):
        raise ValueError("Allergies must be a list of strings")

    if len(allergies) > 50:
        raise ValueError("Allergies must not contain more than 50 entries")

    seen: dict[str, int] = {}
    result: list[str] = []

    for item in allergies:
        if not isinstance(item, str):
            raise ValueError(f"Each allergy must be a string, got {type(item).__name__}")

        if "\0" in item:
            raise ValueError("Allergy must not contain null bytes")

        for ch in item:
            if ord(ch) < 32 and ch not in ("\t", "\n", "\r"):
                raise ValueError("Allergy must not contain control characters")

        trimmed = item.strip()
        if not trimmed:
            raise ValueError("Allergy must not be empty or whitespace-only")

        if len(trimmed) > 100:
            raise ValueError("Allergy must not exceed 100 characters")

        lower = trimmed.lower()
        if lower not in seen:
            seen[lower] = True
            result.append(trimmed)

    return result


# ---------------------------------------------------------------------------
# Reusable validation helpers
# ---------------------------------------------------------------------------


def _validate_date_of_birth(v: object) -> date | None:
    if v is None:
        return None
    if isinstance(v, date):
        d = v
    else:
        try:
            d = date.fromisoformat(str(v))
        except (ValueError, TypeError):
            raise ValueError("Date of birth must be a valid date")
    if d >= date.today():
        raise ValueError("Date of birth must be earlier than today")
    return d


def _validate_decimal_range(
    v: object,
    field_name: str,
    minimum: str,
    maximum: str,
) -> Decimal | None:
    if v is None:
        return None
    try:
        d = Decimal(str(v))
    except Exception:
        raise ValueError(f"{field_name} must be a valid decimal number")
    if not d.is_finite():
        raise ValueError(f"{field_name} must be a finite number")
    min_dec = Decimal(minimum)
    max_dec = Decimal(maximum)
    if d < min_dec:
        raise ValueError(f"{field_name} must be at least {min_dec}")
    if d > max_dec:
        raise ValueError(f"{field_name} must be at most {max_dec}")
    if d.as_tuple().exponent < -2:
        raise ValueError(f"{field_name} must have at most 2 decimal places")
    return d


# ---------------------------------------------------------------------------
# NutritionProfileBase
# ---------------------------------------------------------------------------


class NutritionProfileBase(BaseModel):
    date_of_birth: date | None = None
    biological_sex: BiologicalSex | None = None
    height_cm: Decimal | None = None
    weight_kg: Decimal | None = None
    activity_level: ActivityLevel | None = None
    goal: NutritionGoal | None = None
    target_weight_kg: Decimal | None = None
    dietary_preference: DietaryPreference | None = None
    allergies: list[str] = Field(default_factory=list)
    full_name: str | None = None
    phone: str | None = None
    avatar_url: str | None = None
    fitness_goal: FitnessGoal | None = None
    medical_conditions: list[str] = Field(default_factory=list)
    water_goal_ml: int | None = None
    sleep_goal_hours: Decimal | None = None
    daily_calorie_goal: int | None = None
    daily_protein_goal_g: int | None = None
    daily_carb_goal_g: int | None = None
    daily_fat_goal_g: int | None = None

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    @field_validator("date_of_birth", mode="before")
    @classmethod
    def validate_date_of_birth(cls, v: object) -> date | None:
        return _validate_date_of_birth(v)

    @field_validator("height_cm", mode="before")
    @classmethod
    def validate_height_cm(cls, v: object) -> Decimal | None:
        return _validate_decimal_range(v, "Height", "50.00", "300.00")

    @field_validator("weight_kg", mode="before")
    @classmethod
    def validate_weight_kg(cls, v: object) -> Decimal | None:
        return _validate_decimal_range(v, "Weight", "10.00", "700.00")

    @field_validator("target_weight_kg", mode="before")
    @classmethod
    def validate_target_weight_kg(cls, v: object) -> Decimal | None:
        return _validate_decimal_range(v, "Target weight", "10.00", "700.00")

    @field_validator("allergies", mode="before")
    @classmethod
    def validate_allergies(cls, v: object) -> list[str] | None:
        if v is None:
            return None
        return normalize_allergies(v)


# ---------------------------------------------------------------------------
# NutritionProfileCreate
# ---------------------------------------------------------------------------


class NutritionProfileCreate(NutritionProfileBase):
    pass


# ---------------------------------------------------------------------------
# NutritionProfileUpdate
# ---------------------------------------------------------------------------


class NutritionProfileUpdate(NutritionProfileBase):
    date_of_birth: date | None = None
    biological_sex: BiologicalSex | None = None
    height_cm: Decimal | None = None
    weight_kg: Decimal | None = None
    activity_level: ActivityLevel | None = None
    goal: NutritionGoal | None = None
    target_weight_kg: Decimal | None = None
    dietary_preference: DietaryPreference | None = None
    allergies: list[str] | None = None
    full_name: str | None = None
    phone: str | None = None
    avatar_url: str | None = None
    fitness_goal: FitnessGoal | None = None
    medical_conditions: list[str] | None = None
    water_goal_ml: int | None = None
    sleep_goal_hours: Decimal | None = None
    daily_calorie_goal: int | None = None
    daily_protein_goal_g: int | None = None
    daily_carb_goal_g: int | None = None
    daily_fat_goal_g: int | None = None

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    @model_validator(mode="after")
    @classmethod
    def reject_null_required_and_validate(cls, v: NutritionProfileUpdate) -> NutritionProfileUpdate:
        if "allergies" in v.model_fields_set and getattr(v, "allergies") is None:
            raise ValueError("allergies must not be null")
        if "medical_conditions" in v.model_fields_set and getattr(v, "medical_conditions") is None:
            raise ValueError("medical_conditions must not be null")
        return v


# ---------------------------------------------------------------------------
# NutritionProfilePublic
# ---------------------------------------------------------------------------


class NutritionProfilePublic(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    date_of_birth: date | None = None
    biological_sex: BiologicalSex | None = None
    height_cm: Decimal | None = None
    weight_kg: Decimal | None = None
    activity_level: ActivityLevel | None = None
    goal: NutritionGoal | None = None
    target_weight_kg: Decimal | None = None
    dietary_preference: DietaryPreference | None = None
    allergies: list[str] = Field(default_factory=list)
    full_name: str | None = None
    phone: str | None = None
    avatar_url: str | None = None
    fitness_goal: FitnessGoal | None = None
    medical_conditions: list[str] = Field(default_factory=list)
    water_goal_ml: int | None = None
    sleep_goal_hours: Decimal | None = None
    daily_calorie_goal: int | None = None
    daily_protein_goal_g: int | None = None
    daily_carb_goal_g: int | None = None
    daily_fat_goal_g: int | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, extra="forbid")

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


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class NutritionProfileData(BaseModel):
    profile: NutritionProfilePublic

    model_config = ConfigDict(extra="forbid")


class NutritionProfileSuccessResponse(BaseModel):
    success: bool = True
    message: str
    data: NutritionProfileData

    model_config = ConfigDict(extra="forbid")
