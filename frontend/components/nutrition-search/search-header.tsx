"use client"

import { Sparkles } from "lucide-react"
import { cn } from "@/lib/utils"

interface SearchHeaderProps {
  title?: string
  description?: string
  className?: string
}

export function SearchHeader({
  title = "Nutrition Search",
  description = "Search foods and analyze their macro profile.",
  className,
}: SearchHeaderProps) {
  return (
    <div className={cn("flex items-start justify-between gap-4", className)}>
      <div>
        <div className="flex items-center gap-2 mb-1">
          <Sparkles className="h-5 w-5 text-brand" aria-hidden="true" />
          <h1 className="text-2xl font-bold text-primary">{title}</h1>
        </div>
        <p className="text-sm text-primary-secondary">{description}</p>
      </div>
    </div>
  )
}
