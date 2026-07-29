"use client"

import { motion } from "framer-motion"
import { Bot } from "lucide-react"
import { FOOD_DIARY_PLACEHOLDERS } from "./placeholders"
import { cn } from "@/lib/utils"

interface AIInsightMiniProps {
  delay?: number
  className?: string
}

export function AIInsightMini({ delay = 0, className }: AIInsightMiniProps) {
  const { insight } = FOOD_DIARY_PLACEHOLDERS
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay }}
    >
      <div
        className={cn(
          "flex gap-3 rounded-xl border-l-2 border-brand-primary/40 bg-gradient-to-r from-brand-primary/10 to-transparent p-4",
          className,
        )}
      >
        <span className="grid h-10 w-10 flex-shrink-0 place-items-center rounded-full bg-brand-primary/20">
          <Bot className="h-5 w-5 text-brand-primary" aria-hidden="true" />
        </span>
        <div className="flex flex-col gap-1">
          <p className="text-[10px] font-bold uppercase tracking-widest text-brand-primary">
            {insight.label}
          </p>
          <p className="text-[13px] leading-relaxed text-primary-secondary">
            <span className="text-primary-muted">demo · </span>
            {insight.body}
          </p>
        </div>
      </div>
    </motion.div>
  )
}
