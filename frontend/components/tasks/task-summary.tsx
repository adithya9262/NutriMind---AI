"use client"

import { motion } from "framer-motion"
import { Sparkles, Check } from "lucide-react"
import { Card } from "@/components/ui/card"
import { TaskProgress } from "@/components/tasks/task-progress"
import { TODAY_OPTIMIZATION_DEMO, TASKS_DEMO_LABEL } from "@/components/tasks/placeholders"
import type { TaskData } from "@/types/tasks"

interface TaskSummaryProps {
  tasks: TaskData[]
}

export function TaskSummary({ tasks }: TaskSummaryProps) {
  const doneCount = TODAY_OPTIMIZATION_DEMO.filter((o) => o.done).length

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <TaskProgress tasks={tasks} />

      <Card className="p-5">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-brand" aria-hidden="true" />
            <p className="font-semibold text-primary">Today&apos;s Optimization</p>
          </div>
          <span className="text-[10px] uppercase tracking-wider text-primary-muted border border-border rounded-full px-2 py-0.5">
            {TASKS_DEMO_LABEL}
          </span>
        </div>
        <div className="space-y-2">
          {TODAY_OPTIMIZATION_DEMO.map((item, i) => (
            <motion.div
              key={item.id}
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.05 }}
              className="flex items-center gap-3"
            >
              <span
                className={`flex h-5 w-5 items-center justify-center rounded-full border ${
                  item.done
                    ? "bg-brand border-brand text-[var(--color-bg)]"
                    : "border-border text-transparent"
                }`}
              >
                <Check className="h-3 w-3" aria-hidden="true" />
              </span>
              <span
                className={`text-sm ${
                  item.done ? "text-primary-muted line-through" : "text-primary-secondary"
                }`}
              >
                {item.label}
              </span>
            </motion.div>
          ))}
        </div>
        <p className="mt-3 text-xs text-primary-muted">
          {doneCount} of {TODAY_OPTIMIZATION_DEMO.length} focus areas complete today
        </p>
      </Card>
    </div>
  )
}
