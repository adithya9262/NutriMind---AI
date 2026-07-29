from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.core.nutrition_summaries import (
    NutritionSummaryItem,
    NutritionSummaryResult,
    NutritionSummaryTone,
)

# ---------------------------------------------------------------------------
# Stable structural contract (Phase 4E-1 verified)
# ---------------------------------------------------------------------------

EXPECTED_NUTRITION_SUMMARY_ITEM_COUNT = 6

EXPECTED_NUTRITION_SUMMARY_CODES: tuple[str, ...] = (
    "BMI_SCREENING_CONTEXT",
    "DAILY_ENERGY_ESTIMATE",
    "CALORIE_TARGET_CONTEXT",
    "MACRONUTRIENT_TARGET_CONTEXT",
    "GOAL_CONTEXT",
    "GENERAL_ESTIMATE_LIMITATION",
)

_CODE_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]*$")

_MAX_CODE_LENGTH = 100
_MAX_TITLE_LENGTH = 120
_MAX_MESSAGE_LENGTH = 1000
_MAX_OVERVIEW_LENGTH = 1000


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------


def _validate_text(value: object, field_name: str, max_length: int) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    if "\0" in value:
        raise ValueError(f"{field_name} must not contain null bytes")
    for ch in value:
        if ord(ch) < 32 or ord(ch) == 127:
            raise ValueError(f"{field_name} must not contain control characters")
    stripped = value.strip()
    if not stripped:
        raise ValueError(f"{field_name} must not be empty or whitespace-only")
    if len(stripped) > max_length:
        raise ValueError(f"{field_name} must not exceed {max_length} characters")
    return stripped


def _validate_code(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError("code must be a string")
    if "\0" in value:
        raise ValueError("code must not contain null bytes")
    stripped = value.strip()
    if not stripped:
        raise ValueError("code must not be empty or whitespace-only")
    if len(stripped) > _MAX_CODE_LENGTH:
        raise ValueError(f"code must not exceed {_MAX_CODE_LENGTH} characters")
    if not _CODE_PATTERN.match(stripped):
        raise ValueError(
            "code must contain only uppercase ASCII letters, digits, and "
            "underscores, and must begin with an uppercase ASCII letter"
        )
    return stripped


# ---------------------------------------------------------------------------
# NutritionSummaryItemData
# ---------------------------------------------------------------------------


class NutritionSummaryItemData(BaseModel):
    code: str
    title: str
    message: str
    tone: NutritionSummaryTone

    model_config = ConfigDict(extra="forbid", frozen=True)

    @field_validator("code", mode="before")
    @classmethod
    def validate_code(cls, v: object) -> str:
        return _validate_code(v)

    @field_validator("title", mode="before")
    @classmethod
    def validate_title(cls, v: object) -> str:
        return _validate_text(v, "title", _MAX_TITLE_LENGTH)

    @field_validator("message", mode="before")
    @classmethod
    def validate_message(cls, v: object) -> str:
        return _validate_text(v, "message", _MAX_MESSAGE_LENGTH)

    @classmethod
    def from_result(cls, item: NutritionSummaryItem) -> NutritionSummaryItemData:
        return cls(
            code=item.code,
            title=item.title,
            message=item.message,
            tone=item.tone,
        )


# ---------------------------------------------------------------------------
# NutritionSummaryData
# ---------------------------------------------------------------------------


class NutritionSummaryData(BaseModel):
    overview: str
    items: tuple[NutritionSummaryItemData, ...]

    model_config = ConfigDict(extra="forbid", frozen=True)

    @field_validator("overview", mode="before")
    @classmethod
    def validate_overview(cls, v: object) -> str:
        return _validate_text(v, "overview", _MAX_OVERVIEW_LENGTH)

    @model_validator(mode="after")
    def validate_items_contract(self) -> NutritionSummaryData:
        items = self.items
        if len(items) != EXPECTED_NUTRITION_SUMMARY_ITEM_COUNT:
            raise ValueError(
                f"items must contain exactly {EXPECTED_NUTRITION_SUMMARY_ITEM_COUNT} entries"
            )
        codes = tuple(item.code for item in items)
        if len(set(codes)) != len(codes):
            raise ValueError("item codes must be unique")
        if codes != EXPECTED_NUTRITION_SUMMARY_CODES:
            raise ValueError("item codes must match the expected ordered summary contract")
        return self

    @classmethod
    def from_result(cls, result: NutritionSummaryResult) -> NutritionSummaryData:
        return cls(
            overview=result.overview,
            items=tuple(NutritionSummaryItemData.from_result(item) for item in result.items),
        )


# ---------------------------------------------------------------------------
# NutritionSummarySuccessResponse
# ---------------------------------------------------------------------------


class NutritionSummarySuccessResponse(BaseModel):
    success: Literal[True] = True
    message: str = "Nutrition summary generated successfully."
    data: NutritionSummaryData | None = None

    model_config = ConfigDict(extra="forbid")
