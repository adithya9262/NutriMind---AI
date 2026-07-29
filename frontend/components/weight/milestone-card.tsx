"use client"

import { Flame, Zap, Award, Dumbbell } from "lucide-react"
import { cn } from "@/lib/utils"
import type { WeightMilestone } from "./placeholders"

const iconMap = {
  streak: Award,
  metabolic: Zap,
  fat: Flame,
  lean: Dumbbell,
}

interface MilestoneCardProps {
  milestone: WeightMilestone
}

export function MilestoneCard({ milestone }: MilestoneCardProps) {
  const Icon = iconMap[milestone.icon]

  return (
    <div
      className={cn(
        "rounded-3xl p-4 flex flex-col gap-3 transition-all",
        milestone.unlocked
          ? "glass-card premium-shadow hover:-translate-y-2 cursor-pointer"
          : "bg-surface-low opacity-40 grayscale border border-dashed border-white/10",
      )}
    >
      <div
        className={cn(
          "w-14 h-14 rounded-2xl flex items-center justify-center transition-transform",
          milestone.unlocked ? "bg-brand-light text-brand" : "bg-white/5 text-primary-muted",
        )}
      >
        <Icon className="h-8 w-8" aria-hidden="true" />
      </div>
      <div>
        <p className="font-semibold text-primary mb-1">{milestone.title}</p>
        <p className="text-xs text-primary-secondary leading-relaxed">
          {milestone.description}
        </p>
      </div>
    </div>
  )
}
