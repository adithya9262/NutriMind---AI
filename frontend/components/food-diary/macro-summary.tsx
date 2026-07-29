"use client"

import { motion } from "framer-motion"
import { Card } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { formatDecimalWhole } from "@/lib/format"
import type {
  NutrientProgressData,
  NutritionProgressStatus,
} from "@/types/nutrition"
import { PROGRESS_STATUS_LABELS } from "@/types/nutrition"
import { cn } from "@/lib/utils"

interface MacroSummaryProps {
  protein: NutrientProgressData | null
  carbohydrate: NutrientProgressData | null
  fat: NutrientProgressData | null
  delay?: number
  className?: string
}

const statusVariant: Record<NutritionProgressStatus, "default" | "success" | "warning"> = {
  below_target: "default",
  target_met: "success",
  above_target: "warning",
}

export function MacroSummary({
  protein,
  carbohydrate,
  fat,
  delay = 0,
  className,
}: MacroSummaryProps) {
  const rows = [
    { label: "Protein Protocol", data: protein },
    { label: "Glycogen (Carbs)", data: carbohydrate },
    { label: "Lipids (Fats)", data: fat },
  ]

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay }}
    >
      <Card className={cn("space-y-5 p-5", className)}>
        <div className="flex items-center justify-between">
          <h3 className="text-[11px] font-bold uppercase tracking-widest text-primary">
            Macro-Nutrient Ratios
          </h3>
        </div>
        <div className="space-y-4">
          {rows.map((row) => {
            const data = row.data
            const current = data ? Number(data.consumed) : 0
            const target = data ? Number(data.target) : 0
            const variant = data ? statusVariant[data.status] : "default"
            return (
              <div key={row.label} className="space-y-1.5">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-primary-secondary">{row.label}</span>
                  <span className="text-primary">
                    {data ? (
                      <>
                        <span className="font-semibold text-brand-primary">{formatDecimalWhole(String(current))}g</span>
                        {" / "}{formatDecimalWhole(String(target))}g
                      </>
                    ) : (
                      <span className="text-primary-muted">—</span>
                    )}
                  </span>
                </div>
                <Progress
                  value={current}
                  max={target || 1}
                  variant={variant}
                  size="sm"
                />
                {data && (
                  <p className="text-[10px] uppercase tracking-wide text-primary-muted">
                    {PROGRESS_STATUS_LABELS[data.status]}
                  </p>
                )}
              </div>
            )
          })}
        </div>
      </Card>
    </motion.div>
  )
}
