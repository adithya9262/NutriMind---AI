"use client"

import { cn } from "@/lib/utils"

interface VelocityToGoalRingProps {
  percentage: number
  label?: string
  className?: string
}

export function VelocityToGoalRing({
  percentage,
  label = "Velocity to Goal",
  className,
}: VelocityToGoalRingProps) {
  const clamped = Math.max(0, Math.min(100, percentage))
  const radius = 80
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (clamped / 100) * circumference

  return (
    <div className={cn("flex flex-col items-center justify-center py-5 border-b border-white/5", className)}>
      <h4 className="text-xs uppercase tracking-[0.2em] text-primary-muted mb-4">
        {label}
      </h4>
      <div className="relative w-44 h-44">
        <svg className="w-full h-full -rotate-90" viewBox="0 0 200 200">
          <circle
            className="text-white/5"
            cx="100"
            cy="100"
            fill="transparent"
            r={radius}
            stroke="currentColor"
            strokeWidth="12"
          />
          <circle
            className="text-brand transition-all duration-500"
            cx="100"
            cy="100"
            fill="transparent"
            r={radius}
            stroke="currentColor"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
            strokeWidth="12"
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-[42px] leading-none font-bold text-primary">
            {Math.round(clamped)}%
          </span>
          <span className="text-xs text-brand font-bold uppercase tracking-tight">
            Optimized
          </span>
        </div>
      </div>
    </div>
  )
}
