"use client"

import { useEffect, useState, useRef } from "react"
import { GreetingCard } from "@/components/dashboard/greeting-card"
import { StatCard } from "@/components/dashboard/stat-card"
import { WeeklyChart } from "@/components/dashboard/weekly-chart"
import { NutritionProfileOnboarding } from "@/components/dashboard/nutrition-profile-onboarding"
import { AIInsightCard } from "@/components/dashboard/ai-insight-card"
import { QuickActions } from "@/components/dashboard/quick-actions"
import { MetricRing } from "@/components/dashboard/metric-ring"
import { ModuleCard } from "@/components/dashboard/module-card"
import { InsightBanner } from "@/components/dashboard/insight-banner"
import { DailyProtocol } from "@/components/dashboard/daily-protocol"
import { ActivityFeed, type ActivityEntry } from "@/components/dashboard/activity-feed"
import { GlobalSearch } from "@/components/dashboard/global-search"
import { GoalProgressWidget } from "@/components/dashboard/goal-progress-widget"
import { TaskProgressWidget } from "@/components/dashboard/task-progress-widget"
import { Card } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { useAuth } from "@/contexts/auth-context"
import { useNutritionProfile } from "@/hooks/use-nutrition-profile"
import { useDailyNutritionLogs } from "@/hooks/use-daily-nutrition-logs"
import { useBodyWeight } from "@/hooks/use-body-weight"
import { listGoals } from "@/services/api/goals"
import { listTasks } from "@/services/api/tasks"
import { getDailyNutritionLogSummary } from "@/services/api/nutrition-logs"
import { getLocalCalendarDate } from "@/lib/dates"
import {
  Flame, Droplets, Weight, UtensilsCrossed, TrendingDown,
  Moon,
} from "lucide-react"
import { formatDecimalWhole, formatDecimal } from "@/lib/format"
import type { GoalData } from "@/types/goals"
import type { TaskData } from "@/types/tasks"

const dayLabels = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

function getLast7Days(): { date: string; label: string }[] {
  const days: { date: string; label: string }[] = []
  for (let i = 6; i >= 0; i--) {
    const d = new Date()
    d.setDate(d.getDate() - i)
    days.push({ date: getLocalCalendarDate(d), label: dayLabels[d.getDay()] })
  }
  return days
}

export default function DashboardPage() {
  const { user } = useAuth()
  const {
    profileStatus, calculationsStatus, calculations, calculationsError,
    loadProfile, profile,
  } = useNutritionProfile()

  const {
    summary, summaryStatus, reloadAll: reloadLogs, entries: mealEntries, entriesStatus,
  } = useDailyNutritionLogs()

  const {
    entries: weightEntries, trend, reloadAll: reloadWeight,
  } = useBodyWeight()

  const [goals, setGoals] = useState<GoalData[]>([])
  const [goalsLoading, setGoalsLoading] = useState(true)
  const [goalsError, setGoalsError] = useState<string | null>(null)

  const [tasks, setTasks] = useState<TaskData[]>([])
  const [tasksLoading, setTasksLoading] = useState(true)
  const [tasksError, setTasksError] = useState<string | null>(null)

  const [weeklyCalorieData, setWeeklyCalorieData] = useState<{ label: string; value: number }[]>([])
  const [weeklyCaloriesLoading, setWeeklyCaloriesLoading] = useState(true)

  const [activityEntries, setActivityEntries] = useState<ActivityEntry[]>([])

  const [initialLoad, setInitialLoad] = useState(true)
  const [range, setRange] = useState<"Day" | "Week" | "Month">("Day")

  const goalsFetchedRef = useRef(false)
  const tasksFetchedRef = useRef(false)
  const weeklyFetchedRef = useRef(false)

  useEffect(() => {
    loadProfile()
    reloadLogs()
    reloadWeight()
    const timer = setTimeout(() => setInitialLoad(false), 300)
    return () => clearTimeout(timer)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    if (goalsFetchedRef.current) {
      setGoalsLoading(false)
      return
    }
    goalsFetchedRef.current = true
    const controller = new AbortController()
    setGoalsLoading(true)
    listGoals().then(res => {
      if (controller.signal.aborted) return
      if (res.success) {
        setGoals(res.data.goals)
      } else {
        setGoalsError(res.error.message)
      }
      setGoalsLoading(false)
    })
    return () => controller.abort()
  }, [])

  useEffect(() => {
    if (tasksFetchedRef.current) {
      setTasksLoading(false)
      return
    }
    tasksFetchedRef.current = true
    const controller = new AbortController()
    setTasksLoading(true)
    listTasks().then(res => {
      if (controller.signal.aborted) return
      if (res.success) {
        setTasks(res.data.tasks || [])
      } else {
        setTasksError(res.error.message)
      }
      setTasksLoading(false)
    })
    return () => controller.abort()
  }, [])

  useEffect(() => {
    const handleVisibility = () => {
      if (document.visibilityState === "visible") {
        loadProfile()
        reloadLogs()
        reloadWeight()
      }
    }
    document.addEventListener("visibilitychange", handleVisibility)
    return () => document.removeEventListener("visibilitychange", handleVisibility)
  }, [loadProfile, reloadLogs, reloadWeight])

  useEffect(() => {
    if (weeklyFetchedRef.current) {
      setWeeklyCaloriesLoading(false)
      return
    }
    weeklyFetchedRef.current = true
    const controller = new AbortController()
    setWeeklyCaloriesLoading(true)
    const days = getLast7Days()
    Promise.allSettled(
      days.map(d => getDailyNutritionLogSummary(d.date)),
    ).then(results => {
      if (controller.signal.aborted) return
      const data = days.map((d, i) => {
        const result = results[i]
        let calories = 0
        if (result.status === 'fulfilled' && result.value.success && result.value.data.totals) {
          calories = Number(result.value.data.totals.calories_kcal) || 0
        }
        return { label: d.label, value: calories }
      })
      setWeeklyCalorieData(data)
      setWeeklyCaloriesLoading(false)
    })
    return () => controller.abort()
  }, [])

  useEffect(() => {
    const activities: ActivityEntry[] = []

    for (const entry of mealEntries) {
      activities.push({
        id: `food-${entry.entry_id}`,
        category: "Food",
        title: entry.food_name,
        detail: `${formatDecimalWhole(entry.calories_kcal)} kcal`,
      })
    }

    const recentWeights = weightEntries.slice(-3)
    for (const entry of recentWeights) {
      activities.push({
        id: `weight-${entry.entry_id}`,
        category: "Weight",
        title: `${formatDecimal(entry.weight_kg)} kg`,
        detail: entry.logged_date,
      })
    }

    const completedTasks = tasks
      .filter(t => t.status === "completed" && t.completed_at)
      .slice(-3)
    for (const task of completedTasks) {
      activities.push({
        id: `task-${task.task_id}`,
        category: "Task",
        title: task.title,
        detail: task.completed_at
          ? new Date(task.completed_at).toLocaleDateString()
          : "",
      })
    }

    setActivityEntries(activities.length > 0 ? activities : [])
  }, [mealEntries, weightEntries, tasks])

  const displayName = user?.email?.split("@")[0] || "there"
  const hasCalculations = calculationsStatus === "available" && calculations
  const hasProfile = profileStatus === "available" && profile
  const isProfileIncomplete = profileStatus === "missing" || (calculationsStatus === "available" && calculations === null && hasProfile)

  const consumedCalories = summary?.totals?.calories_kcal ? Number(summary.totals.calories_kcal) : 0
  const calorieTarget = profile?.daily_calorie_goal ? profile.daily_calorie_goal : (hasCalculations ? Number(calculations!.targets.calorie_target_kcal_per_day) : 2400)

  const proteinTarget = profile?.daily_protein_goal_g ? profile.daily_protein_goal_g : (hasCalculations ? Number(calculations!.targets.protein_g_per_day) : 180)

  const proteinCurrent = summary?.totals?.protein_g ? Number(summary.totals.protein_g) : 0

  const latestWeight = weightEntries.length > 0 ? weightEntries[weightEntries.length - 1] : null
  const weightChange = trend?.absolute_change_kg ? Number(trend.absolute_change_kg) : null
  const weightTrendPositive = weightChange !== null ? weightChange < 0 : true

  const waterGoalMl = profile?.water_goal_ml ?? null
  const waterGoalL = waterGoalMl !== null ? waterGoalMl / 1000 : null

  const sleepGoalHours = profile?.sleep_goal_hours ?? null

  const activeGoals = goals.filter(g => g.status === "active")
  const avgGoalProgress = activeGoals.length > 0
    ? Math.round(activeGoals.reduce((sum, g) => sum + Number(g.progress_percentage || 0), 0) / activeGoals.length)
    : 0

  function buildInsight(): { quote: string; mealTitle: string } {
    if (!hasProfile || isProfileIncomplete) {
      return {
        quote: "Set up your nutrition profile to unlock personalized AI insights and recommendations.",
        mealTitle: "Complete your profile",
      }
    }
    if (mealEntries.length === 0 && weightEntries.length === 0) {
      return {
        quote: "Start logging meals and weight data so our AI can give you tailored nutrition advice.",
        mealTitle: "Log your first meal",
      }
    }
    if (consumedCalories === 0) {
      return {
        quote: "No meals logged today. Track your food intake to get real-time AI feedback on your nutrition.",
        mealTitle: "Log today's meals",
      }
    }
    if (activeGoals.length > 0) {
      return {
        quote: `You're ${avgGoalProgress}% toward your "${activeGoals[0].title}" goal. Keep up the momentum!`,
        mealTitle: activeGoals[0].title,
      }
    }
    return {
      quote: "Great work tracking your nutrition! Your AI insights will improve as you log more data.",
      mealTitle: `${formatDecimalWhole(String(consumedCalories))} kcal today`,
    }
  }

  const insight = buildInsight()

  const isLoading = initialLoad || profileStatus === "loading" || calculationsStatus === "loading" || summaryStatus === "loading" || entriesStatus === "loading"

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton variant="rectangular" className="h-44" />
        <Skeleton variant="rectangular" className="h-10 w-80" />
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} variant="rectangular" className="h-28" />
          ))}
        </div>
        <div className="grid gap-6 lg:grid-cols-12">
          <Skeleton variant="rectangular" className="h-80 lg:col-span-8" />
          <Skeleton variant="rectangular" className="h-80 lg:col-span-4" />
        </div>
      </div>
    )
  }

  if (isProfileIncomplete) {
    return (
      <div className="space-y-6">
        <GreetingCard name={displayName} />
        <GlobalSearch />

        <div className="flex flex-col lg:flex-row gap-6 items-start">
          <div className="flex-1 min-w-0 flex flex-col gap-6">
            <NutritionProfileOnboarding delay={0.1} />
            <ActivityFeed entries={[]} delay={0.3} />
          </div>
          <div className="w-full lg:w-80 flex flex-col gap-6 lg:shrink-0">
            <QuickActions />
            <AIInsightCard profileStatus={profileStatus} hasWeight={weightEntries.length > 0} />
            <DailyProtocol items={[]} delay={0.35} />
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <GreetingCard name={displayName} />
      <GlobalSearch />

      <div className="flex items-center gap-1 rounded-xl border border-border bg-surface-high/40 p-1 w-fit">
        {(["Day", "Week", "Month"] as const).map((r) => (
          <button
            key={r}
            type="button"
            onClick={() => setRange(r)}
            className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-colors ${range === r ? "bg-brand-primary/10 text-brand-primary" : "text-primary-muted hover:text-primary"
              }`}
            aria-pressed={range === r}
          >
            {r}
          </button>
        ))}
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        <StatCard label="Calories" value={hasCalculations ? formatDecimalWhole(String(calorieTarget)) : "—"} unit="kcal/day" icon={<Flame className="h-5 w-5" />} color="brand" delay={0.05} />
        <StatCard label="Protein Target" value={hasCalculations ? formatDecimal(String(proteinTarget)) : "—"} unit="g/day" icon={<UtensilsCrossed className="h-5 w-5" />} color="info" delay={0.1} />
        <StatCard label="Hydration" value={waterGoalL !== null ? String(waterGoalL) : "—"} unit="L" icon={<Droplets className="h-5 w-5" />} color="info" delay={0.15} />
        <StatCard label="Sleep Goal" value={sleepGoalHours !== null ? formatDecimal(sleepGoalHours) : "—"} unit="hours" icon={<Moon className="h-5 w-5" />} color="info" delay={0.175} />
        <StatCard label="Weight" value={latestWeight ? formatDecimal(String(latestWeight.weight_kg)) : "—"} unit="kg" icon={<Weight className="h-5 w-5" />} color="warning" trend={weightChange !== null ? { value: `${Math.abs(weightChange).toFixed(1)} kg`, positive: weightTrendPositive } : undefined} delay={0.2} />
      </div>

      <div className="flex flex-col lg:flex-row gap-6 items-start">
        <div className="lg:flex-[4]">
          <Card className="p-5 card-hover">
                <MetricRing value={consumedCalories} max={calorieTarget} centerValue={consumedCalories > 0 ? formatDecimalWhole(String(consumedCalories)) : "—"} centerUnit="kcal" footerLabel="Daily Budget" footerValue={formatDecimalWhole(String(calorieTarget))} delay={0.1} />
              </Card>
        </div>

        <div className="grid gap-4 sm:grid-cols-3 lg:flex-[8]">
          <ModuleCard title="Protein Intake" icon={UtensilsCrossed} badge="+12% vs avg" value={`${Math.round(proteinCurrent)} / ${Math.round(proteinTarget)}g`} progress={{ value: proteinCurrent, max: proteinTarget, variant: "default" }} delay={0.15} />
          <ModuleCard title="Hydration Level" icon={Droplets} iconClassName="text-info bg-info-light" value={waterGoalL !== null ? `0 / ${waterGoalL}L` : "—"} progress={waterGoalL !== null ? { value: 0, max: waterGoalL, variant: "default" } : undefined} delay={0.2} />
          <ModuleCard title="Body Weight" icon={TrendingDown} iconClassName="text-warning bg-warning-light" value={latestWeight ? `${formatDecimal(latestWeight.weight_kg)} kg` : "—"} note={latestWeight ? "Target: 75.0kg" : "No entries yet"} delay={0.25} />
        </div>
      </div>

      <div className="flex flex-col lg:flex-row gap-6 items-start">
        <div className="flex-1 min-w-0">
          {weeklyCaloriesLoading ? (
            <Skeleton variant="rectangular" className="h-64" />
          ) : (
            <WeeklyChart title="Weekly Calorie Intake" description="Your daily calorie consumption this week" data={weeklyCalorieData} />
          )}
          {calculationsStatus === "error" && (
            <div className="rounded-xl border border-border bg-surface p-6 text-center">
              <p className="text-sm font-semibold text-error">Could not load targets</p>
              <p className="text-xs text-primary-secondary mt-1">{calculationsError || "An error occurred loading nutrition targets."}</p>
            </div>
          )}
        </div>
        <div className="w-full lg:w-80 lg:shrink-0">
          {weightEntries.length === 0 ? (
            <AIInsightCard profileStatus={profileStatus} hasWeight={false} />
          ) : (
            <InsightBanner quote={insight.quote} mealTitle={insight.mealTitle} delay={0.3} />
          )}
        </div>
      </div>

      <div className="flex flex-col lg:flex-row gap-6 items-start">
        <div className="flex-1 min-w-0">
          <ActivityFeed entries={activityEntries} delay={0.3} />
        </div>
        <div className="w-full lg:w-80 lg:shrink-0">
          <DailyProtocol items={[]} delay={0.35} />
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
        <GoalProgressWidget goals={goals} loading={goalsLoading} error={goalsError} />
        <TaskProgressWidget tasks={tasks} loading={tasksLoading} error={tasksError} />
        <QuickActions />
      </div>
    </div>
  )
}
