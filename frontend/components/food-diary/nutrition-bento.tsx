"use client"

import { motion } from "framer-motion"
import { Card } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Droplets, Compass } from "lucide-react"
import { FOOD_DIARY_PLACEHOLDERS } from "./placeholders"
import { cn } from "@/lib/utils"

interface NutritionBentoProps {
  delay?: number
  className?: string
}

export function NutritionBento({ delay = 0, className }: NutritionBentoProps) {
  const { hydration, fiber } = FOOD_DIARY_PLACEHOLDERS
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay }}
    >
      <div className={cn("grid grid-cols-2 gap-4", className)}>
        <Card className="flex flex-col gap-2 p-4">
          <div className="flex items-center gap-2 text-brand-primary">
            <Droplets className="h-4 w-4" aria-hidden="true" />
            <span className="text-[9px] font-bold uppercase tracking-widest">Hydration</span>
          </div>
          <p className="text-xl font-bold text-primary">{hydration.currentL}L</p>
          <Progress value={hydration.currentL} max={hydration.targetL} size="sm" />
          <span className="text-[10px] text-primary-muted">demo · target {hydration.targetL}L</span>
        </Card>

        <Card className="flex flex-col gap-2 p-4">
          <div className="flex items-center gap-2 text-tertiary">
            <Compass className="h-4 w-4" aria-hidden="true" />
            <span className="text-[9px] font-bold uppercase tracking-widest">Fiber</span>
          </div>
          <p className="text-xl font-bold text-primary">{fiber.currentG}g</p>
          <Progress value={fiber.currentG} max={fiber.targetG} size="sm" />
          <span className="text-[10px] text-primary-muted">demo · target {fiber.targetG}g</span>
        </Card>
      </div>
    </motion.div>
  )
}
