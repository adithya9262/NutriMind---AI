from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.authentication import get_current_user
from app.core.middleware import get_request_id
from app.core.nutrition_calculation_exceptions import (
    CalorieTargetBelowMinimumError,
    UnsupportedBMRCalculationError,
)
from app.core.nutrition_calculations import (
    calculate_nutrition_metrics,
    calculate_nutrition_targets,
)
from app.core.nutrition_log_exceptions import (
    NutritionLogEntryAlreadyExistsError,
    NutritionLogEntryNotFoundError,
    NutritionLogPersistenceError,
)
from app.core.nutrition_logs import (
    NutritionLogEntry,
    calculate_daily_nutrition_totals,
    summarize_daily_nutrition_log,
)
from app.core.nutrition_profile_exceptions import (
    NutritionProfileNotFoundError,
)
from app.core.nutrition_progress import (
    calculate_daily_nutrition_progress,
)
from app.db.dependencies import get_db_session
from app.models.user import User
from app.repositories.nutrition_log import NutritionLogRepository
from app.repositories.nutrition_profile import NutritionProfileRepository
from app.schemas.nutrition_logs import (
    DailyNutritionLogSuccessResponse,
    DailyNutritionLogSummaryData,
    NutritionLogDeleteSuccessResponse,
    NutritionLogEntryCreate,
    NutritionLogEntryData,
    NutritionLogEntryListData,
    NutritionLogEntryListSuccessResponse,
    NutritionLogEntrySuccessResponse,
)
from app.schemas.nutrition_progress import (
    DailyNutritionProgressData,
    DailyNutritionProgressSuccessResponse,
    NutrientProgressData,
)
from app.core.nutrition_progress import NutritionProgressStatus
from app.services.nutrition_log import NutritionLogService
from app.services.nutrition_profile import NutritionProfileService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/nutrition-logs", tags=["Nutrition Logs"])


@router.post(
    "",
    response_model=NutritionLogEntrySuccessResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_nutrition_log_entry(
    request: Request,
    body: NutritionLogEntryCreate,
    logged_date: date = Query(..., description="Logged date (YYYY-MM-DD) for the entry."),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> NutritionLogEntrySuccessResponse | JSONResponse:
    request_id = get_request_id() or "-"
    repo = NutritionLogRepository(session)
    service = NutritionLogService(repo)

    try:
        entry = await service.create_entry(
            user_id=current_user.id,
            logged_date=logged_date,
            data=body,
        )
    except NutritionLogEntryAlreadyExistsError:
        await session.rollback()
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "success": False,
                "error": {
                    "code": "NUTRITION_LOG_ENTRY_ALREADY_EXISTS",
                    "message": str(NutritionLogEntryAlreadyExistsError()),
                    "request_id": request_id,
                },
            },
        )
    except NutritionLogPersistenceError:
        await session.rollback()
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "success": False,
                "error": {
                    "code": "NUTRITION_LOG_PERSISTENCE_ERROR",
                    "message": str(NutritionLogPersistenceError()),
                    "request_id": request_id,
                },
            },
        )

    try:
        await session.commit()
        await session.refresh(entry)
    except Exception:
        await session.rollback()
        logger.exception(
            "Failed to persist nutrition log entry",
            extra={"request_id": request_id},
        )
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "success": False,
                "error": {
                    "code": "NUTRITION_LOG_PERSISTENCE_ERROR",
                    "message": str(NutritionLogPersistenceError()),
                    "request_id": request_id,
                },
            },
        )

    entry_data = NutritionLogEntryData.model_validate(entry)
    return NutritionLogEntrySuccessResponse(
        message="Nutrition log entry created successfully.",
        data=entry_data,
    )


@router.get(
    "",
    response_model=NutritionLogEntryListSuccessResponse,
)
async def list_nutrition_log_entries(
    request: Request,
    logged_date: date = Query(..., description="Logged date (YYYY-MM-DD) to retrieve entries for."),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> NutritionLogEntryListSuccessResponse | JSONResponse:
    request_id = get_request_id() or "-"
    repo = NutritionLogRepository(session)
    service = NutritionLogService(repo)

    try:
        entries = await service.list_daily_entries(
            user_id=current_user.id,
            logged_date=logged_date,
        )
    except Exception:
        logger.exception(
            "Failed to list nutrition log entries",
            extra={"request_id": request_id},
        )
        raise

    entry_data = [NutritionLogEntryData.model_validate(e) for e in entries]
    list_data = NutritionLogEntryListData(
        logged_date=logged_date,
        entries=entry_data,
    )
    return NutritionLogEntryListSuccessResponse(
        message="Nutrition log entries retrieved successfully.",
        data=list_data,
    )


@router.get(
    "/summary",
    response_model=DailyNutritionLogSuccessResponse,
)
async def get_daily_nutrition_log_summary(
    request: Request,
    logged_date: date = Query(..., description="Logged date (YYYY-MM-DD) for the summary."),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> DailyNutritionLogSuccessResponse | JSONResponse:
    request_id = get_request_id() or "-"
    repo = NutritionLogRepository(session)
    service = NutritionLogService(repo)

    try:
        entries = await service.list_daily_entries(
            user_id=current_user.id,
            logged_date=logged_date,
        )
    except Exception:
        logger.exception(
            "Failed to list nutrition log entries for summary",
            extra={"request_id": request_id},
        )
        raise

    domain_entries = tuple(
        NutritionLogEntry(
            entry_id=e.entry_id,
            food_name=e.food_name,
            meal_type=e.meal_type,
            serving_description=e.serving_description,
            calories_kcal=e.calories_kcal,
            protein_g=e.protein_g,
            carbohydrate_g=e.carbohydrate_g,
            fat_g=e.fat_g,
        )
        for e in entries
    )

    summary = summarize_daily_nutrition_log(entries=domain_entries)

    summary_data = DailyNutritionLogSummaryData.from_domain(summary)
    return DailyNutritionLogSuccessResponse(
        message="Daily nutrition log summarized successfully.",
        data=summary_data,
    )


@router.get(
    "/progress",
    response_model=DailyNutritionProgressSuccessResponse,
)
async def get_daily_nutrition_target_progress(
    request: Request,
    logged_date: date = Query(
        ...,
        description="Logged date (YYYY-MM-DD) for the progress calculation.",
    ),
    reference_date: date = Query(
        ...,
        description="Reference date (YYYY-MM-DD) used for deterministic age calculation.",
    ),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> DailyNutritionProgressSuccessResponse | JSONResponse:
    request_id = get_request_id() or "-"

    profile_repo = NutritionProfileRepository(session)
    profile_service = NutritionProfileService(profile_repo)
    try:
        profile = await profile_service.get_profile(user_id=current_user.id)
    except NutritionProfileNotFoundError:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "success": False,
                "error": {
                    "code": "NUTRITION_PROFILE_NOT_FOUND",
                    "message": "Nutrition profile not found.",
                    "request_id": request_id,
                },
            },
        )

    log_repo = NutritionLogRepository(session)
    log_service = NutritionLogService(log_repo)
    try:
        entries = await log_service.list_daily_entries(
            user_id=current_user.id,
            logged_date=logged_date,
        )
    except Exception:
        logger.exception(
            "Failed to list nutrition log entries for progress",
            extra={"request_id": request_id},
        )
        raise

    domain_entries = tuple(
        NutritionLogEntry(
            entry_id=e.entry_id,
            food_name=e.food_name,
            meal_type=e.meal_type,
            serving_description=e.serving_description,
            calories_kcal=e.calories_kcal,
            protein_g=e.protein_g,
            carbohydrate_g=e.carbohydrate_g,
            fat_g=e.fat_g,
        )
        for e in entries
    )

    if not all(
        [
            profile.date_of_birth,
            profile.biological_sex,
            profile.height_cm,
            profile.weight_kg,
            profile.activity_level,
            profile.goal,
        ]
    ):
        return DailyNutritionProgressSuccessResponse(
            message="Profile incomplete",
            data=DailyNutritionProgressData(
                calories=NutrientProgressData(consumed=Decimal(0), target=Decimal("1"), remaining=Decimal(0), percentage=Decimal(0), status=NutritionProgressStatus.BELOW_TARGET),
                protein=NutrientProgressData(consumed=Decimal(0), target=Decimal("1"), remaining=Decimal(0), percentage=Decimal(0), status=NutritionProgressStatus.BELOW_TARGET),
                carbohydrate=NutrientProgressData(consumed=Decimal(0), target=Decimal("1"), remaining=Decimal(0), percentage=Decimal(0), status=NutritionProgressStatus.BELOW_TARGET),
                fat=NutrientProgressData(consumed=Decimal(0), target=Decimal("1"), remaining=Decimal(0), percentage=Decimal(0), status=NutritionProgressStatus.BELOW_TARGET),
            ),
        )

    try:
        totals = calculate_daily_nutrition_totals(entries=domain_entries)
        metrics = calculate_nutrition_metrics(
            date_of_birth=profile.date_of_birth,
            reference_date=reference_date,
            biological_sex=profile.biological_sex,
            height_cm=profile.height_cm,
            weight_kg=profile.weight_kg,
            activity_level=profile.activity_level,
        )
        targets = calculate_nutrition_targets(
            tdee_kcal_per_day=metrics.tdee_kcal_per_day,
            goal=profile.goal,
        )
        from app.core.nutrition_calculations import NutritionTargetResult
        custom_targets = NutritionTargetResult(
            calorie_target_kcal_per_day=Decimal(profile.daily_calorie_goal) if profile.daily_calorie_goal is not None else targets.calorie_target_kcal_per_day,
            protein_g_per_day=Decimal(profile.daily_protein_goal_g) if profile.daily_protein_goal_g is not None else targets.protein_g_per_day,
            carbohydrate_g_per_day=Decimal(profile.daily_carb_goal_g) if profile.daily_carb_goal_g is not None else targets.carbohydrate_g_per_day,
            fat_g_per_day=Decimal(profile.daily_fat_goal_g) if profile.daily_fat_goal_g is not None else targets.fat_g_per_day,
        )
        progress = calculate_daily_nutrition_progress(
            totals=totals,
            targets=custom_targets,
        )
    except UnsupportedBMRCalculationError:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "error": {
                    "code": "BMR_CALCULATION_UNSUPPORTED",
                    "message": (
                        "BMR cannot be calculated with the selected biological-sex "
                        "option using the Mifflin-St Jeor equation."
                    ),
                    "request_id": request_id,
                },
            },
        )
    except CalorieTargetBelowMinimumError:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "error": {
                    "code": "CALORIE_TARGET_BELOW_MINIMUM",
                    "message": (
                        "The calculated calorie target is below the supported "
                        "minimum for this general nutrition estimate."
                    ),
                    "request_id": request_id,
                },
            },
        )
    except ValueError:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "error": {
                    "code": "INVALID_CALCULATION_INPUT",
                    "message": (
                        "The supplied reference date is not valid for this nutrition profile."
                    ),
                    "request_id": request_id,
                },
            },
        )
    except TypeError:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "error": {
                    "code": "INVALID_CALCULATION_INPUT",
                    "message": "Complete your nutrition profile (date of birth, sex, height, weight, activity level, goal) before viewing progress.",
                    "request_id": request_id,
                },
            },
        )

    progress_data = DailyNutritionProgressData.from_result(progress)
    return DailyNutritionProgressSuccessResponse(
        message="Daily nutrition target progress calculated successfully.",
        data=progress_data,
    )


@router.delete(
    "/{entry_id}",
    response_model=NutritionLogDeleteSuccessResponse,
)
async def delete_nutrition_log_entry(
    request: Request,
    entry_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> NutritionLogDeleteSuccessResponse | JSONResponse:
    request_id = get_request_id() or "-"
    repo = NutritionLogRepository(session)
    service = NutritionLogService(repo)

    try:
        await service.delete_entry(
            user_id=current_user.id,
            entry_id=entry_id,
        )
    except NutritionLogEntryNotFoundError:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "success": False,
                "error": {
                    "code": "NUTRITION_LOG_ENTRY_NOT_FOUND",
                    "message": str(NutritionLogEntryNotFoundError()),
                    "request_id": request_id,
                },
            },
        )
    except NutritionLogPersistenceError:
        await session.rollback()
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "success": False,
                "error": {
                    "code": "NUTRITION_LOG_PERSISTENCE_ERROR",
                    "message": str(NutritionLogPersistenceError()),
                    "request_id": request_id,
                },
            },
        )

    try:
        await session.commit()
    except Exception:
        await session.rollback()
        logger.exception(
            "Failed to persist nutrition log deletion",
            extra={"request_id": request_id},
        )
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "success": False,
                "error": {
                    "code": "NUTRITION_LOG_PERSISTENCE_ERROR",
                    "message": str(NutritionLogPersistenceError()),
                    "request_id": request_id,
                },
            },
        )

    return NutritionLogDeleteSuccessResponse(
        message="Nutrition log entry deleted successfully.",
    )
