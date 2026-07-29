"use client"

import { Card } from "@/components/ui/card"
import type { DemoFood } from "@/components/nutrition-search/placeholders"
import { cn } from "@/lib/utils"

interface NutritionFactsProps {
  food: DemoFood
  className?: string
}

export function NutritionFacts({ food, className }: NutritionFactsProps) {
  return (
    <div className={cn("space-y-4", className)}>
      <div>
        <h4 className="text-xs text-primary-muted uppercase tracking-widest mb-2 opacity-60">
          Metabolic Insight
        </h4>
        <p className="text-sm text-primary/80 leading-relaxed italic">{food.insight}</p>
      </div>

      <div className="grid grid-cols-2 gap-3">
        {food.stats.map((stat) => (
          <Card
            key={stat.label}
            variant="glass"
            className="p-3 rounded-2xl flex flex-col gap-1"
          >
            <span className="text-[9px] uppercase tracking-widest text-primary-muted opacity-50">
              {stat.label}
            </span>
            <span className="font-semibold text-brand">{stat.value}</span>
          </Card>
        ))}
      </div>
    </div>
  )
}
