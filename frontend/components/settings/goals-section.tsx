"use client"

import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Spinner } from "@/components/ui/spinner"
import { Calendar, Target, Trophy } from "lucide-react"
import type { GoalData } from "@/types/goals"

interface GoalsSectionProps {
  goals: GoalData[]
  listStatus: string
  onNavigateToGoal: () => void
}

export function GoalsSection({ goals, listStatus, onNavigateToGoal }: GoalsSectionProps) {
  const activeGoals = goals.filter((g) => g.status === "active").length
  const completedGoals = goals.filter((g) => g.status === "completed").length

  return (
    <Card className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-base font-semibold text-primary">Your Goals</h3>
          <p className="text-sm text-primary-secondary mt-0.5">Track and manage your nutrition goals</p>
        </div>
        <Button variant="secondary" onClick={onNavigateToGoal}>
          <Target className="h-4 w-4" />
          New Goal
        </Button>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="rounded-xl border border-border bg-bg p-4 flex items-center gap-3">
          <div className="h-10 w-10 rounded-full bg-brand-light flex items-center justify-center">
            <Calendar className="h-5 w-5 text-brand" />
          </div>
          <div>
            <p className="text-2xl font-bold text-primary">{activeGoals}</p>
            <p className="text-xs text-primary-secondary">Active Goals</p>
          </div>
        </div>
        <div className="rounded-xl border border-border bg-bg p-4 flex items-center gap-3">
          <div className="h-10 w-10 rounded-full bg-success-light flex items-center justify-center">
            <Trophy className="h-5 w-5 text-success" />
          </div>
          <div>
            <p className="text-2xl font-bold text-primary">{completedGoals}</p>
            <p className="text-xs text-primary-secondary">Completed</p>
          </div>
        </div>
      </div>

      {listStatus === "loading" ? (
        <div className="flex justify-center py-6">
          <Spinner />
        </div>
      ) : listStatus === "error" ? (
        <div className="text-center py-8">
          <p className="text-sm text-red-500">Failed to load goals. Please try again.</p>
        </div>
      ) : listStatus === "empty" ? (
        <div className="text-center py-8">
          <Target className="h-10 w-10 text-primary-muted mx-auto mb-2" />
          <p className="text-sm text-primary-secondary">No goals yet. Create your first goal!</p>
        </div>
      ) : (
        <div className="space-y-3">
          {goals.slice(0, 5).map((g) => (
            <div key={g.id} className="flex flex-col gap-2 rounded-xl border border-border bg-bg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-primary">{g.title}</p>
                  <Badge variant={g.status === "completed" ? "success" : g.status === "active" ? "brand" : "default"}>
                    {g.status}
                  </Badge>
                </div>
              </div>
              {g.progress_percentage && (
                <Progress
                  value={Number(g.progress_percentage)}
                  variant={Number(g.progress_percentage) >= 100 ? "success" : "default"}
                  size="sm"
                />
              )}
            </div>
          ))}
          {goals.length > 5 && (
            <Button variant="ghost" size="sm" className="w-full" onClick={onNavigateToGoal}>
              View all {goals.length} goals
            </Button>
          )}
        </div>
      )}
    </Card>
  )
}
