export interface SearchFood {
  id: string;
  food_name: string;
  meal_type: string | null;
  logged_date: string | null;
  calories_kcal: string;
  source?: string;
  is_suggestion?: boolean;
}

export interface SearchTask {
  id: string;
  task_id: string;
  title: string;
  status: string;
  due_date: string | null;
}

export interface SearchResult {
  foods: SearchFood[];
  tasks: SearchTask[];
}

export interface GlobalSearchResponse {
  success: boolean;
  message: string;
  data: SearchResult;
}
