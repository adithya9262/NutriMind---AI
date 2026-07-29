"use client"

import { Card } from "@/components/ui/card"
import { cn } from "@/lib/utils"
import type { TaskData } from "@/types/tasks"

interface TaskProgressProps {
  tasks: TaskData[]
  className?: string
}

export function TaskProgress({ tasks, className }: TaskProgressProps) {
  const total = tasks.length
  const completed = tasks.filter((t) => t.status === "completed").length
  const percentage = total > 0 ? Math.round((completed / total) * 100) : 0
  const radius = 52
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (percentage / 100) * circumference

  return (
    <Card className={cn("p-5 flex items-center gap-5", className)}>
      <div className="relative w-28 h-28 shrink-0">
        <svg className="w-full h-full -rotate-90" viewBox="0 0 120 120">
          <circle
            className="text-white/5"
            cx="60"
            cy="60"
            fill="transparent"
            r={radius}
            stroke="currentColor"
            strokeWidth="10"
          />
          <circle
            className="text-brand transition-all duration-500"
            cx="60"
            cy="60"
            fill="transparent"
            r={radius}
            stroke="currentColor"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
            strokeWidth="10"
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-2xl font-bold text-primary">{percentage}%</span>
          <span className="text-[10px] uppercase tracking-wider text-primary-muted">
            Done
          </span>
        </div>
      </div>
      <div className="flex-1">
        <p className="text-sm font-semibold text-primary">Progress Overview</p>
        <p className="text-xs text-primary-secondary mt-1">
          {completed} of {total} tasks completed
        </p>
        <div className="mt-3 h-2 w-full rounded-full bg-white/5 overflow-hidden">
          <div
            className="h-full rounded-full bg-brand transition-all duration-500"
            style={{ width: `${percentage}%` }}
            role="progressbar"
            aria-valuenow={percentage}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-label={`${percentage}% of tasks completed`}
          />
        </div>
      </div>
    </Card>
  )
}
