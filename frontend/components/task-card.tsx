"use client";

import { CheckCircle, RotateCcw, Trash2, Calendar, Repeat, Pencil } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  PRIORITY_LABELS,
  PRIORITY_VARIANTS,
  STATUS_LABELS,
  STATUS_VARIANTS,
  TASK_CATEGORY_LABELS,
  TASK_RECURRENCE_LABELS,
  CATEGORY_VARIANTS,
  RECURRENCE_VARIANTS,
  type TaskData,
} from "@/types/tasks";

interface TaskCardProps {
  task: TaskData;
  onComplete: (taskId: string) => void;
  onReopen: (taskId: string) => void;
  onEdit?: (task: TaskData) => void;
  onDelete: (taskId: string) => void;
  completing: boolean;
  reopening: boolean;
  deleting: boolean;
  isActionTarget: boolean;
}

function formatDate(dateStr: string): string {
  const d = new Date(dateStr);
  return d.toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export function TaskCard({
  task,
  onComplete,
  onReopen,
  onEdit,
  onDelete,
  completing,
  reopening,
  deleting,
  isActionTarget,
}: TaskCardProps) {
  const isPending = task.status === "pending";
  const showLoader = isActionTarget && (completing || reopening || deleting);

  return (
    <Card
      className={`p-4 space-y-3 card-hover ${task.status === "completed" ? "opacity-70" : ""}`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            {task.status === "completed" && (
              <CheckCircle className="h-4 w-4 text-success shrink-0" aria-hidden="true" />
            )}
            <h3
              className={`text-sm font-medium break-words ${
                task.status === "completed"
                  ? "text-primary-muted line-through"
                  : "text-primary"
              }`}
            >
              {task.title}
            </h3>
          </div>
          {task.description && (
            <p className="mt-1.5 text-sm text-primary-secondary whitespace-pre-wrap break-words">
              {task.description}
            </p>
          )}
          <div className="flex items-center gap-1.5 mt-2">
            {task.category && (
              <Badge variant={CATEGORY_VARIANTS[task.category]}>
                {TASK_CATEGORY_LABELS[task.category]}
              </Badge>
            )}
            {task.recurrence && task.recurrence !== "none" && (
              <Badge variant={RECURRENCE_VARIANTS[task.recurrence]}>
                <Repeat className="h-3 w-3 mr-0.5" aria-hidden="true" />
                {TASK_RECURRENCE_LABELS[task.recurrence]}
              </Badge>
            )}
          </div>
        </div>
        <div className="flex items-center gap-1.5 shrink-0">
          <Badge variant={PRIORITY_VARIANTS[task.priority]}>
            {PRIORITY_LABELS[task.priority]}
          </Badge>
          <Badge variant={STATUS_VARIANTS[task.status]}>
            {STATUS_LABELS[task.status]}
          </Badge>
        </div>
      </div>

      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-3 text-xs text-primary-muted">
          {task.due_date && (
            <span className="inline-flex items-center gap-1">
              <Calendar className="h-3 w-3" aria-hidden="true" />
              {formatDate(task.due_date)}
            </span>
          )}
          {task.completed_at && (
            <span>Completed: {formatDate(task.completed_at)}</span>
          )}
        </div>

        <div className="flex items-center gap-1">
          {isPending ? (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onComplete(task.task_id)}
              disabled={showLoader}
              aria-label={`Complete "${task.title}"`}
            >
              {showLoader ? (
                <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-border border-t-brand" />
              ) : (
                <CheckCircle className="h-4 w-4 text-success" aria-hidden="true" />
              )}
              <span className="ml-1 sr-only sm:not-sr-only">Complete</span>
            </Button>
          ) : (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onReopen(task.task_id)}
              disabled={showLoader}
              aria-label={`Reopen "${task.title}"`}
            >
              {showLoader ? (
                <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-border border-t-brand" />
              ) : (
                <RotateCcw className="h-4 w-4 text-primary-secondary" aria-hidden="true" />
              )}
              <span className="ml-1 sr-only sm:not-sr-only">Reopen</span>
            </Button>
          )}

          {onEdit && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onEdit(task)}
              disabled={showLoader}
              aria-label={`Edit "${task.title}"`}
            >
              <Pencil className="h-4 w-4 text-primary-secondary" aria-hidden="true" />
              <span className="ml-1 sr-only sm:not-sr-only">Edit</span>
            </Button>
          )}

          <Button
            variant="ghost"
            size="sm"
            onClick={() => onDelete(task.task_id)}
            disabled={showLoader}
            aria-label={`Delete "${task.title}"`}
          >
            <Trash2 className="h-4 w-4 text-[var(--color-error)]" aria-hidden="true" />
            <span className="ml-1 sr-only sm:not-sr-only">Delete</span>
          </Button>
        </div>
      </div>
    </Card>
  );
}
