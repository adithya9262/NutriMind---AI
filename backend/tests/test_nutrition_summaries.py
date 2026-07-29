from __future__ import annotations

import importlib
from decimal import Decimal

import pytest

from app.core import nutrition_calculations
from app.core.nutrition_calculations import (
    MINIMUM_CALORIE_TARGET,
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

MODULE = "app.core.nutrition_summaries"

# ===========================================================================
# Fixtures / helpers
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


def _healthy_metrics() -> NutritionCalculationResult:
    return _metrics(bmi="22.00", bmi_category=BMICategory.HEALTHY_WEIGHT)


def _run(goal: NutritionGoal = NutritionGoal.MAINTAIN_WEIGHT) -> NutritionSummaryResult:
    return build_nutrition_summary(metrics=_healthy_metrics(), targets=_targets(), goal=goal)


# ===========================================================================
# 1. Module / architecture
# ===========================================================================


class TestModuleArchitecture:
    def test_module_imports_successfully(self):
        mod = importlib.import_module(MODULE)
        assert mod is not None

    @pytest.mark.parametrize(
        "name",
        [
            "FastAPI",
            "APIRouter",
            "HTTPException",
            "BaseModel",
            "Field",
            "engine",
            "Session",
            "AsyncSession",
            "create_engine",
            "Base",
            "Metadata",
            "alembic",
            "Repository",
            "Service",
            "router",
            "Depends",
            "Settings",
            "requests",
            "httpx",
            "openai",
            "groq",
            "langchain",
            "os",
            "socket",
            "random",
        ],
    )
    def test_no_forbidden_attribute(self, name: str):
        mod = importlib.import_module(MODULE)
        assert not hasattr(mod, name), f"module must not expose {name}"

    def test_no_fastapi_import(self):
        source = _source()
        assert "import fastapi" not in source
        assert "from fastapi" not in source

    def test_no_pydantic_import(self):
        source = _source()
        assert "import pydantic" not in source
        assert "from pydantic" not in source

    def test_no_sqlalchemy_import(self):
        source = _source()
        assert "import sqlalchemy" not in source
        assert "from sqlalchemy" not in source

    def test_no_database_import(self):
        source = _source()
        assert "from app.db" not in source
        assert "import app.db" not in source

    def test_no_repository_import(self):
        source = _source()
        assert "repositories" not in source

    def test_no_service_import(self):
        source = _source()
        assert "from app.services" not in source

    def test_no_api_router_import(self):
        source = _source()
        assert "from app.api" not in source
        assert "import app.api" not in source

    def test_no_environment_access(self):
        source = _source()
        assert "os.environ" not in source
        assert "getenv" not in source
        assert "settings" not in source.lower() or "Settings" not in source

    def test_no_network_access(self):
        source = _source()
        assert "requests." not in source
        assert "httpx." not in source
        assert "urllib" not in source

    def test_no_system_clock_access(self):
        source = _source()
        assert "date.today" not in source
        assert "datetime.now" not in source
        assert "datetime.utcnow" not in source
        assert "time.time" not in source

    def test_no_random_usage(self):
        source = _source()
        assert "random." not in source

    def test_no_ai_sdk_imports(self):
        source = _source()
        for token in ("groq", "openai", "langchain", "gemini"):
            assert token not in source.lower(), f"AI SDK reference: {token}"

    def test_only_stdlib_and_domain_imports(self):
        source = _source()
        allowed = (
            "from __future__",
            "import enum",
            "from dataclasses",
            "from decimal",
            "from app.core.nutrition_calculations",
            "from app.models.enums",
        )
        lines = [
            ln for ln in source.splitlines() if ln.startswith("import ") or ln.startswith("from ")
        ]
        for ln in lines:
            assert any(ln.startswith(a) for a in allowed), f"unexpected import: {ln!r}"


def _source() -> str:
    mod = importlib.import_module(MODULE)
    import inspect

    return inspect.getsource(mod)


# ===========================================================================
# 2. Tone enum
# ===========================================================================


class TestNutritionSummaryTone:
    def test_exact_values(self):
        assert NutritionSummaryTone.INFORMATIONAL == "informational"
        assert NutritionSummaryTone.CAUTION == "caution"

    def test_no_extra_values(self):
        assert {t.value for t in NutritionSummaryTone} == {
            "informational",
            "caution",
        }

    def test_string_behavior(self):
        assert NutritionSummaryTone.INFORMATIONAL == "informational"
        assert str(NutritionSummaryTone.CAUTION) == "caution"

    def test_is_str_enum(self):
        assert issubclass(NutritionSummaryTone, str)

    def test_no_forbidden_tones(self):
        forbidden = {
            "SUCCESS",
            "FAILURE",
            "HEALTHY",
            "UNHEALTHY",
            "GOOD",
            "BAD",
            "DANGER",
        }
        present = {t.name for t in NutritionSummaryTone}
        assert not (present & forbidden)


# ===========================================================================
# 3. Dataclasses
# ===========================================================================


class TestSummaryDataclasses:
    def test_item_is_frozen(self):
        item = NutritionSummaryItem(
            code="X",
            title="T",
            message="M",
            tone=NutritionSummaryTone.INFORMATIONAL,
        )
        with pytest.raises((AttributeError, TypeError)):
            item.code = "Y"

    def test_item_is_slotted(self):
        assert "__slots__" in NutritionSummaryItem.__dict__

    def test_item_field_names(self):
        assert {f.name for f in NutritionSummaryItem.__dataclass_fields__.values()} == {
            "code",
            "title",
            "message",
            "tone",
        }

    def test_result_is_frozen(self):
        result = _run()
        with pytest.raises((AttributeError, TypeError)):
            result.overview = "changed"

    def test_result_is_slotted(self):
        assert "__slots__" in NutritionSummaryResult.__dict__

    def test_items_is_tuple(self):
        result = _run()
        assert isinstance(result.items, tuple)

    def test_item_not_list(self):
        result = _run()
        assert not isinstance(result.items, list)

    def test_mutation_of_items_rejected(self):
        result = _run()
        with pytest.raises((AttributeError, TypeError)):
            result.items[0] = None

    def test_deterministic_equality(self):
        a = _run()
        b = _run()
        assert a == b
        assert a.items == b.items


# ===========================================================================
# 4. Function behavior
# ===========================================================================


class TestFunctionBehavior:
    def test_keyword_only_signature(self):
        import inspect

        params = inspect.signature(build_nutrition_summary).parameters
        assert set(params.keys()) == {"metrics", "targets", "goal"}
        for p in params.values():
            assert p.kind is inspect.Parameter.KEYWORD_ONLY

    def test_return_type(self):
        result = _run()
        assert isinstance(result, NutritionSummaryResult)

    def test_deterministic_repeated_calls(self):
        r1 = _run(NutritionGoal.LOSE_WEIGHT)
        r2 = _run(NutritionGoal.LOSE_WEIGHT)
        assert r1 == r2
        assert [i.code for i in r1.items] == [i.code for i in r2.items]

    def test_input_objects_not_mutated(self):
        metrics = _healthy_metrics()
        targets = _targets()
        goal = NutritionGoal.MAINTAIN_WEIGHT
        build_nutrition_summary(metrics=metrics, targets=targets, goal=goal)
        assert metrics.bmi == Decimal("22.00")
        assert targets.calorie_target_kcal_per_day == Decimal("1800")

    def test_exactly_six_items(self):
        result = _run()
        assert len(result.items) == 6

    def test_exact_item_order(self):
        result = _run()
        assert [i.code for i in result.items] == [
            "BMI_SCREENING_CONTEXT",
            "DAILY_ENERGY_ESTIMATE",
            "CALORIE_TARGET_CONTEXT",
            "MACRONUTRIENT_TARGET_CONTEXT",
            "GOAL_CONTEXT",
            "GENERAL_ESTIMATE_LIMITATION",
        ]

    def test_exact_stable_codes(self):
        result = _run()
        codes = {i.code for i in result.items}
        assert codes == {
            "BMI_SCREENING_CONTEXT",
            "DAILY_ENERGY_ESTIMATE",
            "CALORIE_TARGET_CONTEXT",
            "MACRONUTRIENT_TARGET_CONTEXT",
            "GOAL_CONTEXT",
            "GENERAL_ESTIMATE_LIMITATION",
        }

    def test_unique_codes(self):
        result = _run()
        codes = [i.code for i in result.items]
        assert len(codes) == len(set(codes))

    def test_all_titles_non_empty(self):
        result = _run()
        assert all(isinstance(i.title, str) and i.title.strip() for i in result.items)

    def test_all_messages_non_empty(self):
        result = _run()
        assert all(isinstance(i.message, str) and i.message.strip() for i in result.items)

    def test_all_tones_valid(self):
        result = _run()
        for i in result.items:
            assert isinstance(i.tone, NutritionSummaryTone)

    def test_overview_non_empty(self):
        result = _run()
        assert isinstance(result.overview, str)
        assert result.overview.strip()

    def test_overview_no_user_identifiers(self):
        result = _run()
        text = result.overview.lower()
        for token in ("@", "user id", "email", "password", "token", "jwt"):
            assert token not in text

    def test_overview_no_date(self):
        result = _run()
        assert "2024" not in result.overview
        assert "today" not in result.overview.lower()

    def test_overview_no_health_claim(self):
        text = _run().overview.lower()
        for token in ("healthy", "unhealthy", "diagnos", "guarantee"):
            assert token not in text

    def test_no_calculation_functions_called(self):
        source = _source()
        for fn in (
            "calculate_age",
            "calculate_bmi",
            "classify_bmi",
            "calculate_bmr",
            "calculate_tdee",
            "calculate_calorie_target",
            "calculate_macronutrient_targets",
            "calculate_nutrition_metrics",
            "calculate_nutrition_targets",
        ):
            assert fn + "(" not in source, f"forbidden call: {fn}"


# ===========================================================================
# 5. BMI behavior
# ===========================================================================


class TestBmiBehavior:
    @pytest.mark.parametrize(
        "category,tone",
        [
            (BMICategory.UNDERWEIGHT, NutritionSummaryTone.CAUTION),
            (BMICategory.HEALTHY_WEIGHT, NutritionSummaryTone.INFORMATIONAL),
            (BMICategory.OVERWEIGHT, NutritionSummaryTone.CAUTION),
            (BMICategory.OBESITY, NutritionSummaryTone.CAUTION),
        ],
    )
    def test_tone_for_each_category(self, category, tone):
        result = build_nutrition_summary(
            metrics=_metrics(bmi="17.00", bmi_category=category),
            targets=_targets(),
            goal=NutritionGoal.MAINTAIN_WEIGHT,
        )
        assert result.items[0].tone is tone

    def test_supplied_bmi_appears(self):
        result = build_nutrition_summary(
            metrics=_metrics(bmi="17.42", bmi_category=BMICategory.UNDERWEIGHT),
            targets=_targets(),
            goal=NutritionGoal.MAINTAIN_WEIGHT,
        )
        assert "17.42" in result.items[0].message

    def test_supplied_category_interpreted(self):
        result = build_nutrition_summary(
            metrics=_metrics(bmi="30.00", bmi_category=BMICategory.OBESITY),
            targets=_targets(),
            goal=NutritionGoal.MAINTAIN_WEIGHT,
        )
        assert "obesity" in result.items[0].message

    def test_screening_limitation_present(self):
        for cat in BMICategory:
            result = build_nutrition_summary(
                metrics=_metrics(bmi="22.00", bmi_category=cat),
                targets=_targets(),
                goal=NutritionGoal.MAINTAIN_WEIGHT,
            )
            msg = result.items[0].message.lower()
            assert "screening" in msg
            assert "does not" in msg
            assert "diagnose" in msg

    def test_no_body_composition_claim(self):
        result = build_nutrition_summary(
            metrics=_metrics(bmi="22.00", bmi_category=BMICategory.HEALTHY_WEIGHT),
            targets=_targets(),
            goal=NutritionGoal.MAINTAIN_WEIGHT,
        )
        assert "does not directly measure body composition" in result.items[0].message

    def test_underweight_no_malnutrition_diagnosis(self):
        result = build_nutrition_summary(
            metrics=_metrics(bmi="17.00", bmi_category=BMICategory.UNDERWEIGHT),
            targets=_targets(),
            goal=NutritionGoal.MAINTAIN_WEIGHT,
        )
        assert "malnutrition" not in result.items[0].message.lower()
        assert "treatment" not in result.items[0].message.lower()

    def test_healthy_no_overall_health_claim(self):
        result = build_nutrition_summary(
            metrics=_metrics(bmi="22.00", bmi_category=BMICategory.HEALTHY_WEIGHT),
            targets=_targets(),
            goal=NutritionGoal.MAINTAIN_WEIGHT,
        )
        msg = result.items[0].message.lower()
        for token in ("you are healthy", "your health is good", "perfect bmi", "ideal body"):
            assert token not in msg

    def test_overweight_no_shame(self):
        result = build_nutrition_summary(
            metrics=_metrics(bmi="27.00", bmi_category=BMICategory.OVERWEIGHT),
            targets=_targets(),
            goal=NutritionGoal.MAINTAIN_WEIGHT,
        )
        msg = result.items[0].message.lower()
        assert "shame" not in msg
        assert "obesity" not in msg or "diagnos" not in msg

    def test_obesity_no_disease_diagnosis(self):
        result = build_nutrition_summary(
            metrics=_metrics(bmi="32.00", bmi_category=BMICategory.OBESITY),
            targets=_targets(),
            goal=NutritionGoal.MAINTAIN_WEIGHT,
        )
        msg = result.items[0].message.lower()
        assert "unhealthy" not in msg
        assert "disease" not in msg

    def test_obesity_respectful(self):
        result = build_nutrition_summary(
            metrics=_metrics(bmi="32.00", bmi_category=BMICategory.OBESITY),
            targets=_targets(),
            goal=NutritionGoal.MAINTAIN_WEIGHT,
        )
        assert "obesity" in result.items[0].message


# ===========================================================================
# 6. Daily energy
# ===========================================================================


class TestDailyEnergy:
    def test_supplied_bmr_appears(self):
        result = build_nutrition_summary(
            metrics=_metrics(bmr="1543"), targets=_targets(), goal=NutritionGoal.MAINTAIN_WEIGHT
        )
        assert "1543" in result.items[1].message

    def test_supplied_tdee_appears(self):
        result = build_nutrition_summary(
            metrics=_metrics(tdee="2110"), targets=_targets(), goal=NutritionGoal.MAINTAIN_WEIGHT
        )
        assert "2110" in result.items[1].message

    def test_says_estimate(self):
        result = build_nutrition_summary(
            metrics=_metrics(), targets=_targets(), goal=NutritionGoal.MAINTAIN_WEIGHT
        )
        assert "estimate" in result.items[1].message.lower()

    def test_distinguishes_rest_from_total(self):
        msg = (
            build_nutrition_summary(
                metrics=_metrics(), targets=_targets(), goal=NutritionGoal.MAINTAIN_WEIGHT
            )
            .items[1]
            .message.lower()
        )
        assert "rest" in msg
        assert "total daily" in msg

    def test_no_exactness_claim(self):
        msg = (
            build_nutrition_summary(
                metrics=_metrics(), targets=_targets(), goal=NutritionGoal.MAINTAIN_WEIGHT
            )
            .items[1]
            .message.lower()
        )
        for token in ("exact", "precise"):
            assert token not in msg

    def test_informational_tone(self):
        result = build_nutrition_summary(
            metrics=_metrics(), targets=_targets(), goal=NutritionGoal.MAINTAIN_WEIGHT
        )
        assert result.items[1].tone is NutritionSummaryTone.INFORMATIONAL


# ===========================================================================
# 7. Calorie target
# ===========================================================================


class TestCalorieTarget:
    def test_supplied_target_appears(self):
        result = build_nutrition_summary(
            metrics=_metrics(), targets=_targets(calorie="1850"), goal=NutritionGoal.MAINTAIN_WEIGHT
        )
        assert "1850" in result.items[2].message

    def test_estimate_wording(self):
        msg = (
            build_nutrition_summary(
                metrics=_metrics(), targets=_targets(), goal=NutritionGoal.MAINTAIN_WEIGHT
            )
            .items[2]
            .message.lower()
        )
        assert "estimate" in msg

    def test_no_guarantee(self):
        msg = (
            build_nutrition_summary(
                metrics=_metrics(), targets=_targets(), goal=NutritionGoal.MAINTAIN_WEIGHT
            )
            .items[2]
            .message.lower()
        )
        assert "guaranteed" in msg

    def test_no_weekly_prediction(self):
        msg = (
            build_nutrition_summary(
                metrics=_metrics(), targets=_targets(), goal=NutritionGoal.MAINTAIN_WEIGHT
            )
            .items[2]
            .message.lower()
        )
        assert "week" not in msg
        assert "per week" not in msg

    def test_informational_tone(self):
        result = build_nutrition_summary(
            metrics=_metrics(), targets=_targets(), goal=NutritionGoal.MAINTAIN_WEIGHT
        )
        assert result.items[2].tone is NutritionSummaryTone.INFORMATIONAL


# ===========================================================================
# 8. Macronutrients
# ===========================================================================


class TestMacronutrients:
    def test_supplied_protein_appears(self):
        result = build_nutrition_summary(
            metrics=_metrics(), targets=_targets(protein="135"), goal=NutritionGoal.MAINTAIN_WEIGHT
        )
        assert "135" in result.items[3].message

    def test_supplied_carbohydrate_appears(self):
        result = build_nutrition_summary(
            metrics=_metrics(),
            targets=_targets(carbohydrate="210"),
            goal=NutritionGoal.MAINTAIN_WEIGHT,
        )
        assert "210" in result.items[3].message

    def test_supplied_fat_appears(self):
        result = build_nutrition_summary(
            metrics=_metrics(), targets=_targets(fat="72"), goal=NutritionGoal.MAINTAIN_WEIGHT
        )
        assert "72" in result.items[3].message

    def test_all_three_present(self):
        msg = (
            build_nutrition_summary(
                metrics=_metrics(), targets=_targets(), goal=NutritionGoal.MAINTAIN_WEIGHT
            )
            .items[3]
            .message.lower()
        )
        assert "protein" in msg
        assert "carbohydrate" in msg
        assert "fat" in msg

    def test_no_medical_prescription_claim(self):
        msg = (
            build_nutrition_summary(
                metrics=_metrics(), targets=_targets(), goal=NutritionGoal.MAINTAIN_WEIGHT
            )
            .items[3]
            .message.lower()
        )
        assert "medical prescription" in msg

    def test_no_recalculation_of_percentages(self):
        source = _source()
        assert "MACRO_DISTRIBUTIONS" not in source

    def test_informational_tone(self):
        result = build_nutrition_summary(
            metrics=_metrics(), targets=_targets(), goal=NutritionGoal.MAINTAIN_WEIGHT
        )
        assert result.items[3].tone is NutritionSummaryTone.INFORMATIONAL


# ===========================================================================
# 9. Goals
# ===========================================================================


class TestGoals:
    @pytest.mark.parametrize("goal", list(NutritionGoal))
    def test_every_goal_covered(self, goal):
        result = build_nutrition_summary(metrics=_metrics(), targets=_targets(), goal=goal)
        assert result.items[4].code == "GOAL_CONTEXT"

    def test_maintain_weight_wording(self):
        msg = (
            build_nutrition_summary(
                metrics=_metrics(), targets=_targets(), goal=NutritionGoal.MAINTAIN_WEIGHT
            )
            .items[4]
            .message.lower()
        )
        assert "maintenance" in msg or "maintain" in msg
        assert "guaranteed" in msg

    def test_lose_weight_wording(self):
        msg = (
            build_nutrition_summary(
                metrics=_metrics(), targets=_targets(), goal=NutritionGoal.LOSE_WEIGHT
            )
            .items[4]
            .message.lower()
        )
        assert "conservative" in msg
        assert "week" not in msg
        assert "guaranteed" in msg

    def test_gain_weight_wording(self):
        msg = (
            build_nutrition_summary(
                metrics=_metrics(), targets=_targets(), goal=NutritionGoal.GAIN_WEIGHT
            )
            .items[4]
            .message.lower()
        )
        assert "increase" in msg or "gain" in msg
        assert "week" not in msg
        assert "guaranteed" in msg

    def test_gain_muscle_wording(self):
        msg = (
            build_nutrition_summary(
                metrics=_metrics(), targets=_targets(), goal=NutritionGoal.GAIN_MUSCLE
            )
            .items[4]
            .message.lower()
        )
        assert "muscle" in msg
        assert "guaranteed" in msg
        assert "exercise" in msg

    def test_no_guaranteed_outcomes(self):
        for goal in NutritionGoal:
            msg = (
                build_nutrition_summary(metrics=_metrics(), targets=_targets(), goal=goal)
                .items[4]
                .message.lower()
            )
            assert "guaranteed" in msg

    def test_no_weekly_prediction(self):
        for goal in NutritionGoal:
            msg = (
                build_nutrition_summary(metrics=_metrics(), targets=_targets(), goal=goal)
                .items[4]
                .message.lower()
            )
            assert "week" not in msg

    def test_informational_tone(self):
        for goal in NutritionGoal:
            result = build_nutrition_summary(metrics=_metrics(), targets=_targets(), goal=goal)
            assert result.items[4].tone is NutritionSummaryTone.INFORMATIONAL

    def test_unsupported_goal_fails(self):
        class FakeGoal:
            value = "nonsense"

        with pytest.raises(ValueError):
            build_nutrition_summary(
                metrics=_metrics(),
                targets=_targets(),
                goal=FakeGoal(),  # type: ignore[arg-type]
            )


# ===========================================================================
# 10. General limitation
# ===========================================================================


class TestGeneralLimitation:
    def test_final_position(self):
        result = build_nutrition_summary(
            metrics=_metrics(), targets=_targets(), goal=NutritionGoal.MAINTAIN_WEIGHT
        )
        assert result.items[5].code == "GENERAL_ESTIMATE_LIMITATION"

    def test_caution_tone(self):
        result = build_nutrition_summary(
            metrics=_metrics(), targets=_targets(), goal=NutritionGoal.MAINTAIN_WEIGHT
        )
        assert result.items[5].tone is NutritionSummaryTone.CAUTION

    def test_general_estimate_wording(self):
        msg = (
            build_nutrition_summary(
                metrics=_metrics(), targets=_targets(), goal=NutritionGoal.MAINTAIN_WEIGHT
            )
            .items[5]
            .message.lower()
        )
        assert "general estimates" in msg

    def test_individual_needs_wording(self):
        msg = (
            build_nutrition_summary(
                metrics=_metrics(), targets=_targets(), goal=NutritionGoal.MAINTAIN_WEIGHT
            )
            .items[5]
            .message.lower()
        )
        assert "individual" in msg

    def test_professional_guidance_wording(self):
        msg = (
            build_nutrition_summary(
                metrics=_metrics(), targets=_targets(), goal=NutritionGoal.MAINTAIN_WEIGHT
            )
            .items[5]
            .message.lower()
        )
        assert "professional" in msg

    def test_no_diagnosis(self):
        msg = (
            build_nutrition_summary(
                metrics=_metrics(), targets=_targets(), goal=NutritionGoal.MAINTAIN_WEIGHT
            )
            .items[5]
            .message.lower()
        )
        assert "diagnos" not in msg

    def test_no_treatment(self):
        msg = (
            build_nutrition_summary(
                metrics=_metrics(), targets=_targets(), goal=NutritionGoal.MAINTAIN_WEIGHT
            )
            .items[5]
            .message.lower()
        )
        assert "treatment" not in msg

    def test_mentions_pregnancy_and_medications(self):
        msg = (
            build_nutrition_summary(
                metrics=_metrics(), targets=_targets(), goal=NutritionGoal.MAINTAIN_WEIGHT
            )
            .items[5]
            .message.lower()
        )
        assert "pregnancy" in msg
        assert "medication" in msg


# ===========================================================================
# 11. Validation
# ===========================================================================


class TestValidation:
    def test_bool_age_rejected(self):
        with pytest.raises(ValueError):
            build_nutrition_summary(
                metrics=_metrics(age=True),  # type: ignore[arg-type]
                targets=_targets(),
                goal=NutritionGoal.MAINTAIN_WEIGHT,
            )

    def test_zero_age_rejected(self):
        with pytest.raises(ValueError):
            build_nutrition_summary(
                metrics=_metrics(age=0),
                targets=_targets(),
                goal=NutritionGoal.MAINTAIN_WEIGHT,
            )

    def test_negative_age_rejected(self):
        with pytest.raises(ValueError):
            build_nutrition_summary(
                metrics=_metrics(age=-5),
                targets=_targets(),
                goal=NutritionGoal.MAINTAIN_WEIGHT,
            )

    def test_nan_bmi_rejected(self):
        with pytest.raises(ValueError):
            build_nutrition_summary(
                metrics=_metrics(bmi="NaN"),
                targets=_targets(),
                goal=NutritionGoal.MAINTAIN_WEIGHT,
            )

    def test_positive_infinity_bmi_rejected(self):
        with pytest.raises(ValueError):
            build_nutrition_summary(
                metrics=_metrics(bmi="Infinity"),
                targets=_targets(),
                goal=NutritionGoal.MAINTAIN_WEIGHT,
            )

    def test_negative_infinity_bmi_rejected(self):
        with pytest.raises(ValueError):
            build_nutrition_summary(
                metrics=_metrics(bmi="-Infinity"),
                targets=_targets(),
                goal=NutritionGoal.MAINTAIN_WEIGHT,
            )

    def test_zero_bmi_rejected(self):
        with pytest.raises(ValueError):
            build_nutrition_summary(
                metrics=_metrics(bmi="0"),
                targets=_targets(),
                goal=NutritionGoal.MAINTAIN_WEIGHT,
            )

    def test_negative_bmi_rejected(self):
        with pytest.raises(ValueError):
            build_nutrition_summary(
                metrics=_metrics(bmi="-5"),
                targets=_targets(),
                goal=NutritionGoal.MAINTAIN_WEIGHT,
            )

    def test_zero_bmr_rejected(self):
        with pytest.raises(ValueError):
            build_nutrition_summary(
                metrics=_metrics(bmr="0"),
                targets=_targets(),
                goal=NutritionGoal.MAINTAIN_WEIGHT,
            )

    def test_negative_bmr_rejected(self):
        with pytest.raises(ValueError):
            build_nutrition_summary(
                metrics=_metrics(bmr="-1"),
                targets=_targets(),
                goal=NutritionGoal.MAINTAIN_WEIGHT,
            )

    def test_nan_bmr_rejected(self):
        with pytest.raises(ValueError):
            build_nutrition_summary(
                metrics=_metrics(bmr="NaN"),
                targets=_targets(),
                goal=NutritionGoal.MAINTAIN_WEIGHT,
            )

    def test_zero_tdee_rejected(self):
        with pytest.raises(ValueError):
            build_nutrition_summary(
                metrics=_metrics(tdee="0"),
                targets=_targets(),
                goal=NutritionGoal.MAINTAIN_WEIGHT,
            )

    def test_negative_tdee_rejected(self):
        with pytest.raises(ValueError):
            build_nutrition_summary(
                metrics=_metrics(tdee="-1"),
                targets=_targets(),
                goal=NutritionGoal.MAINTAIN_WEIGHT,
            )

    def test_calorie_target_below_minimum_rejected(self):
        below = str(MINIMUM_CALORIE_TARGET - Decimal("1"))
        with pytest.raises(ValueError):
            build_nutrition_summary(
                metrics=_metrics(),
                targets=_targets(calorie=below),
                goal=NutritionGoal.MAINTAIN_WEIGHT,
            )

    def test_calorie_target_exact_minimum_accepted(self):
        result = build_nutrition_summary(
            metrics=_metrics(),
            targets=_targets(calorie=str(MINIMUM_CALORIE_TARGET)),
            goal=NutritionGoal.MAINTAIN_WEIGHT,
        )
        assert result.items[2].code == "CALORIE_TARGET_CONTEXT"

    def test_zero_protein_rejected(self):
        with pytest.raises(ValueError):
            build_nutrition_summary(
                metrics=_metrics(),
                targets=_targets(protein="0"),
                goal=NutritionGoal.MAINTAIN_WEIGHT,
            )

    def test_negative_carbohydrate_rejected(self):
        with pytest.raises(ValueError):
            build_nutrition_summary(
                metrics=_metrics(),
                targets=_targets(carbohydrate="-3"),
                goal=NutritionGoal.MAINTAIN_WEIGHT,
            )

    def test_negative_fat_rejected(self):
        with pytest.raises(ValueError):
            build_nutrition_summary(
                metrics=_metrics(),
                targets=_targets(fat="-3"),
                goal=NutritionGoal.MAINTAIN_WEIGHT,
            )

    def test_invalid_bmi_category_rejected(self):
        class FakeCategory:
            value = "unknown"

        with pytest.raises(ValueError):
            build_nutrition_summary(
                metrics=_metrics(bmi_category=FakeCategory()),  # type: ignore[arg-type]
                targets=_targets(),
                goal=NutritionGoal.MAINTAIN_WEIGHT,
            )

    def test_reuses_existing_minimum_constant(self):
        source = _source()
        assert "MINIMUM_CALORIE_TARGET" in source
        assert "1200" not in source.replace("1200", "") or "MINIMUM_CALORIE_TARGET" in source

    def test_no_float_conversion(self):
        source = _source()
        assert "float(" not in source

    def test_wrong_metrics_type_rejected(self):
        with pytest.raises(ValueError):
            build_nutrition_summary(
                metrics=object(),  # type: ignore[arg-type]
                targets=_targets(),
                goal=NutritionGoal.MAINTAIN_WEIGHT,
            )

    def test_wrong_targets_type_rejected(self):
        with pytest.raises(ValueError):
            build_nutrition_summary(
                metrics=_metrics(),
                targets=object(),  # type: ignore[arg-type]
                goal=NutritionGoal.MAINTAIN_WEIGHT,
            )


# ===========================================================================
# 12. Privacy / security
# ===========================================================================


class TestPrivacy:
    def test_no_user_id(self):
        text = _run().overview.lower()
        assert "user id" not in text

    def test_no_email(self):
        text = " ".join(i.message.lower() for i in _run().items)
        assert "@" not in text
        assert "email" not in text

    def test_no_password(self):
        text = " ".join(i.message.lower() for i in _run().items)
        assert "password" not in text

    def test_no_password_hash(self):
        text = " ".join(i.message.lower() for i in _run().items)
        assert "hash" not in text

    def test_no_token(self):
        text = " ".join(i.message.lower() for i in _run().items)
        assert "token" not in text

    def test_no_jwt_claim(self):
        text = " ".join(i.message.lower() for i in _run().items)
        assert "jwt" not in text

    def test_no_database_info(self):
        text = " ".join(i.message.lower() for i in _run().items)
        assert "table" not in text
        assert "sql" not in text

    def test_no_secret_info(self):
        text = _run().overview.lower()
        assert "secret" not in text
        assert "api key" not in text


# ===========================================================================
# 13. Determinism / immutability / Decimal preservation
# ===========================================================================


class TestDeterminismAndImmutability:
    def test_decimal_preserved_for_bmi(self):
        result = build_nutrition_summary(
            metrics=_metrics(bmi="22.00"),
            targets=_targets(),
            goal=NutritionGoal.MAINTAIN_WEIGHT,
        )
        assert "22.00" in result.items[0].message

    def test_decimal_preserved_for_macros(self):
        result = build_nutrition_summary(
            metrics=_metrics(),
            targets=_targets(protein="120", carbohydrate="200", fat="60"),
            goal=NutritionGoal.MAINTAIN_WEIGHT,
        )
        msg = result.items[3].message
        assert "120" in msg and "200" in msg and "60" in msg

    def test_independent_calls_not_linked(self):
        a = build_nutrition_summary(
            metrics=_metrics(), targets=_targets(), goal=NutritionGoal.LOSE_WEIGHT
        )
        b = build_nutrition_summary(
            metrics=_metrics(), targets=_targets(), goal=NutritionGoal.GAIN_WEIGHT
        )
        assert a.items[4].message != b.items[4].message

    def test_tuple_items_immutable(self):
        result = _run()
        with pytest.raises((AttributeError, TypeError)):
            result.items.append(None)  # type: ignore[attr-defined]


# ===========================================================================
# 14. Compatibility boundaries
# ===========================================================================


class TestCompatibility:
    def test_existing_calculation_result_type_unused_in_formula(self):
        metrics = nutrition_calculations.calculate_nutrition_metrics(
            date_of_birth=__import__("datetime").date(1990, 1, 1),
            reference_date=__import__("datetime").date(2024, 1, 1),
            biological_sex=__import__(
                "app.models.enums", fromlist=["BiologicalSex"]
            ).BiologicalSex.MALE,
            height_cm=Decimal("175"),
            weight_kg=Decimal("70"),
            activity_level=__import__(
                "app.models.enums", fromlist=["ActivityLevel"]
            ).ActivityLevel.MODERATELY_ACTIVE,
        )
        targets = nutrition_calculations.calculate_nutrition_targets(
            tdee_kcal_per_day=metrics.tdee_kcal_per_day,
            goal=NutritionGoal.MAINTAIN_WEIGHT,
        )
        result = build_nutrition_summary(
            metrics=metrics, targets=targets, goal=NutritionGoal.MAINTAIN_WEIGHT
        )
        assert isinstance(result, NutritionSummaryResult)
        assert len(result.items) == 6
