import { apiGet, apiPost, apiDelete } from "./client";
import type {
  BodyWeightEntryData,
  BodyWeightEntrySuccessResponse,
  BodyWeightHistorySuccessResponse,
  BodyWeightHistoryData,
  BodyWeightTrendData,
  BodyWeightGoalProgressData,
} from "@/types/body-weight";

export async function listBodyWeightHistory(signal?: AbortSignal) {
  return apiGet<BodyWeightHistoryData>(
    "/body-weights",
    { signal }
  );
}

export async function createBodyWeightEntry(
  loggedDate: string,
  weightKg: string,
  signal?: AbortSignal
) {
  const qs = `logged_date=${encodeURIComponent(loggedDate)}`;
  return apiPost<BodyWeightEntryData>(
    `/body-weights?${qs}`,
    { weight_kg: weightKg },
    { signal }
  );
}

export async function deleteBodyWeightEntry(
  entryId: string,
  signal?: AbortSignal
) {
  return apiDelete<Record<string, never>>(
    `/body-weights/${encodeURIComponent(entryId)}`,
    { signal }
  );
}

export async function getBodyWeightTrend(signal?: AbortSignal) {
  return apiGet<BodyWeightTrendData>(
    "/body-weights/trend",
    { signal }
  );
}

export async function getBodyWeightGoalProgress(signal?: AbortSignal) {
  return apiGet<BodyWeightGoalProgressData>(
    "/body-weights/goal-progress",
    { signal }
  );
}
