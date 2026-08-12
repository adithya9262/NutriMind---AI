/**
 * Resolves the public application URL for frontend navigation, redirects,
 * and Supabase OAuth callback parameters.
 *
 * Priorities:
 * 1. NEXT_PUBLIC_APP_URL environment variable if defined and non-empty.
 * 2. Client-side window.location.origin (if running in browser and not 0.0.0.0).
 * 3. Default fallback: http://localhost:3000
 */
export function getAppUrl(): string {
  const envAppUrl = process.env.NEXT_PUBLIC_APP_URL
  if (envAppUrl && envAppUrl.trim() !== "") {
    return envAppUrl.trim().replace(/\/$/, "")
  }

  if (typeof window !== "undefined" && window.location?.origin) {
    const origin = window.location.origin.trim().replace(/\/$/, "")
    if (!origin.includes("0.0.0.0")) {
      return origin
    }
  }

  return "http://localhost:3000"
}
