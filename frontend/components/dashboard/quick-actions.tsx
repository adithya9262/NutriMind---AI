"use client"

import { motion } from "framer-motion"
import { Card } from "@/components/ui/card"
import Link from "next/link"
import { ClipboardList, Weight, CheckSquare, Bot, ArrowRight } from "lucide-react"
import { cn } from "@/lib/utils"

const actions = [
  { label: "Log Food", href: "/nutrition/logs", icon: ClipboardList, color: "text-brand bg-brand-light" },
  { label: "Add Weight", href: "/body-weight", icon: Weight, color: "text-info bg-info-light" },
  { label: "Add Task", href: "/tasks", icon: CheckSquare, color: "text-warning bg-warning-light" },
  { label: "Open AI Coach", href: "/ai-coach", icon: Bot, color: "text-brand bg-brand-light" },
]

export function QuickActions() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: 0.35 }}
    >
      <Card className="p-5">
        <h3 className="text-sm font-semibold text-primary mb-3">Quick Actions</h3>
        <div className="grid grid-cols-2 gap-2">
          {actions.map((action) => (
            <Link
              key={action.href}
              href={action.href}
              className={cn(
                "flex items-center gap-2.5 p-3 rounded-xl transition-all duration-200 group",
                "hover:bg-brand-subtle hover:shadow-sm",
              )}
            >
              <div className={cn("p-2 rounded-lg", action.color)}>
                <action.icon className="h-4 w-4" />
              </div>
              <span className="text-xs font-medium text-primary group-hover:text-brand transition-colors flex-1">
                {action.label}
              </span>
              <ArrowRight className="h-3.5 w-3.5 text-primary-muted group-hover:text-brand transition-colors" />
            </Link>
          ))}
        </div>
      </Card>
    </motion.div>
  )
}
