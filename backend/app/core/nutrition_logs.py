from __future__ import annotations

import enum
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID

from app.core.nutrition_log_exceptions import InvalidNutritionLogEntryError

# ---------------------------------------------------------------------------
# Meal type
# ---------------------------------------------------------------------------


class MealType(enum.StrEnum):
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"


MEAL_TYPE_ORDER: tuple[MealType, ...] = (
    MealType.BREAKFAST,
    MealType.LUNCH,
    MealType.DINNER,
    MealType.SNACK,
)

# ---------------------------------------------------------------------------
# Nutrition limit constants
# ---------------------------------------------------------------------------

MAX_CALORIES_KCAL: Decimal = Decimal("10000")
MAX_PROTEIN_G: Decimal = Decimal("1000")
MAX_CARBOHYDRATE_G: Decimal = Decimal("2000")
MAX_FAT_G: Decimal = Decimal("1000")

NUTRITION_DECIMAL_QUANTUM: Decimal = Decimal("0.01")

# ---------------------------------------------------------------------------
# Text validation helpers
# ---------------------------------------------------------------------------


def _reject_control_characters(value: str, field_name: str) -> None:
    for ch in value:
        code = ord(ch)
        if code < 32 or code == 127:
            raise InvalidNutritionLogEntryError(f"{field_name} must not contain control characters")


def _validate_text(value: object, field_name: str, max_length: int) -> str:
    if not isinstance(value, str) or isinstance(value, bool):
        raise InvalidNutritionLogEntryError(f"{field_name} must be a string")
    if "\0" in value:
        raise InvalidNutritionLogEntryError(f"{field_name} must not contain null bytes")
    _reject_control_characters(value, field_name)
    trimmed = value.strip()
    if not trimmed:
        raise InvalidNutritionLogEntryError(f"{field_name} must not be empty or whitespace-only")
    if len(trimmed) > max_length:
        raise InvalidNutritionLogEntryError(f"{field_name} must not exceed {max_length} characters")
    return trimmed


def _validate_food_name(value: object) -> str:
    return _validate_text(value, "food_name", 200)


def _validate_serving_description(value: object) -> str:
    return _validate_text(value, "serving_description", 200)


# ---------------------------------------------------------------------------
# Decimal validation helpers
# ---------------------------------------------------------------------------

_NUTRITION_MAXES: dict[str, Decimal] = {
    "calories_kcal": MAX_CALORIES_KCAL,
    "protein_g": MAX_PROTEIN_G,
    "carbohydrate_g": MAX_CARBOHYDRATE_G,
    "fat_g": MAX_FAT_G,
}


def _validate_nutrition_decimal(value: object, field_name: str) -> Decimal:
    if isinstance(value, bool):
        raise InvalidNutritionLogEntryError(f"{field_name} must be a Decimal, not a boolean")
    if not isinstance(value, Decimal):
        raise InvalidNutritionLogEntryError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise InvalidNutritionLogEntryError(f"{field_name} must be a finite number")
    if value < Decimal("0"):
        raise InvalidNutritionLogEntryError(f"{field_name} must not be negative")
    maximum = _NUTRITION_MAXES.get(field_name)
    if maximum is not None and value > maximum:
        raise InvalidNutritionLogEntryError(f"{field_name} must not exceed {maximum}")
    return value.quantize(NUTRITION_DECIMAL_QUANTUM, rounding=ROUND_HALF_UP)


# ---------------------------------------------------------------------------
# Nutrition-log entry
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class NutritionLogEntry:
    entry_id: UUID
    food_name: str
    meal_type: MealType
    serving_description: str
    calories_kcal: Decimal
    protein_g: Decimal
    carbohydrate_g: Decimal
    fat_g: Decimal

    def __post_init__(self) -> None:
        if not isinstance(self.entry_id, UUID):
            raise InvalidNutritionLogEntryError("entry_id must be a UUID instance")

        _validate_food_name(self.food_name)
        object.__setattr__(self, "food_name", self.food_name.strip())

        if not isinstance(self.meal_type, MealType):
            raise InvalidNutritionLogEntryError("meal_type must be a MealType member")
        _validate_serving_description(self.serving_description)
        object.__setattr__(self, "serving_description", self.serving_description.strip())

        object.__setattr__(
            self,
            "calories_kcal",
            _validate_nutrition_decimal(self.calories_kcal, "calories_kcal"),
        )
        object.__setattr__(
            self,
            "protein_g",
            _validate_nutrition_decimal(self.protein_g, "protein_g"),
        )
        object.__setattr__(
            self,
            "carbohydrate_g",
            _validate_nutrition_decimal(self.carbohydrate_g, "carbohydrate_g"),
        )
        object.__setattr__(
            self,
            "fat_g",
            _validate_nutrition_decimal(self.fat_g, "fat_g"),
        )


# ---------------------------------------------------------------------------
# Daily nutrition totals
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class DailyNutritionTotals:
    calories_kcal: Decimal
    protein_g: Decimal
    carbohydrate_g: Decimal
    fat_g: Decimal

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "calories_kcal",
            _validate_nutrition_decimal(self.calories_kcal, "calories_kcal"),
        )
        object.__setattr__(
            self,
            "protein_g",
            _validate_nutrition_decimal(self.protein_g, "protein_g"),
        )
        object.__setattr__(
            self,
            "carbohydrate_g",
            _validate_nutrition_decimal(self.carbohydrate_g, "carbohydrate_g"),
        )
        object.__setattr__(
            self,
            "fat_g",
            _validate_nutrition_decimal(self.fat_g, "fat_g"),
        )


# ---------------------------------------------------------------------------
# Meal nutrition summary
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class MealNutritionSummary:
    meal_type: MealType
    entry_count: int
    totals: DailyNutritionTotals

    def __post_init__(self) -> None:
        if not isinstance(self.meal_type, MealType):
            raise InvalidNutritionLogEntryError("meal_type must be a MealType member")
        if isinstance(self.entry_count, bool) or not isinstance(self.entry_count, int):
            raise InvalidNutritionLogEntryError("entry_count must be a non-negative integer")
        if self.entry_count < 0:
            raise InvalidNutritionLogEntryError("entry_count must be non-negative")
        if not isinstance(self.totals, DailyNutritionTotals):
            raise InvalidNutritionLogEntryError("totals must be a DailyNutritionTotals instance")


# ---------------------------------------------------------------------------
# Daily nutrition log summary
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class DailyNutritionLogSummary:
    entry_count: int
    totals: DailyNutritionTotals
    meals: tuple[MealNutritionSummary, ...]

    def __post_init__(self) -> None:
        if isinstance(self.entry_count, bool) or not isinstance(self.entry_count, int):
            raise InvalidNutritionLogEntryError("entry_count must be a non-negative integer")
        if self.entry_count < 0:
            raise InvalidNutritionLogEntryError("entry_count must be non-negative")
        if not isinstance(self.totals, DailyNutritionTotals):
            raise InvalidNutritionLogEntryError("totals must be a DailyNutritionTotals instance")
        if not isinstance(self.meals, tuple):
            raise InvalidNutritionLogEntryError("meals must be a tuple")
        if len(self.meals) != 4:
            raise InvalidNutritionLogEntryError(
                "meals must contain exactly 4 MealNutritionSummary entries"
            )
        seen: set[str] = set()
        for i, meal in enumerate(self.meals):
            if not isinstance(meal, MealNutritionSummary):
                raise InvalidNutritionLogEntryError(
                    "each meal must be a MealNutritionSummary instance"
                )
            if meal.meal_type.value in seen:
                raise InvalidNutritionLogEntryError("meals must not contain duplicate meal types")
            seen.add(meal.meal_type.value)
            if meal.meal_type is not MEAL_TYPE_ORDER[i]:
                raise InvalidNutritionLogEntryError(
                    "meals must be in stable order: breakfast, lunch, dinner, snack"
                )


# ---------------------------------------------------------------------------
# Calculate daily totals
# ---------------------------------------------------------------------------


def calculate_daily_nutrition_totals(
    *,
    entries: tuple[NutritionLogEntry, ...],
) -> DailyNutritionTotals:
    if not isinstance(entries, tuple):
        raise InvalidNutritionLogEntryError(
            "entries must be a tuple of NutritionLogEntry instances"
        )
    for item in entries:
        if not isinstance(item, NutritionLogEntry):
            raise InvalidNutritionLogEntryError("each entry must be a NutritionLogEntry instance")

    total_calories = sum((e.calories_kcal for e in entries), Decimal("0"))
    total_protein = sum((e.protein_g for e in entries), Decimal("0"))
    total_carb = sum((e.carbohydrate_g for e in entries), Decimal("0"))
    total_fat = sum((e.fat_g for e in entries), Decimal("0"))

    return DailyNutritionTotals(
        calories_kcal=total_calories,
        protein_g=total_protein,
        carbohydrate_g=total_carb,
        fat_g=total_fat,
    )


# ---------------------------------------------------------------------------
# Summarize daily nutrition log
# ---------------------------------------------------------------------------


def summarize_daily_nutrition_log(
    *,
    entries: tuple[NutritionLogEntry, ...],
) -> DailyNutritionLogSummary:
    if not isinstance(entries, tuple):
        raise InvalidNutritionLogEntryError(
            "entries must be a tuple of NutritionLogEntry instances"
        )
    for item in entries:
        if not isinstance(item, NutritionLogEntry):
            raise InvalidNutritionLogEntryError("each entry must be a NutritionLogEntry instance")

    overall_totals = calculate_daily_nutrition_totals(entries=entries)

    meal_entries: dict[MealType, list[NutritionLogEntry]] = {mt: [] for mt in MEAL_TYPE_ORDER}
    for entry in entries:
        meal_entries[entry.meal_type].append(entry)

    meal_summaries: list[MealNutritionSummary] = []
    for mt in MEAL_TYPE_ORDER:
        mt_entries = tuple(meal_entries[mt])
        mt_totals = calculate_daily_nutrition_totals(entries=mt_entries)
        meal_summaries.append(
            MealNutritionSummary(
                meal_type=mt,
                entry_count=len(mt_entries),
                totals=mt_totals,
            )
        )

    return DailyNutritionLogSummary(
        entry_count=len(entries),
        totals=overall_totals,
        meals=tuple(meal_summaries),
    )
