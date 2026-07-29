export type BodyWeightTrendDirection = "decreased" | "stable" | "increased";

export type BodyWeightGoalDirection = "decrease" | "maintain" | "increase";

export type BodyWeightGoalStatus =
  | "not_started"
  | "in_progress"
  | "target_reached"
  | "target_passed";

export interface BodyWeightEntryData {
  entry_id: string;
  logged_date: string;
  weight_kg: string;
}

export interface BodyWeightHistoryData {
  entries: BodyWeightEntryData[];
}

export interface BodyWeightEntrySuccessResponse {
  success: true;
  message: string;
  data: BodyWeightEntryData;
}

export interface BodyWeightHistorySuccessResponse {
  success: true;
  message: string;
  data: BodyWeightHistoryData;
}

export interface BodyWeightDeleteSuccessResponse {
  success: true;
  message: string;
}

export interface BodyWeightTrendData {
  observation_count: number;
  first_logged_date: string;
  latest_logged_date: string;
  starting_weight_kg: string;
  latest_weight_kg: string;
  absolute_change_kg: string;
  percentage_change: string;
  direction: BodyWeightTrendDirection;
}

export interface BodyWeightTrendSuccessResponse {
  success: true;
  message: string;
  data: BodyWeightTrendData;
}

export interface BodyWeightGoalProgressData {
  starting_weight_kg: string;
  current_weight_kg: string;
  target_weight_kg: string;
  direction: BodyWeightGoalDirection;
  total_change_required_kg: string;
  change_achieved_kg: string;
  remaining_change_kg: string;
  progress_percentage: string;
  status: BodyWeightGoalStatus;
}

export interface BodyWeightGoalProgressSuccessResponse {
  success: true;
  message: string;
  data: BodyWeightGoalProgressData;
}

export type BodyWeightEntryFormState = {
  logged_date: string;
  weight_kg: string;
};

export const INITIAL_ENTRY_FORM: BodyWeightEntryFormState = {
  logged_date: "",
  weight_kg: "",
};

export const MIN_WEIGHT_KG = 10;
export const MAX_WEIGHT_KG = 700;
export const WEIGHT_STEP = "0.01";

export const TREND_DIRECTION_LABELS: Record<BodyWeightTrendDirection, string> = {
  decreased: "Decreased",
  stable: "Stable",
  increased: "Increased",
};

export const GOAL_DIRECTION_LABELS: Record<BodyWeightGoalDirection, string> = {
  decrease: "Decrease",
  maintain: "Maintain",
  increase: "Increase",
};

export const GOAL_STATUS_LABELS: Record<BodyWeightGoalStatus, string> = {
  not_started: "Not Started",
  in_progress: "In Progress",
  target_reached: "Target Reached",
  target_passed: "Target Passed",
};

export type HistoryStatus = "loading" | "available" | "empty" | "error";
export type TrendStatus = "idle" | "loading" | "available" | "insufficient" | "error";
export type GoalStatus = "idle" | "loading" | "available" | "missing_profile" | "missing_current_weight" | "invalid_goal" | "error";
export type CreateStatus = "idle" | "submitting" | "success" | "error";
export type DeleteStatus = "idle" | "confirming" | "deleting" | "error";
