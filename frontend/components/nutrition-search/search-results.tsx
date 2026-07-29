"use client"

import { Heart, Search } from "lucide-react"
import { FoodCard } from "@/components/nutrition-search/food-card"
import { EmptySearchState } from "@/components/nutrition-search/empty-search-state"
import { DEMO_FAVORITES, type DemoFood } from "@/components/nutrition-search/placeholders"
import { Card } from "@/components/ui/card"
import { cn } from "@/lib/utils"

interface SearchResultsProps {
  foods: DemoFood[]
  status: "idle" | "loading" | "available" | "empty" | "error"
  query: string
  favorites: string[]
  onToggleFavorite: (food: DemoFood) => void
  onSelect: (food: DemoFood) => void
}

const favoriteIcons: Record<string, typeof Heart> = {
  egg: Heart,
  leaf: Heart,
  seed: Heart,
  fish: Heart,
}

export function SearchResults({
  foods,
  status,
  query,
  favorites,
  onToggleFavorite,
  onSelect,
}: SearchResultsProps) {
  if (status === "idle") {
    return (
      <div className="space-y-8">
        <section>
          <h2 className="text-lg font-semibold text-primary mb-3">
            Bio-Consistent Staples
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {DEMO_FAVORITES.map((fav) => {
              const Icon = favoriteIcons[fav.icon] ?? Heart
              return (
                <Card
                  key={fav.id}
                  variant="glass"
                  className={cn(
                    "p-4 flex items-center justify-between hover:bg-surface-high/30 transition-all cursor-pointer group",
                  )}
                >
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 bg-brand-light rounded-xl flex items-center justify-center text-brand border border-brand-light">
                      <Icon className="h-5 w-5" aria-hidden="true" />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-primary group-hover:text-brand transition-colors">
                        {fav.name}
                      </p>
                      <p className="text-xs text-primary-muted opacity-60">{fav.note}</p>
                    </div>
                  </div>
                  <Heart className="h-5 w-5 text-brand fill-current" aria-hidden="true" />
                </Card>
              )
            })}
          </div>
        </section>
      </div>
    )
  }

  if (status === "empty") {
    return <EmptySearchState query={query} />
  }

  if (status === "available" && foods.length === 0) {
    return <EmptySearchState query={query} />
  }

  return (
    <section>
      <div className="flex justify-between items-center mb-3">
        <h2 className="text-lg font-semibold text-primary flex items-center gap-2">
          <Search className="h-4 w-4 text-brand" aria-hidden="true" />
          Optimal Matches
        </h2>
        <span className="text-xs text-primary-muted">
          {foods.length} result{foods.length === 1 ? "" : "s"}
        </span>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
        {foods.map((food) => (
          <FoodCard
            key={food.id}
            food={food}
            favorite={favorites.includes(food.id)}
            onToggleFavorite={onToggleFavorite}
            onSelect={onSelect}
          />
        ))}
      </div>
    </section>
  )
}
