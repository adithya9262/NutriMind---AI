"use client"

import { useEffect, useCallback } from "react"
import { motion } from "framer-motion"
import { PageHeader } from "@/components/ui/page-header"
import { Card } from "@/components/ui/card"
import { Alert } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { StatCard } from "@/components/dashboard/stat-card"
import { BodyWeightEntryForm } from "@/components/body-weight-entry-form"
import { BodyWeightHistoryList } from "@/components/body-weight-history-list"
import { BodyWeightTrendCard } from "@/components/body-weight-trend-card"
import { BodyWeightGoalProgressCard } from "@/components/body-weight-goal-progress-card"
import { WeightChart } from "@/components/weight/weight-chart"
import { VelocityToGoalRing } from "@/components/weight/velocity-to-goal-ring"

import { useBodyWeight } from "@/hooks/use-body-weight"
import { Activity, TrendingDown, Target, Weight, AlertCircle, Plus } from "lucide-react"
import { formatDecimal } from "@/lib/format"

export default function BodyWeightPage() {
  const {
    historyStatus,
    entries,
    historyError,
    trendStatus,
    trend,
    trendError,
    goalStatus,
    goalProgress,
    goalError,
    createStatus,
    createError,
    deleteStatus,
    deletingEntryId,
    deleteError,
    reloadAll,
    retryHistory,
    retryTrend,
    retryGoalProgress,
    createEntry,
    requestDelete,
    confirmDelete,
    cancelDelete,
    clearCreateSuccess,
  } = useBodyWeight()

  useEffect(() => {
    reloadAll()
  }, [reloadAll])

  const handleCreate = useCallback(
    async (loggedDate: string, weightKg: string): Promise<boolean> => {
      const ok = await createEntry(loggedDate, weightKg)
      if (ok) setTimeout(() => clearCreateSuccess(), 3000)
      return ok
    },
    [createEntry, clearCreateSuccess],
  )

  const deletingEntry = deletingEntryId
    ? entries.find((e) => e.entry_id === deletingEntryId) ?? null
    : null

  const showDeleteConfirm = deleteStatus === "confirming" && deletingEntry
  const isDeleting = deleteStatus === "deleting"

  const latestWeight = entries.length > 0 ? entries[entries.length - 1] : null
  const weightChange = trend?.absolute_change_kg ? Number(trend.absolute_change_kg) : null
  const weightTrendPositive = weightChange !== null ? weightChange < 0 : true
  const observations = trend?.observation_count ?? entries.length
  const goalPercentage =
    goalStatus === "available" && goalProgress
      ? Number(goalProgress.progress_percentage) || 0
      : 0
  const targetWeight =
    goalStatus === "available" && goalProgress
      ? formatDecimal(goalProgress.target_weight_kg)
      : "—"

  return (
    <div className="space-y-6">
      <PageHeader
        title="Body Weight"
        description="Track your body weight and monitor progress toward your goals."
      />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Current Weight"
          value={latestWeight ? formatDecimal(latestWeight.weight_kg) : "—"}
          unit="kg"
          icon={<Weight className="h-5 w-5" />}
          color="brand"
          delay={0.05}
        />
        <StatCard
          label="Total Change"
          value={weightChange !== null ? `${Math.abs(weightChange).toFixed(1)}` : "—"}
          unit="kg"
          icon={<TrendingDown className="h-5 w-5" />}
          color={weightTrendPositive ? "brand" : "warning"}
          trend={weightChange !== null ? { value: weightTrendPositive ? "loss" : "gain", positive: weightTrendPositive } : undefined}
          delay={0.1}
        />
        <StatCard
          label="Entries"
          value={observations}
          icon={<Activity className="h-5 w-5" />}
          color="info"
          delay={0.15}
        />
        <StatCard
          label="Goal Progress"
          value={goalStatus === "available" && goalProgress ? `${Math.round(goalPercentage)}` : "—"}
          unit="%"
          icon={<Target className="h-5 w-5" />}
          color="brand"
          delay={0.2}
        />
      </div>

      <div className="grid grid-cols-12 gap-4 bg-surface-low rounded-3xl p-4 border border-white/5 premium-shadow">
        <div className="col-span-12 lg:col-span-9 flex flex-col min-w-0">
          <div className="flex justify-between items-center mb-4 px-2">
            <div>
              <h3 className="font-semibold text-primary">Metabolic Trendline</h3>
              <p className="text-xs text-primary-secondary">Dynamic body mass variance over time</p>
            </div>
          </div>
          <div className="flex-1 px-2">
            <WeightChart entries={entries} className="p-0 border-0 bg-transparent" />
          </div>
        </div>
        <div className="col-span-12 lg:col-span-3 flex flex-col gap-4 border-t lg:border-t-0 lg:border-l border-white/5 lg:pl-4">
          <VelocityToGoalRing percentage={goalPercentage} />
          <div className="flex flex-col gap-2 justify-center">
            <div className="flex justify-between items-center bg-surface-high p-3 rounded-2xl border border-white/5">
              <span className="text-xs text-primary-secondary">Target Weight</span>
              <span className="font-bold text-primary">{targetWeight} kg</span>
            </div>
            <div className="flex justify-between items-center bg-surface-high p-3 rounded-2xl border border-white/5">
              <span className="text-xs text-primary-secondary">Net Variance</span>
              <span className="font-bold text-brand">
                {weightChange !== null ? `${weightChange > 0 ? "+" : ""}${weightChange.toFixed(1)} kg` : "—"}
              </span>
            </div>
            <div className="flex justify-between items-center bg-surface-high p-3 rounded-2xl border border-white/5">
              <span className="text-xs text-primary-secondary">Est. Duration</span>
              <span className="font-bold text-primary">{goalStatus === "available" && goalProgress ? "On track" : "—"}</span>
            </div>
          </div>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          {createStatus === "success" && (
            <Alert variant="success" role="status" className="mb-4">
              Weight entry saved successfully.
            </Alert>
          )}

          {createStatus === "error" && createError && (
            <Alert variant="error" role="alert" className="mb-4">
              {createError}
            </Alert>
          )}

          {deleteStatus === "error" && deleteError && (
            <Alert variant="error" role="alert" className="mb-4">
              {deleteError}
            </Alert>
          )}

          <h2 className="text-lg font-semibold text-primary mb-3">Add Weight</h2>
          <Card className="p-5">
            <BodyWeightEntryForm
              onSubmit={handleCreate}
              loading={createStatus === "submitting"}
              error={createStatus === "error" && createError ? createError : null}
              onCancel={undefined}
            />
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
        >
          <h2 className="text-lg font-semibold text-primary mb-3">Weight History</h2>
          <BodyWeightHistoryList
            entries={entries}
            historyStatus={historyStatus}
            historyError={historyError}
            deleteStatus={deleteStatus}
            deletingEntryId={deletingEntryId}
            onDelete={requestDelete}
            onRetry={retryHistory}
          />
        </motion.div>
      </div>

      {showDeleteConfirm && (
        <Card
          role="dialog"
          aria-modal="true"
          aria-label="Confirm delete"
          className="border-error/50 p-5"
        >
          <div className="flex items-start gap-3">
            <AlertCircle className="h-5 w-5 text-error mt-0.5 shrink-0" aria-hidden="true" />
            <div className="flex-1">
              <p className="text-sm font-semibold text-primary">Delete weight entry?</p>
              <p className="text-sm text-primary-secondary mt-1">
                This will permanently delete the weight entry for{" "}
                {deletingEntry.logged_date} ({deletingEntry.weight_kg} kg).
                This action cannot be undone.
              </p>
              <div className="flex gap-2 mt-3">
                <Button variant="secondary" size="sm" onClick={cancelDelete} disabled={isDeleting}>
                  Cancel
                </Button>
                <Button variant="danger" size="sm" onClick={confirmDelete} disabled={isDeleting}>
                  {isDeleting ? "Deleting..." : "Delete"}
                </Button>
              </div>
            </div>
          </div>
        </Card>
      )}

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="grid gap-6 lg:grid-cols-2"
      >
        <BodyWeightTrendCard
          trend={trend}
          trendStatus={trendStatus}
          trendError={trendError}
          onRetry={retryTrend}
        />
        <BodyWeightGoalProgressCard
          goalProgress={goalProgress}
          goalStatus={goalStatus}
          goalError={goalError}
          onRetry={retryGoalProgress}
        />
      </motion.div>

      <button
        type="button"
        aria-label="Add weight entry"
        className="fixed bottom-24 right-6 z-20 h-14 w-14 rounded-full bg-brand text-[var(--color-bg)] shadow-lg flex items-center justify-center hover:brightness-110 transition-all lg:bottom-6"
        onClick={() => {
          document.getElementById("bw-weight-kg")?.focus()
        }}
      >
        <Plus className="h-6 w-6" aria-hidden="true" />
      </button>
    </div>
  )
}
