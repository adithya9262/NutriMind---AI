"use client"

import { ListTodo } from "lucide-react"
import { EmptyState } from "@/components/ui/empty-state"

interface EmptyTaskStateProps {
  onAddTask: () => void
}

export function EmptyTaskState({ onAddTask }: EmptyTaskStateProps) {
  return (
    <EmptyState
      icon={<ListTodo className="h-8 w-8" aria-hidden="true" />}
      title="No tasks yet"
      description="Create your first task to get started."
      action={
        <button
          type="button"
          onClick={onAddTask}
          className="inline-flex items-center gap-2 rounded-xl bg-brand px-4 py-2 text-sm font-semibold text-[var(--color-bg)] hover:brightness-110 transition-all"
        >
          <ListTodo className="h-4 w-4" aria-hidden="true" />
          Add your first task
        </button>
      }
    />
  )
}
