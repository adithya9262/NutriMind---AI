export type BiologicalSex = "male" | "female" | "other" | "prefer_not_to_say";

export type ActivityLevel =
  | "sedentary"
  | "lightly_active"
  | "moderately_active"
  | "very_active"
  | "extra_active";

export type NutritionGoal =
  | "lose_weight"
  | "maintain_weight"
  | "gain_weight"
  | "gain_muscle";

export type DietaryPreference =
  | "no_preference"
  | "vegetarian"
  | "vegan"
  | "pescatarian"
  | "eggetarian";

export type BMICategory =
  | "underweight"
  | "healthy_weight"
  | "overweight"
  | "obesity";

export type NutritionSummaryTone = "informational" | "caution";

export interface NutritionProfilePublic {
  id: string;
  user_id: string;
  date_of_birth: string | null;
  biological_sex: string | null;
  height_cm: string | null;
  weight_kg: string | null;
  activity_level: string | null;
  goal: string | null;
  target_weight_kg: string | null;
  dietary_preference: string | null;
  allergies: string[];
  created_at: string;
  updated_at: string;
  full_name: string | null;
  phone: string | null;
  avatar_url: string | null;
  fitness_goal: string | null;
  medical_conditions: string[];
  water_goal_ml: number | null;
  sleep_goal_hours: string | null;
  daily_calorie_goal: number | null;
  daily_protein_goal_g: number | null;
  daily_carb_goal_g: number | null;
  daily_fat_goal_g: number | null;
}

export interface NutritionProfileCreateRequest {
  date_of_birth?: string | null;
  biological_sex?: string | null;
  height_cm?: string | null;
  weight_kg?: string | null;
  activity_level?: string | null;
  goal?: string | null;
  target_weight_kg?: string | null;
  dietary_preference?: string | null;
  allergies?: string[];
  full_name?: string | null;
  phone?: string | null;
  avatar_url?: string | null;
  fitness_goal?: string | null;
  medical_conditions?: string[];
  water_goal_ml?: number | null;
  sleep_goal_hours?: string | null;
  daily_calorie_goal?: number | null;
  daily_protein_goal_g?: number | null;
  daily_carb_goal_g?: number | null;
  daily_fat_goal_g?: number | null;
}

export interface NutritionProfileUpdateRequest {
  date_of_birth?: string | null;
  biological_sex?: string | null;
  height_cm?: string | null;
  weight_kg?: string | null;
  activity_level?: string | null;
  goal?: string | null;
  target_weight_kg?: string | null;
  dietary_preference?: string | null;
  allergies?: string[] | null;
  full_name?: string | null;
  phone?: string | null;
  avatar_url?: string | null;
  fitness_goal?: string | null;
  medical_conditions?: string[] | null;
  water_goal_ml?: number | null;
  sleep_goal_hours?: string | null;
  daily_calorie_goal?: number | null;
  daily_protein_goal_g?: number | null;
  daily_carb_goal_g?: number | null;
  daily_fat_goal_g?: number | null;
}

export interface NutritionProfileData {
  profile: NutritionProfilePublic;
}

export interface NutritionProfileSuccessResponse {
  success: true;
  message: string;
  data: NutritionProfileData;
}

export interface NutritionMetricsData {
  age_years: number;
  bmi: string;
  bmi_category: string;
  bmr_kcal_per_day: string;
  tdee_kcal_per_day: string;
}

export interface NutritionTargetsData {
  calorie_target_kcal_per_day: string;
  protein_g_per_day: string;
  carbohydrate_g_per_day: string;
  fat_g_per_day: string;
}

export interface CalculatedNutritionData {
  metrics: NutritionMetricsData;
  targets: NutritionTargetsData;
}

export interface CalculatedNutritionSuccessResponse {
  success: true;
  message: string;
  data: CalculatedNutritionData | null;
}

export interface NutritionSummaryItemData {
  code: string;
  title: string;
  message: string;
  tone: string;
}

export interface NutritionSummaryData {
  overview: string;
  items: NutritionSummaryItemData[];
}

export interface NutritionSummarySuccessResponse {
  success: true;
  message: string;
  data: NutritionSummaryData | null;
}

export const BIOLOGICAL_SEX_LABELS: Record<string, string> = {
  male: "Male",
  female: "Female",
  other: "Other",
  prefer_not_to_say: "Prefer not to say",
};

export const ACTIVITY_LEVEL_LABELS: Record<string, string> = {
  sedentary: "Sedentary",
  lightly_active: "Lightly Active",
  moderately_active: "Moderately Active",
  very_active: "Very Active",
  extra_active: "Extra Active",
};

export const NUTRITION_GOAL_LABELS: Record<string, string> = {
  lose_weight: "Lose Weight",
  maintain_weight: "Maintain Weight",
  gain_weight: "Gain Weight",
  gain_muscle: "Gain Muscle",
};

export const DIETARY_PREFERENCE_LABELS: Record<string, string> = {
  no_preference: "No Preference",
  vegetarian: "Vegetarian",
  vegan: "Vegan",
  pescatarian: "Pescatarian",
  eggetarian: "Eggetarian",
};

export const BMI_CATEGORY_LABELS: Record<string, string> = {
  underweight: "Underweight",
  healthy_weight: "Healthy Weight",
  overweight: "Overweight",
  obesity: "Obesity",
};

export type NutritionProfileStatus =
  | "loading"
  | "missing"
  | "available"
  | "creating"
  | "updating"
  | "create_error"
  | "update_error"
  | "read_error";

export type CalculationsStatus =
  | "idle"
  | "loading"
  | "available"
  | "error";

export type SummaryStatus =
  | "idle"
  | "loading"
  | "available"
  | "error";

// ---------------------------------------------------------------------------
// Nutrition-log types (Phase 6A-3)
// ---------------------------------------------------------------------------

export type MealType = "breakfast" | "lunch" | "dinner" | "snack";

export type NutritionProgressStatus = "below_target" | "target_met" | "above_target";

export const MEAL_TYPE_LABELS: Record<MealType, string> = {
  breakfast: "Breakfast",
  lunch: "Lunch",
  dinner: "Dinner",
  snack: "Snack",
};

export const MEAL_TYPE_ORDER: MealType[] = ["breakfast", "lunch", "dinner", "snack"];

export const PROGRESS_STATUS_LABELS: Record<NutritionProgressStatus, string> = {
  below_target: "Below Target",
  target_met: "Target Met",
  above_target: "Above Target",
};

export interface NutritionLogEntryCreateRequest {
  entry_id: string;
  food_name: string;
  meal_type: MealType;
  serving_description: string;
  calories_kcal: string;
  protein_g: string;
  carbohydrate_g: string;
  fat_g: string;
}

export interface NutritionLogEntryData {
  entry_id: string;
  food_name: string;
  meal_type: MealType;
  serving_description: string;
  calories_kcal: string;
  protein_g: string;
  carbohydrate_g: string;
  fat_g: string;
}

export interface NutritionLogEntryListData {
  logged_date: string;
  entries: NutritionLogEntryData[];
}

export interface NutritionLogEntrySuccessResponse {
  success: true;
  message: string;
  data: NutritionLogEntryData;
}

export interface NutritionLogEntryListSuccessResponse {
  success: true;
  message: string;
  data: NutritionLogEntryListData;
}

export interface NutritionLogDeleteSuccessResponse {
  success: true;
  message: string;
}

export interface DailyNutritionTotalsData {
  calories_kcal: string;
  protein_g: string;
  carbohydrate_g: string;
  fat_g: string;
}

export interface MealNutritionSummaryData {
  meal_type: MealType;
  entry_count: number;
  totals: DailyNutritionTotalsData;
}

export interface DailyNutritionLogSummaryData {
  entry_count: number;
  totals: DailyNutritionTotalsData;
  meals: MealNutritionSummaryData[];
}

export interface DailyNutritionLogSuccessResponse {
  success: true;
  message: string;
  data: DailyNutritionLogSummaryData;
}

export interface NutrientProgressData {
  consumed: string;
  target: string;
  remaining: string;
  percentage: string;
  status: NutritionProgressStatus;
}

export interface DailyNutritionProgressData {
  calories: NutrientProgressData;
  protein: NutrientProgressData;
  carbohydrate: NutrientProgressData;
  fat: NutrientProgressData;
}

export interface DailyNutritionProgressSuccessResponse {
  success: true;
  message: string;
  data: DailyNutritionProgressData;
}

export type NutritionLogEntryFormState = {
  food_name: string;
  meal_type: MealType;
  serving_description: string;
  calories_kcal: string;
  protein_g: string;
  carbohydrate_g: string;
  fat_g: string;
};

export const EMPTY_ENTRY_FORM: NutritionLogEntryFormState = {
  food_name: "",
  meal_type: "breakfast",
  serving_description: "",
  calories_kcal: "",
  protein_g: "",
  carbohydrate_g: "",
  fat_g: "",
};

export const NUTRITION_FIELD_LIMITS: Record<string, { min: number; max: number; step: string }> = {
  calories_kcal: { min: 0, max: 10000, step: "0.01" },
  protein_g: { min: 0, max: 1000, step: "0.01" },
  carbohydrate_g: { min: 0, max: 2000, step: "0.01" },
  fat_g: { min: 0, max: 1000, step: "0.01" },
};

export type EntryReadStatus = "loading" | "available" | "empty" | "error";
export type SummaryReadStatus = "loading" | "available" | "empty" | "error";
export type ProgressReadStatus = "loading" | "available" | "missing_profile" | "error";
export type CreateStatus = "idle" | "submitting" | "success" | "error";
export type DeleteStatus = "idle" | "confirming" | "deleting" | "error";

// ---------------------------------------------------------------------------
// Food Search types
// ---------------------------------------------------------------------------

export type FitnessGoal =
  | "weight_loss"
  | "weight_goal"
  | "maintain_weight"
  | "muscle_gain"
  | "fat_loss"
  | "custom"
  | "general_fitness";

export interface FoodSearchItem {
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
}

export interface FoodSearchResponse {
  success: boolean;
  message: string;
  data: {
    query: string;
    total_results: number;
    foods: FoodSearchItem[];
  };
}

export interface DetectedFood {
  food_name: string;
  calories_kcal: string;
  protein_g: string;
  carbohydrate_g: string;
  fat_g: string;
  serving_size_g: string;
  ingredients: string[];
  confidence_score: string;
}

export interface FoodRecognitionResponse {
  success: boolean;
  message: string;
  data: {
    foods: DetectedFood[];
    raw_response: string;
  };
}

export const FITNESS_GOAL_LABELS: Record<string, string> = {
  weight_loss: "Weight Loss",
  weight_gain: "Weight Gain",
  maintain_weight: "Maintain Weight",
  muscle_gain: "Muscle Gain",
  fat_loss: "Fat Loss",
  custom: "Custom",
  general_fitness: "General Fitness",
};

// ---------------------------------------------------------------------------
// Calendar / History types
// ---------------------------------------------------------------------------

export interface CalendarDayEntry {
  date: string;
  total_calories: number;
  entry_count: number;
}

export interface CalendarMonthData {
  year: number;
  month: number;
  days: CalendarDayEntry[];
}