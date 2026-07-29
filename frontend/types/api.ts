import type { ApiErrorDetail } from "./auth";

export interface HealthResponseData {
  status: "healthy";
}

export interface ApiSuccessResponse<T> {
  success: true;
  message: string;
  data: T;
}

export type ApiErrorResponseBody = {
  success: false;
  error: ApiErrorDetail;
};

export type ApiResponse<T> = ApiSuccessResponse<T> | ApiErrorResponseBody;

export function isHealthResponse(
  response: unknown
): response is ApiSuccessResponse<HealthResponseData> {
  if (!response || typeof response !== "object") return false;
  const r = response as Record<string, unknown>;
  if (r.success !== true) return false;
  if (typeof r.message !== "string") return false;
  if (!r.data || typeof r.data !== "object") return false;
  const d = r.data as Record<string, unknown>;
  return d.status === "healthy";
}
