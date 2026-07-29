"use client"

import { motion } from "framer-motion"
import { Card } from "@/components/ui/card"
import { Leaf, Sparkles } from "lucide-react"

interface GreetingCardProps {
  name: string
}

export function GreetingCard({ name }: GreetingCardProps) {
  const hour = new Date().getHours()
  let greeting = "Good evening"
  if (hour < 12) greeting = "Good morning"
  else if (hour < 17) greeting = "Good afternoon"

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      <Card variant="brand" className="p-6 sm:p-8 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-64 h-64 bg-white/5 rounded-full -translate-y-1/2 translate-x-1/2" />
        <div className="absolute bottom-0 left-0 w-48 h-48 bg-white/5 rounded-full translate-y-1/2 -translate-x-1/2" />

        <div className="relative">
          <div className="flex items-center gap-2 text-white/80 text-sm font-medium mb-2">
            <Sparkles className="h-4 w-4" />
            <span>AI Nutrition Dashboard</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white">
            {greeting}, {name}
          </h1>
          <p className="text-white/70 mt-2 max-w-xl text-sm sm:text-base">
            Here&apos;s your personalized nutrition overview for today.
            Stay consistent, stay healthy.
          </p>
          <div className="flex items-center gap-4 mt-4 flex-wrap">
            <div className="flex items-center gap-1.5 text-white/60 text-xs">
              <Leaf className="h-3.5 w-3.5" />
              AI-powered insights
            </div>
          </div>
        </div>
      </Card>
    </motion.div>
  )
}
