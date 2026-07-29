"use client"

import { Card } from "@/components/ui/card"
import type { DemoFood } from "@/components/nutrition-search/placeholders"
import { cn } from "@/lib/utils"

interface MacroCardProps {
  food: DemoFood
  className?: string
}

export function MacroCard({ food, className }: MacroCardProps) {
  const proteinPct =
    food.protein_g + food.fat_g + food.carbs_g > 0
      ? Math.round(
          (food.protein_g / (food.protein_g + food.fat_g + food.carbs_g)) * 100,
        )
      : 0
  const fatPct =
    food.protein_g + food.fat_g + food.carbs_g > 0
      ? Math.round((food.fat_g / (food.protein_g + food.fat_g + food.carbs_g)) * 100)
      : 0
  const carbPct = Math.max(0, 100 - proteinPct - fatPct)

  const rows = [
    { label: "Protein", value: `${food.protein_g}g`, pct: proteinPct, color: "bg-brand", ring: "ring-brand-light" },
    { label: "Lipids", value: `${food.fat_g}g`, pct: fatPct, color: "bg-warning", ring: "ring-warning/10" },
    { label: "Glycogen", value: `${food.carbs_g}g`, pct: carbPct, color: "bg-info", ring: "ring-info/10" },
  ]

  return (
    <Card variant="glass" className={cn("p-4 rounded-2xl border-white/5", className)}>
      <h4 className="text-xs text-primary-muted uppercase tracking-widest mb-3 opacity-60">
        Macro Profile
      </h4>
      <div className="flex h-3 w-full rounded-full overflow-hidden mb-4 bg-surface-highest">
        <div className={cn("h-full", rows[0].color)} style={{ width: `${proteinPct}%` }} />
        <div className={cn("h-full", rows[1].color)} style={{ width: `${fatPct}%` }} />
        <div className={cn("h-full", rows[2].color)} style={{ width: `${carbPct}%` }} />
      </div>
      <div className="space-y-3">
        {rows.map((row) => (
          <div key={row.label} className="flex justify-between items-center">
            <div className="flex items-center gap-3">
              <span className={cn("w-2.5 h-2.5 rounded-full ring-4", row.color, row.ring)} />
              <span className="text-sm text-primary-secondary">{row.label}</span>
            </div>
            <span className="font-semibold text-primary">
              {row.value}{" "}
              <span className="text-xs font-normal opacity-40 ml-1">{row.pct}%</span>
            </span>
          </div>
        ))}
      </div>
    </Card>
  )
}
