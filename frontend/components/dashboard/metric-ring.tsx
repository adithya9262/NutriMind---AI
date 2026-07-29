"use client"

import { motion } from "framer-motion"
import { cn } from "@/lib/utils"

interface MetricRingProps {
  value: number
  max: number
  centerValue: string
  centerUnit?: string
  footerLabel?: string
  footerValue?: string
  size?: number
  stroke?: number
  delay?: number
  className?: string
}

export function MetricRing({
  value,
  max,
  centerValue,
  centerUnit,
  footerLabel,
  footerValue,
  size = 180,
  stroke = 12,
  delay = 0,
  className,
}: MetricRingProps) {
  const radius = (size - stroke) / 2
  const circumference = 2 * Math.PI * radius
  const pct = max > 0 ? Math.min(value / max, 1) : 0
  const offset = circumference * (1 - pct)

  return (
    <div className={cn("flex flex-col items-center", className)}>
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="-rotate-90">
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="rgba(255,255,255,0.08)"
            strokeWidth={stroke}
          />
          <motion.circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="var(--color-brand-primary)"
            strokeWidth={stroke}
            strokeLinecap="round"
            strokeDasharray={circumference}
            initial={{ strokeDashoffset: circumference }}
            animate={{ strokeDashoffset: offset }}
            transition={{ duration: 1, delay, ease: "easeOut" }}
            style={{ filter: "drop-shadow(0 0 6px rgba(98,223,125,0.5))" }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-3xl font-bold text-primary leading-none">{centerValue}</span>
          {centerUnit && (
            <span className="mt-1 text-[10px] font-semibold uppercase tracking-[0.2em] text-primary-muted">
              {centerUnit}
            </span>
          )}
        </div>
      </div>
      {(footerLabel || footerValue) && (
        <div className="mt-4 flex w-full items-center justify-between border-t border-border pt-3">
          {footerLabel && <span className="text-xs text-primary-secondary">{footerLabel}</span>}
          {footerValue && <span className="text-sm font-semibold text-primary">{footerValue}</span>}
        </div>
      )}
    </div>
  )
}
