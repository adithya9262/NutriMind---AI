"use client"

import { TaskStatistics } from "@/components/tasks/task-statistics"
import { TaskSummary } from "@/components/tasks/task-summary"
import type { TaskData } from "@/types/tasks"

interface TaskOverviewProps {
  tasks: TaskData[]
}

export function TaskOverview({ tasks }: TaskOverviewProps) {
  return (
    <div className="space-y-4">
      <TaskStatistics tasks={tasks} />
      <TaskSummary tasks={tasks} />
    </div>
  )
}
