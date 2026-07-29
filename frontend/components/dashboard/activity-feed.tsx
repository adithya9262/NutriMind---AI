"use client"

import { motion } from "framer-motion"
import Link from "next/link"
import { Card } from "@/components/ui/card"
import { cn } from "@/lib/utils"

export interface ActivityEntry {
  id: string
  category: string
  title: string
  detail: string
  isDemo?: boolean
}

interface ActivityFeedProps {
  entries: ActivityEntry[]
  onViewAllHref?: string
  delay?: number
  className?: string
}

export function ActivityFeed({
  entries,
  onViewAllHref = "/nutrition/logs",
  delay = 0,
  className,
}: ActivityFeedProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay }}
    >
      <Card className={cn("p-5 card-hover", className)}>
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-primary">Recent Nutritional Log</h3>
          <Link
            href={onViewAllHref}
            className="text-xs font-semibold text-brand-primary transition-colors hover:text-brand"
          >
            FULL HISTORY →
          </Link>
        </div>

        <div className="mt-4 space-y-3">
          {entries.length === 0 ? (
            <p className="text-sm text-primary-muted">No meals logged yet today.</p>
          ) : (
            entries.map((entry) => (
              <div
                key={entry.id}
                className="flex items-center gap-3 rounded-xl border border-border bg-surface-high/30 p-3"
              >
                <span className="rounded-full bg-brand-primary/15 px-2.5 py-1 text-[11px] font-semibold text-brand-primary">
                  {entry.category}
                </span>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium text-primary">{entry.title}</p>
                  <p className="truncate text-xs text-primary-muted">{entry.detail}</p>
                </div>
                {entry.isDemo && (
                  <span className="rounded-full border border-border px-2 py-0.5 text-[10px] text-primary-muted">
                    demo
                  </span>
                )}
              </div>
            ))
          )}
        </div>
      </Card>
    </motion.div>
  )
}
