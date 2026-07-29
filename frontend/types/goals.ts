export type GoalType = "weight_loss" | "weight_gain" | "maintain_weight" | "muscle_gain" | "fat_loss" | "custom";
export type GoalStatus = "active" | "completed" | "cancelled" | "paused";

export interface GoalData {
  id: string;
  user_id: string;
  goal_type: GoalType;
  title: string;
  description: string | null;
  status: GoalStatus;
  start_date: string | null;
  end_date: string | null;
  weekly_target: string | null;
  target_calories: number | null;
  target_protein_g: number | null;
  target_carbs_g: number | null;
  target_fats_g: number | null;
  target_water_ml: number | null;
  progress_percentage: string | null;
  created_at: string;
  updated_at: string;
}

export interface GoalCreateRequest {
  goal_type: GoalType;
  title: string;
  description?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  weekly_target?: string | null;
  target_calories?: number | null;
  target_protein_g?: number | null;
  target_carbs_g?: number | null;
  target_fats_g?: number | null;
  target_water_ml?: number | null;
}

export interface GoalUpdateRequest {
  goal_type?: GoalType | null;
  title?: string | null;
  description?: string | null;
  status?: GoalStatus | null;
  start_date?: string | null;
  end_date?: string | null;
  weekly_target?: string | null;
  target_calories?: number | null;
  target_protein_g?: number | null;
  target_carbs_g?: number | null;
  target_fats_g?: number | null;
  target_water_ml?: number | null;
}

export const GOAL_TYPE_LABELS: Record<GoalType, string> = {
  weight_loss: "Weight Loss",
  weight_gain: "Weight Gain",
  maintain_weight: "Maintain Weight",
  muscle_gain: "Muscle Gain",
  fat_loss: "Fat Loss",
  custom: "Custom",
};

export const GOAL_STATUS_LABELS: Record<GoalStatus, string> = {
  active: "Active",
  completed: "Completed",
  cancelled: "Cancelled",
  paused: "Paused",
};

export type GoalListStatus = "loading" | "available" | "empty" | "error";
export type GoalActionStatus = "idle" | "updating" | "deleting" | "error";
export type GoalCreateStatus = "idle" | "submitting" | "success" | "error";
