import { apiGet, apiPost, apiPatch } from "./client";
import type {
  NutritionProfileCreateRequest,
  NutritionProfileUpdateRequest,
  NutritionProfileData,
  CalculatedNutritionData,
  NutritionSummaryData,
} from "@/types/nutrition";

export async function getNutritionProfile(signal?: AbortSignal) {
  return apiGet<NutritionProfileData>(
    "/nutrition-profile",
    { signal }
  );
}

export async function createNutritionProfile(
  payload: NutritionProfileCreateRequest,
  signal?: AbortSignal
) {
  return apiPost<NutritionProfileData>(
    "/nutrition-profile",
    payload,
    { signal }
  );
}

export async function updateNutritionProfile(
  payload: NutritionProfileUpdateRequest,
  signal?: AbortSignal
) {
  return apiPatch<NutritionProfileData>(
    "/nutrition-profile",
    payload,
    { signal }
  );
}

export async function getNutritionCalculations(
  referenceDate: string,
  signal?: AbortSignal
) {
  return apiGet<CalculatedNutritionData | null>(
    `/nutrition-profile/calculations?reference_date=${encodeURIComponent(referenceDate)}`,
    { signal }
  );
}

export async function getPersonalizedNutritionSummary(
  referenceDate: string,
  signal?: AbortSignal
) {
  return apiGet<NutritionSummaryData | null>(
    `/nutrition-profile/summary?reference_date=${encodeURIComponent(referenceDate)}`,
    { signal }
  );
}
