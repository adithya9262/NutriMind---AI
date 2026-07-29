"use client"

import { useEffect, useCallback, useState, useMemo } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Plus, ListTodo, Flame, Zap } from "lucide-react"
import { PageHeader } from "@/components/ui/page-header"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Alert } from "@/components/ui/alert"
import { Progress } from "@/components/ui/progress"
import { TaskForm } from "@/components/task-form"
import { TaskList } from "@/components/task-list"
import { TaskDeleteConfirm } from "@/components/task-delete-confirm"
import { TaskOverview } from "@/components/tasks/task-overview"
import { TaskPriorityGroup } from "@/components/tasks/task-priority-group"
import { EmptyTaskState } from "@/components/tasks/empty-task-state"
import { useTasks } from "@/hooks/use-tasks"
import type { TaskData, TaskPriority, TaskFormState, TaskUpdateRequest, TaskCreateRequest } from "@/types/tasks"


type TaskFilter = "all" | "pending" | "completed" | "habits"

const PRIORITY_ORDER: TaskPriority[] = ["high", "medium", "low"]

const FILTER_OPTIONS: { value: TaskFilter; label: string }[] = [
  { value: "all", label: "All" },
  { value: "pending", label: "Pending" },
  { value: "completed", label: "Completed" },
  { value: "habits", label: "Habits" },
]

function getTodayStr(): string {
  const now = new Date()
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`
}

function getYesterdayStr(): string {
  const now = new Date(Date.now() - 86400000)
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`
}

function calculateStreaks(tasks: TaskData[]): { currentStreak: number; bestStreak: number } {
  const completedDates = new Set<string>()

  tasks
    .filter((t) => t.status === "completed" && t.completed_at)
    .forEach((t) => {
      const date = t.completed_at!.split("T")[0]
      completedDates.add(date)
    })

  if (completedDates.size === 0) {
    return { currentStreak: 0, bestStreak: 0 }
  }

  const sorted = Array.from(completedDates).sort()

  let bestStreak = 1
  let currentStreak = 0
  let run = 1

  for (let i = 1; i < sorted.length; i++) {
    const prev = new Date(sorted[i - 1])
    const curr = new Date(sorted[i])
    const diff = (curr.getTime() - prev.getTime()) / 86400000

    if (Math.abs(diff - 1) < 0.1) {
      run++
      bestStreak = Math.max(bestStreak, run)
    } else {
      run = 1
    }
  }
  bestStreak = Math.max(bestStreak, run)

  const today = getTodayStr()
  const yesterday = getYesterdayStr()
  const lastDate = sorted[sorted.length - 1]

  if (lastDate === today || lastDate === yesterday) {
    currentStreak = 1
    for (let i = sorted.length - 2; i >= 0; i--) {
      const next = new Date(sorted[i + 1])
      const curr = new Date(sorted[i])
      const diff = (next.getTime() - curr.getTime()) / 86400000
      if (Math.abs(diff - 1) < 0.1) {
        currentStreak++
      } else {
        break
      }
    }
  }

  return { currentStreak, bestStreak }
}

function getTodayCompletion(tasks: TaskData[]): { completed: number; total: number; percentage: number } {
  const today = getTodayStr()
  const completedToday = tasks.filter(
    (t) => t.status === "completed" && t.completed_at?.startsWith(today)
  ).length
  const pendingCount = tasks.filter((t) => t.status === "pending").length
  const totalActive = completedToday + pendingCount
  const percentage = totalActive > 0 ? Math.round((completedToday / totalActive) * 100) : 0

  return { completed: completedToday, total: totalActive, percentage }
}

function taskToFormState(task: TaskData): TaskFormState {
  return {
    title: task.title,
    description: task.description || "",
    priority: task.priority,
    due_date: task.due_date || "",
    category: task.category || "custom",
    recurrence: task.recurrence || "none",
  }
}

export default function TasksPage() {
  const {
    listStatus,
    tasks,
    listError,
    createStatus,
    createError,
    createValidationErrors,
    actionStatus,
    actionError,
    actionValidationErrors,
    actionTaskId,
    deleteConfirmTaskId,
    reloadTasks,
    retryTasks,
    createTask,
    updateTask,
    completeTask,
    reopenTask,
    requestDelete,
    confirmDelete,
    cancelDelete,
    clearCreateSuccess,
  } = useTasks()

  const [showForm, setShowForm] = useState(false)
  const [filter, setFilter] = useState<TaskFilter>("all")
  useEffect(() => {
    reloadTasks()
  }, [reloadTasks])

  const [editingTask, setEditingTask] = useState<TaskData | null>(null)

  const openCreateForm = useCallback(() => {
    setEditingTask(null)
    setShowForm(true)
    clearCreateSuccess()
  }, [clearCreateSuccess])

  const openEditForm = useCallback((task: TaskData) => {
    setEditingTask(task)
    setShowForm(true)
    clearCreateSuccess()
  }, [clearCreateSuccess])

  const handleSubmit = useCallback(
    async (payload: TaskCreateRequest): Promise<boolean> => {
      if (editingTask) {
        const updatePayload: TaskUpdateRequest = {
          title: payload.title,
          description: payload.description || null,
          priority: payload.priority,
          due_date: payload.due_date || null,
          category: payload.category || null,
          recurrence: payload.recurrence || null,
        }
        const ok = await updateTask(editingTask.task_id, updatePayload)
        if (ok) {
          setShowForm(false)
          setEditingTask(null)
        }
        return ok
      } else {
        const ok = await createTask(payload)
        if (ok) {
          setShowForm(false)
          setTimeout(() => clearCreateSuccess(), 3000)
        }
        return ok
      }
    },
    [editingTask, updateTask, createTask, clearCreateSuccess]
  )

  const deletingTask = deleteConfirmTaskId
    ? tasks.find((t) => t.task_id === deleteConfirmTaskId) ?? null
    : null

  const isDeleting = actionStatus === "deleting"
  const showDeleteConfirm = deleteConfirmTaskId !== null && deletingTask

  const habits = useMemo(
    () => tasks.filter((t) => t.category === "daily_habit"),
    [tasks]
  )

  const regularTasks = useMemo(
    () => tasks.filter((t) => t.category !== "daily_habit"),
    [tasks]
  )

  const filteredTasks = useMemo(() => {
    const source = filter === "habits" ? habits : regularTasks
    if (filter === "pending") return source.filter((t) => t.status === "pending")
    if (filter === "completed") return source.filter((t) => t.status === "completed")
    return source
  }, [filter, habits, regularTasks])

  const filteredHabits = useMemo(() => {
    if (filter === "pending") return habits.filter((t) => t.status === "pending")
    if (filter === "completed") return habits.filter((t) => t.status === "completed")
    return habits
  }, [filter, habits])

  const grouped = useMemo(
    () =>
      PRIORITY_ORDER.reduce<Record<TaskPriority, typeof tasks>>(
        (acc, p) => {
          acc[p] = filteredTasks.filter((t) => t.priority === p)
          return acc
        },
        { high: [], medium: [], low: [] },
      ),
    [filteredTasks],
  )

  const { currentStreak, bestStreak } = useMemo(() => calculateStreaks(tasks), [tasks])

  const todayProgress = useMemo(() => getTodayCompletion(tasks), [tasks])

  const showHabitsSection = filter === "all" || filter === "habits" || filter === "pending" || filter === "completed"
  const hasHabits = filteredHabits.length > 0
  const hasRegular = filteredTasks.length > 0

  return (
    <div className="space-y-6">
      <PageHeader
        title="Tasks"
        description="Manage your daily health and wellness tasks."
        actions={
          !showForm ? (
            <Button size="sm" onClick={openCreateForm}>
              <Plus className="h-4 w-4" />
              Add Task
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
              Task created successfully.
            </Alert>
          </motion.div>
        )}
      </AnimatePresence>

      {actionError && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <Alert variant="error" role="alert">
            {actionError}
          </Alert>
        </motion.div>
      )}

      <AnimatePresence>
        {showForm && (
          <motion.div
            initial={{ opacity: 0, y: -10, height: 0 }}
            animate={{ opacity: 1, y: 0, height: "auto" }}
            exit={{ opacity: 0, y: -10, height: 0 }}
          >
            <h2 className="text-lg font-semibold text-primary mb-3">Create Task</h2>
            <Card className="p-5">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2 rounded-xl bg-brand-light">
                  <ListTodo className="h-4 w-4 text-brand" />
                </div>
                <div>
                  <p className="text-sm font-semibold text-primary">
                    {editingTask ? "Edit Task" : "New Task"}
                  </p>
                  <p className="text-xs text-primary-secondary">
                    {editingTask ? "Update your task details" : "Define your next action item"}
                  </p>
                </div>
              </div>
              <TaskForm
                onSubmit={handleSubmit}
                loading={createStatus === "submitting" || actionStatus === "updating"}
                error={
                  (createStatus === "error" && createError) ||
                  (actionStatus === "error" && actionError) ? (createError || actionError) : null
                }
                apiFieldErrors={editingTask ? actionValidationErrors : createValidationErrors}
                onCancel={() => {
                  setShowForm(false)
                  setEditingTask(null)
                }}
                initialData={editingTask ? taskToFormState(editingTask) : undefined}
                isEditing={!!editingTask}
              />
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

      {(listStatus === "available" || (listStatus === "loading" && tasks.length > 0)) && (
        <div className="space-y-6">
          <TaskOverview tasks={tasks} />

          <Card className="p-5">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <Zap className="h-4 w-4 text-brand" aria-hidden="true" />
                <span className="text-sm font-semibold text-primary">Today&apos;s Progress</span>
              </div>
              <div className="flex items-center gap-4 text-xs">
                {currentStreak > 0 && (
                  <span className="inline-flex items-center gap-1 text-primary-secondary">
                    <Flame className="h-3.5 w-3.5 text-warning" aria-hidden="true" />
                    <span className="font-semibold text-primary">{currentStreak}</span>
                    <span className="text-primary-muted">day streak</span>
                  </span>
                )}
                {bestStreak > 0 && (
                  <span className="text-primary-muted">
                    Best: <span className="font-semibold text-primary-secondary">{bestStreak}</span>
                  </span>
                )}
              </div>
            </div>
            <Progress
              value={todayProgress.percentage}
              variant="default"
              size="md"
              showLabel
            />
            <p className="text-xs text-primary-muted mt-1.5">
              {todayProgress.completed} of {todayProgress.total} tasks completed today
            </p>
          </Card>

          <div className="flex items-center gap-1 p-1 rounded-xl bg-white/5 w-fit" role="tablist" aria-label="Filter tasks">
            {FILTER_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                type="button"
                role="tab"
                aria-selected={filter === opt.value}
                onClick={() => setFilter(opt.value)}
                className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-all ${
                  filter === opt.value
                    ? "bg-brand text-[var(--color-bg)] shadow-sm"
                    : "text-primary-secondary hover:text-primary"
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>

          {showHabitsSection && hasHabits && (
            <section aria-labelledby="habits-heading">
              <h2
                id="habits-heading"
                className="text-lg font-semibold text-primary mb-3"
              >
                Habits
              </h2>
              <div className="space-y-3">
                <TaskList
                  tasks={filteredHabits}
                  listStatus="available"
                  listError={null}
                  actionStatus={actionStatus}
                  actionTaskId={actionTaskId}
                  onComplete={completeTask}
                  onReopen={reopenTask}
                  onEdit={openEditForm}
                  onDelete={requestDelete}
                  onRetry={retryTasks}
                />
              </div>
            </section>
          )}

          {hasRegular && (
            <section aria-labelledby="task-list-heading">
              <h2
                id="task-list-heading"
                className="text-lg font-semibold text-primary mb-3"
              >
                {filter === "habits" ? "Tasks" : "Your Tasks"}
              </h2>
              <div className="space-y-4">
                {PRIORITY_ORDER.map((priority) => (
                  <TaskPriorityGroup
                    key={priority}
                    priority={priority}
                    tasks={grouped[priority]}
                    actionStatus={actionStatus}
                    actionTaskId={actionTaskId}
                    onComplete={completeTask}
                    onReopen={reopenTask}
                    onEdit={openEditForm}
                    onDelete={requestDelete}
                  />
                ))}
              </div>
            </section>
          )}

          {!hasHabits && !hasRegular && (
            <EmptyTaskState onAddTask={openCreateForm} />
          )}
        </div>
      )}

      {listStatus === "empty" && <EmptyTaskState onAddTask={openCreateForm} />}

      {(listStatus === "loading" && tasks.length === 0) && (
        <TaskList
          tasks={tasks}
          listStatus={listStatus}
          listError={listError}
          actionStatus={actionStatus}
          actionTaskId={actionTaskId}
          onComplete={completeTask}
          onReopen={reopenTask}
          onEdit={openEditForm}
          onDelete={requestDelete}
          onRetry={retryTasks}
        />
      )}

      {listStatus === "error" && (
        <TaskList
          tasks={tasks}
          listStatus={listStatus}
          listError={listError}
          actionStatus={actionStatus}
          actionTaskId={actionTaskId}
          onComplete={completeTask}
          onReopen={reopenTask}
          onEdit={openEditForm}
          onDelete={requestDelete}
          onRetry={retryTasks}
        />
      )}

      <AnimatePresence>
        {showDeleteConfirm && deletingTask && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
          >
            <TaskDeleteConfirm
              task={deletingTask}
              deleting={isDeleting}
              onConfirm={confirmDelete}
              onCancel={cancelDelete}
            />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
