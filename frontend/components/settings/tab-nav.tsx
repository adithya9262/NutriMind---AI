"use client"

import { cn } from "@/lib/utils"
import { ChevronRight } from "lucide-react"
import type { LucideIcon } from "lucide-react"

export interface Tab {
  id: string
  label: string
  icon: LucideIcon
}

export function TabNav({ tabs, activeTab, onTabChange }: { tabs: readonly Tab[]; activeTab: string; onTabChange: (id: string) => void }) {
  return (
    <nav className="lg:w-56 shrink-0" aria-label="Settings tabs">
      <div className="flex lg:flex-col gap-1 overflow-x-auto lg:overflow-visible pb-2 lg:pb-0">
        {tabs.map((tab) => {
          const active = activeTab === tab.id
          return (
            <button
              key={tab.id}
              type="button"
              onClick={() => onTabChange(tab.id)}
              className={cn(
                "flex items-center gap-2.5 px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 whitespace-nowrap",
                active
                  ? "bg-brand-light text-brand shadow-sm"
                  : "text-primary-secondary hover:bg-brand-subtle hover:text-primary",
              )}
              aria-current={active ? "true" : undefined}
            >
              <tab.icon className="h-4 w-4 flex-shrink-0" />
              <span className="hidden lg:inline">{tab.label}</span>
              <ChevronRight className={cn("h-3.5 w-3.5 ml-auto hidden lg:block", active ? "text-brand" : "text-transparent")} />
            </button>
          )
        })}
      </div>
    </nav>
  )
}
