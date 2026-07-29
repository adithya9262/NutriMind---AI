"use client"

import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  useRef,
  type ReactNode,
} from "react"
import type { PublicUser, AuthState } from "@/types/auth"
import type { AuthChangeEvent, Session } from "@supabase/supabase-js"
import { createClient } from "@/lib/supabase/client"
import { setAccessToken, getAccessToken, clearAllTokens } from "@/lib/token-storage"
import { syncSupabaseUser } from "@/lib/supabase-sync"
import { fetchCurrentUser } from "@/services/api/auth"

interface AuthContextValue {
  state: AuthState
  user: PublicUser | null
  logout: () => Promise<void>
  signInWithGoogle: () => Promise<void>
  signInWithApple: () => Promise<void>
  resetPassword: (email: string) => Promise<string | null>
  updatePassword: (newPassword: string) => Promise<string | null>
  refreshSession: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

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

function clearSessionCookie() {
  if (typeof document !== "undefined") {
    document.cookie = "nutrimind_session=; path=/; max-age=0; SameSite=Lax"
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>("loading")
  const [user, setUser] = useState<PublicUser | null>(null)
  const initRef = useRef(false)
  const supabaseRef = useRef(createClient())
  const signOutInProgressRef = useRef(false)

  console.log("[AuthProvider] Component function executed, initRef.current =", initRef.current)

  const setStateLogged = useCallback((newState: AuthState) => {
    console.log("[AuthProvider] setState:", "->", newState)
    setState(newState)
  }, [])

  const refreshSession = useCallback(async () => {
    console.log("[refreshSession] START")
    const backendToken = getAccessToken("backend")
    console.log("[refreshSession] backendToken:", backendToken ? "PRESENT" : "NONE")
    if (backendToken) {
      try {
        console.log("[refreshSession] Calling fetchCurrentUser()")
        const result = await fetchCurrentUser()
        console.log("[refreshSession] fetchCurrentUser result:", result)
        if (result.success && result.data) {
          console.log("[refreshSession] Setting authenticated via backend token")
          setUser(result.data)
          setStateLogged("authenticated")
          return
        }
      } catch (err) {
        console.error("[refreshSession] fetchCurrentUser threw:", err)
      }
      console.log("[refreshSession] Backend token invalid, clearing")
      clearAllTokens()
      clearSessionCookie()
    }

    console.log("[refreshSession] Checking Supabase session")
    const { data: { session } } = await supabaseRef.current.auth.getSession()
    console.log("[refreshSession] Supabase session:", session ? "PRESENT" : "NONE")

    if (session?.user) {
      setAccessToken(session.access_token, "supabase")
      setUser(mapSupabaseUser(session.user))
      setStateLogged("authenticated")
      syncSupabaseUser().catch(console.error)
    } else {
      clearAllTokens()
      clearSessionCookie()
      setUser(null)
      setStateLogged("unauthenticated")
    }
  }, [setStateLogged])

  useEffect(() => {
    console.log("[AuthProvider] useEffect running, initRef.current =", initRef.current)
    if (initRef.current) return
    initRef.current = true

    let cancelled = false
    const supabase = supabaseRef.current

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((event: AuthChangeEvent, session: Session | null) => {
      if (cancelled) return
      if (signOutInProgressRef.current) return

      if (
        event === "SIGNED_IN" ||
        event === "TOKEN_REFRESHED" ||
        event === "USER_UPDATED" ||
        event === "INITIAL_SESSION"
      ) {
        if (session?.user) {
          setAccessToken(session.access_token, "supabase")
          setUser(mapSupabaseUser(session.user))
          setStateLogged("authenticated")
          syncSupabaseUser().catch(console.error)
        }
      } else if (event === "SIGNED_OUT") {
        const backendToken = getAccessToken("backend")
        if (!backendToken) {
          clearAllTokens()
          clearSessionCookie()
          setUser(null)
          setStateLogged("unauthenticated")
        }
      }
    })

    async function restoreSession() {
      try {
        console.log("[restoreSession] START")
        const backendToken = getAccessToken("backend")
        console.log("[restoreSession] backendToken:", backendToken ? "PRESENT" : "NONE")
        if (backendToken) {
          console.log("[restoreSession] Calling fetchCurrentUser()")
          const result = await fetchCurrentUser()
          console.log("[restoreSession] fetchCurrentUser result:", result)
          if (!cancelled && result.success && result.data) {
            setUser(result.data)
            setStateLogged("authenticated")
            return
          }
          console.log("[restoreSession] Backend token invalid, clearing")
          clearAllTokens()
          clearSessionCookie()
        }

        console.log("[restoreSession] Checking Supabase session")
        const { data: { session } } = await supabase.auth.getSession()
        console.log("[restoreSession] Supabase session:", session ? "PRESENT" : "NONE")
        if (cancelled) return

        if (session?.user) {
          setAccessToken(session.access_token, "supabase")
          setUser(mapSupabaseUser(session.user))
          setStateLogged("authenticated")
          syncSupabaseUser().catch(console.error)
        } else {
          if (!cancelled) {
            clearAllTokens()
            clearSessionCookie()
            setUser(null)
            setStateLogged("unauthenticated")
          }
        }
      } catch (err) {
        console.error("[restoreSession] Caught error:", err)
        if (!cancelled) {
          clearAllTokens()
          clearSessionCookie()
          setUser(null)
          setStateLogged("unauthenticated")
        }
      }
    }

    restoreSession()

    async function handleSessionExpired() {
      if (cancelled || signOutInProgressRef.current) return
      signOutInProgressRef.current = true
      try {
        clearAllTokens()
        clearSessionCookie()
        await supabaseRef.current.auth.signOut()
      } catch {
      } finally {
        if (!cancelled) {
          setUser(null)
          setStateLogged("unauthenticated")
        }
        signOutInProgressRef.current = false
      }
    }
    window.addEventListener("nutrimind:session-expired", handleSessionExpired)

    return () => {
      console.log("[AuthProvider] useEffect cleanup, cancelled =", cancelled)
      cancelled = true
      subscription.unsubscribe()
      window.removeEventListener("nutrimind:session-expired", handleSessionExpired)
    }
  }, [])

  const logout = useCallback(async () => {
    if (signOutInProgressRef.current) return
    signOutInProgressRef.current = true
    try {
      clearAllTokens()
      clearSessionCookie()
      const supabase = supabaseRef.current
      await supabase.auth.signOut()
    } catch {
    } finally {
      setUser(null)
      setStateLogged("unauthenticated")
      signOutInProgressRef.current = false
    }
  }, [setStateLogged])

  const signInWithGoogle = useCallback(async () => {
    const supabase = supabaseRef.current
    const { error } = await supabase.auth.signInWithOAuth({
      provider: "google",
      options: {
        redirectTo: `${window.location.origin}/auth/callback`,
      },
    })
    if (error) throw error
  }, [])

  const signInWithApple = useCallback(async () => {
    const supabase = supabaseRef.current
    const { error } = await supabase.auth.signInWithOAuth({
      provider: "apple",
      options: {
        redirectTo: `${window.location.origin}/auth/callback`,
      },
    })
    if (error) throw error
  }, [])

  const resetPassword = useCallback(async (email: string): Promise<string | null> => {
    const supabase = supabaseRef.current
    const { error } = await supabase.auth.resetPasswordForEmail(email, {
      redirectTo: `${window.location.origin}/reset-password`,
    })
    return error ? error.message : null
  }, [])

  const updatePassword = useCallback(async (newPassword: string): Promise<string | null> => {
    const supabase = supabaseRef.current
    const { error } = await supabase.auth.updateUser({ password: newPassword })
    return error ? error.message : null
  }, [])

  return (
    <AuthContext.Provider
      value={{ state, user, logout, signInWithGoogle, signInWithApple, resetPassword, updatePassword, refreshSession }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) {
    throw new Error("useAuth must be used within an AuthProvider")
  }
  return ctx
}