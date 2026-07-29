"use client"

import { CheckCircle2, ListTodo, AlertTriangle, CircleDashed } from "lucide-react"
import { Card } from "@/components/ui/card"
import { cn } from "@/lib/utils"
import type { TaskData } from "@/types/tasks"

interface TaskStatisticsProps {
  tasks: TaskData[]
  className?: string
}

export function TaskStatistics({ tasks, className }: TaskStatisticsProps) {
  const total = tasks.length
  const completed = tasks.filter((t) => t.status === "completed").length
  const pending = total - completed
  const highPriority = tasks.filter(
    (t) => t.priority === "high" && t.status === "pending",
  ).length

  const stats = [
    {
      label: "Total",
      value: total,
      icon: ListTodo,
      tone: "brand" as const,
    },
    {
      label: "Completed",
      value: completed,
      icon: CheckCircle2,
      tone: "success" as const,
    },
    {
      label: "Pending",
      value: pending,
      icon: CircleDashed,
      tone: "info" as const,
    },
    {
      label: "High Priority",
      value: highPriority,
      icon: AlertTriangle,
      tone: "warning" as const,
    },
  ]

  const toneClasses: Record<string, string> = {
    brand: "bg-brand-light text-brand",
    success: "bg-success-light text-success",
    info: "bg-info-light text-info",
    warning: "bg-warning-light text-warning",
  }

  return (
    <div className={cn("grid grid-cols-2 lg:grid-cols-4 gap-4", className)}>
      {stats.map((s) => {
        const Icon = s.icon
        return (
          <Card key={s.label} className="p-4 card-hover">
            <div className="flex items-center justify-between mb-3">
              <span className={cn("p-2 rounded-xl", toneClasses[s.tone])}>
                <Icon className="h-4 w-4" aria-hidden="true" />
              </span>
            </div>
            <p className="text-xs font-medium text-primary-muted uppercase tracking-wider">
              {s.label}
            </p>
            <p className="text-2xl font-bold text-primary mt-1">{s.value}</p>
          </Card>
        )
      })}
    </div>
  )
}
