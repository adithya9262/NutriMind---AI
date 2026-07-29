export type TaskPriority = "low" | "medium" | "high";

export type TaskStatus = "pending" | "completed";

export type TaskCategory = "daily_habit" | "exercise" | "water" | "sleep" | "medication" | "appointment" | "custom";

export type TaskRecurrence = "none" | "daily" | "weekly" | "monthly" | "weekdays" | "weekends";

export interface TaskData {
  task_id: string;
  title: string;
  description: string | null;
  priority: TaskPriority;
  status: TaskStatus;
  due_date: string | null;
  completed_at: string | null;
  category?: TaskCategory;
  recurrence?: TaskRecurrence;
}

export interface TaskCreateRequest {
  title: string;
  description?: string | null;
  priority?: TaskPriority;
  due_date?: string | null;
  category?: TaskCategory;
  recurrence?: TaskRecurrence;
}

export interface TaskUpdateRequest {
  title?: string | null;
  description?: string | null;
  priority?: TaskPriority | null;
  due_date?: string | null;
  category?: TaskCategory | null;
  recurrence?: TaskRecurrence | null;
}

export interface TaskCompleteRequest {
  completed_at: string;
}

export interface TaskListData {
  tasks: TaskData[];
}

export interface TaskSuccessResponse {
  success: true;
  message: string;
  data: TaskData;
}

export interface TaskListSuccessResponse {
  success: true;
  message: string;
  data: TaskListData;
}

export interface TaskDeleteSuccessResponse {
  success: true;
  message: string;
}

export const PRIORITY_LABELS: Record<TaskPriority, string> = {
  low: "Low",
  medium: "Medium",
  high: "High",
};

export const STATUS_LABELS: Record<TaskStatus, string> = {
  pending: "Pending",
  completed: "Completed",
};

export const PRIORITY_VARIANTS: Record<TaskPriority, "default" | "warning" | "error"> = {
  low: "default",
  medium: "warning",
  high: "error",
};

export const STATUS_VARIANTS: Record<TaskStatus, "default" | "success"> = {
  pending: "default",
  completed: "success",
};

export const TASK_CATEGORY_LABELS: Record<TaskCategory, string> = {
  daily_habit: "Daily Habit",
  exercise: "Exercise",
  water: "Water",
  sleep: "Sleep",
  medication: "Medication",
  appointment: "Appointment",
  custom: "Custom",
};

export const TASK_RECURRENCE_LABELS: Record<TaskRecurrence, string> = {
  none: "None",
  daily: "Daily",
  weekly: "Weekly",
  monthly: "Monthly",
  weekdays: "Weekdays",
  weekends: "Weekends",
};

export const CATEGORY_VARIANTS: Record<TaskCategory, "default" | "success" | "warning" | "error" | "info" | "brand"> = {
  daily_habit: "success",
  exercise: "brand",
  water: "info",
  sleep: "warning",
  medication: "error",
  appointment: "brand",
  custom: "default",
};

export const RECURRENCE_VARIANTS: Record<TaskRecurrence, "default" | "success" | "warning" | "info" | "brand"> = {
  none: "default",
  daily: "success",
  weekly: "brand",
  monthly: "default",
  weekdays: "warning",
  weekends: "brand",
};

export const MIN_TASK_TITLE_LENGTH = 1;
export const MAX_TASK_TITLE_LENGTH = 200;
export const MAX_TASK_DESCRIPTION_LENGTH = 2000;

export interface TaskFormState {
  title: string;
  description: string;
  priority: TaskPriority;
  due_date: string;
  category: TaskCategory;
  recurrence: TaskRecurrence;
}

export const EMPTY_TASK_FORM: TaskFormState = {
  title: "",
  description: "",
  priority: "medium",
  due_date: "",
  category: "custom",
  recurrence: "none",
};

export type TaskListStatus = "loading" | "available" | "empty" | "error";
export type TaskCreateStatus = "idle" | "submitting" | "success" | "error";
export type TaskActionStatus = "idle" | "completing" | "reopening" | "deleting" | "updating" | "error";
