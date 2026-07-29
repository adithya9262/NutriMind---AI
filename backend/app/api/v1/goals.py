from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.authentication import get_current_user
from app.core.goal_exceptions import GoalNotFoundError
from app.core.middleware import get_request_id
from app.db.dependencies import get_db_session
from app.models.user import User
from app.repositories.goal import GoalRepository
from app.schemas.goals import (
    GoalCreate,
    GoalData,
    GoalDeleteSuccessResponse,
    GoalListData,
    GoalListSuccessResponse,
    GoalSuccessResponse,
    GoalUpdate,
)
from app.services.goal import GoalService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/goals", tags=["Goals"])


@router.post(
    "",
    response_model=GoalSuccessResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_goal_endpoint(
    request: Request,
    body: GoalCreate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> GoalSuccessResponse | JSONResponse:
    request_id = get_request_id() or "-"
    repo = GoalRepository(session)
    service = GoalService(repo)

    try:
        goal = await service.create_goal(user_id=current_user.id, data=body)
    except Exception:
        await session.rollback()
        logger.exception(
            "Failed to create goal",
            extra={"request_id": request_id},
        )
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "success": False,
                "error": {
                    "code": "GOAL_PERSISTENCE_ERROR",
                    "message": "Goal could not be saved.",
                    "request_id": request_id,
                },
            },
        )

    try:
        await session.commit()
        await session.refresh(goal)
    except Exception:
        await session.rollback()
        logger.exception(
            "Failed to persist goal creation",
            extra={"request_id": request_id},
        )
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "success": False,
                "error": {
                    "code": "GOAL_PERSISTENCE_ERROR",
                    "message": "Goal data could not be saved.",
                    "request_id": request_id,
                },
            },
        )

    return GoalSuccessResponse(
        message="Goal created successfully.",
        data=GoalData.from_orm_model(goal),
    )


@router.get(
    "",
    response_model=GoalListSuccessResponse,
)
async def list_goals_endpoint(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> GoalListSuccessResponse | JSONResponse:
    request_id = get_request_id() or "-"
    repo = GoalRepository(session)
    service = GoalService(repo)

    try:
        goals = await service.list_goals(user_id=current_user.id)
    except Exception:
        logger.exception(
            "Failed to list goals",
            extra={"request_id": request_id},
        )
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "success": False,
                "error": {
                    "code": "GOAL_LIST_ERROR",
                    "message": "Unable to retrieve goals.",
                    "request_id": request_id,
                },
            },
        )

    return GoalListSuccessResponse(
        message="Goals retrieved successfully.",
        data=GoalListData.from_domain(goals),
    )


@router.get(
    "/{goal_id}",
    response_model=GoalSuccessResponse,
)
async def get_goal_endpoint(
    request: Request,
    goal_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> GoalSuccessResponse | JSONResponse:
    request_id = get_request_id() or "-"
    repo = GoalRepository(session)
    service = GoalService(repo)

    try:
        goal = await service.get_goal(user_id=current_user.id, goal_id=goal_id)
    except GoalNotFoundError:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "success": False,
                "error": {
                    "code": "GOAL_NOT_FOUND",
                    "message": str(GoalNotFoundError()),
                    "request_id": request_id,
                },
            },
        )

    return GoalSuccessResponse(
        message="Goal retrieved successfully.",
        data=GoalData.from_orm_model(goal),
    )


@router.patch(
    "/{goal_id}",
    response_model=GoalSuccessResponse,
)
async def update_goal_endpoint(
    request: Request,
    goal_id: UUID,
    body: GoalUpdate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> GoalSuccessResponse | JSONResponse:
    request_id = get_request_id() or "-"
    repo = GoalRepository(session)
    service = GoalService(repo)

    try:
        goal = await service.update_goal(
            user_id=current_user.id,
            goal_id=goal_id,
            data=body,
        )
    except GoalNotFoundError:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "success": False,
                "error": {
                    "code": "GOAL_NOT_FOUND",
                    "message": str(GoalNotFoundError()),
                    "request_id": request_id,
                },
            },
        )

    try:
        await session.commit()
        await session.refresh(goal)
    except Exception:
        await session.rollback()
        logger.exception(
            "Failed to persist goal update",
            extra={"request_id": request_id},
        )
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "success": False,
                "error": {
                    "code": "GOAL_PERSISTENCE_ERROR",
                    "message": "Goal data could not be saved.",
                    "request_id": request_id,
                },
            },
        )

    return GoalSuccessResponse(
        message="Goal updated successfully.",
        data=GoalData.from_orm_model(goal),
    )


@router.delete(
    "/{goal_id}",
    response_model=GoalDeleteSuccessResponse,
)
async def delete_goal_endpoint(
    request: Request,
    goal_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> GoalDeleteSuccessResponse | JSONResponse:
    request_id = get_request_id() or "-"
    repo = GoalRepository(session)
    service = GoalService(repo)

    try:
        await service.delete_goal(user_id=current_user.id, goal_id=goal_id)
    except GoalNotFoundError:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "success": False,
                "error": {
                    "code": "GOAL_NOT_FOUND",
                    "message": str(GoalNotFoundError()),
                    "request_id": request_id,
                },
            },
        )

    try:
        await session.commit()
    except Exception:
        await session.rollback()
        logger.exception(
            "Failed to persist goal deletion",
            extra={"request_id": request_id},
        )
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "success": False,
                "error": {
                    "code": "GOAL_PERSISTENCE_ERROR",
                    "message": "Goal could not be deleted.",
                    "request_id": request_id,
                },
            },
        )

    return GoalDeleteSuccessResponse(
        message="Goal deleted successfully.",
    )
