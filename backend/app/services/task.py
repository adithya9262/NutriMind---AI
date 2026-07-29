from __future__ import annotations

import uuid
from datetime import datetime

from app.core.task_exceptions import TaskNotFoundError
from app.core.tasks import (
    Task,
    TaskCategory,
    TaskRecurrence,
    complete_task,
    order_tasks,
    reopen_task,
    update_task,
)
from app.models.task import Task as TaskORM
from app.repositories.task import TaskRepository


def _orm_to_domain(task: TaskORM) -> Task:
    """Convert a tracked Task ORM row to an immutable domain Task.

    Performs an exact field copy.  No IDs are generated, no text is
    modified, no timestamps are changed, and no system clock is consulted.
    """
    # Use getattr with defaults so that test mocks that do not explicitly set
    # category/recurrence (which have server_default in the real ORM) do not
    # cause validation errors.  In production the ORM always supplies these.
    raw_category = getattr(task, "category", None)
    raw_recurrence = getattr(task, "recurrence", None)
    category = raw_category if isinstance(raw_category, TaskCategory) else TaskCategory.CUSTOM
    recurrence = raw_recurrence if isinstance(raw_recurrence, TaskRecurrence) else TaskRecurrence.NONE
    return Task(
        task_id=task.task_id,
        title=task.title,
        description=task.description,
        priority=task.priority,
        status=task.status,
        due_date=task.due_date,
        completed_at=task.completed_at,
        category=category,
        recurrence=recurrence,
    )


class TaskService:
    """Service for task business logic.

    Encapsulates user-scoped task listing, lookup, creation, completion,
    reopening, and deletion workflows.  Reuses the frozen domain functions
    ``order_tasks``, ``complete_task``, and ``reopen_task`` rather than
    reimplementing their rules.  Framework-independent, database-framework
    independent, and transaction-free: it never imports the ORM layer or the
    session.
    """

    def __init__(self, repository: TaskRepository) -> None:
        self._repository = repository

    async def list_tasks(
        self,
        *,
        user_id: uuid.UUID,
    ) -> tuple[Task, ...]:
        """List tasks for one user in frozen deterministic order.

        Delegates the user-scoped lookup to the repository, converts the
        ORM rows to domain Tasks, and applies the frozen ``order_tasks``
        function exactly once.  Does not mutate caller inputs and does not
        consult the system clock.
        """
        orm_tasks = await self._repository.list_by_user_id(user_id=user_id)
        domain_tasks = [_orm_to_domain(task) for task in orm_tasks]
        return order_tasks(tasks=domain_tasks)

    async def get_task(
        self,
        *,
        user_id: uuid.UUID,
        task_id: uuid.UUID,
    ) -> Task:
        """Retrieve a single task by user and task ID.

        Raises ``TaskNotFoundError`` when the task does not exist or is not
        owned by the user.  Never performs an unscoped lookup.
        """
        orm_task = await self._repository.get_by_user_and_task_id(
            user_id=user_id,
            task_id=task_id,
        )
        if orm_task is None:
            raise TaskNotFoundError()
        return _orm_to_domain(orm_task)

    async def create_task(
        self,
        *,
        user_id: uuid.UUID,
        task: Task,
    ) -> Task:
        """Create a task for the given user.

        Delegates persistence to the repository, preserving the exact
        frozen domain values of ``task``.  Does not revalidate or
        reconstruct an already-valid domain Task.
        """
        orm_task = await self._repository.create(user_id=user_id, task=task)
        return _orm_to_domain(orm_task)

    async def complete_task(
        self,
        *,
        user_id: uuid.UUID,
        task_id: uuid.UUID,
        completed_at: datetime,
    ) -> Task:
        """Complete a task owned by the given user.

        Loads the task using both user_id and task_id, raises
        ``TaskNotFoundError`` when absent, converts the ORM row to a domain
        Task, and calls the frozen ``complete_task`` exactly once with the
        caller-provided ``completed_at``.  Applies only ``status`` and
        ``completed_at`` to the tracked ORM row and persists it through the
        repository.  The frozen ``TaskAlreadyCompletedError`` propagates
        unchanged.  No system-clock fallback is used.
        """
        orm_task = await self._repository.get_by_user_and_task_id(
            user_id=user_id,
            task_id=task_id,
        )
        if orm_task is None:
            raise TaskNotFoundError()
        domain = _orm_to_domain(orm_task)
        updated = complete_task(task=domain, completed_at=completed_at)
        orm_task.status = updated.status
        orm_task.completed_at = updated.completed_at
        await self._repository.update(task=orm_task)
        return _orm_to_domain(orm_task)

    async def update_task(
        self,
        *,
        user_id: uuid.UUID,
        task_id: uuid.UUID,
        title: str | None = None,
        description: str | None = None,
        priority: str | None = None, # TaskPriority enum type internally handled
        due_date: str | None = None,
        category: str | None = None,
        recurrence: str | None = None,
    ) -> Task:
        """Update a task owned by the given user.

        Loads the task using both user_id and task_id, raises
        ``TaskNotFoundError`` when absent, converts the ORM row to a domain
        Task, and calls the frozen ``update_task`` exactly once with the
        caller-provided fields. Applies the new domain values to the tracked
        ORM row and persists it through the repository.
        """
        orm_task = await self._repository.get_by_user_and_task_id(
            user_id=user_id,
            task_id=task_id,
        )
        if orm_task is None:
            raise TaskNotFoundError()
        domain = _orm_to_domain(orm_task)
        updated = update_task(
            task=domain,
            title=title,
            description=description,
            priority=priority,
            due_date=due_date,
            category=category,
            recurrence=recurrence,
        )
        
        orm_task.title = updated.title
        orm_task.description = updated.description
        orm_task.priority = updated.priority
        orm_task.due_date = updated.due_date
        orm_task.category = updated.category
        orm_task.recurrence = updated.recurrence
        
        await self._repository.update(task=orm_task)
        return _orm_to_domain(orm_task)

    async def reopen_task(
        self,
        *,
        user_id: uuid.UUID,
        task_id: uuid.UUID,
    ) -> Task:
        """Reopen a completed task owned by the given user.

        Loads the task using both user_id and task_id, raises
        ``TaskNotFoundError`` when absent, converts the ORM row to a domain
        Task, and calls the frozen ``reopen_task`` exactly once.  Applies
        only ``status`` (pending) and ``completed_at`` (None) to the tracked
        ORM row and persists it through the repository.  The frozen
        ``TaskNotCompletedError`` propagates unchanged.
        """
        orm_task = await self._repository.get_by_user_and_task_id(
            user_id=user_id,
            task_id=task_id,
        )
        if orm_task is None:
            raise TaskNotFoundError()
        domain = _orm_to_domain(orm_task)
        updated = reopen_task(task=domain)
        orm_task.status = updated.status
        orm_task.completed_at = updated.completed_at
        await self._repository.update(task=orm_task)
        return _orm_to_domain(orm_task)

    async def delete_task(
        self,
        *,
        user_id: uuid.UUID,
        task_id: uuid.UUID,
    ) -> None:
        """Delete a task owned by the given user.

        Verifies ownership by querying with both user_id and task_id,
        raises ``TaskNotFoundError`` when absent, and passes the loaded ORM
        object to the repository delete.  Never deletes by task_id alone.
        """
        orm_task = await self._repository.get_by_user_and_task_id(
            user_id=user_id,
            task_id=task_id,
        )
        if orm_task is None:
            raise TaskNotFoundError()
        await self._repository.delete(task=orm_task)
