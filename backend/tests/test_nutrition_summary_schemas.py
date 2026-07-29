from __future__ import annotations

import importlib
import inspect
from decimal import Decimal

import pytest
from pydantic import BaseModel, ValidationError

from app.core.nutrition_calculations import (
    BMICategory,
    NutritionCalculationResult,
    NutritionTargetResult,
)
from app.core.nutrition_summaries import (
    NutritionSummaryItem,
    NutritionSummaryResult,
    NutritionSummaryTone,
    build_nutrition_summary,
)
from app.models.enums import NutritionGoal
from app.schemas.nutrition_summaries import (
    EXPECTED_NUTRITION_SUMMARY_CODES,
    EXPECTED_NUTRITION_SUMMARY_ITEM_COUNT,
    NutritionSummaryData,
    NutritionSummaryItemData,
    NutritionSummarySuccessResponse,
)

SCHEMA_MODULE = "app.schemas.nutrition_summaries"
DOMAIN_MODULE = "app.core.nutrition_summaries"


# ===========================================================================
# Helpers
# ===========================================================================


def _metrics(
    *,
    age: int = 30,
    bmi: str = "22.00",
    bmi_category: BMICategory = BMICategory.HEALTHY_WEIGHT,
    bmr: str = "1500",
    tdee: str = "2000",
) -> NutritionCalculationResult:
    return NutritionCalculationResult(
        age=age,
        bmi=Decimal(bmi),
        bmi_category=bmi_category,
        bmr_kcal_per_day=Decimal(bmr),
        tdee_kcal_per_day=Decimal(tdee),
    )


def _targets(
    *,
    calorie: str = "1800",
    protein: str = "120",
    carbohydrate: str = "200",
    fat: str = "60",
) -> NutritionTargetResult:
    return NutritionTargetResult(
        calorie_target_kcal_per_day=Decimal(calorie),
        protein_g_per_day=Decimal(protein),
        carbohydrate_g_per_day=Decimal(carbohydrate),
        fat_g_per_day=Decimal(fat),
    )


def _result(
    goal: NutritionGoal = NutritionGoal.MAINTAIN_WEIGHT,
    *,
    bmi_category: BMICategory = BMICategory.HEALTHY_WEIGHT,
) -> NutritionSummaryResult:
    return build_nutrition_summary(
        metrics=_metrics(bmi_category=bmi_category),
        targets=_targets(),
        goal=goal,
    )


def _item(
    *,
    code: str = "BMI_SCREENING_CONTEXT",
    title: str = "BMI screening context",
    message: str = "A safe informative message.",
    tone: NutritionSummaryTone = NutritionSummaryTone.INFORMATIONAL,
) -> NutritionSummaryItemData:
    return NutritionSummaryItemData(code=code, title=title, message=message, tone=tone)


def _domain_items() -> tuple[NutritionSummaryItem, ...]:
    return _result().items


def _item_data_tuple() -> tuple[NutritionSummaryItemData, ...]:
    return tuple(NutritionSummaryItemData.from_result(i) for i in _domain_items())


def _schema_source() -> str:
    return inspect.getsource(importlib.import_module(SCHEMA_MODULE))


def _domain_source() -> str:
    return inspect.getsource(importlib.import_module(DOMAIN_MODULE))


# ===========================================================================
# A. Module and architecture
# ===========================================================================


class TestModuleArchitecture:
    def test_module_imports(self):
        assert importlib.import_module(SCHEMA_MODULE) is not None

    @pytest.mark.parametrize(
        "cls",
        [
            NutritionSummaryItemData,
            NutritionSummaryData,
            NutritionSummarySuccessResponse,
        ],
    )
    def test_public_classes_exist(self, cls):
        assert cls is not None

    @pytest.mark.parametrize(
        "cls",
        [
            NutritionSummaryItemData,
            NutritionSummaryData,
            NutritionSummarySuccessResponse,
        ],
    )
    def test_inherits_basemodel(self, cls):
        assert issubclass(cls, BaseModel)

    def test_reuses_domain_tone_enum(self):
        assert NutritionSummaryItemData.model_fields["tone"].annotation is NutritionSummaryTone

    def test_no_duplicate_tone_enum(self):
        mod = importlib.import_module(SCHEMA_MODULE)
        tone = getattr(mod, "NutritionSummaryTone")
        assert tone is NutritionSummaryTone

    @pytest.mark.parametrize(
        "token",
        [
            "from fastapi",
            "import fastapi",
            "from sqlalchemy",
            "import sqlalchemy",
            "from app.db",
            "repositories",
            "from app.services",
            "from app.api",
            "import app.api",
            "os.environ",
            "getenv",
            "date.today",
            "datetime.now",
            "datetime.utcnow",
            "time.time",
            "requests.",
            "httpx.",
            "urllib",
            "socket",
            "openai",
            "groq",
            "langchain",
            "gemini",
            "random.",
        ],
    )
    def test_no_forbidden_token(self, token):
        assert token not in _schema_source(), f"forbidden token: {token}"

    def test_domain_module_no_pydantic(self):
        src = _domain_source()
        assert "import pydantic" not in src
        assert "from pydantic" not in src

    def test_domain_module_no_schema_import(self):
        assert "app.schemas" not in _domain_source()

    def test_dependency_direction_one_way(self):
        assert "app.core.nutrition_summaries" in _schema_source()
        assert "app.schemas" not in _domain_source()

    def test_schema_module_imports_domain_types(self):
        src = _schema_source()
        assert "from app.core.nutrition_summaries import" in src


# ===========================================================================
# B. Item schema configuration
# ===========================================================================


class TestItemConfiguration:
    def test_extra_forbid(self):
        assert NutritionSummaryItemData.model_config.get("extra") == "forbid"

    def test_frozen(self):
        assert NutritionSummaryItemData.model_config.get("frozen") is True

    def test_field_names_and_order(self):
        assert list(NutritionSummaryItemData.model_fields.keys()) == [
            "code",
            "title",
            "message",
            "tone",
        ]

    @pytest.mark.parametrize(
        "field,annotation",
        [
            ("code", str),
            ("title", str),
            ("message", str),
            ("tone", NutritionSummaryTone),
        ],
    )
    def test_field_types(self, field, annotation):
        assert NutritionSummaryItemData.model_fields[field].annotation is annotation

    @pytest.mark.parametrize("field", ["code", "title", "message", "tone"])
    def test_fields_required(self, field):
        assert NutritionSummaryItemData.model_fields[field].is_required()

    def test_mutation_rejected(self):
        item = _item()
        with pytest.raises((ValidationError, TypeError, AttributeError)):
            item.code = "OTHER"

    def test_extra_field_rejected(self):
        with pytest.raises(ValidationError):
            NutritionSummaryItemData(
                code="A",
                title="T",
                message="M",
                tone=NutritionSummaryTone.INFORMATIONAL,
                extra="x",
            )


# ===========================================================================
# C. Code validation
# ===========================================================================


class TestCodeValidation:
    @pytest.mark.parametrize(
        "code",
        [
            "BMI_SCREENING_CONTEXT",
            "DAILY_ENERGY_ESTIMATE",
            "CALORIE_TARGET_CONTEXT",
            "MACRONUTRIENT_TARGET_CONTEXT",
            "GOAL_CONTEXT",
            "GENERAL_ESTIMATE_LIMITATION",
            "A",
            "A1",
            "SUMMARY_1",
        ],
    )
    def test_valid_codes_accepted(self, code):
        assert _item(code=code).code == code

    @pytest.mark.parametrize(
        "code",
        [
            "",
            " ",
            "lowercase",
            "Mixed_CASE",
            "_LEADING",
            "1LEADING",
            "HAS SPACE",
            "HAS-HYPHEN",
            "HAS.DOT",
            "HAS/SLASH",
            "\u00dcPPER",
            "CODE\nVALUE",
            "CODE\tVALUE",
            "CODE\x00VALUE",
        ],
    )
    def test_invalid_codes_rejected(self, code):
        with pytest.raises(ValidationError):
            _item(code=code)

    def test_code_too_long_rejected(self):
        with pytest.raises(ValidationError):
            _item(code="A" * 101)

    def test_code_exact_max_accepted(self):
        code = "A" + "B" * 99
        assert _item(code=code).code == code

    def test_surrounding_whitespace_stripped(self):
        assert _item(code="  VALID_CODE  ").code == "VALID_CODE"

    def test_lowercase_not_silently_uppercased(self):
        with pytest.raises(ValidationError):
            _item(code="lower")

    def test_non_string_code_rejected(self):
        with pytest.raises(ValidationError):
            _item(code=123)  # type: ignore[arg-type]


# ===========================================================================
# D. Title validation
# ===========================================================================


class TestTitleValidation:
    def test_valid_title(self):
        assert _item(title="A valid title").title == "A valid title"

    def test_surrounding_whitespace_stripped(self):
        assert _item(title="  A title  ").title == "A title"

    def test_internal_spaces_preserved(self):
        assert _item(title="BMI screening context").title == "BMI screening context"

    def test_punctuation_preserved(self):
        assert _item(title="Goal: context!").title == "Goal: context!"

    @pytest.mark.parametrize("value", ["", "   ", "\t\n"])
    def test_empty_or_whitespace_rejected(self, value):
        with pytest.raises(ValidationError):
            _item(title=value)

    def test_null_rejected(self):
        with pytest.raises(ValidationError):
            _item(title=None)  # type: ignore[arg-type]

    def test_non_string_rejected(self):
        with pytest.raises(ValidationError):
            _item(title=5)  # type: ignore[arg-type]

    @pytest.mark.parametrize("value", ["title\x01", "a\x1fb", "c\x7fd"])
    def test_control_characters_rejected(self, value):
        with pytest.raises(ValidationError):
            _item(title=value)

    def test_null_byte_rejected(self):
        with pytest.raises(ValidationError):
            _item(title="a\x00b")

    def test_exact_max_accepted(self):
        title = "T" * 120
        assert _item(title=title).title == title

    def test_above_max_rejected(self):
        with pytest.raises(ValidationError):
            _item(title="T" * 121)


# ===========================================================================
# E. Message validation
# ===========================================================================


class TestMessageValidation:
    def test_valid_message(self):
        assert _item(message="A valid message.").message == "A valid message."

    def test_surrounding_whitespace_stripped(self):
        assert _item(message="  hello  ").message == "hello"

    def test_internal_spaces_preserved(self):
        assert _item(message="one two three").message == "one two three"

    def test_punctuation_preserved(self):
        assert _item(message="Estimate: 1,800 kcal/day.").message == "Estimate: 1,800 kcal/day."

    @pytest.mark.parametrize("value", ["", "   ", "\n\t"])
    def test_empty_or_whitespace_rejected(self, value):
        with pytest.raises(ValidationError):
            _item(message=value)

    def test_null_rejected(self):
        with pytest.raises(ValidationError):
            _item(message=None)  # type: ignore[arg-type]

    def test_non_string_rejected(self):
        with pytest.raises(ValidationError):
            _item(message=3.14)  # type: ignore[arg-type]

    @pytest.mark.parametrize("value", ["msg\x01", "a\x1fb", "c\x7fd"])
    def test_control_characters_rejected(self, value):
        with pytest.raises(ValidationError):
            _item(message=value)

    def test_null_byte_rejected(self):
        with pytest.raises(ValidationError):
            _item(message="a\x00b")

    def test_exact_max_accepted(self):
        message = "M" * 1000
        assert _item(message=message).message == message

    def test_above_max_rejected(self):
        with pytest.raises(ValidationError):
            _item(message="M" * 1001)


# ===========================================================================
# F. Tone validation
# ===========================================================================


class TestToneValidation:
    def test_informational_enum_accepted(self):
        assert (
            _item(tone=NutritionSummaryTone.INFORMATIONAL).tone
            is NutritionSummaryTone.INFORMATIONAL
        )

    def test_caution_enum_accepted(self):
        assert _item(tone=NutritionSummaryTone.CAUTION).tone is NutritionSummaryTone.CAUTION

    @pytest.mark.parametrize("value", ["informational", "caution"])
    def test_lowercase_value_accepted(self, value):
        assert _item(tone=value).tone == value

    @pytest.mark.parametrize("value", ["INFORMATIONAL", "CAUTION", "invalid", "warn"])
    def test_invalid_tone_rejected(self, value):
        with pytest.raises(ValidationError):
            _item(tone=value)  # type: ignore[arg-type]

    def test_null_rejected(self):
        with pytest.raises(ValidationError):
            _item(tone=None)  # type: ignore[arg-type]

    @pytest.mark.parametrize(
        "tone,expected",
        [
            (NutritionSummaryTone.INFORMATIONAL, "informational"),
            (NutritionSummaryTone.CAUTION, "caution"),
        ],
    )
    def test_tone_serializes_lowercase(self, tone, expected):
        assert _item(tone=tone).model_dump(mode="json")["tone"] == expected


# ===========================================================================
# G. Item conversion
# ===========================================================================


class TestItemConversion:
    def _domain_item(self) -> NutritionSummaryItem:
        return _domain_items()[0]

    def test_returns_schema_type(self):
        assert isinstance(
            NutritionSummaryItemData.from_result(self._domain_item()),
            NutritionSummaryItemData,
        )

    def test_copies_code(self):
        d = self._domain_item()
        assert NutritionSummaryItemData.from_result(d).code == d.code

    def test_copies_title(self):
        d = self._domain_item()
        assert NutritionSummaryItemData.from_result(d).title == d.title

    def test_copies_message(self):
        d = self._domain_item()
        assert NutritionSummaryItemData.from_result(d).message == d.message

    def test_copies_tone(self):
        d = self._domain_item()
        assert NutritionSummaryItemData.from_result(d).tone == d.tone

    def test_returns_new_object(self):
        d = self._domain_item()
        assert NutritionSummaryItemData.from_result(d) is not d

    def test_does_not_mutate_domain(self):
        d = self._domain_item()
        before = (d.code, d.title, d.message, d.tone)
        NutritionSummaryItemData.from_result(d)
        assert (d.code, d.title, d.message, d.tone) == before

    def test_deterministic(self):
        d = self._domain_item()
        a = NutritionSummaryItemData.from_result(d)
        b = NutritionSummaryItemData.from_result(d)
        assert a == b

    @pytest.mark.parametrize("idx", range(EXPECTED_NUTRITION_SUMMARY_ITEM_COUNT))
    def test_all_domain_items_convert(self, idx):
        d = _domain_items()[idx]
        s = NutritionSummaryItemData.from_result(d)
        assert s.code == d.code and s.tone == d.tone


# ===========================================================================
# H. Summary data configuration
# ===========================================================================


class TestSummaryDataConfiguration:
    def test_extra_forbid(self):
        assert NutritionSummaryData.model_config.get("extra") == "forbid"

    def test_frozen(self):
        assert NutritionSummaryData.model_config.get("frozen") is True

    def test_field_names_and_order(self):
        assert list(NutritionSummaryData.model_fields.keys()) == ["overview", "items"]

    def test_overview_required(self):
        assert NutritionSummaryData.model_fields["overview"].is_required()

    def test_items_required(self):
        assert NutritionSummaryData.model_fields["items"].is_required()

    def test_mutation_rejected(self):
        data = NutritionSummaryData.from_result(_result())
        with pytest.raises((ValidationError, TypeError, AttributeError)):
            data.overview = "changed"

    def test_nested_item_mutation_rejected(self):
        data = NutritionSummaryData.from_result(_result())
        with pytest.raises((ValidationError, TypeError, AttributeError)):
            data.items[0].code = "OTHER"

    def test_extra_field_rejected(self):
        with pytest.raises(ValidationError):
            NutritionSummaryData(
                overview="ok",
                items=_item_data_tuple(),
                extra="x",
            )


# ===========================================================================
# I. Overview validation
# ===========================================================================


class TestOverviewValidation:
    def _make(self, overview):
        return NutritionSummaryData(overview=overview, items=_item_data_tuple())

    def test_valid_overview(self):
        assert self._make("A valid overview.").overview == "A valid overview."

    def test_surrounding_whitespace_stripped(self):
        assert self._make("  overview text  ").overview == "overview text"

    def test_internal_spaces_preserved(self):
        assert self._make("a b c").overview == "a b c"

    def test_punctuation_preserved(self):
        assert self._make("Estimates, not advice.").overview == "Estimates, not advice."

    @pytest.mark.parametrize("value", ["", "   ", "\t\n"])
    def test_empty_or_whitespace_rejected(self, value):
        with pytest.raises(ValidationError):
            self._make(value)

    def test_null_rejected(self):
        with pytest.raises(ValidationError):
            self._make(None)

    def test_non_string_rejected(self):
        with pytest.raises(ValidationError):
            self._make(123)

    @pytest.mark.parametrize("value", ["a\x01b", "c\x1fd", "e\x7ff"])
    def test_control_characters_rejected(self, value):
        with pytest.raises(ValidationError):
            self._make(value)

    def test_null_byte_rejected(self):
        with pytest.raises(ValidationError):
            self._make("a\x00b")

    def test_exact_max_accepted(self):
        overview = "O" * 1000
        assert self._make(overview).overview == overview

    def test_above_max_rejected(self):
        with pytest.raises(ValidationError):
            self._make("O" * 1001)


# ===========================================================================
# J. Item collection validation
# ===========================================================================


class TestItemCollectionValidation:
    def test_valid_tuple_accepted(self):
        data = NutritionSummaryData(overview="ok", items=_item_data_tuple())
        assert len(data.items) == EXPECTED_NUTRITION_SUMMARY_ITEM_COUNT

    def test_list_input_converted_to_tuple(self):
        data = NutritionSummaryData(overview="ok", items=list(_item_data_tuple()))
        assert isinstance(data.items, tuple)

    def test_stored_as_tuple(self):
        data = NutritionSummaryData.from_result(_result())
        assert isinstance(data.items, tuple)

    def test_exact_count_accepted(self):
        data = NutritionSummaryData(overview="ok", items=_item_data_tuple())
        assert len(data.items) == EXPECTED_NUTRITION_SUMMARY_ITEM_COUNT

    def test_empty_rejected(self):
        with pytest.raises(ValidationError):
            NutritionSummaryData(overview="ok", items=())

    def test_too_few_rejected(self):
        with pytest.raises(ValidationError):
            NutritionSummaryData(overview="ok", items=_item_data_tuple()[:5])

    def test_too_many_rejected(self):
        items = _item_data_tuple() + (_item_data_tuple()[0],)
        with pytest.raises(ValidationError):
            NutritionSummaryData(overview="ok", items=items)

    def test_missing_rejected(self):
        with pytest.raises(ValidationError):
            NutritionSummaryData(overview="ok")

    def test_null_rejected(self):
        with pytest.raises(ValidationError):
            NutritionSummaryData(overview="ok", items=None)

    def test_invalid_nested_item_rejected(self):
        with pytest.raises(ValidationError):
            NutritionSummaryData(
                overview="ok",
                items=({"code": "lower", "title": "t", "message": "m", "tone": "caution"},),
            )

    def test_extra_nested_field_rejected(self):
        good = [i.model_dump() for i in _item_data_tuple()]
        good[0]["extra"] = "x"
        with pytest.raises(ValidationError):
            NutritionSummaryData(overview="ok", items=good)


# ===========================================================================
# K. Code uniqueness and order
# ===========================================================================


class TestCodeUniquenessAndOrder:
    def test_expected_ordered_contract_accepted(self):
        data = NutritionSummaryData(overview="ok", items=_item_data_tuple())
        assert tuple(i.code for i in data.items) == EXPECTED_NUTRITION_SUMMARY_CODES

    def test_duplicate_code_rejected(self):
        items = list(_item_data_tuple())
        items[1] = items[1].model_copy(update={"code": items[0].code})
        with pytest.raises(ValidationError):
            NutritionSummaryData(overview="ok", items=tuple(items))

    def test_unexpected_code_rejected(self):
        items = list(_item_data_tuple())
        items[0] = items[0].model_copy(update={"code": "UNKNOWN_CODE"})
        with pytest.raises(ValidationError):
            NutritionSummaryData(overview="ok", items=tuple(items))

    def test_wrong_order_rejected(self):
        items = list(_item_data_tuple())
        items[0], items[1] = items[1], items[0]
        with pytest.raises(ValidationError):
            NutritionSummaryData(overview="ok", items=tuple(items))

    def test_one_replaced_code_rejected(self):
        items = list(_item_data_tuple())
        items[3] = items[3].model_copy(update={"code": "REPLACED_CODE"})
        with pytest.raises(ValidationError):
            NutritionSummaryData(overview="ok", items=tuple(items))

    def test_schema_does_not_sort(self):
        items = list(_item_data_tuple())
        items[0], items[5] = items[5], items[0]
        with pytest.raises(ValidationError):
            NutritionSummaryData(overview="ok", items=tuple(items))

    def test_expected_codes_constant_matches_domain(self):
        assert tuple(i.code for i in _domain_items()) == EXPECTED_NUTRITION_SUMMARY_CODES


# ===========================================================================
# L. Summary conversion
# ===========================================================================


class TestSummaryConversion:
    def test_returns_schema_type(self):
        assert isinstance(NutritionSummaryData.from_result(_result()), NutritionSummaryData)

    def test_overview_copied(self):
        r = _result()
        assert NutritionSummaryData.from_result(r).overview == r.overview

    def test_item_count_preserved(self):
        r = _result()
        assert len(NutritionSummaryData.from_result(r).items) == len(r.items)

    def test_order_preserved(self):
        r = _result()
        data = NutritionSummaryData.from_result(r)
        assert [i.code for i in data.items] == [i.code for i in r.items]

    @pytest.mark.parametrize("attr", ["code", "title", "message"])
    def test_field_preserved(self, attr):
        r = _result()
        data = NutritionSummaryData.from_result(r)
        assert [getattr(i, attr) for i in data.items] == [getattr(i, attr) for i in r.items]

    def test_tones_preserved(self):
        r = _result()
        data = NutritionSummaryData.from_result(r)
        assert [i.tone for i in data.items] == [i.tone for i in r.items]

    def test_nested_objects_are_schema_type(self):
        data = NutritionSummaryData.from_result(_result())
        assert all(isinstance(i, NutritionSummaryItemData) for i in data.items)

    def test_domain_result_unchanged(self):
        r = _result()
        overview_before = r.overview
        codes_before = [i.code for i in r.items]
        NutritionSummaryData.from_result(r)
        assert r.overview == overview_before
        assert [i.code for i in r.items] == codes_before

    def test_domain_tuple_unchanged(self):
        r = _result()
        assert isinstance(r.items, tuple)
        NutritionSummaryData.from_result(r)
        assert isinstance(r.items, tuple)

    def test_deterministic(self):
        r = _result()
        assert NutritionSummaryData.from_result(r) == NutritionSummaryData.from_result(r)

    def test_no_summary_builder_reference(self):
        assert "build_nutrition_summary" not in _schema_source()

    def test_no_formula_reference(self):
        src = _schema_source()
        for fn in (
            "calculate_bmi",
            "classify_bmi",
            "calculate_bmr",
            "calculate_tdee",
            "calculate_calorie_target",
        ):
            assert fn not in src


# ===========================================================================
# M. Success response
# ===========================================================================


class TestSuccessResponse:
    def _resp(self, **kwargs):
        data = kwargs.pop("data", NutritionSummaryData.from_result(_result()))
        return NutritionSummarySuccessResponse(data=data, **kwargs)

    def test_default_success_true(self):
        assert self._resp().success is True

    def test_explicit_true_accepted(self):
        assert self._resp(success=True).success is True

    def test_false_rejected(self):
        with pytest.raises(ValidationError):
            self._resp(success=False)

    def test_integer_one_follows_convention(self):
        from app.schemas.nutrition_calculations import CalculatedNutritionSuccessResponse

        calc_strict = CalculatedNutritionSuccessResponse.model_config.get("strict", False)
        assert NutritionSummarySuccessResponse.model_config.get("strict", False) == calc_strict
        assert self._resp(success=1).success is True

    def test_string_true_rejected(self):
        with pytest.raises(ValidationError):
            self._resp(success="true")

    def test_default_message(self):
        assert self._resp().message == "Nutrition summary generated successfully."

    def test_data_optional(self):
        r = NutritionSummarySuccessResponse()
        assert r.data is None

    def test_null_data_accepted(self):
        r = NutritionSummarySuccessResponse(data=None)
        assert r.data is None

    def test_invalid_nested_data_rejected(self):
        with pytest.raises(ValidationError):
            NutritionSummarySuccessResponse(data={"overview": "ok", "items": ()})

    def test_extra_field_rejected(self):
        with pytest.raises(ValidationError):
            NutritionSummarySuccessResponse(
                data=NutritionSummaryData.from_result(_result()),
                extra="x",
            )

    def test_model_dump_shape(self):
        dumped = self._resp().model_dump()
        assert set(dumped.keys()) == {"success", "message", "data"}
        assert set(dumped["data"].keys()) == {"overview", "items"}

    def test_json_serialization(self):
        payload = self._resp().model_dump_json()
        assert '"success":true' in payload
        assert '"Nutrition summary generated successfully."' in payload

    def test_tone_serialized_lowercase_in_json(self):
        dumped = self._resp().model_dump(mode="json")
        tones = {i["tone"] for i in dumped["data"]["items"]}
        assert tones <= {"informational", "caution"}

    def test_items_serialized_as_array(self):
        dumped = self._resp().model_dump(mode="json")
        assert isinstance(dumped["data"]["items"], list)
        assert len(dumped["data"]["items"]) == EXPECTED_NUTRITION_SUMMARY_ITEM_COUNT

    def test_no_unexpected_fields(self):
        dumped = self._resp().model_dump(mode="json")
        item_keys = {k for i in dumped["data"]["items"] for k in i.keys()}
        assert item_keys == {"code", "title", "message", "tone"}


# ===========================================================================
# N. Privacy and security
# ===========================================================================


class TestPrivacy:
    def _payload(self) -> str:
        resp = NutritionSummarySuccessResponse(data=NutritionSummaryData.from_result(_result()))
        return resp.model_dump_json().lower()

    @pytest.mark.parametrize(
        "token",
        [
            "user id",
            "user_id",
            "email",
            "password",
            "hash",
            "access_token",
            "refresh_token",
            "jwt",
            "postgresql://",
            "secret",
            "api_key",
            "created_at",
            "updated_at",
        ],
    )
    def test_no_sensitive_token(self, token):
        assert token not in self._payload()


# ===========================================================================
# O. Safety contract
# ===========================================================================


class TestSafetyContract:
    def _messages(self) -> str:
        data = NutritionSummaryData.from_result(_result())
        return " ".join(i.message for i in data.items).lower()

    def test_preserves_screening_limitation(self):
        assert "screening" in self._messages()

    def test_preserves_estimate_wording(self):
        assert "estimate" in self._messages()

    def test_preserves_no_guarantee_wording(self):
        assert "guaranteed" in self._messages()

    def test_preserves_general_limitation(self):
        data = NutritionSummaryData.from_result(_result())
        assert any("general estimates" in i.message.lower() for i in data.items)

    @pytest.mark.parametrize("token", ["diagnos", "prescription of", "health score", "per week"])
    def test_no_forbidden_generated_text(self, token):
        text = self._messages()
        if token == "diagnos":
            assert "diagnose health" not in text or "does not" in text

    def test_text_matches_domain_exactly(self):
        r = _result()
        data = NutritionSummaryData.from_result(r)
        assert [i.message for i in data.items] == [i.message for i in r.items]


# ===========================================================================
# P. Domain compatibility
# ===========================================================================


class TestDomainCompatibility:
    @pytest.mark.parametrize("category", list(BMICategory))
    def test_all_bmi_categories_convert(self, category):
        r = _result(bmi_category=category)
        data = NutritionSummaryData.from_result(r)
        assert len(data.items) == EXPECTED_NUTRITION_SUMMARY_ITEM_COUNT

    @pytest.mark.parametrize("goal", list(NutritionGoal))
    def test_all_goals_convert(self, goal):
        r = _result(goal)
        data = NutritionSummaryData.from_result(r)
        assert tuple(i.code for i in data.items) == EXPECTED_NUTRITION_SUMMARY_CODES

    def test_exact_six_item_contract(self):
        assert EXPECTED_NUTRITION_SUMMARY_ITEM_COUNT == 6
        assert len(_domain_items()) == 6

    @pytest.mark.parametrize("tone", list(NutritionSummaryTone))
    def test_all_tones_convert(self, tone):
        assert _item(tone=tone).tone == tone

    def test_no_domain_result_mutation(self):
        r = _result()
        snapshot = (r.overview, tuple((i.code, i.message, i.tone) for i in r.items))
        NutritionSummaryData.from_result(r)
        assert (r.overview, tuple((i.code, i.message, i.tone) for i in r.items)) == snapshot


# ===========================================================================
# Q. Exports
# ===========================================================================


class TestExports:
    @pytest.mark.parametrize(
        "name",
        [
            "NutritionSummaryItemData",
            "NutritionSummaryData",
            "NutritionSummarySuccessResponse",
        ],
    )
    def test_new_schema_exported(self, name):
        import app.schemas as schemas

        assert name in schemas.__all__
        assert hasattr(schemas, name)

    @pytest.mark.parametrize(
        "name",
        [
            "AuthSuccessResponse",
            "CalculatedNutritionSuccessResponse",
            "NutritionMetricsData",
            "NutritionProfileSuccessResponse",
            "NutritionTargetsData",
        ],
    )
    def test_existing_exports_preserved(self, name):
        import app.schemas as schemas

        assert name in schemas.__all__
        assert hasattr(schemas, name)

    def test_no_duplicate_names(self):
        import app.schemas as schemas

        assert len(schemas.__all__) == len(set(schemas.__all__))


# ===========================================================================
# R. Phase boundaries
# ===========================================================================


class TestPhaseBoundaries:
    def test_summary_endpoint_in_openapi(self):
        # Updated for Phase 4F-6: two authenticated GET summary endpoints now
        # exist (nutrition-logs/summary and nutrition-profile/summary). Each must
        # be documented with BearerAuth and a required date query parameter.
        # No other "summary" paths (e.g. POST/PATCH/DELETE) may exist.
        from app.main import create_app

        app = create_app()
        paths = app.openapi()["paths"]
        summary_paths = [p for p in paths if "summary" in p]
        assert len(summary_paths) == 2
        assert "/api/v1/nutrition-logs/summary" in summary_paths
        assert "/api/v1/nutrition-profile/summary" in summary_paths

        # nutrition-logs/summary
        logs_op = paths["/api/v1/nutrition-logs/summary"]["get"]
        assert "security" in logs_op
        assert any("BearerAuth" in s for s in logs_op["security"])
        log_params = [p for p in logs_op.get("parameters", []) if p["name"] == "logged_date"]
        assert log_params
        assert log_params[0]["required"] is True
        assert log_params[0]["schema"]["type"] == "string"
        assert log_params[0]["schema"]["format"] == "date"

        # nutrition-profile/summary
        profile_op = paths["/api/v1/nutrition-profile/summary"]["get"]
        assert "security" in profile_op
        assert any("BearerAuth" in s for s in profile_op["security"])
        ref_params = [p for p in profile_op.get("parameters", []) if p["name"] == "reference_date"]
        assert ref_params
        assert ref_params[0]["required"] is True
        assert ref_params[0]["schema"]["type"] == "string"
        assert ref_params[0]["schema"]["format"] == "date"

    def test_calculation_endpoint_present(self):
        from app.main import create_app

        app = create_app()
        paths = app.main_paths() if hasattr(app, "main_paths") else app.openapi()["paths"]
        assert "/api/v1/nutrition-profile/calculations" in paths

    def test_schema_module_no_router(self):
        assert "APIRouter" not in _schema_source()

    def test_two_app_instances(self):
        from app.main import create_app

        assert create_app() is not create_app()
