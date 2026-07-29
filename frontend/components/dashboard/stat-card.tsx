"use client"

import { motion } from "framer-motion"
import { cn } from "@/lib/utils"
import { Card } from "@/components/ui/card"
import type { ReactNode } from "react"

interface StatCardProps {
  label: string
  value: string | number
  unit?: string
  icon: ReactNode
  trend?: { value: string; positive: boolean }
  color?: "brand" | "warning" | "error" | "info"
  className?: string
  delay?: number
}

const colorVariants = {
  brand: "bg-brand-light text-brand",
  warning: "bg-warning-light text-warning",
  error: "bg-error-light text-error",
  info: "bg-info-light text-info",
}

export function StatCard({
  label,
  value,
  unit,
  icon,
  trend,
  color = "brand",
  className = "",
  delay = 0,
}: StatCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay }}
    >
      <Card className={cn("p-5 card-hover", className)}>
        <div className="flex items-start justify-between mb-3">
          <div className={cn("p-2.5 rounded-xl", colorVariants[color])}>
            {icon}
          </div>
          {trend && (
            <span
              className={cn(
                "text-xs font-medium px-2 py-0.5 rounded-full",
                trend.positive
                  ? "bg-success-light text-success"
                  : "bg-error-light text-error",
              )}
            >
              {trend.positive ? "↑" : "↓"} {trend.value}
            </span>
          )}
        </div>
        <p className="text-xs font-medium text-primary-muted uppercase tracking-wider">
          {label}
        </p>
        <div className="flex items-baseline gap-1 mt-1">
          <span className="text-2xl font-bold text-primary">{value}</span>
          {unit && (
            <span className="text-sm text-primary-secondary">{unit}</span>
          )}
        </div>
      </Card>
    </motion.div>
  )
}
