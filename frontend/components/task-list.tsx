"use client";

import { CheckSquare } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { TaskCard } from "@/components/task-card";
import type {
  TaskData,
  TaskListStatus,
  TaskActionStatus,
} from "@/types/tasks";

interface TaskListProps {
  tasks: TaskData[];
  listStatus: TaskListStatus;
  listError: string | null;
  actionStatus: TaskActionStatus;
  actionTaskId: string | null;
  onComplete: (taskId: string) => void;
  onReopen: (taskId: string) => void;
  onEdit?: (task: TaskData) => void;
  onDelete: (taskId: string) => void;
  onRetry: () => void;
}

export function TaskList({
  tasks,
  listStatus,
  listError,
  actionStatus,
  actionTaskId,
  onComplete,
  onReopen,
  onEdit,
  onDelete,
  onRetry,
}: TaskListProps) {
  if (listStatus === "loading") {
    return (
      <div
        className="flex items-center justify-center py-12"
        role="status"
        aria-label="Loading tasks"
      >
        <Spinner size="lg" />
      </div>
    );
  }

  if (listStatus === "error") {
    return (
      <ErrorState
        title="Failed to load tasks"
        message={listError ?? "An unexpected error occurred."}
        action={
          <Button variant="primary" size="sm" onClick={onRetry}>
            Retry
          </Button>
        }
      />
    );
  }

  if (listStatus === "empty") {
    return (
      <EmptyState
        icon={<CheckSquare className="h-8 w-8" aria-hidden="true" />}
        title="No tasks yet"
        description="Create your first task to get started."
      />
    );
  }

  const completing = actionStatus === "completing";
  const reopening = actionStatus === "reopening";
  const deleting = actionStatus === "deleting";

  return (
    <div className="space-y-3" role="list" aria-label="Task list">
      {tasks.map((task) => (
        <div key={task.task_id} role="listitem">
          <TaskCard
            task={task}
            onComplete={onComplete}
            onReopen={onReopen}
            onEdit={onEdit}
            onDelete={onDelete}
            completing={completing}
            reopening={reopening}
            deleting={deleting}
            isActionTarget={actionTaskId === task.task_id}
          />
        </div>
      ))}
    </div>
  );
}
