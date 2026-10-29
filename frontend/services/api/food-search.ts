import { apiGet } from "./client";

export async function searchFoodsApi(query: string, maxResults: number = 25) {
  // Use longer timeout (25s) to account for external API calls (USDA + OpenFoodFacts)
  // Disable retries since retries on timeout would multiply slow external API requests
  return apiGet<{
    query: string;
    total_results: number;
    foods: {
      fdc_id: string;
      food_name: string;
      brand_name: string | null;
      calories_kcal: string;
      protein_g: string;
      carbohydrate_g: string;
      fat_g: string;
      fiber_g: string;
      sugar_g: string;
      serving_size_g: string | null;
      serving_description: string | null;
      source: string;
    }[];
  }>(
    `/food-search/search?query=${encodeURIComponent(query)}&max_results=${maxResults}`,
    { timeout: 25000, retryable: false }
  );
}
