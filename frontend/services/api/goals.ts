import { apiGet, apiPost, apiPatch, apiDelete } from "./client";
import type { GoalData, GoalCreateRequest, GoalUpdateRequest } from "@/types/goals";

export async function listGoals() {
  return apiGet<{ goals: GoalData[] }>("/goals");
}

export async function getGoal(goalId: string) {
  return apiGet<GoalData>(`/goals/${encodeURIComponent(goalId)}`);
}

export async function createGoal(payload: GoalCreateRequest) {
  return apiPost<GoalData>("/goals", payload);
}

export async function updateGoal(goalId: string, payload: GoalUpdateRequest) {
  return apiPatch<GoalData>(`/goals/${encodeURIComponent(goalId)}`, payload);
}

export async function deleteGoal(goalId: string) {
  return apiDelete<Record<string, never>>(`/goals/${encodeURIComponent(goalId)}`);
}
