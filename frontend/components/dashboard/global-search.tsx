"use client"

import { useState, useRef, useEffect, useCallback } from "react"
import { Search, Loader2, AlertCircle, Database, Leaf } from "lucide-react"
import { Input } from "@/components/ui/input"
import { globalSearch } from "@/services/api/search"
import { cn } from "@/lib/utils"
import type { SearchResult, SearchFood } from "@/types/search"

export function GlobalSearch() {
  const [query, setQuery] = useState("")
  const [results, setResults] = useState<SearchResult | null>(null)
  const [open, setOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const queryIdRef = useRef(0)

  const performSearch = useCallback(async (searchQuery: string, currentQueryId: number) => {
    setLoading(true)
    setError(null)
    try {
      const res = await globalSearch(searchQuery)
      // Ignore stale responses
      if (currentQueryId !== queryIdRef.current) return
      if (res.success) {
        setResults(res.data)
        setOpen(true)
      } else {
        setError(res.error?.message || "Search failed. Please try again.")
        setResults(null)
        setOpen(false)
      }
    } catch {
      if (currentQueryId !== queryIdRef.current) return
      setError("An unexpected error occurred. Please try again.")
      setResults(null)
      setOpen(false)
    } finally {
      if (currentQueryId === queryIdRef.current) {
        setLoading(false)
      }
    }
  }, [])

  useEffect(() => {
    if (!query.trim()) {
      setResults(null)
      setOpen(false)
      setError(null)
      return
    }
    if (timerRef.current) clearTimeout(timerRef.current)
    const currentQueryId = ++queryIdRef.current
    timerRef.current = setTimeout(() => {
      performSearch(query.trim(), currentQueryId)
    }, 300)
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current)
    }
  }, [query, performSearch])

  // Separate personal logs from external suggestions
  const personalFoods = results?.foods?.filter((f: SearchFood) => !f.is_suggestion) ?? []
  const suggestedFoods = results?.foods?.filter((f: SearchFood) => f.is_suggestion) ?? []
  const tasks = results?.tasks ?? []

  const resultCount = (personalFoods.length + suggestedFoods.length + tasks.length)

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
          aria-describedby={loading ? "search-loading" : error ? "search-error" : undefined}
        />
        {loading && (
          <Loader2
            id="search-loading"
            className="absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-primary-muted animate-spin"
            aria-live="polite"
            aria-label="Searching"
          />
        )}
        {error && (
          <AlertCircle
            id="search-error"
            className="absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-error"
            aria-live="assertive"
            aria-label={`Search error: ${error}`}
          />
        )}
      </div>
      {open && results && resultCount > 0 && (
        <div className="absolute z-50 mt-1 w-full rounded-xl border border-border bg-surface shadow-lg">
          {/* Personal logged meals */}
          {personalFoods.length > 0 && (
            <div className="p-2">
              <div className="flex items-center gap-1.5 px-2 py-1 text-[11px] font-semibold uppercase tracking-wider text-primary-muted">
                <Database className="h-3 w-3" aria-hidden="true" />
                <span>Your Meals</span>
              </div>
              {personalFoods.slice(0, 5).map((food, i) => (
                <div
                  key={`personal-food-${i}`}
                  className="flex items-center justify-between rounded-lg px-2 py-1.5 text-sm hover:bg-surface-high"
                >
                  <span className="text-primary">{food.food_name}</span>
                  <span className="text-xs text-primary-muted">{food.calories_kcal} kcal</span>
                </div>
              ))}
            </div>
          )}
          {/* External nutrition database suggestions */}
          {suggestedFoods.length > 0 && (
            <div className={cn("p-2", personalFoods.length > 0 && "border-t border-border")}>
              <div className="flex items-center gap-1.5 px-2 py-1 text-[11px] font-semibold uppercase tracking-wider text-primary-muted">
                <Leaf className="h-3 w-3" aria-hidden="true" />
                <span>Food Suggestions</span>
              </div>
              {suggestedFoods.slice(0, 5).map((food, i) => (
                <div
                  key={`suggestion-food-${i}`}
                  className="flex items-center justify-between rounded-lg px-2 py-1.5 text-sm hover:bg-surface-high"
                >
                  <div className="flex items-center gap-1.5 flex-1 min-w-0">
                    <span className="text-primary truncate">{food.food_name}</span>
                    {food.source && (
                      <span className="shrink-0 text-[10px] uppercase tracking-wider text-primary-muted/50 border border-border rounded-full px-1.5 py-0.5">
                        {food.source === "usda" ? "USDA" : "OFF"}
                      </span>
                    )}
                  </div>
                  <span className="text-xs text-primary-muted">{food.calories_kcal} kcal</span>
                </div>
              ))}
            </div>
          )}
          {tasks.length > 0 && (
            <div className="border-t border-border p-2">
              <p className="px-2 py-1 text-[11px] font-semibold uppercase tracking-wider text-primary-muted">
                Tasks
              </p>
              {tasks.slice(0, 5).map((task, i) => (
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
      {error && (
        <div className="absolute z-50 mt-1 w-full rounded-xl border border-error/20 bg-error/5 p-3 text-center text-sm text-error shadow-lg" role="alert">
          {error}
        </div>
      )}
    </div>
  )
}
