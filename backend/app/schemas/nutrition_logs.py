from __future__ import annotations

from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.core.nutrition_logs import (
    MAX_CALORIES_KCAL,
    MAX_CARBOHYDRATE_G,
    MAX_FAT_G,
    MAX_PROTEIN_G,
    MEAL_TYPE_ORDER,
    NUTRITION_DECIMAL_QUANTUM,
    DailyNutritionLogSummary,
    DailyNutritionTotals,
    MealNutritionSummary,
    MealType,
    NutritionLogEntry,
)

# ---------------------------------------------------------------------------
# Decimal validation helpers
# ---------------------------------------------------------------------------

_NUTRITION_MAXES: dict[str, Decimal] = {
    "calories_kcal": MAX_CALORIES_KCAL,
    "protein_g": MAX_PROTEIN_G,
    "carbohydrate_g": MAX_CARBOHYDRATE_G,
    "fat_g": MAX_FAT_G,
}


def _reject_control_characters(value: str) -> None:
    if "\0" in value:
        raise ValueError("Must not contain null bytes")
    for ch in value:
        if ord(ch) < 32 or ord(ch) == 127:
            raise ValueError("Must not contain control characters")


def _validate_nutrition_value(value: object, field_name: str) -> Decimal:
    if isinstance(value, bool):
        raise ValueError(f"{field_name} must not be a boolean")
    try:
        d = Decimal(str(value))
    except Exception:
        raise ValueError(f"{field_name} must be a valid decimal number")
    if not d.is_finite():
        raise ValueError(f"{field_name} must be a finite number")
    if d < Decimal("0"):
        raise ValueError(f"{field_name} must not be negative")
    maximum = _NUTRITION_MAXES.get(field_name)
    if maximum is not None and d > maximum:
        raise ValueError(f"{field_name} must not exceed {maximum}")
    return d.quantize(NUTRITION_DECIMAL_QUANTUM, rounding=ROUND_HALF_UP)


# ---------------------------------------------------------------------------
# NutritionLogEntryCreate
# ---------------------------------------------------------------------------


class NutritionLogEntryCreate(BaseModel):
    entry_id: UUID
    food_name: str
    meal_type: MealType
    serving_description: str
    calories_kcal: Decimal
    protein_g: Decimal
    carbohydrate_g: Decimal
    fat_g: Decimal

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
    )

    @field_validator("food_name", "serving_description")
    @classmethod
    def validate_text(cls, v: str) -> str:
        _reject_control_characters(v)
        if not v:
            raise ValueError("Must not be empty")
        if len(v) > 200:
            raise ValueError("Must not exceed 200 characters")
        return v

    @field_validator(
        "calories_kcal",
        "protein_g",
        "carbohydrate_g",
        "fat_g",
        mode="before",
    )
    @classmethod
    def validate_nutrition(cls, v: object, info) -> Decimal:
        return _validate_nutrition_value(v, info.field_name)

    def to_domain(self) -> NutritionLogEntry:
        return NutritionLogEntry(
            entry_id=self.entry_id,
            food_name=self.food_name,
            meal_type=self.meal_type,
            serving_description=self.serving_description,
            calories_kcal=self.calories_kcal,
            protein_g=self.protein_g,
            carbohydrate_g=self.carbohydrate_g,
            fat_g=self.fat_g,
        )


# ---------------------------------------------------------------------------
# NutritionLogEntryData
# ---------------------------------------------------------------------------


class NutritionLogEntryData(BaseModel):
    entry_id: UUID
    food_name: str
    meal_type: MealType
    serving_description: str
    calories_kcal: Decimal
    protein_g: Decimal
    carbohydrate_g: Decimal
    fat_g: Decimal

    model_config = ConfigDict(from_attributes=True, extra="forbid", frozen=True)

    @field_validator(
        "calories_kcal",
        "protein_g",
        "carbohydrate_g",
        "fat_g",
        mode="before",
    )
    @classmethod
    def validate_nutrition(cls, v: object, info) -> Decimal:
        return _validate_nutrition_value(v, info.field_name)

    @classmethod
    def from_domain(cls, entry: NutritionLogEntry) -> NutritionLogEntryData:
        if not isinstance(entry, NutritionLogEntry):
            raise TypeError("entry must be a NutritionLogEntry")
        return cls(
            entry_id=entry.entry_id,
            food_name=entry.food_name,
            meal_type=entry.meal_type,
            serving_description=entry.serving_description,
            calories_kcal=entry.calories_kcal,
            protein_g=entry.protein_g,
            carbohydrate_g=entry.carbohydrate_g,
            fat_g=entry.fat_g,
        )


# ---------------------------------------------------------------------------
# DailyNutritionTotalsData
# ---------------------------------------------------------------------------


class DailyNutritionTotalsData(BaseModel):
    calories_kcal: Decimal
    protein_g: Decimal
    carbohydrate_g: Decimal
    fat_g: Decimal

    model_config = ConfigDict(extra="forbid", frozen=True)

    @field_validator(
        "calories_kcal",
        "protein_g",
        "carbohydrate_g",
        "fat_g",
        mode="before",
    )
    @classmethod
    def validate_nutrition(cls, v: object, info) -> Decimal:
        return _validate_nutrition_value(v, info.field_name)

    @classmethod
    def from_domain(cls, totals: DailyNutritionTotals) -> DailyNutritionTotalsData:
        if not isinstance(totals, DailyNutritionTotals):
            raise TypeError("totals must be a DailyNutritionTotals")
        return cls(
            calories_kcal=totals.calories_kcal,
            protein_g=totals.protein_g,
            carbohydrate_g=totals.carbohydrate_g,
            fat_g=totals.fat_g,
        )


# ---------------------------------------------------------------------------
# MealNutritionSummaryData
# ---------------------------------------------------------------------------


class MealNutritionSummaryData(BaseModel):
    meal_type: MealType
    entry_count: int
    totals: DailyNutritionTotalsData

    model_config = ConfigDict(extra="forbid", frozen=True)

    @field_validator("entry_count", mode="before")
    @classmethod
    def validate_entry_count(cls, v: object) -> int:
        if isinstance(v, bool):
            raise ValueError("entry_count must be an integer, not a boolean")
        if not isinstance(v, int):
            raise ValueError("entry_count must be an integer")
        if v < 0:
            raise ValueError("entry_count must not be negative")
        return v

    @classmethod
    def from_domain(cls, summary: MealNutritionSummary) -> MealNutritionSummaryData:
        if not isinstance(summary, MealNutritionSummary):
            raise TypeError("summary must be a MealNutritionSummary")
        return cls(
            meal_type=summary.meal_type,
            entry_count=summary.entry_count,
            totals=DailyNutritionTotalsData.from_domain(summary.totals),
        )


# ---------------------------------------------------------------------------
# DailyNutritionLogSummaryData
# ---------------------------------------------------------------------------


class DailyNutritionLogSummaryData(BaseModel):
    entry_count: int
    totals: DailyNutritionTotalsData
    meals: tuple[MealNutritionSummaryData, ...]

    model_config = ConfigDict(extra="forbid", frozen=True)

    @field_validator("entry_count", mode="before")
    @classmethod
    def validate_entry_count(cls, v: object) -> int:
        if isinstance(v, bool):
            raise ValueError("entry_count must be an integer, not a boolean")
        if not isinstance(v, int):
            raise ValueError("entry_count must be an integer")
        if v < 0:
            raise ValueError("entry_count must not be negative")
        return v

    @model_validator(mode="after")
    def validate_meals_order(self) -> DailyNutritionLogSummaryData:
        meals = self.meals
        if len(meals) != len(MEAL_TYPE_ORDER):
            raise ValueError(f"meals must contain exactly {len(MEAL_TYPE_ORDER)} entries")
        for i, (meal, expected) in enumerate(zip(meals, MEAL_TYPE_ORDER)):
            if meal.meal_type is not expected:
                raise ValueError("meals must be in stable order: breakfast, lunch, dinner, snack")
        return self

    @classmethod
    def from_domain(
        cls,
        summary: DailyNutritionLogSummary,
    ) -> DailyNutritionLogSummaryData:
        if not isinstance(summary, DailyNutritionLogSummary):
            raise TypeError("summary must be a DailyNutritionLogSummary")
        return cls(
            entry_count=summary.entry_count,
            totals=DailyNutritionTotalsData.from_domain(summary.totals),
            meals=tuple(MealNutritionSummaryData.from_domain(meal) for meal in summary.meals),
        )


# ---------------------------------------------------------------------------
# DailyNutritionLogSuccessResponse
# ---------------------------------------------------------------------------


class DailyNutritionLogSuccessResponse(BaseModel):
    success: Literal[True] = True
    message: str = "Daily nutrition log summarized successfully."
    data: DailyNutritionLogSummaryData

    model_config = ConfigDict(extra="forbid")


# ---------------------------------------------------------------------------
# NutritionLogEntrySuccessResponse  (create response)
# ---------------------------------------------------------------------------


class NutritionLogEntrySuccessResponse(BaseModel):
    success: Literal[True] = True
    message: str = "Nutrition log entry created successfully."
    data: NutritionLogEntryData

    model_config = ConfigDict(extra="forbid")


# ---------------------------------------------------------------------------
# NutritionLogEntryListData  (list data wrapper)
# ---------------------------------------------------------------------------


class NutritionLogEntryListData(BaseModel):
    logged_date: date
    entries: list[NutritionLogEntryData]

    model_config = ConfigDict(extra="forbid", frozen=True)


# ---------------------------------------------------------------------------
# NutritionLogEntryListSuccessResponse  (list response)
# ---------------------------------------------------------------------------


class NutritionLogEntryListSuccessResponse(BaseModel):
    success: Literal[True] = True
    message: str = "Nutrition log entries retrieved successfully."
    data: NutritionLogEntryListData

    model_config = ConfigDict(extra="forbid")


# ---------------------------------------------------------------------------
# NutritionLogDeleteSuccessResponse  (delete response)
# ---------------------------------------------------------------------------


class NutritionLogDeleteSuccessResponse(BaseModel):
    success: Literal[True] = True
    message: str = "Nutrition log entry deleted successfully."

    model_config = ConfigDict(extra="forbid")
