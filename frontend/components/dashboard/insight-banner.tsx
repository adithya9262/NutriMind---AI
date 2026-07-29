"use client"

import { motion } from "framer-motion"
import { Card } from "@/components/ui/card"
import { Sparkles, Salad } from "lucide-react"
import { cn } from "@/lib/utils"

interface InsightBannerProps {
  quote: string
  mealLabel?: string
  mealTitle?: string
  delay?: number
  className?: string
}

export function InsightBanner({
  quote,
  mealLabel = "Optimization Meal",
  mealTitle,
  delay = 0,
  className,
}: InsightBannerProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay }}
    >
      <Card className={cn("border-brand-primary/20 bg-brand-primary/[0.06] p-5 card-hover", className)}>
        <div className="flex items-center gap-2">
          <span className="grid h-7 w-7 place-items-center rounded-lg bg-brand-primary/15">
            <Sparkles className="h-4 w-4 text-brand-primary" aria-hidden="true" />
          </span>
          <span className="text-xs font-semibold uppercase tracking-wider text-brand-primary">
            NutriMind Insight
          </span>
        </div>

        <blockquote className="mt-3 text-sm leading-relaxed text-primary/90">
          &ldquo;{quote}&rdquo;
        </blockquote>

        {mealTitle && (
          <div className="mt-4 flex items-center gap-3 rounded-xl border border-border bg-surface-high/40 p-3">
            <span className="grid h-9 w-9 place-items-center rounded-lg bg-brand-primary/15">
              <Salad className="h-4 w-4 text-brand-primary" aria-hidden="true" />
            </span>
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-wide text-primary-muted">
                {mealLabel}
              </p>
              <p className="text-sm font-medium text-primary">{mealTitle}</p>
            </div>
          </div>
        )}
      </Card>
    </motion.div>
  )
}
