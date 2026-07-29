"use client"

import { motion } from "framer-motion"
import { Card } from "@/components/ui/card"
import { formatDecimalWhole } from "@/lib/format"
import { cn } from "@/lib/utils"

interface RemainingCaloriesCardProps {
  consumed: string | null
  target: string | null
  remaining: string | null
  burnedKcal?: number
  delay?: number
  className?: string
}

export function RemainingCaloriesCard({
  consumed,
  target,
  remaining,
  burnedKcal = 0,
  delay = 0,
  className,
}: RemainingCaloriesCardProps) {
  const consumedNum = consumed ? Number(consumed) : 0
  const targetNum = target ? Number(target) : 0
  const remainingNum = remaining ? Number(remaining) : Math.max(targetNum - consumedNum, 0)

  const size = 200
  const stroke = 14
  const radius = (size - stroke) / 2
  const circumference = 2 * Math.PI * radius
  const pct = targetNum > 0 ? Math.min(consumedNum / targetNum, 1) : 0
  const offset = circumference * (1 - pct)

  return (
    <Card className={cn("relative overflow-hidden p-6", className)}>
      <div className="pointer-events-none absolute inset-0 bg-gradient-to-b from-brand-primary/5 to-transparent" />
      <div className="relative flex flex-col items-center">
        <div className="relative" style={{ width: size, height: size }}>
          <svg width={size} height={size} className="-rotate-90">
            <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth={stroke} />
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
              style={{ filter: "drop-shadow(0 0 12px rgba(98,223,125,0.4))" }}
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
            <span className="text-4xl font-bold text-primary leading-none">
              {formatDecimalWhole(String(remainingNum))}
            </span>
            <span className="mt-2 text-[10px] font-bold uppercase tracking-[0.2em] text-primary-muted">
              Kcal Remaining
            </span>
          </div>
        </div>

        <div className="mt-5 grid w-full grid-cols-2 gap-3">
          <div className="rounded-2xl border border-border bg-surface-high/40 p-3">
            <p className="text-[9px] font-bold uppercase tracking-widest text-primary-muted">Total Intake</p>
            <p className="mt-1 text-xl font-bold text-primary">{formatDecimalWhole(String(consumedNum))}</p>
          </div>
          <div className="rounded-2xl border border-border bg-surface-high/40 p-3">
            <p className="text-[9px] font-bold uppercase tracking-widest text-primary-muted">Burned</p>
            <p className="mt-1 text-xl font-bold text-brand-primary">{burnedKcal ? burnedKcal : "—"}</p>
          </div>
        </div>
      </div>
    </Card>
  )
}
