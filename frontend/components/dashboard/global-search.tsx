"use client"

import { useState, useRef, useEffect, useCallback } from "react"
import { Search, Loader2, AlertCircle } from "lucide-react"
import { Input } from "@/components/ui/input"
import { globalSearch } from "@/services/api/search"
import { cn } from "@/lib/utils"
import type { SearchResult } from "@/types/search"

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
      {error && (
        <div className="absolute z-50 mt-1 w-full rounded-xl border border-error/20 bg-error/5 p-3 text-center text-sm text-error shadow-lg" role="alert">
          {error}
        </div>
      )}
    </div>
  )
}
