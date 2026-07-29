from __future__ import annotations

import logging
import uuid
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.authentication import get_current_user
from app.core.middleware import get_request_id
from app.core.task_exceptions import (
    DuplicateTaskIdError,
    InvalidTaskError,
    TaskAlreadyCompletedError,
    TaskNotCompletedError,
    TaskNotFoundError,
)
from app.core.tasks import create_task
from app.db.dependencies import get_db_session
from app.models.user import User
from app.repositories.task import TaskRepository
from app.schemas.tasks import (
    TaskCompletionSuccessResponse,
    TaskCreate,
    TaskData,
    TaskDeleteSuccessResponse,
    TaskListData,
    TaskListSuccessResponse,
    TaskReopenSuccessResponse,
    TaskSuccessResponse,
    TaskUpdate,
)
from app.services.task import TaskService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tasks", tags=["Tasks"])


class TaskCompleteRequest(BaseModel):
    """Caller-supplied completion timestamp.

    The completion time is owned entirely by the caller; the API never
    consults the system clock.
    """

    completed_at: datetime

    model_config = {"extra": "forbid"}


@router.post(
    "",
    response_model=TaskSuccessResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_task_endpoint(
    request: Request,
    body: TaskCreate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> TaskSuccessResponse | JSONResponse:
    request_id = get_request_id() or "-"
    repo = TaskRepository(session)
    service = TaskService(repo)

    try:
        domain_task = create_task(
            task_id=uuid.uuid4(),
            title=body.title,
            description=body.description,
            priority=body.priority,
            due_date=body.due_date,
            category=body.category,
            recurrence=body.recurrence,
        )
        task = await service.create_task(user_id=current_user.id, task=domain_task)
    except DuplicateTaskIdError:
        await session.rollback()
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "success": False,
                "error": {
                    "code": "TASK_ID_ALREADY_EXISTS",
                    "message": str(DuplicateTaskIdError()),
                    "request_id": request_id,
                },
            },
        )
    except InvalidTaskError:
        await session.rollback()
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "error": {
                    "code": "INVALID_TASK",
                    "message": str(InvalidTaskError()),
                    "request_id": request_id,
                },
            },
        )

    try:
        await session.commit()
    except Exception:
        await session.rollback()
        logger.exception(
            "Failed to persist task creation",
            extra={"request_id": request_id},
        )
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "success": False,
                "error": {
                    "code": "TASK_PERSISTENCE_ERROR",
                    "message": "Task data could not be saved.",
                    "request_id": request_id,
                },
            },
        )

    return TaskSuccessResponse(
        message="Task created successfully.",
        data=TaskData.from_domain(task),
    )


@router.get(
    "",
    response_model=TaskListSuccessResponse,
)
async def list_tasks_endpoint(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> TaskListSuccessResponse | JSONResponse:
    request_id = get_request_id() or "-"
    repo = TaskRepository(session)
    service = TaskService(repo)

    try:
        tasks = await service.list_tasks(user_id=current_user.id)
    except Exception:
        logger.exception(
            "Failed to list tasks",
            extra={"request_id": request_id},
        )
        raise

    return TaskListSuccessResponse(
        message="Tasks retrieved successfully.",
        data=TaskListData.from_domain(tasks),
    )


@router.get(
    "/{task_id}",
    response_model=TaskSuccessResponse,
)
async def get_task_endpoint(
    request: Request,
    task_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> TaskSuccessResponse | JSONResponse:
    request_id = get_request_id() or "-"
    repo = TaskRepository(session)
    service = TaskService(repo)

    try:
        task = await service.get_task(user_id=current_user.id, task_id=task_id)
    except TaskNotFoundError:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "success": False,
                "error": {
                    "code": "TASK_NOT_FOUND",
                    "message": str(TaskNotFoundError()),
                    "request_id": request_id,
                },
            },
        )

    return TaskSuccessResponse(
        message="Task retrieved successfully.",
        data=TaskData.from_domain(task),
    )


@router.post(
    "/{task_id}/complete",
    response_model=TaskCompletionSuccessResponse,
)
async def complete_task_endpoint(
    request: Request,
    task_id: UUID,
    body: TaskCompleteRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> TaskCompletionSuccessResponse | JSONResponse:
    request_id = get_request_id() or "-"
    repo = TaskRepository(session)
    service = TaskService(repo)

    try:
        task = await service.complete_task(
            user_id=current_user.id,
            task_id=task_id,
            completed_at=body.completed_at,
        )
    except TaskNotFoundError:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "success": False,
                "error": {
                    "code": "TASK_NOT_FOUND",
                    "message": str(TaskNotFoundError()),
                    "request_id": request_id,
                },
            },
        )
    except TaskAlreadyCompletedError:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "success": False,
                "error": {
                    "code": "TASK_ALREADY_COMPLETED",
                    "message": str(TaskAlreadyCompletedError()),
                    "request_id": request_id,
                },
            },
        )

    try:
        await session.commit()
    except Exception:
        await session.rollback()
        logger.exception(
            "Failed to persist task completion",
            extra={"request_id": request_id},
        )
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "success": False,
                "error": {
                    "code": "TASK_PERSISTENCE_ERROR",
                    "message": "Task data could not be saved.",
                    "request_id": request_id,
                },
            },
        )

    return TaskCompletionSuccessResponse(
        message="Task completed successfully.",
        data=TaskData.from_domain(task),
    )


@router.post(
    "/{task_id}/reopen",
    response_model=TaskReopenSuccessResponse,
)
async def reopen_task_endpoint(
    request: Request,
    task_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> TaskReopenSuccessResponse | JSONResponse:
    request_id = get_request_id() or "-"
    repo = TaskRepository(session)
    service = TaskService(repo)

    try:
        task = await service.reopen_task(user_id=current_user.id, task_id=task_id)
    except TaskNotFoundError:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "success": False,
                "error": {
                    "code": "TASK_NOT_FOUND",
                    "message": str(TaskNotFoundError()),
                    "request_id": request_id,
                },
            },
        )
    except TaskNotCompletedError:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "success": False,
                "error": {
                    "code": "TASK_NOT_COMPLETED",
                    "message": str(TaskNotCompletedError()),
                    "request_id": request_id,
                },
            },
        )

    try:
        await session.commit()
    except Exception:
        await session.rollback()
        logger.exception(
            "Failed to persist task reopening",
            extra={"request_id": request_id},
        )
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "success": False,
                "error": {
                    "code": "TASK_PERSISTENCE_ERROR",
                    "message": "Task data could not be saved.",
                    "request_id": request_id,
                },
            },
        )

    return TaskReopenSuccessResponse(
        message="Task reopened successfully.",
        data=TaskData.from_domain(task),
    )


@router.delete(
    "/{task_id}",
    response_model=TaskDeleteSuccessResponse,
)
async def delete_task_endpoint(
    request: Request,
    task_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> TaskDeleteSuccessResponse | JSONResponse:
    request_id = get_request_id() or "-"
    repo = TaskRepository(session)
    service = TaskService(repo)

    try:
        await service.delete_task(user_id=current_user.id, task_id=task_id)
    except TaskNotFoundError:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "success": False,
                "error": {
                    "code": "TASK_NOT_FOUND",
                    "message": str(TaskNotFoundError()),
                    "request_id": request_id,
                },
            },
        )

    try:
        await session.commit()
    except Exception:
        await session.rollback()
        logger.exception(
            "Failed to persist task deletion",
            extra={"request_id": request_id},
        )
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "success": False,
                "error": {
                    "code": "TASK_PERSISTENCE_ERROR",
                    "message": "Task data could not be saved.",
                    "request_id": request_id,
                },
            },
        )

    return TaskDeleteSuccessResponse(
        message="Task deleted successfully.",
    )


@router.patch(
    "/{task_id}",
    response_model=TaskSuccessResponse,
)
async def update_task_endpoint(
    request: Request,
    task_id: UUID,
    body: TaskUpdate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> TaskSuccessResponse | JSONResponse:
    request_id = get_request_id() or "-"
    repo = TaskRepository(session)
    service = TaskService(repo)

    try:
        task = await service.update_task(
            user_id=current_user.id,
            task_id=task_id,
            title=body.title,
            description=body.description,
            priority=body.priority,
            due_date=body.due_date,
            category=body.category,
            recurrence=body.recurrence,
        )
    except TaskNotFoundError:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "success": False,
                "error": {
                    "code": "TASK_NOT_FOUND",
                    "message": str(TaskNotFoundError()),
                    "request_id": request_id,
                },
            },
        )
    except InvalidTaskError:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "error": {
                    "code": "INVALID_TASK",
                    "message": str(InvalidTaskError()),
                    "request_id": request_id,
                },
            },
        )

    try:
        await session.commit()
    except Exception:
        await session.rollback()
        logger.exception(
            "Failed to persist task update",
            extra={"request_id": request_id},
        )
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "success": False,
                "error": {
                    "code": "TASK_PERSISTENCE_ERROR",
                    "message": "Task data could not be saved.",
                    "request_id": request_id,
                },
            },
        )

    return TaskSuccessResponse(
        message="Task updated successfully.",
        data=TaskData.from_domain(task),
    )
