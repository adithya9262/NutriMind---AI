import type { AuthAdapter } from "./auth-adapter"
import type { PublicUser } from "@/types/auth"
import { createClient } from "./supabase/client"

function mapSupabaseUser(sbUser: { id: string; email?: string | null; email_confirmed_at?: string | null; created_at?: string; updated_at?: string }): PublicUser {
  return {
    id: sbUser.id,
    email: sbUser.email ?? "",
    is_active: true,
    is_verified: !!sbUser.email_confirmed_at,
    created_at: sbUser.created_at ?? new Date().toISOString(),
    updated_at: sbUser.updated_at ?? new Date().toISOString(),
  }
}

export const supabaseAuthAdapter: AuthAdapter = {
  async register(data: { email: string; password: string }) {
    const supabase = createClient()
    const { data: authData, error } = await supabase.auth.signUp({
      email: data.email,
      password: data.password,
    })
    if (error) {
      return { success: false, error: error.message }
    }
    if (!authData.user) {
      return { success: false, error: "Registration failed. No user returned." }
    }
    const accessToken = authData.session?.access_token ?? ""
    const user = mapSupabaseUser(authData.user)
    return { success: true, data: { access_token: accessToken, user } }
  },

  async login(data: { email: string; password: string }) {
    const supabase = createClient()
    const { data: authData, error } = await supabase.auth.signInWithPassword({
      email: data.email,
      password: data.password,
    })
    if (error) {
      return { success: false, error: error.message }
    }
    if (!authData.user || !authData.session) {
      return { success: false, error: "Login failed. No session returned." }
    }
    const user = mapSupabaseUser(authData.user)
    return {
      success: true,
      data: {
        access_token: authData.session.access_token,
        user,
      },
    }
  },

  async fetchCurrentUser(_signal?: AbortSignal) {
    void _signal
    const supabase = createClient()
    const { data: { user }, error } = await supabase.auth.getUser()
    if (error || !user) {
      return { success: false, error: error?.message ?? "No authenticated user." }
    }
    return { success: true, data: mapSupabaseUser(user) }
  },

  logout() {
    const supabase = createClient()
    supabase.auth.signOut()
  },

  getAccessToken(): string | null {
    return null
  },

  setSession(_token: string) {
    void _token
  },

  clearSession() {
    // Supabase manages sessions via cookies automatically
  },
}
