"use client"

import { motion } from "framer-motion"
import { Card } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { cn } from "@/lib/utils"

interface NutrientData {
  label: string
  current: number
  target: number
  unit: string
  color?: "default" | "success" | "warning" | "error"
}

interface NutritionProgressProps {
  data: NutrientData[]
  className?: string
  delay?: number
}

export function NutritionProgress({
  data,
  className = "",
  delay = 0,
}: NutritionProgressProps) {
  if (!data.length) {
    data = [
      { label: "Calories", current: 0, target: 2000, unit: "kcal" },
      { label: "Protein", current: 0, target: 120, unit: "g" },
      { label: "Carbs", current: 0, target: 250, unit: "g" },
      { label: "Fat", current: 0, target: 65, unit: "g" },
    ]
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay }}
    >
      <Card className={cn("p-5 card-hover", className)}>
        <h3 className="text-sm font-semibold text-primary mb-4">Today&apos;s Nutrition</h3>
        <div className="space-y-4">
          {data.map((item, i) => {
            const color = item.current > item.target
              ? "warning"
              : item.color || "default"

            return (
              <div key={i}>
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-xs font-medium text-primary">{item.label}</span>
                  <span className="text-xs text-primary-muted">
                    <span className="font-semibold text-primary">{Math.round(item.current)}</span>
                    {" / "}{item.target}{item.unit}
                  </span>
                </div>
                <Progress value={item.current} max={item.target} variant={color} size="sm" />
              </div>
            )
          })}
        </div>
      </Card>
    </motion.div>
  )
}
