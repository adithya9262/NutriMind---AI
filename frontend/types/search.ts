export interface SearchResult {
  foods: { id: string; food_name: string; meal_type: string; logged_date: string; calories_kcal: string }[];
  tasks: { id: string; task_id: string; title: string; status: string; due_date: string | null }[];
}

export interface GlobalSearchResponse {
  success: boolean;
  message: string;
  data: SearchResult;
}
