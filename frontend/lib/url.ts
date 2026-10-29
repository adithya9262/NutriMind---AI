/**
 * Resolves the public application URL for frontend navigation, redirects,
 * and Supabase OAuth callback parameters.
 *
 * In production, NEXT_PUBLIC_APP_URL MUST be set to the canonical
 * production URL (e.g., https://nutrimind-frontend.onrender.com).
 *
 * In development, falls back to window.location.origin or localhost:3000.
 *
 * During Next.js build (static generation), we allow fallback to avoid
 * build failures when environment variables are only available at runtime.
 */
export function getAppUrl(): string {
  const envAppUrl = process.env.NEXT_PUBLIC_APP_URL
  if (envAppUrl && envAppUrl.trim() !== "") {
    return envAppUrl.trim().replace(/\/$/, "")
  }

  const isProduction = process.env.NODE_ENV === "production"
  const isBuildTime =
    typeof window === "undefined" &&
    (process.env.NEXT_PHASE === "phase-production-build" ||
      process.env.NEXT_PHASE === "phase-development-build")

  if (isProduction && !isBuildTime) {
    throw new Error(
      "Missing required configuration: NEXT_PUBLIC_APP_URL must be set in production."
    )
  }

  if (typeof window !== "undefined" && window.location?.origin) {
    const origin = window.location.origin.trim().replace(/\/$/, "")
    if (!origin.includes("0.0.0.0")) {
      return origin
    }
  }

  if (isBuildTime) {
    return "http://localhost:3000"
  }

  return "http://localhost:3000"
}
