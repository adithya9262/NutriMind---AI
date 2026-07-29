import { apiGet, apiPost } from "./client";
import type { RegisterRequest, LoginRequest, AuthSuccessResponse, AuthMeResponse } from "@/types/auth";

export async function registerUser(
  data: RegisterRequest,
  signal?: AbortSignal
) {
  return apiPost<AuthSuccessResponse["data"]>("/auth/register", data, {
    token: false,
    signal,
  });
}

export async function loginUser(
  data: LoginRequest,
  signal?: AbortSignal
) {
  return apiPost<AuthSuccessResponse["data"]>("/auth/login", data, {
    token: false,
    signal,
  });
}

export async function fetchCurrentUser(signal?: AbortSignal) {
  return apiGet<AuthMeResponse["data"]>("/auth/me", {
    token: true,
    signal,
  });
}
