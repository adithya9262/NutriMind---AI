"use client"

import { useState, useRef, useEffect } from "react"
import { Search, Loader2 } from "lucide-react"
import { Input } from "@/components/ui/input"
import { globalSearch } from "@/services/api/search"
import { cn } from "@/lib/utils"
import type { SearchResult } from "@/types/search"

export function GlobalSearch() {
  const [query, setQuery] = useState("")
  const [results, setResults] = useState<SearchResult | null>(null)
  const [open, setOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    if (!query.trim()) {
      setResults(null)
      setOpen(false)
      return
    }
    if (timerRef.current) clearTimeout(timerRef.current)
    setLoading(true)
    timerRef.current = setTimeout(async () => {
      const res = await globalSearch(query.trim())
      if (res.success) {
        setResults(res.data)
        setOpen(true)
      }
      setLoading(false)
    }, 300)
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current)
    }
  }, [query])

  const resultCount = results
    ? (results.foods?.length || 0) + (results.tasks?.length || 0)
    : 0

  return (
    <div className="relative max-w-md">
      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-primary-muted" />
        <Input
          value={query}
          onChange={e => setQuery(e.target.value)}
          onFocus={() => results && setOpen(true)}
          onBlur={() => setTimeout(() => setOpen(false), 200)}
          placeholder="Search meals, tasks..."
          aria-label="Global search"
          className="pl-10 pr-10"
        />
        {loading && (
          <Loader2 className="absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-primary-muted animate-spin" />
        )}
      </div>
      {open && results && resultCount > 0 && (
        <div className="absolute z-50 mt-1 w-full rounded-xl border border-border bg-surface shadow-lg">
          {results.foods?.length > 0 && (
            <div className="p-2">
              <p className="px-2 py-1 text-[11px] font-semibold uppercase tracking-wider text-primary-muted">
                Meals
              </p>
              {results.foods.slice(0, 5).map((food, i) => (
                <div
                  key={`food-${i}`}
                  className="flex items-center justify-between rounded-lg px-2 py-1.5 text-sm hover:bg-surface-high"
                >
                  <span className="text-primary">{food.food_name}</span>
                  <span className="text-xs text-primary-muted">{food.calories_kcal} kcal</span>
                </div>
              ))}
            </div>
          )}
          {results.tasks?.length > 0 && (
            <div className="border-t border-border p-2">
              <p className="px-2 py-1 text-[11px] font-semibold uppercase tracking-wider text-primary-muted">
                Tasks
              </p>
              {results.tasks.slice(0, 5).map((task, i) => (
                <div
                  key={`task-${i}`}
                  className="flex items-center justify-between rounded-lg px-2 py-1.5 text-sm hover:bg-surface-high"
                >
                  <span className="text-primary">{task.title}</span>
                  <span className={cn("text-xs", task.status === "completed" ? "text-success" : "text-primary-muted")}>
                    {task.status}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
      {open && results && resultCount === 0 && (
        <div className="absolute z-50 mt-1 w-full rounded-xl border border-border bg-surface p-4 text-center text-sm text-primary-muted shadow-lg">
          No results found for &ldquo;{query}&rdquo;
        </div>
      )}
    </div>
  )
}
