import type { AuthAdapter } from "./auth-adapter"
import { loginUser, registerUser, fetchCurrentUser } from "@/services/api/auth"
import { getAccessToken, setAccessToken, removeAccessToken } from "@/lib/token-storage"
import type { PublicUser } from "@/types/auth"

export const apiAuthAdapter: AuthAdapter = {
  async register(data: { email: string; password: string }) {
    const result = await registerUser(data)
    if (result.success) {
      return { success: true, data: result.data }
    }
    return { success: false, error: result.error?.message || "Registration failed." }
  },

  async login(data: { email: string; password: string }) {
    const result = await loginUser(data)
    if (result.success) {
      return { success: true, data: result.data }
    }
    return { success: false, error: result.error?.message || "Login failed." }
  },

  async fetchCurrentUser(signal?: AbortSignal) {
    const result = await fetchCurrentUser(signal)
    if (result.success) {
      return { success: true, data: result.data as PublicUser }
    }
    return { success: false, error: result.error?.message || "Failed to fetch user." }
  },

  logout() {
    removeAccessToken("backend")
    removeAccessToken("supabase")
  },

  getAccessToken(): string | null {
    return getAccessToken("backend") || getAccessToken("supabase")
  },

  setSession(token: string) {
    setAccessToken(token, "backend")
  },

  clearSession() {
    removeAccessToken("backend")
    removeAccessToken("supabase")
  },
}
