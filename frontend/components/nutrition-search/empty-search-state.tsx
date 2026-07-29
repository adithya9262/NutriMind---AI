"use client"

import { SearchX } from "lucide-react"
import { EmptyState } from "@/components/ui/empty-state"

interface EmptySearchStateProps {
  query?: string
}

export function EmptySearchState({ query }: EmptySearchStateProps) {
  return (
    <EmptyState
      icon={<SearchX className="h-8 w-8" aria-hidden="true" />}
      title={query ? "No matches found" : "Start your nutrition search"}
      description={
        query
          ? `No demo results for “${query}”. Try a sample term like “Salmon”.`
          : "Search for foods to view their macro profile and metabolic insights."
      }
    />
  )
}
