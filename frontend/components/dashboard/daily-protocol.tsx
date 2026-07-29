"use client"

import { motion } from "framer-motion"
import { Card } from "@/components/ui/card"
import { Check } from "lucide-react"
import { cn } from "@/lib/utils"

interface ProtocolItem {
  label: string
  done: boolean
}

interface DailyProtocolProps {
  items: ProtocolItem[]
  delay?: number
  className?: string
}

const defaultItems: ProtocolItem[] = [
  { label: "Log your breakfast", done: false },
  { label: "Drink 8 glasses of water", done: false },
  { label: "Log your lunch", done: false },
  { label: "Complete your meals for today", done: false },
]

export function DailyProtocol({ items, delay = 0, className }: DailyProtocolProps) {
  const displayItems = items.length > 0 ? items : defaultItems

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay }}
    >
      <Card className={cn("p-5 card-hover", className)}>
        <h3 className="text-sm font-semibold text-primary">
          {items.length > 0 ? "Daily Protocol" : "Daily Recommendations"}
        </h3>
        <ul className="mt-3 space-y-1">
          {displayItems.map((item, i) => (
            <li
              key={i}
              className={cn(
                "flex items-center gap-3 rounded-xl px-2 py-2 text-sm",
                item.done ? "text-primary-muted line-through" : "text-primary",
              )}
            >
              <span
                className={cn(
                  "grid h-5 w-5 flex-shrink-0 place-items-center rounded-md border transition-colors",
                  item.done
                    ? "border-brand-primary bg-brand-primary/20 text-brand-primary"
                    : "border-border",
                )}
                aria-hidden="true"
              >
                {item.done && <Check className="h-3.5 w-3.5" />}
              </span>
              {item.label}
            </li>
          ))}
        </ul>
      </Card>
    </motion.div>
  )
}
