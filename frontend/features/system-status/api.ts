import { apiGet } from "@/services/api/client";
import { isHealthResponse } from "@/types/api";
import type { HealthResponseData } from "@/types/api";

export async function checkHealth(
  signal?: AbortSignal
): Promise<{
  status: "connected" | "unavailable";
  message: string;
}> {
  const result = await apiGet<HealthResponseData>("/health", {
    signal,
  });

  if (!result.success) {
    return {
      status: "unavailable",
      message: result.error.message,
    };
  }

  if (!isHealthResponse(result)) {
    return {
      status: "unavailable",
      message: "Unexpected response format from the server.",
    };
  }

  return {
    status: "connected",
    message: "Backend connected",
  };
}
