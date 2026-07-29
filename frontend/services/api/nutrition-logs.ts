import { apiGet, apiPost, apiDelete } from "./client";
import type {
  NutritionLogEntryCreateRequest,
  NutritionLogEntryData,
  NutritionLogEntryListData,
  DailyNutritionLogSummaryData,
  DailyNutritionProgressData,
  CalendarMonthData,
} from "@/types/nutrition";

export async function listNutritionLogEntries(
  loggedDate: string,
  signal?: AbortSignal
) {
  const qs = `logged_date=${encodeURIComponent(loggedDate)}`;
  return apiGet<NutritionLogEntryListData>(
    `/nutrition-logs?${qs}`,
    { signal }
  );
}

export async function createNutritionLogEntry(
  loggedDate: string,
  payload: NutritionLogEntryCreateRequest,
  signal?: AbortSignal
) {
  const qs = `logged_date=${encodeURIComponent(loggedDate)}`;
  return apiPost<NutritionLogEntryData>(
    `/nutrition-logs?${qs}`,
    payload,
    { signal }
  );
}

export async function deleteNutritionLogEntry(
  entryId: string,
  signal?: AbortSignal
) {
  return apiDelete<Record<string, never>>(
    `/nutrition-logs/${encodeURIComponent(entryId)}`,
    { signal }
  );
}

export async function getDailyNutritionLogSummary(
  loggedDate: string,
  signal?: AbortSignal
) {
  const qs = `logged_date=${encodeURIComponent(loggedDate)}`;
  return apiGet<DailyNutritionLogSummaryData>(
    `/nutrition-logs/summary?${qs}`,
    { signal }
  );
}

export async function listNutritionLogEntriesByMonth(
  year: number,
  month: number,
  signal?: AbortSignal
) {
  const qs = `year=${year}&month=${month}`;
  return apiGet<CalendarMonthData>(
    `/nutrition-logs/calendar?${qs}`,
    { signal }
  );
}

export async function getDailyNutritionTargetProgress(
  loggedDate: string,
  referenceDate: string,
  signal?: AbortSignal
) {
  const qs = [
    `logged_date=${encodeURIComponent(loggedDate)}`,
    `reference_date=${encodeURIComponent(referenceDate)}`,
  ].join("&");
  return apiGet<DailyNutritionProgressData>(
    `/nutrition-logs/progress?${qs}`,
    { signal }
  );
}
