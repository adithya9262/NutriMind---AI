"use client"

import { useEffect, useRef, useState } from "react"
import { useRouter, usePathname } from "next/navigation"
import { useAuth } from "@/contexts/auth-context"
import { Spinner } from "@/components/ui/spinner"

const LOADING_TIMEOUT = 10000
const REDIRECT_DELAY = 300

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { state } = useAuth()
  const router = useRouter()
  const pathname = usePathname()
  const [timedOut, setTimedOut] = useState(false)
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined)
  const redirectingRef = useRef(false)

  console.log("[ProtectedRoute] Render, state =", state)

  useEffect(() => {
    if (state === "loading") {
      timeoutRef.current = setTimeout(() => {
        setTimedOut(true)
      }, LOADING_TIMEOUT)
    }
    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current)
    }
  }, [state])

  useEffect(() => {
    if (state === "unauthenticated" && !redirectingRef.current) {
      redirectingRef.current = true
      const target = pathname ?? "/dashboard"
      const encoded = encodeURIComponent(target)
      const delay = redirectingRef.current ? 0 : REDIRECT_DELAY
      const timeout = setTimeout(() => {
        router.replace(`/login?redirect=${encoded}`)
      }, delay)
      return () => clearTimeout(timeout)
    }
    if (state !== "unauthenticated") {
      redirectingRef.current = false
    }
  }, [state, router, pathname])

  if (state === "loading" && timedOut) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-background p-8">
        <h2 className="mb-2 text-xl font-semibold text-primary">Still loading...</h2>
        <p className="mb-6 text-sm text-primary-secondary">
          Having trouble connecting. Please try refreshing the page.
        </p>
        <button
          onClick={() => window.location.reload()}
          className="text-sm font-medium text-brand hover:underline"
        >
          Refresh Page
        </button>
      </div>
    )
  }

  if (state === "loading") {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-3">
          <Spinner size="lg" />
          <p className="text-sm text-primary-secondary">Loading...</p>
        </div>
      </div>
    )
  }

  if (state === "unauthenticated") {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-3">
          <Spinner size="lg" />
          <p className="text-sm text-primary-secondary">Redirecting to login...</p>
        </div>
      </div>
    )
  }

  return <div className="min-h-screen">{children}</div>
}
