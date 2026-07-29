"use client"

import { History, TrendingUp } from "lucide-react"
import {
  DEMO_RECENT_SEARCHES,
  DEMO_SUGGESTIONS,
} from "@/components/nutrition-search/placeholders"

interface SearchSuggestionsProps {
  onSelect: (term: string) => void
}

export function SearchSuggestions({ onSelect }: SearchSuggestionsProps) {
  return (
    <div className="space-y-6">
      <section>
        <div className="flex items-center gap-2 mb-3">
          <History className="h-4 w-4 text-brand" aria-hidden="true" />
          <h2 className="text-sm font-semibold text-primary">Recent Analysis</h2>
        </div>
        <div className="flex flex-wrap gap-2">
          {DEMO_RECENT_SEARCHES.map((term) => (
            <button
              key={term}
              type="button"
              onClick={() => onSelect(term)}
              className="px-4 py-2 bg-surface-high border border-border rounded-2xl text-xs text-primary-secondary cursor-pointer hover:border-brand hover:text-brand transition-all"
            >
              {term}
            </button>
          ))}
        </div>
      </section>

      <section>
        <div className="flex items-center gap-2 mb-3">
          <TrendingUp className="h-4 w-4 text-brand" aria-hidden="true" />
          <h2 className="text-sm font-semibold text-primary">Suggestions</h2>
        </div>
        <div className="flex flex-wrap gap-2">
          {DEMO_SUGGESTIONS.map((term) => (
            <button
              key={term}
              type="button"
              onClick={() => onSelect(term)}
              className="px-4 py-2 bg-surface-high border border-border rounded-2xl text-xs text-primary-secondary cursor-pointer hover:border-brand hover:text-brand transition-all"
            >
              {term}
            </button>
          ))}
        </div>
      </section>
    </div>
  )
}
