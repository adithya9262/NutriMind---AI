from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.task_exceptions import DuplicateTaskIdError
from app.core.tasks import Task as DomainTask
from app.models.task import Task as TaskORM


def _is_unique_constraint_violation(
    exc: IntegrityError,
    constraint_name: str,
) -> bool:
    """Check if an IntegrityError is caused by a specific named constraint."""
    orig = exc.orig
    if orig is None:
        return False
    if hasattr(orig, "constraint_name"):
        return orig.constraint_name == constraint_name
    return constraint_name in str(orig)


class TaskRepository:
    """Repository for Task database operations.

    Encapsulates user-scoped reads, creation, mutation, and deletion of
    task rows.  Does not commit, roll back, or close the session; the
    caller (a future API layer) owns transaction boundaries.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_user_id(
        self,
        *,
        user_id: uuid.UUID,
    ) -> list[TaskORM]:
        """List tasks for one user.

        Returns all tasks owned by ``user_id`` in a stable deterministic
        database order (task_id ascending).  The service applies the frozen
        domain ordering on top of this tie-safe retrieval contract.
        Returns an empty list when no tasks exist.
        Does not commit, flush, roll back, or close the session.
        """
        stmt = select(TaskORM).where(TaskORM.user_id == user_id).order_by(TaskORM.task_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_user_and_task_id(
        self,
        *,
        user_id: uuid.UUID,
        task_id: uuid.UUID,
    ) -> TaskORM | None:
        """Look up a task by both user_id and task_id.

        Returns the Task ORM object when found, or None when not found or
        when the task is owned by a different user.  Never queries by
        task_id alone.
        Does not commit, flush, roll back, or close the session.
        """
        stmt = select(TaskORM).where(TaskORM.user_id == user_id).where(TaskORM.task_id == task_id)
        result = await self._session.execute(stmt)
        return result.scalars().one_or_none()

    async def create(
        self,
        *,
        user_id: uuid.UUID,
        task: DomainTask,
    ) -> TaskORM:
        """Create and persist a new task.

        Accepts a trusted user_id and an already-validated domain Task.
        The public ``task_id`` is caller/domain owned and is persisted
        exactly as supplied.  Adds the Task to the session and flushes.
        The caller owns transaction commit/rollback.

        Raises ``DuplicateTaskIdError`` on a duplicate
        (user_id, task_id) composite.
        """
        orm_task = TaskORM(
            user_id=user_id,
            task_id=task.task_id,
            title=task.title,
            description=task.description,
            priority=task.priority,
            status=task.status,
            due_date=task.due_date,
            completed_at=task.completed_at,
            category=task.category,
            recurrence=task.recurrence,
        )
        self._session.add(orm_task)
        try:
            await self._session.flush()
        except IntegrityError as exc:
            if _is_unique_constraint_violation(exc, "uq_tasks_user_id_task_id"):
                raise DuplicateTaskIdError() from exc
            raise
        return orm_task

    async def update(
        self,
        *,
        task: TaskORM,
    ) -> TaskORM:
        """Persist tracked changes to an already loaded Task ORM object.

        Flushes pending changes for the supplied tracked object.  The
        caller performs mutation of allowed fields before invoking this
        method.  The caller owns transaction commit/rollback.
        """
        await self._session.flush()
        return task

    async def delete(
        self,
        *,
        task: TaskORM,
    ) -> None:
        """Delete an existing task.

        Deletes the exact supplied ORM object and flushes.  The caller
        owns transaction commit/rollback.
        """
        await self._session.delete(task)
        await self._session.flush()
