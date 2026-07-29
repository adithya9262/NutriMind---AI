"use client"

import { motion } from "framer-motion"
import { Card } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { cn } from "@/lib/utils"
import type { LucideIcon } from "lucide-react"

interface ModuleCardProps {
  title: string
  icon: LucideIcon
  iconClassName?: string
  value: string
  target?: string
  badge?: string
  note?: string
  progress?: { value: number; max: number; variant?: "default" | "warning" | "error" | "success" }
  delay?: number
  className?: string
}

export function ModuleCard({
  title,
  icon: Icon,
  iconClassName = "text-brand-primary bg-brand-primary/15",
  value,
  target,
  badge,
  note,
  progress,
  delay = 0,
  className,
}: ModuleCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay }}
    >
      <Card className={cn("p-5 card-hover", className)}>
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2.5">
            <span className={cn("grid h-9 w-9 place-items-center rounded-xl", iconClassName)}>
              <Icon className="h-4 w-4" aria-hidden="true" />
            </span>
            <span className="text-sm font-medium text-primary-secondary">{title}</span>
          </div>
          {badge && (
            <span className="rounded-full bg-brand-primary/15 px-2 py-0.5 text-[11px] font-semibold text-brand-primary">
              {badge}
            </span>
          )}
        </div>

        <div className="mt-3 flex items-baseline gap-1.5">
          <span className="text-2xl font-bold text-primary">{value}</span>
          {target && <span className="text-sm text-primary-secondary">{target}</span>}
        </div>

        {note && <p className="mt-1 text-xs italic text-primary-muted">{note}</p>}

        {progress && (
          <div className="mt-3">
            <Progress value={progress.value} max={progress.max} variant={progress.variant} size="sm" />
          </div>
        )}
      </Card>
    </motion.div>
  )
}
