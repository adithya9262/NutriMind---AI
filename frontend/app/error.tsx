"use client"

import { useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Leaf, RefreshCw } from "lucide-react"

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    console.error(error)
  }, [error])

  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4">
      <div className="text-center max-w-md">
        <div className="mx-auto mb-6 p-4 rounded-2xl bg-error-light w-fit">
          <Leaf className="h-8 w-8 text-error" aria-hidden="true" />
        </div>
        <h1 className="text-2xl font-bold text-primary">Something went wrong</h1>
        <p className="mt-2 text-sm text-primary-secondary">
          An unexpected error occurred. Please try again.
        </p>
        <Button onClick={reset} className="mt-6">
          <RefreshCw className="h-4 w-4" />
          Try again
        </Button>
      </div>
    </div>
  )
}
