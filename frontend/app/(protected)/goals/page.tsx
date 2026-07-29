"use client"

import { useEffect, useCallback, useState, useRef } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Plus, Target, Pencil, Trash2, Calendar } from "lucide-react"
import { PageHeader } from "@/components/ui/page-header"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select } from "@/components/ui/select"
import { Alert } from "@/components/ui/alert"
import { Spinner } from "@/components/ui/spinner"
import { EmptyState } from "@/components/ui/empty-state"
import { ErrorState } from "@/components/ui/error-state"
import { SectionHeader } from "@/components/ui/section-header"
import { useGoals } from "@/hooks/use-goals"
import type { GoalData, GoalType, GoalStatus, GoalCreateRequest, GoalUpdateRequest } from "@/types/goals"
import { GOAL_TYPE_LABELS, GOAL_STATUS_LABELS } from "@/types/goals"
import { getFieldError, type FieldError } from "@/lib/validation"

const STATUS_BADGE_VARIANTS: Record<GoalStatus, "success" | "info" | "error" | "warning"> = {
  active: "success",
  completed: "info",
  cancelled: "error",
  paused: "warning",
}

const GOAL_TYPE_OPTIONS: GoalType[] = [
  "weight_loss",
  "weight_gain",
  "maintain_weight",
  "muscle_gain",
  "fat_loss",
  "custom",
]

interface GoalFormState {
  goal_type: GoalType
  title: string
  description: string
  start_date: string
  end_date: string
  weekly_target: string
  target_calories: string
  target_protein_g: string
  target_carbs_g: string
  target_fats_g: string
  target_water_ml: string
}

const EMPTY_FORM: GoalFormState = {
  goal_type: "custom",
  title: "",
  description: "",
  start_date: "",
  end_date: "",
  weekly_target: "",
  target_calories: "",
  target_protein_g: "",
  target_carbs_g: "",
  target_fats_g: "",
  target_water_ml: "",
}

function goalToFormState(goal: GoalData): GoalFormState {
  return {
    goal_type: goal.goal_type,
    title: goal.title,
    description: goal.description ?? "",
    start_date: goal.start_date ?? "",
    end_date: goal.end_date ?? "",
    weekly_target: goal.weekly_target ?? "",
    target_calories: goal.target_calories?.toString() ?? "",
    target_protein_g: goal.target_protein_g?.toString() ?? "",
    target_carbs_g: goal.target_carbs_g?.toString() ?? "",
    target_fats_g: goal.target_fats_g?.toString() ?? "",
    target_water_ml: goal.target_water_ml?.toString() ?? "",
  }
}

function formToCreatePayload(form: GoalFormState): GoalCreateRequest {
  return {
    goal_type: form.goal_type,
    title: form.title,
    description: form.description || null,
    start_date: form.start_date || null,
    end_date: form.end_date || null,
    weekly_target: form.weekly_target || null,
    target_calories: form.target_calories ? Number(form.target_calories) : null,
    target_protein_g: form.target_protein_g ? Number(form.target_protein_g) : null,
    target_carbs_g: form.target_carbs_g ? Number(form.target_carbs_g) : null,
    target_fats_g: form.target_fats_g ? Number(form.target_fats_g) : null,
    target_water_ml: form.target_water_ml ? Number(form.target_water_ml) : null,
  }
}

function formToUpdatePayload(form: GoalFormState): GoalUpdateRequest {
  return {
    goal_type: form.goal_type,
    title: form.title,
    description: form.description || null,
    start_date: form.start_date || null,
    end_date: form.end_date || null,
    weekly_target: form.weekly_target || null,
    target_calories: form.target_calories ? Number(form.target_calories) : null,
    target_protein_g: form.target_protein_g ? Number(form.target_protein_g) : null,
    target_carbs_g: form.target_carbs_g ? Number(form.target_carbs_g) : null,
    target_fats_g: form.target_fats_g ? Number(form.target_fats_g) : null,
    target_water_ml: form.target_water_ml ? Number(form.target_water_ml) : null,
  }
}

export default function GoalsPage() {
  const goalsData = useGoals()
  console.log("[GoalsPage] Component function executed, listStatus =", goalsData.listStatus)
  const {
    listStatus,
    goals,
    listError,
    createStatus,
    createError,
    createValidationErrors,
    actionStatus,
    actionError,
    actionValidationErrors,
    actionGoalId,
    deleteConfirmGoalId,
    reloadGoals,
    retryGoals,
    createGoal,
    updateGoal,
    requestDelete,
    confirmDelete,
    cancelDelete,
    clearCreateSuccess,
  } = goalsData

  const [showForm, setShowForm] = useState(false)
  const [editingGoal, setEditingGoal] = useState<GoalData | null>(null)
  const [form, setForm] = useState<GoalFormState>(EMPTY_FORM)
  const initRef = useRef(false)

  useEffect(() => {
    console.log("[GoalsPage] Mount effect running, initRef.current =", initRef.current)
    if (initRef.current) return
    initRef.current = true
    reloadGoals()
    
    return () => {
      console.log("[GoalsPage] Cleanup, initRef.current =", initRef.current)
    }
  }, [reloadGoals])

  const resetForm = useCallback(() => {
    setForm(EMPTY_FORM)
    setEditingGoal(null)
    setShowForm(false)
    clearCreateSuccess()
  }, [clearCreateSuccess])

  const openCreateForm = useCallback(() => {
    setForm(EMPTY_FORM)
    setEditingGoal(null)
    setShowForm(true)
    clearCreateSuccess()
  }, [clearCreateSuccess])

  const openEditForm = useCallback((goal: GoalData) => {
    setForm(goalToFormState(goal))
    setEditingGoal(goal)
    setShowForm(true)
    clearCreateSuccess()
  }, [clearCreateSuccess])

  const handleFormChange = useCallback((field: keyof GoalFormState, value: string) => {
    setForm((prev) => ({ ...prev, [field]: value }))
  }, [])

  const handleSubmit = useCallback(async () => {
    if (editingGoal) {
      const ok = await updateGoal(editingGoal.id, formToUpdatePayload(form))
      if (ok) {
        resetForm()
      }
    } else {
      const ok = await createGoal(formToCreatePayload(form))
      if (ok) {
        resetForm()
        setTimeout(() => clearCreateSuccess(), 3000)
      }
    }
  }, [editingGoal, form, createGoal, updateGoal, resetForm, clearCreateSuccess])

  const deletingGoal = deleteConfirmGoalId
    ? goals.find((g) => g.id === deleteConfirmGoalId) ?? null
    : null

  const isDeleting = actionStatus === "deleting"
  const showDeleteConfirm = deleteConfirmGoalId !== null && deletingGoal

  const isSubmitting = createStatus === "submitting" || actionStatus === "updating"

  const fieldErrors: FieldError[] = editingGoal ? actionValidationErrors : createValidationErrors

  const formError = editingGoal
    ? (actionStatus === "error" && actionGoalId === editingGoal.id ? actionError : null)
    : (createStatus === "error" ? createError : null)

  function getProgress(goal: GoalData): number {
    const p = goal.progress_percentage
    if (p === null || p === undefined) return 0
    const n = parseFloat(p)
    if (isNaN(n)) return 0
    return Math.min(Math.round(n), 100)
  }

  function formatDate(dateStr: string | null): string {
    if (!dateStr) return "\u2014"
    try {
      return new Date(dateStr).toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
      })
    } catch {
      return dateStr
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Goals"
        description="Set and track your nutrition and fitness goals."
        actions={
          !showForm ? (
            <Button size="sm" onClick={openCreateForm}>
              <Plus className="h-4 w-4" />
              Add Goal
            </Button>
          ) : null
        }
      />

      <AnimatePresence>
        {createStatus === "success" && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
          >
            <Alert variant="success" role="status">
              Goal created successfully.
            </Alert>
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {showForm && (
          <motion.div
            initial={{ opacity: 0, y: -10, height: 0 }}
            animate={{ opacity: 1, y: 0, height: "auto" }}
            exit={{ opacity: 0, y: -10, height: 0 }}
          >
            <Card className="p-5">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2 rounded-xl bg-brand-light">
                  <Target className="h-4 w-4 text-brand" />
                </div>
                <div>
                  <p className="text-sm font-semibold text-primary">
                    {editingGoal ? "Edit Goal" : "New Goal"}
                  </p>
                  <p className="text-xs text-primary-secondary">
                    {editingGoal
                      ? "Update your goal details"
                      : "Define a new nutrition or fitness goal"}
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="goal_type" required>
                    Goal Type
                  </Label>
                  <Select
                    id="goal_type"
                    value={form.goal_type}
                    onChange={(e) => handleFormChange("goal_type", e.target.value)}
                  >
                    {GOAL_TYPE_OPTIONS.map((type) => (
                      <option key={type} value={type}>
                        {GOAL_TYPE_LABELS[type]}
                      </option>
                    ))}
                  </Select>
                  {getFieldError(fieldErrors, "goal_type") && (
                    <p className="text-xs text-error">{getFieldError(fieldErrors, "goal_type")}</p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="title" required>
                    Title
                  </Label>
                  <Input
                    id="title"
                    value={form.title}
                    onChange={(e) => handleFormChange("title", e.target.value)}
                    placeholder="e.g., Lose 10 lbs in 3 months"
                  />
                  {getFieldError(fieldErrors, "title") && (
                    <p className="text-xs text-error">{getFieldError(fieldErrors, "title")}</p>
                  )}
                </div>

                <div className="space-y-2 md:col-span-2">
                  <Label htmlFor="description">Description</Label>
                  <textarea
                    id="description"
                    value={form.description}
                    onChange={(e) => handleFormChange("description", e.target.value)}
                    placeholder="Describe your goal..."
                    rows={3}
                    className="block w-full rounded-[0.5rem] border border-border bg-bg px-4 py-2.5 text-sm text-primary placeholder:text-primary-muted transition-all duration-200 hover:border-brand-primary/30 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary/30 focus-visible:border-brand-primary resize-none"
                  />
                  {getFieldError(fieldErrors, "description") && (
                    <p className="text-xs text-error">{getFieldError(fieldErrors, "description")}</p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="start_date">Start Date</Label>
                  <Input
                    id="start_date"
                    type="date"
                    value={form.start_date}
                    onChange={(e) => handleFormChange("start_date", e.target.value)}
                  />
                  {getFieldError(fieldErrors, "start_date") && (
                    <p className="text-xs text-error">{getFieldError(fieldErrors, "start_date")}</p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="end_date">End Date</Label>
                  <Input
                    id="end_date"
                    type="date"
                    value={form.end_date}
                    onChange={(e) => handleFormChange("end_date", e.target.value)}
                  />
                  {getFieldError(fieldErrors, "end_date") && (
                    <p className="text-xs text-error">{getFieldError(fieldErrors, "end_date")}</p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="weekly_target">Weekly Target</Label>
                  <Input
                    id="weekly_target"
                    value={form.weekly_target}
                    onChange={(e) => handleFormChange("weekly_target", e.target.value)}
                    placeholder="e.g., 1 lb per week"
                  />
                  {getFieldError(fieldErrors, "weekly_target") && (
                    <p className="text-xs text-error">{getFieldError(fieldErrors, "weekly_target")}</p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="target_calories">
                    Target Calories (kcal/day)
                  </Label>
                  <Input
                    id="target_calories"
                    type="number"
                    min={0}
                    value={form.target_calories}
                    onChange={(e) => handleFormChange("target_calories", e.target.value)}
                    placeholder="e.g., 2000"
                  />
                  {getFieldError(fieldErrors, "target_calories") && (
                    <p className="text-xs text-error">{getFieldError(fieldErrors, "target_calories")}</p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="target_protein_g">
                    Target Protein (g/day)
                  </Label>
                  <Input
                    id="target_protein_g"
                    type="number"
                    min={0}
                    value={form.target_protein_g}
                    onChange={(e) => handleFormChange("target_protein_g", e.target.value)}
                    placeholder="e.g., 150"
                  />
                  {getFieldError(fieldErrors, "target_protein_g") && (
                    <p className="text-xs text-error">{getFieldError(fieldErrors, "target_protein_g")}</p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="target_carbs_g">
                    Target Carbs (g/day)
                  </Label>
                  <Input
                    id="target_carbs_g"
                    type="number"
                    min={0}
                    value={form.target_carbs_g}
                    onChange={(e) => handleFormChange("target_carbs_g", e.target.value)}
                    placeholder="e.g., 250"
                  />
                  {getFieldError(fieldErrors, "target_carbs_g") && (
                    <p className="text-xs text-error">{getFieldError(fieldErrors, "target_carbs_g")}</p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="target_fats_g">
                    Target Fats (g/day)
                  </Label>
                  <Input
                    id="target_fats_g"
                    type="number"
                    min={0}
                    value={form.target_fats_g}
                    onChange={(e) => handleFormChange("target_fats_g", e.target.value)}
                    placeholder="e.g., 65"
                  />
                  {getFieldError(fieldErrors, "target_fats_g") && (
                    <p className="text-xs text-error">{getFieldError(fieldErrors, "target_fats_g")}</p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="target_water_ml">
                    Target Water (ml/day)
                  </Label>
                  <Input
                    id="target_water_ml"
                    type="number"
                    min={0}
                    value={form.target_water_ml}
                    onChange={(e) => handleFormChange("target_water_ml", e.target.value)}
                    placeholder="e.g., 2000"
                  />
                  {getFieldError(fieldErrors, "target_water_ml") && (
                    <p className="text-xs text-error">{getFieldError(fieldErrors, "target_water_ml")}</p>
                  )}
                </div>
              </div>

              {formError && (
                <Alert variant="error" className="mt-4" role="alert">
                  {formError}
                </Alert>
              )}

              <div className="flex items-center justify-end gap-3 mt-5">
                <Button variant="secondary" onClick={resetForm}>
                  Cancel
                </Button>
                <Button
                  variant="primary"
                  onClick={handleSubmit}
                  disabled={isSubmitting || !form.title.trim()}
                >
                  {isSubmitting ? (
                    <>
                      <Spinner size="sm" />
                      {editingGoal ? "Saving..." : "Creating..."}
                    </>
                  ) : editingGoal ? (
                    "Save Changes"
                  ) : (
                    "Create Goal"
                  )}
                </Button>
              </div>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

      {(listStatus === "loading" && goals.length === 0) && (
        <div className="flex items-center justify-center py-16">
          <Spinner size="lg" />
        </div>
      )}

      {listStatus === "empty" && (
        <EmptyState
          title="No goals yet"
          description="Create your first nutrition or fitness goal to start tracking your progress."
          icon={<Target className="h-12 w-12" />}
          action={
            !showForm ? (
              <Button size="sm" onClick={openCreateForm}>
                <Plus className="h-4 w-4" />
                Add Goal
              </Button>
            ) : null
          }
        />
      )}

      {listStatus === "error" && (
        <ErrorState
          title="Failed to load goals"
          message={listError ?? "An unexpected error occurred."}
          action={
            <Button size="sm" variant="secondary" onClick={retryGoals}>
              Retry
            </Button>
          }
        />
      )}

      {(listStatus === "available" || (listStatus === "loading" && goals.length > 0)) && (
        <section aria-labelledby="goals-list-heading">
          <SectionHeader
            id="goals-list-heading"
            title={`Your Goals (${goals.length})`}
          />
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            <AnimatePresence>
              {goals.map((goal) => {
                const progress = getProgress(goal)
                const isActing = actionStatus === "updating" && actionGoalId === goal.id

                return (
                  <motion.div
                    key={goal.id}
                    layout
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                  >
                    <Card className="p-5 space-y-4">
                      <div className="flex items-start justify-between gap-4">
                        <div className="space-y-1 min-w-0 flex-1">
                          <div className="flex items-center gap-2 flex-wrap">
                            <h3 className="text-base font-semibold text-primary truncate">
                              {goal.title}
                            </h3>
                            <Badge
                              variant={STATUS_BADGE_VARIANTS[goal.status]}
                              size="sm"
                            >
                              {GOAL_STATUS_LABELS[goal.status]}
                            </Badge>
                          </div>
                          <p className="text-xs text-primary-secondary">
                            {GOAL_TYPE_LABELS[goal.goal_type]}
                          </p>
                        </div>
                        {isActing ? (
                          <Spinner size="sm" />
                        ) : (
                          <div className="flex items-center gap-1 flex-shrink-0">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => openEditForm(goal)}
                              aria-label={`Edit ${goal.title}`}
                            >
                              <Pencil className="h-3.5 w-3.5" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => requestDelete(goal.id)}
                              aria-label={`Delete ${goal.title}`}
                            >
                              <Trash2 className="h-3.5 w-3.5 text-error" />
                            </Button>
                          </div>
                        )}
                      </div>

                      {goal.description && (
                        <p className="text-sm text-primary-secondary line-clamp-2">
                          {goal.description}
                        </p>
                      )}

                      <div className="space-y-1.5">
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-primary-secondary">
                            Progress
                          </span>
                          <span className="text-primary font-medium">
                            {progress}%
                          </span>
                        </div>
                        <Progress
                          value={progress}
                          variant={progress >= 100 ? "success" : "accent"}
                          size="sm"
                        />
                      </div>

                      {(goal.start_date || goal.end_date) && (
                        <div className="flex items-center gap-3 text-xs text-primary-secondary">
                          {goal.start_date && (
                            <span className="flex items-center gap-1">
                              <Calendar className="h-3 w-3" />
                              {formatDate(goal.start_date)}
                            </span>
                          )}
                          {goal.end_date && (
                            <span className="flex items-center gap-1">
                              <Calendar className="h-3 w-3" />
                              {formatDate(goal.end_date)}
                            </span>
                          )}
                        </div>
                      )}
                    </Card>
                  </motion.div>
                )
              })}
            </AnimatePresence>
          </div>
        </section>
      )}

      <AnimatePresence>
        {showDeleteConfirm && deletingGoal && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40"
          >
            <Card className="p-6 max-w-md w-full space-y-4">
              <h3 className="text-lg font-semibold text-primary">Delete Goal</h3>
              <p className="text-sm text-primary-secondary">
                Are you sure you want to delete &ldquo;{deletingGoal.title}&rdquo;?
                This action cannot be undone.
              </p>

              {actionStatus === "error" && actionError && (
                <Alert variant="error" role="alert">
                  {actionError}
                </Alert>
              )}

              <div className="flex items-center justify-end gap-3">
                <Button
                  variant="secondary"
                  onClick={cancelDelete}
                  disabled={isDeleting}
                >
                  Cancel
                </Button>
                <Button
                  variant="danger"
                  onClick={confirmDelete}
                  disabled={isDeleting}
                >
                  {isDeleting ? (
                    <>
                      <Spinner size="sm" />
                      Deleting...
                    </>
                  ) : (
                    "Delete"
                  )}
                </Button>
              </div>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
