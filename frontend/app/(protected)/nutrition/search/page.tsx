"use client"

import { useCallback, useEffect, useRef, useState } from "react"
import { motion } from "framer-motion"
import { Loader2, Plus, Search, SearchX, Utensils } from "lucide-react"
import { Alert } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Skeleton } from "@/components/ui/skeleton"
import { Spinner } from "@/components/ui/spinner"
import { SearchHeader } from "@/components/nutrition-search/search-header"
import { searchFoodsApi } from "@/services/api/food-search"
import { cn } from "@/lib/utils"
import type { FoodSearchItem } from "@/types/nutrition"

type SearchStatus = "idle" | "loading" | "results" | "empty" | "error"

const MACRO_CONFIG = [
  { key: "calories_kcal" as const, label: "Calories", suffix: "", color: "text-primary" },
  { key: "protein_g" as const, label: "Protein", suffix: "g", color: "text-brand" },
  { key: "carbohydrate_g" as const, label: "Carbs", suffix: "g", color: "text-info" },
  { key: "fat_g" as const, label: "Fat", suffix: "g", color: "text-warning" },
  { key: "fiber_g" as const, label: "Fiber", suffix: "g", color: "text-brand" },
  { key: "sugar_g" as const, label: "Sugar", suffix: "g", color: "text-primary-secondary" },
]

function FoodResultCard({
  food,
  onAddToDiary,
}: {
  food: FoodSearchItem
  onAddToDiary: (food: FoodSearchItem) => void
}) {
  return (
    <>
      <Card
        variant="glass"
        className="p-4 space-y-3 transition-all duration-300 hover:border-brand/40 hover:-translate-y-0.5"
      >
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0 flex-1">
            <h3 className="font-semibold text-primary text-sm leading-tight truncate">
              {food.food_name}
            </h3>
            {food.brand_name && (
              <p className="text-[11px] text-primary-muted/60 mt-0.5 truncate">
                {food.brand_name}
              </p>
            )}
          </div>
          {food.source && (
            <span className="shrink-0 text-[10px] uppercase tracking-wider text-primary-muted/50 border border-border rounded-full px-2 py-0.5">
              {food.source}
            </span>
          )}
        </div>

        <div className="flex flex-wrap gap-1.5">
          {MACRO_CONFIG.map((macro) => {
            const value = food[macro.key]
            const display = value && value !== "0" ? value : null
            if (!display) return null
            return (
              <span
                key={macro.key}
                className={cn(
                  "inline-flex items-center gap-1 rounded-lg bg-surface-highest/50 px-2.5 py-1 text-xs font-medium border border-white/5",
                  macro.color,
                )}
              >
                {display}
                {macro.suffix}
                <span className="text-[10px] text-primary-muted/50 font-normal ml-0.5">
                  {macro.label}
                </span>
              </span>
            )
          })}
        </div>

        <div className="flex items-center justify-between gap-2 pt-1 border-t border-border/40">
          <p className="text-[11px] text-primary-muted/60 truncate">
            {food.serving_description
              ? `Per ${food.serving_description}`
              : food.serving_size_g
                ? `Per ${food.serving_size_g} g`
                : "Per 100 g"}
          </p>
          <Button
            variant="secondary"
            size="sm"
            pill
            onClick={() => onAddToDiary(food)}
            className="shrink-0"
          >
            <Plus className="h-3.5 w-3.5" />
            Add to Diary
          </Button>
        </div>
      </Card>
    </>
  )
}

function SkeletonCard() {
  return (
    <Card variant="glass" className="p-4 space-y-3">
      <div className="flex items-start justify-between">
        <div className="space-y-2 flex-1">
          <Skeleton className="h-4 w-3/5" />
          <Skeleton className="h-3 w-2/5" />
        </div>
        <Skeleton className="h-5 w-12 rounded-full" />
      </div>
      <div className="flex flex-wrap gap-1.5">
        <Skeleton className="h-6 w-16 rounded-lg" />
        <Skeleton className="h-6 w-20 rounded-lg" />
        <Skeleton className="h-6 w-14 rounded-lg" />
        <Skeleton className="h-6 w-12 rounded-lg" />
      </div>
      <div className="flex items-center justify-between pt-1 border-t border-border/40">
        <Skeleton className="h-3 w-24" />
        <Skeleton className="h-8 w-28 rounded-full" />
      </div>
    </Card>
  )
}

export default function NutritionSearchPage() {
  const [query, setQuery] = useState("")
  const [status, setStatus] = useState<SearchStatus>("idle")
  const [foods, setFoods] = useState<FoodSearchItem[]>([])
  const [totalResults, setTotalResults] = useState(0)
  const [errorMessage, setErrorMessage] = useState("")
  const abortRef = useRef<AbortController | null>(null)
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const doSearch = useCallback(async (q: string) => {
    const trimmed = q.trim()
    if (!trimmed) {
      setStatus("idle")
      setFoods([])
      setTotalResults(0)
      setErrorMessage("")
      return
    }

    if (abortRef.current) {
      abortRef.current.abort()
    }
    const controller = new AbortController()
    abortRef.current = controller

    setStatus("loading")

    try {
      const response = await searchFoodsApi(trimmed, 25)

      if (controller.signal.aborted) return

      if (!response.success) {
        setStatus("error")
        setErrorMessage(
          response.error?.message || "Search failed. Please try again.",
        )
        setFoods([])
        setTotalResults(0)
        return
      }

      const data = response.data
      if (!data.foods || data.foods.length === 0) {
        setStatus("empty")
        setFoods([])
        setTotalResults(0)
      } else {
        setStatus("results")
        setFoods(data.foods)
        setTotalResults(data.total_results)
      }
      setErrorMessage("")
    } catch (err) {
      if (controller.signal.aborted) return
      setStatus("error")
      setErrorMessage(
        err instanceof Error ? err.message : "An unexpected error occurred.",
      )
      setFoods([])
      setTotalResults(0)
    }
  }, [])

  useEffect(() => {
    if (timerRef.current) {
      clearTimeout(timerRef.current)
    }
    timerRef.current = setTimeout(() => {
      doSearch(query)
    }, 300)
    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current)
      }
    }
  }, [query, doSearch])

  useEffect(() => {
    return () => {
      if (abortRef.current) {
        abortRef.current.abort()
      }
    }
  }, [])

  function handleQueryChange(value: string) {
    setQuery(value)
  }

  function handleRetry() {
    doSearch(query)
  }

  function handleAddToDiary(food: FoodSearchItem) {
    const hour = new Date().getHours()
    let meal_type = "breakfast"
    if (hour >= 11 && hour < 15) meal_type = "lunch"
    else if (hour >= 15 && hour < 21) meal_type = "dinner"
    else if (hour >= 21 || hour < 6) meal_type = "snack"
    const params = new URLSearchParams({
      food_name: food.food_name,
      serving_description: food.serving_description ?? `${food.serving_size_g ?? 100}g`,
      calories_kcal: food.calories_kcal ?? "0",
      protein_g: food.protein_g ?? "0",
      carbohydrate_g: food.carbohydrate_g ?? "0",
      fat_g: food.fat_g ?? "0",
      meal_type,
    })
    window.location.href = `/nutrition/logs?${params.toString()}`
  }

  return (
    <div className="space-y-6">
      <SearchHeader
        title="Nutrition Search"
        description="Search clinical-grade foods and analyze their macro profile."
      />

      <form
        role="search"
        onSubmit={(e) => {
          e.preventDefault()
          doSearch(query)
        }}
        className="relative"
      >
        <Search
          className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-primary-muted pointer-events-none"
          aria-hidden="true"
        />
        <Input
          ref={inputRef}
          type="search"
          value={query}
          onChange={(e) => handleQueryChange(e.target.value)}
          placeholder="Search foods by name (e.g. chicken, apple, quinoa)..."
          aria-label="Search foods"
          className="pl-12 pr-12 py-3 h-12 rounded-xl text-sm"
        />
        {status === "loading" && (
          <div className="absolute right-4 top-1/2 -translate-y-1/2">
            <Spinner size="sm" />
          </div>
        )}
      </form>

      {status === "error" && (
        <Alert variant="error" className="animate-in fade-in">
          <div className="flex items-center justify-between w-full">
            <span>{errorMessage || "An error occurred while searching."}</span>
            <Button variant="secondary" size="sm" onClick={handleRetry}>
              Retry
            </Button>
          </div>
        </Alert>
      )}

      {status === "idle" && (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <div className="mb-5 grid h-16 w-16 place-items-center rounded-2xl bg-brand-light">
            <Search className="h-8 w-8 text-brand" aria-hidden="true" />
          </div>
          <h3 className="text-lg font-semibold text-primary">Search the Nutrition Database</h3>
          <p className="mt-1.5 text-sm text-primary-secondary max-w-md">
            Type a food name above to search thousands of clinical-grade foods
            and view their complete macro-nutrient profile.
          </p>
        </div>
      )}

      {status === "loading" && (
        <div className="space-y-3" role="status" aria-label="Searching foods">
          <div className="flex items-center gap-2 text-sm text-primary-secondary">
            <Loader2 className="h-4 w-4 animate-spin text-brand" aria-hidden="true" />
            <span>Searching...</span>
          </div>
          <div className="grid grid-cols-1 gap-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <SkeletonCard key={i} />
            ))}
          </div>
        </div>
      )}

      {status === "empty" && (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <div className="mb-5 grid h-16 w-16 place-items-center rounded-2xl bg-surface-high">
            <SearchX className="h-8 w-8 text-primary-muted" aria-hidden="true" />
          </div>
          <h3 className="text-lg font-semibold text-primary">No results found</h3>
          <p className="mt-1.5 text-sm text-primary-secondary max-w-md">
            No foods match &ldquo;{query}&rdquo;. Try a different search term or
            check the spelling.
          </p>
        </div>
      )}

      {status === "results" && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm text-primary-secondary">
              <Utensils className="h-4 w-4 text-brand" aria-hidden="true" />
              <span>
                Found{" "}
                <span className="font-semibold text-primary">{totalResults}</span>{" "}
                result{totalResults === 1 ? "" : "s"}
              </span>
            </div>
            <span className="text-[11px] text-primary-muted/50">
              Showing {foods.length} of {totalResults}
            </span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {foods.map((food, index) => (
              <motion.div
                key={food.fdc_id}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: index * 0.05 }}
              >
                <FoodResultCard
                  food={food}
                  onAddToDiary={handleAddToDiary}
                />
              </motion.div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
