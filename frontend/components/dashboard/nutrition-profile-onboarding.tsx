"use client"

import { motion } from "framer-motion"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { ArrowRight, Salad } from "lucide-react"
import { useRouter } from "next/navigation"

interface NutritionProfileOnboardingProps {
  delay?: number
}

const features = [
  "Daily Calories",
  "Protein Goal",
  "Carbohydrate Goal",
  "Fat Goal",
  "BMI & Analytics",
  "Progress Tracking",
  "AI Recommendations",
  "Dashboard Insights",
]

export function NutritionProfileOnboarding({
  delay = 0,
}: NutritionProfileOnboardingProps) {
  const router = useRouter()

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay }}
    >
      <Card className="p-6 text-center card-hover">
        <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-brand-primary/10">
          <Salad className="h-6 w-6 text-brand-primary" />
        </div>

        <h2 className="text-lg font-bold text-primary">
          Complete Your Nutrition Profile
        </h2>

        <p className="mt-1.5 text-sm text-primary-secondary max-w-md mx-auto">
          Unlock personalized nutrition targets, AI insights, and progress tracking.
        </p>

        <div className="mt-4 grid grid-cols-2 gap-x-4 gap-y-1 text-left max-w-xs mx-auto">
          {features.map((feature) => (
            <div key={feature} className="flex items-center gap-1.5">
              <span className="h-1 w-1 rounded-full bg-brand shrink-0" />
              <span className="text-xs text-primary-secondary leading-tight">{feature}</span>
            </div>
          ))}
        </div>

        <Button
          size="sm"
          className="mt-4"
          onClick={() => router.push("/settings?tab=profile")}
        >
          Complete Profile
          <ArrowRight className="ml-1.5 h-3.5 w-3.5" />
        </Button>
      </Card>
    </motion.div>
  )
}
