from __future__ import annotations

import logging
import uuid
from datetime import date

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
from app.core.nutrition_profile_exceptions import (
    NutritionProfileAlreadyExistsError,
    NutritionProfileNotFoundError,
)
from app.core.nutrition_summaries import build_nutrition_summary
from app.db.dependencies import get_db_session
from app.models.nutrition_profile import NutritionProfile
from app.models.user import User
from app.repositories.nutrition_profile import NutritionProfileRepository
from app.schemas.nutrition_calculations import (
    CalculatedNutritionData,
    CalculatedNutritionSuccessResponse,
)
from app.schemas.nutrition_profile import (
    NutritionProfileCreate,
    NutritionProfileData,
    NutritionProfilePublic,
    NutritionProfileSuccessResponse,
    NutritionProfileUpdate,
)
from app.schemas.nutrition_summaries import (
    NutritionSummaryData,
    NutritionSummarySuccessResponse,
)
from app.services.nutrition_profile import NutritionProfileService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/nutrition-profile", tags=["Nutrition Profile"])


async def get_or_create_profile(
    user_id: uuid.UUID,
    service: NutritionProfileService,
    session: AsyncSession,
) -> NutritionProfile:
    try:
        return await service.get_profile(user_id=user_id)
    except NutritionProfileNotFoundError:
        default_data = NutritionProfileCreate()
        try:
            profile = await service.create_profile(user_id=user_id, data=default_data)
            await session.commit()
            await session.refresh(profile)
            return profile
        except NutritionProfileAlreadyExistsError:
            await session.rollback()
            return await service.get_profile(user_id=user_id)



@router.get(
    "/summary",
    response_model=NutritionSummarySuccessResponse,
)
async def get_nutrition_summary(
    request: Request,
    reference_date: date = Query(
        ...,
        description="Reference date (YYYY-MM-DD) used for deterministic age calculation.",
    ),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> NutritionSummarySuccessResponse | JSONResponse:
    request_id = get_request_id() or "-"
    repo = NutritionProfileRepository(session)
    service = NutritionProfileService(repo)

    profile = await get_or_create_profile(
        user_id=current_user.id, service=service, session=session
    )

    if (
        profile.date_of_birth is None
        or profile.biological_sex is None
        or profile.height_cm is None
        or profile.weight_kg is None
        or profile.activity_level is None
        or profile.goal is None
    ):
        return NutritionSummarySuccessResponse(
            message="Nutrition profile is incomplete. Cannot generate summary.",
            data=None,
        )

    try:
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
        summary = build_nutrition_summary(
            metrics=metrics,
            targets=targets,
            goal=profile.goal,
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

    data = NutritionSummaryData.from_result(summary)
    return NutritionSummarySuccessResponse(
        message="Nutrition summary generated successfully.",
        data=data,
    )


@router.get(
    "/calculations",
    response_model=CalculatedNutritionSuccessResponse,
)
async def get_nutrition_calculations(
    request: Request,
    reference_date: date = Query(
        ...,
        description="Reference date (YYYY-MM-DD) used for deterministic age calculation.",
    ),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> CalculatedNutritionSuccessResponse | JSONResponse:
    request_id = get_request_id() or "-"
    repo = NutritionProfileRepository(session)
    service = NutritionProfileService(repo)

    profile = await get_or_create_profile(
        user_id=current_user.id, service=service, session=session
    )

    if (
        profile.date_of_birth is None
        or profile.biological_sex is None
        or profile.height_cm is None
        or profile.weight_kg is None
        or profile.activity_level is None
        or profile.goal is None
    ):
        return CalculatedNutritionSuccessResponse(
            message="Nutrition profile is incomplete. Cannot generate calculations.",
            data=None,
        )

    try:
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

    data = CalculatedNutritionData.from_results(metrics, targets)
    return CalculatedNutritionSuccessResponse(
        message="Nutrition calculations completed successfully.",
        data=data,
    )


@router.post(
    "",
    response_model=NutritionProfileSuccessResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_nutrition_profile(
    request: Request,
    body: NutritionProfileCreate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> NutritionProfileSuccessResponse | JSONResponse:
    request_id = get_request_id() or "-"
    repo = NutritionProfileRepository(session)
    service = NutritionProfileService(repo)

    try:
        profile = await service.create_profile(user_id=current_user.id, data=body)
    except NutritionProfileAlreadyExistsError:
        await session.rollback()
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "success": False,
                "error": {
                    "code": "NUTRITION_PROFILE_ALREADY_EXISTS",
                    "message": "A nutrition profile already exists for this user.",
                    "request_id": request_id,
                },
            },
        )

    try:
        await session.commit()
        await session.refresh(profile)
    except Exception:
        await session.rollback()
        logger.exception(
            "Failed to persist nutrition profile",
            extra={"request_id": request_id},
        )
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "success": False,
                "error": {
                    "code": "NUTRITION_PROFILE_UNAVAILABLE",
                    "message": "Unable to save the nutrition profile.",
                    "request_id": request_id,
                },
            },
        )

    public_profile = NutritionProfilePublic.model_validate(profile)
    return NutritionProfileSuccessResponse(
        message="Nutrition profile created successfully.",
        data=NutritionProfileData(profile=public_profile),
    )


@router.get(
    "",
    response_model=NutritionProfileSuccessResponse,
)
async def get_nutrition_profile(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> NutritionProfileSuccessResponse | JSONResponse:
    request_id = get_request_id() or "-"
    repo = NutritionProfileRepository(session)
    service = NutritionProfileService(repo)

    profile = await get_or_create_profile(
        user_id=current_user.id, service=service, session=session
    )

    public_profile = NutritionProfilePublic.model_validate(profile)
    return NutritionProfileSuccessResponse(
        message="Nutrition profile retrieved successfully.",
        data=NutritionProfileData(profile=public_profile),
    )


@router.patch(
    "",
    response_model=NutritionProfileSuccessResponse,
)
async def update_nutrition_profile(
    request: Request,
    body: NutritionProfileUpdate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> NutritionProfileSuccessResponse | JSONResponse:
    request_id = get_request_id() or "-"
    repo = NutritionProfileRepository(session)
    service = NutritionProfileService(repo)

    try:
        profile = await service.update_profile(user_id=current_user.id, data=body)
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

    try:
        await session.commit()
        await session.refresh(profile)
    except Exception:
        await session.rollback()
        logger.exception(
            "Failed to persist nutrition profile update",
            extra={"request_id": request_id},
        )
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "success": False,
                "error": {
                    "code": "NUTRITION_PROFILE_UNAVAILABLE",
                    "message": "Unable to save the nutrition profile.",
                    "request_id": request_id,
                },
            },
        )

    public_profile = NutritionProfilePublic.model_validate(profile)
    return NutritionProfileSuccessResponse(
        message="Nutrition profile updated successfully.",
        data=NutritionProfileData(profile=public_profile),
    )
