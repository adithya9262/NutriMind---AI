"use client"

import { CheckCircle2, Plus } from "lucide-react"
import Link from "next/link"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { ErrorState } from "@/components/ui/error-state"
import { Skeleton } from "@/components/ui/skeleton"
import type { TaskData } from "@/types/tasks"

interface TaskProgressWidgetProps {
  tasks: TaskData[]
  loading: boolean
  error: string | null
}

function calculateStreak(tasks: TaskData[]): number {
  const completedDates = tasks
    .filter(t => t.status === "completed" && t.completed_at)
    .map(t => t.completed_at!.split("T")[0])
  const unique = [...new Set(completedDates)].sort().reverse()
  if (unique.length === 0) return 0
  const today = new Date().toISOString().split("T")[0]
  const latest = unique[0]
  const diff = Math.floor(
    (new Date(today + "T12:00:00").getTime() - new Date(latest + "T12:00:00").getTime()) /
      (1000 * 60 * 60 * 24),
  )
  if (diff > 1) return 0
  let streak = 1
  for (let i = 1; i < unique.length; i++) {
    const prevDate = new Date(unique[i - 1] + "T12:00:00")
    const currDate = new Date(unique[i] + "T12:00:00")
    const dayDiff = (prevDate.getTime() - currDate.getTime()) / (1000 * 60 * 60 * 24)
    if (dayDiff === 1) streak++
    else break
  }
  return streak
}

export function TaskProgressWidget({ tasks, loading, error }: TaskProgressWidgetProps) {
  if (loading) return <Skeleton variant="rectangular" className="h-24" />
  if (error) return <ErrorState title="Could not load tasks" message={error} />

  if (tasks.length === 0) {
    return (
      <Card className="p-5 card-hover text-center">
        <div className="flex flex-col items-center gap-2 py-3">
          <div className="p-2.5 rounded-full bg-success-light">
            <CheckCircle2 className="h-5 w-5 text-success" aria-hidden="true" />
          </div>
          <p className="text-sm font-semibold text-primary">No tasks yet</p>
          <p className="text-xs text-primary-secondary">Build healthy habits with daily tasks</p>
          <Link href="/tasks">
            <Button variant="primary" size="sm" className="mt-1">
              <Plus className="h-3.5 w-3.5" />
              Create Task
            </Button>
          </Link>
        </div>
      </Card>
    )
  }

  const totalTaskCount = tasks.length
  const completedTaskCount = tasks.filter(t => t.status === "completed").length
  const taskCompletionPct = totalTaskCount > 0 ? Math.round((completedTaskCount / totalTaskCount) * 100) : 0
  const streak = calculateStreak(tasks)

  return (
    <Card className="p-5 card-hover">
      <div className="flex items-center gap-2 mb-3">
        <CheckCircle2 className="h-4 w-4 text-success" aria-hidden="true" />
        <h3 className="text-sm font-semibold text-primary">Task Progress</h3>
      </div>
      <div className="flex items-baseline gap-2">
        <span className="text-2xl font-bold text-primary">{taskCompletionPct}%</span>
        <span className="text-xs text-primary-muted">complete</span>
      </div>
      <p className="text-xs text-primary-muted mt-1">
        {completedTaskCount} / {totalTaskCount} tasks done
      </p>
      {streak > 0 && (
        <p className="text-xs font-medium text-brand-primary mt-1">
          {streak}-day streak
        </p>
      )}
    </Card>
  )
}
