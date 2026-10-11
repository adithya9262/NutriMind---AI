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
import type { AuthChangeEvent, Session, User as SupabaseUser } from "@supabase/supabase-js"
import { createClient } from "@/lib/supabase/client"
import { syncSupabaseUser } from "@/lib/supabase-sync"
import { getAppUrl } from "@/lib/url"

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

function mapSupabaseUser(sbUser: SupabaseUser): PublicUser {
  return {
    id: sbUser.id,
    email: sbUser.email ?? "",
    is_active: true,
    is_verified: !!sbUser.email_confirmed_at,
    created_at: sbUser.created_at ?? new Date().toISOString(),
    updated_at: sbUser.updated_at ?? new Date().toISOString(),
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>("loading")
  const [user, setUser] = useState<PublicUser | null>(null)
  const initRef = useRef(false)
  const supabaseRef = useRef(createClient())
  const signOutInProgressRef = useRef(false)

  const setStateLogged = useCallback((newState: AuthState) => setState(newState), [])

  const refreshSession = useCallback(async () => {
    const { data: { user: supabaseUser }, error } = await supabaseRef.current.auth.getUser()
    if (error || !supabaseUser) {
      setUser(null)
      setStateLogged("unauthenticated")
      return
    }
    const sync = await syncSupabaseUser()
    setUser(sync.success && sync.data?.user ? sync.data.user : mapSupabaseUser(supabaseUser))
    setStateLogged("authenticated")
  }, [setStateLogged])

  useEffect(() => {
    if (initRef.current) return
    initRef.current = true
    let cancelled = false
    const supabase = supabaseRef.current

    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      (event: AuthChangeEvent, session: Session | null) => {
        if (cancelled || signOutInProgressRef.current) return
        if (session?.user && ["SIGNED_IN", "TOKEN_REFRESHED", "USER_UPDATED", "INITIAL_SESSION"].includes(event)) {
          setUser(mapSupabaseUser(session.user))
          setStateLogged("authenticated")
          syncSupabaseUser().then((result) => {
            if (!cancelled && result.success && result.data?.user) setUser(result.data.user)
          }).catch(() => undefined)
        } else if (event === "SIGNED_OUT") {
          setUser(null)
          setStateLogged("unauthenticated")
        }
      },
    )

    void (async () => {
      try {
        const { data: { user: supabaseUser }, error } = await supabase.auth.getUser()
        if (cancelled) return
        if (error || !supabaseUser) {
          setUser(null)
          setStateLogged("unauthenticated")
          return
        }
        const sync = await syncSupabaseUser()
        if (cancelled) return
        setUser(sync.success && sync.data?.user ? sync.data.user : mapSupabaseUser(supabaseUser))
        setStateLogged("authenticated")
      } catch {
        if (!cancelled) {
          setUser(null)
          setStateLogged("unauthenticated")
        }
      }
    })()

    const handleSessionExpired = async () => {
      if (cancelled || signOutInProgressRef.current) return
      signOutInProgressRef.current = true
      try {
        await supabaseRef.current.auth.signOut()
      } catch {
        // The local Supabase session is cleared by signOut even if revocation is unavailable.
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
      cancelled = true
      subscription.unsubscribe()
      window.removeEventListener("nutrimind:session-expired", handleSessionExpired)
    }
  }, [setStateLogged])

  const logout = useCallback(async () => {
    if (signOutInProgressRef.current) return
    signOutInProgressRef.current = true
    try {
      await supabaseRef.current.auth.signOut()
    } finally {
      setUser(null)
      setStateLogged("unauthenticated")
      signOutInProgressRef.current = false
    }
  }, [setStateLogged])

  const signInWithGoogle = useCallback(async () => {
    const { error } = await supabaseRef.current.auth.signInWithOAuth({
      provider: "google",
      options: { redirectTo: `${getAppUrl()}/auth/callback` },
    })
    if (error) throw error
  }, [])

  const signInWithApple = useCallback(async () => {
    const { error } = await supabaseRef.current.auth.signInWithOAuth({
      provider: "apple",
      options: { redirectTo: `${getAppUrl()}/auth/callback` },
    })
    if (error) throw error
  }, [])

  const resetPassword = useCallback(async (email: string): Promise<string | null> => {
    const { error } = await supabaseRef.current.auth.resetPasswordForEmail(email, {
      redirectTo: `${getAppUrl()}/reset-password`,
    })
    return error ? error.message : null
  }, [])

  const updatePassword = useCallback(async (newPassword: string): Promise<string | null> => {
    const { error } = await supabaseRef.current.auth.updateUser({ password: newPassword })
    return error ? error.message : null
  }, [])

  return (
    <AuthContext.Provider value={{ state, user, logout, signInWithGoogle, signInWithApple, resetPassword, updatePassword, refreshSession }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider")
  return ctx
}
