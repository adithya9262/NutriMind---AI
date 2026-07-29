from __future__ import annotations

import logging
import uuid
from datetime import date
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.authentication import get_current_user
from app.core.body_weight import BodyWeightEntry
from app.core.body_weight_exceptions import (
    BodyWeightNotFoundError,
    DuplicateBodyWeightDateError,
    DuplicateBodyWeightEntryIdError,
)
from app.core.body_weight_goal_exceptions import (
    BodyWeightGoalCurrentWeightNotFoundError,
    InvalidBodyWeightGoalProgressError,
)
from app.core.body_weight_goals import calculate_body_weight_goal_progress
from app.core.body_weight_trend_exceptions import InsufficientBodyWeightHistoryError
from app.core.body_weight_trends import calculate_body_weight_trend
from app.core.middleware import get_request_id
from app.core.nutrition_profile_exceptions import NutritionProfileNotFoundError
from app.db.dependencies import get_db_session
from app.models.user import User
from app.repositories.body_weight import BodyWeightRepository
from app.repositories.nutrition_profile import NutritionProfileRepository
from app.schemas.body_weight import (
    BodyWeightDeleteSuccessResponse,
    BodyWeightEntryCreate,
    BodyWeightEntryData,
    BodyWeightEntrySuccessResponse,
    BodyWeightHistoryData,
    BodyWeightHistorySuccessResponse,
)
from app.schemas.body_weight_goals import (
    BodyWeightGoalProgressData,
    BodyWeightGoalProgressSuccessResponse,
)
from app.schemas.body_weight_trends import (
    BodyWeightTrendData,
    BodyWeightTrendSuccessResponse,
)
from app.services.body_weight import BodyWeightService
from app.services.nutrition_profile import NutritionProfileService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/body-weights", tags=["Body Weights"])


@router.post(
    "",
    response_model=BodyWeightEntrySuccessResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_body_weight_entry(
    request: Request,
    body: BodyWeightEntryCreate,
    logged_date: date = Query(..., description="Logged date (YYYY-MM-DD) for the entry."),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> BodyWeightEntrySuccessResponse | JSONResponse:
    request_id = get_request_id() or "-"
    repo = BodyWeightRepository(session)
    service = BodyWeightService(repo)

    try:
        entry = await service.create_entry(
            user_id=current_user.id,
            entry_id=uuid.uuid4(),
            logged_date=logged_date,
            weight_kg=body.weight_kg,
        )
    except DuplicateBodyWeightDateError:
        await session.rollback()
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "success": False,
                "error": {
                    "code": "BODY_WEIGHT_ENTRY_ALREADY_EXISTS",
                    "message": str(DuplicateBodyWeightDateError()),
                    "request_id": request_id,
                },
            },
        )
    except DuplicateBodyWeightEntryIdError:
        await session.rollback()
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "success": False,
                "error": {
                    "code": "BODY_WEIGHT_ENTRY_ID_ALREADY_EXISTS",
                    "message": str(DuplicateBodyWeightEntryIdError()),
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
            "Failed to persist body-weight entry",
            extra={"request_id": request_id},
        )
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "success": False,
                "error": {
                    "code": "BODY_WEIGHT_PERSISTENCE_ERROR",
                    "message": "Body-weight data could not be saved.",
                    "request_id": request_id,
                },
            },
        )

    entry_data = BodyWeightEntryData.model_validate(entry)
    return BodyWeightEntrySuccessResponse(
        message="Body-weight entry created successfully.",
        data=entry_data,
    )


@router.get(
    "",
    response_model=BodyWeightHistorySuccessResponse,
)
async def list_body_weight_history(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> BodyWeightHistorySuccessResponse | JSONResponse:
    request_id = get_request_id() or "-"
    repo = BodyWeightRepository(session)
    service = BodyWeightService(repo)

    try:
        entries = await service.list_history(
            user_id=current_user.id,
        )
    except Exception:
        logger.exception(
            "Failed to list body-weight history",
            extra={"request_id": request_id},
        )
        raise

    domain_entries = [
        BodyWeightEntry(
            entry_id=e.entry_id,
            logged_date=e.logged_date,
            weight_kg=e.weight_kg,
        )
        for e in entries
    ]
    history_data = BodyWeightHistoryData.from_domain(domain_entries)
    return BodyWeightHistorySuccessResponse(
        message="Body-weight history retrieved successfully.",
        data=history_data,
    )


@router.get(
    "/trend",
    response_model=BodyWeightTrendSuccessResponse,
)
async def get_body_weight_trend(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> BodyWeightTrendSuccessResponse | JSONResponse:
    request_id = get_request_id() or "-"
    repo = BodyWeightRepository(session)
    service = BodyWeightService(repo)

    entries = await service.list_history(
        user_id=current_user.id,
    )

    domain_entries = [
        BodyWeightEntry(
            entry_id=entry.entry_id,
            logged_date=entry.logged_date,
            weight_kg=entry.weight_kg,
        )
        for entry in entries
    ]

    try:
        result = calculate_body_weight_trend(entries=domain_entries)
    except InsufficientBodyWeightHistoryError:
        from datetime import date
        from app.core.body_weight_trends import BodyWeightTrendDirection
        return BodyWeightTrendSuccessResponse(
            message="Insufficient history for trend calculation.",
            data=BodyWeightTrendData(
                observation_count=0,
                first_logged_date=date.today(),
                latest_logged_date=date.today(),
                starting_weight_kg=Decimal("1"),
                latest_weight_kg=Decimal("1"),
                absolute_change_kg=Decimal("0"),
                percentage_change=Decimal("0"),
                direction=BodyWeightTrendDirection.STABLE,
                requires_onboarding=True
            )
        )

    trend_data = BodyWeightTrendData.from_result(result)
    return BodyWeightTrendSuccessResponse(
        message="Body-weight trend calculated successfully.",
        data=trend_data,
    )


@router.get(
    "/goal-progress",
    response_model=BodyWeightGoalProgressSuccessResponse,
)
async def get_body_weight_goal_progress(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> BodyWeightGoalProgressSuccessResponse | JSONResponse:
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
            headers={"X-Request-ID": request_id},
        )

    weight_repo = BodyWeightRepository(session)
    weight_service = BodyWeightService(weight_repo)
    history = await weight_service.list_history(user_id=current_user.id)
    if not history or profile.weight_kg is None or profile.target_weight_kg is None:
        from app.core.body_weight_goals import BodyWeightGoalDirection, BodyWeightGoalStatus
        target = profile.target_weight_kg if profile and profile.target_weight_kg else Decimal("70")
        current = profile.weight_kg if profile and profile.weight_kg else Decimal("70")
        return BodyWeightGoalProgressSuccessResponse(
            message="Goal progress requires complete profile and at least one weight entry.",
            data=BodyWeightGoalProgressData(
                starting_weight_kg=current,
                current_weight_kg=current,
                target_weight_kg=target,
                direction=BodyWeightGoalDirection.MAINTAIN,
                total_change_required_kg=Decimal("0"),
                change_achieved_kg=Decimal("0"),
                remaining_change_kg=Decimal("0"),
                progress_percentage=Decimal("0"),
                status=BodyWeightGoalStatus.NOT_STARTED,
                requires_onboarding=True
            )
        )

    latest_entry = history[0]
    starting_weight_kg = profile.weight_kg
    current_weight_kg = latest_entry.weight_kg
    target_weight_kg = profile.target_weight_kg

    try:
        result = calculate_body_weight_goal_progress(
            starting_weight_kg=starting_weight_kg,
            current_weight_kg=current_weight_kg,
            target_weight_kg=target_weight_kg,
        )
    except InvalidBodyWeightGoalProgressError:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "error": {
                    "code": "BODY_WEIGHT_GOAL_PROGRESS_INVALID",
                    "message": str(InvalidBodyWeightGoalProgressError()),
                    "request_id": request_id,
                },
            },
            headers={"X-Request-ID": request_id},
        )

    data = BodyWeightGoalProgressData.from_result(result)
    return BodyWeightGoalProgressSuccessResponse(data=data)


@router.delete(
    "/{entry_id}",
    response_model=BodyWeightDeleteSuccessResponse,
)
async def delete_body_weight_entry(
    request: Request,
    entry_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> BodyWeightDeleteSuccessResponse | JSONResponse:
    request_id = get_request_id() or "-"
    repo = BodyWeightRepository(session)
    service = BodyWeightService(repo)

    try:
        await service.delete_entry(
            user_id=current_user.id,
            entry_id=entry_id,
        )
    except BodyWeightNotFoundError:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "success": False,
                "error": {
                    "code": "BODY_WEIGHT_ENTRY_NOT_FOUND",
                    "message": str(BodyWeightNotFoundError()),
                    "request_id": request_id,
                },
            },
        )

    try:
        await session.commit()
    except Exception:
        await session.rollback()
        logger.exception(
            "Failed to persist body-weight deletion",
            extra={"request_id": request_id},
        )
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "success": False,
                "error": {
                    "code": "BODY_WEIGHT_PERSISTENCE_ERROR",
                    "message": "Body-weight data could not be saved.",
                    "request_id": request_id,
                },
            },
        )

    return BodyWeightDeleteSuccessResponse(
        message="Body-weight entry deleted successfully.",
    )
