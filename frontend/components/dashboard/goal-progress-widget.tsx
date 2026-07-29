"use client"

import { Target, Plus } from "lucide-react"
import Link from "next/link"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { ErrorState } from "@/components/ui/error-state"
import { Skeleton } from "@/components/ui/skeleton"
import type { GoalData } from "@/types/goals"

interface GoalProgressWidgetProps {
  goals: GoalData[]
  loading: boolean
  error: string | null
}

export function GoalProgressWidget({ goals, loading, error }: GoalProgressWidgetProps) {
  const activeGoals = goals.filter(g => g.status === "active")

  if (loading) return <Skeleton variant="rectangular" className="h-32" />
  if (error) return <ErrorState title="Could not load goals" message={error} />

  if (activeGoals.length === 0) {
    return (
      <Card className="p-5 card-hover text-center">
        <div className="flex flex-col items-center gap-2 py-3">
          <div className="p-2.5 rounded-full bg-brand-light">
            <Target className="h-5 w-5 text-brand" aria-hidden="true" />
          </div>
          <p className="text-sm font-semibold text-primary">No active goals</p>
          <p className="text-xs text-primary-secondary">Set nutrition goals to track your progress</p>
          <Link href="/goals">
            <Button variant="primary" size="sm" className="mt-1">
              <Plus className="h-3.5 w-3.5" />
              Create Goal
            </Button>
          </Link>
        </div>
      </Card>
    )
  }

  return (
    <Card className="p-5 card-hover">
      <div className="flex items-center gap-2 mb-3">
        <Target className="h-4 w-4 text-brand-primary" aria-hidden="true" />
        <h3 className="text-sm font-semibold text-primary">Goal Progress</h3>
      </div>
      <div className="space-y-3">
        {activeGoals.slice(0, 3).map(goal => (
          <div key={goal.id}>
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs font-medium text-primary truncate">{goal.title}</span>
              <span className="text-xs text-primary-muted shrink-0 ml-2">
                {goal.progress_percentage ? `${Math.round(Number(goal.progress_percentage))}%` : "—"}
              </span>
            </div>
            {goal.progress_percentage && (
              <div
                className="h-1.5 w-full rounded-full bg-surface-high overflow-hidden"
                role="progressbar"
                aria-valuenow={Math.round(Number(goal.progress_percentage))}
                aria-valuemin={0}
                aria-valuemax={100}
                aria-label={`${goal.title}: ${Math.round(Number(goal.progress_percentage))}% complete`}
              >
                <div
                  className="h-full rounded-full bg-brand-primary transition-all duration-500"
                  style={{ width: `${Math.min(Number(goal.progress_percentage), 100)}%` }}
                />
              </div>
            )}
          </div>
        ))}
      </div>
    </Card>
  )
}
