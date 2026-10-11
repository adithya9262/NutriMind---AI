import { apiGet } from "./client";
import { supabaseAuthAdapter } from "@/lib/supabase-adapter";
import type { RegisterRequest, LoginRequest, AuthMeResponse, AccessTokenData } from "@/types/auth";

function authFailure(message: string) {
  const duplicate = /already|registered/i.test(message)
  return {
    success: false as const,
    error: { code: duplicate ? "EMAIL_ALREADY_REGISTERED" : "AUTHENTICATION_FAILED", message, request_id: "" },
  }
}

export async function registerUser(
  data: RegisterRequest,
  signal?: AbortSignal
) {
  void signal
  const result = await supabaseAuthAdapter.register(data)
  if (!result.success || !result.data) return authFailure(result.error || "Registration failed.")
  const payload: AccessTokenData = {
    user: result.data.user,
    access_token: result.data.access_token,
    token_type: "bearer",
    expires_in: 0,
  }
  return { success: true as const, message: "Registration submitted.", data: payload }
}

export async function loginUser(
  data: LoginRequest,
  signal?: AbortSignal
) {
  void signal
  const result = await supabaseAuthAdapter.login(data)
  if (!result.success || !result.data) return authFailure(result.error || "Login failed.")
  const payload: AccessTokenData = {
    user: result.data.user,
    access_token: result.data.access_token,
    token_type: "bearer",
    expires_in: 0,
  }
  return { success: true as const, message: "Login successful.", data: payload }
}

export async function fetchCurrentUser(signal?: AbortSignal) {
  return apiGet<AuthMeResponse["data"]>("/auth/me", {
    token: true,
    signal,
  });
}
