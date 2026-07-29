"use client"

import { Card } from "@/components/ui/card"
import { TaskCard } from "@/components/task-card"
import type { TaskData, TaskPriority } from "@/types/tasks"
import { PRIORITY_LABELS } from "@/types/tasks"

interface TaskPriorityGroupProps {
  priority: TaskPriority
  tasks: TaskData[]
  actionStatus: "idle" | "completing" | "reopening" | "deleting" | "error" | "updating"
  actionTaskId: string | null
  onComplete: (taskId: string) => void
  onReopen: (taskId: string) => void
  onEdit?: (task: TaskData) => void
  onDelete: (taskId: string) => void
}

const priorityAccent: Record<TaskPriority, string> = {
  high: "bg-error-light text-error",
  medium: "bg-warning/15 text-warning",
  low: "bg-info/15 text-info",
}

export function TaskPriorityGroup({
  priority,
  tasks,
  actionStatus,
  actionTaskId,
  onComplete,
  onReopen,
  onEdit,
  onDelete,
}: TaskPriorityGroupProps) {
  const completed = tasks.filter((t) => t.status === "completed").length
  const total = tasks.length
  const percentage = total > 0 ? Math.round((completed / total) * 100) : 0

  return (
    <Card className="p-4">
      <div className="flex items-center justify-between gap-3 mb-3">
        <div className="flex items-center gap-2">
          <span
            className={`px-2 py-0.5 rounded-lg text-xs font-semibold ${priorityAccent[priority]}`}
          >
            {PRIORITY_LABELS[priority]}
          </span>
          <span className="text-xs text-primary-muted">
            {completed}/{total}
          </span>
        </div>
        <div className="h-1.5 w-24 rounded-full bg-white/5 overflow-hidden">
          <div
            className="h-full rounded-full bg-brand transition-all duration-500"
            style={{ width: `${percentage}%` }}
            role="progressbar"
            aria-valuenow={percentage}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-label={`${PRIORITY_LABELS[priority]} priority completion`}
          />
        </div>
      </div>
      <div className="space-y-2" role="list" aria-label={`${PRIORITY_LABELS[priority]} priority tasks`}>
        {tasks.map((task) => (
          <div key={task.task_id} role="listitem">
            <TaskCard
              task={task}
              onComplete={onComplete}
              onReopen={onReopen}
              onEdit={onEdit}
              onDelete={onDelete}
              completing={actionStatus === "completing"}
              reopening={actionStatus === "reopening"}
              deleting={actionStatus === "deleting"}
              isActionTarget={actionTaskId === task.task_id}
            />
          </div>
        ))}
      </div>
    </Card>
  )
}
