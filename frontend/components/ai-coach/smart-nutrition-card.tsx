import React from "react"
import { motion } from "framer-motion"
import { Activity, Apple, Target, List, Droplet, Zap, type LucideIcon } from "lucide-react"
import { cn } from "@/lib/utils"

interface CardData {
  type: string
  title?: string
  current_value?: string
  target?: string
  progress_percent?: number
  recommendations?: string[]
}

const icons: Record<string, LucideIcon> = {
  NutritionCard: Apple,
  MealSuggestionCard: Activity,
  MacroProgressCard: Target,
  ShoppingListCard: List,
  HydrationCard: Droplet,
  MicronutrientCard: Zap,
}

export function SmartNutritionCard({ data }: { data: CardData }) {
  const Icon = icons[data.type] || Activity

  return (
    <div className="my-4 overflow-hidden rounded-2xl border border-border bg-surface-high shadow-sm">
      <div className="flex items-center gap-3 border-b border-border bg-brand/5 px-4 py-3">
        <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-brand/10">
          <Icon className="h-4 w-4 text-brand" />
        </div>
        <h4 className="font-semibold text-primary">{data.title || "Nutrition Update"}</h4>
      </div>
      
      <div className="p-4 space-y-4">
        {(data.current_value || data.target) && (
          <div className="grid grid-cols-2 gap-4">
            {data.current_value && (
              <div className="rounded-xl bg-surface px-3 py-2 border border-border/50">
                <p className="text-xs font-medium text-primary-secondary uppercase tracking-wider mb-1">Current</p>
                <p className="text-sm font-semibold text-primary">{data.current_value}</p>
              </div>
            )}
            {data.target && (
              <div className="rounded-xl bg-surface px-3 py-2 border border-border/50">
                <p className="text-xs font-medium text-primary-secondary uppercase tracking-wider mb-1">Target</p>
                <p className="text-sm font-semibold text-primary">{data.target}</p>
              </div>
            )}
          </div>
        )}
        
        {typeof data.progress_percent === 'number' && (
          <div className="space-y-1.5">
            <div className="flex justify-between text-xs">
              <span className="font-medium text-primary-secondary">Progress</span>
              <span className="font-bold text-primary">{data.progress_percent}%</span>
            </div>
            <div className="h-2 w-full overflow-hidden rounded-full bg-surface border border-border/50">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${Math.min(100, Math.max(0, data.progress_percent))}%` }}
                transition={{ duration: 1, ease: "easeOut" }}
                className={cn(
                  "h-full rounded-full",
                  data.progress_percent >= 100 ? "bg-green-500" : "bg-brand"
                )}
              />
            </div>
          </div>
        )}
        
        {data.recommendations && data.recommendations.length > 0 && (
          <div className="pt-2 border-t border-border/50">
            <h5 className="text-xs font-semibold text-primary-secondary uppercase tracking-wider mb-2">Recommendations</h5>
            <ul className="space-y-2">
              {data.recommendations.map((rec, idx) => (
                <li key={idx} className="flex items-start gap-2 text-sm text-primary">
                  <span className="mt-1 flex h-1.5 w-1.5 shrink-0 rounded-full bg-brand/60" />
                  <span className="leading-snug">{rec}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  )
}
