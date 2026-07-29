import {
  DEMO_FOODS,
  type DemoFood,
} from "@/components/nutrition-search/placeholders"

export type FoodSearchStatus = "idle" | "loading" | "available" | "empty" | "error"

export interface FoodSearchResult {
  status: FoodSearchStatus
  foods: DemoFood[]
  query: string
  isDemo: boolean
  error?: string
}

// Frontend-only nutrition search adapter.
// No backend search endpoint exists, so this filters a clearly-labeled
// DEMO catalog. It does NOT fabricate nutrition data for arbitrary queries.
export async function searchFoods(query: string): Promise<FoodSearchResult> {
  const trimmed = query.trim().toLowerCase()

  await new Promise((resolve) => setTimeout(resolve, 350))

  if (!trimmed) {
    return { status: "idle", foods: [], query, isDemo: true }
  }

  const foods = DEMO_FOODS.filter((food) => {
    const haystack = [
      food.name,
      food.source,
      food.serving,
      ...food.tags,
    ]
      .join(" ")
      .toLowerCase()
    return haystack.includes(trimmed)
  })

  if (foods.length === 0) {
    return {
      status: "empty",
      foods: [],
      query,
      isDemo: true,
      error: "No demo matches found. Try a sample term like “Salmon”.",
    }
  }

  return { status: "available", foods, query, isDemo: true }
}
