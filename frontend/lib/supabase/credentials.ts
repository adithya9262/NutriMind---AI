/**
 * Supabase credentials resolution.
 *
 * In production (NODE_ENV === "production"), required environment variables
 * MUST be set. The function throws a clear error if they are missing.
 *
 * In development, placeholder values are allowed for local testing without
 * a real Supabase project, but a warning is logged.
 *
 * During Next.js build (static generation), we allow placeholders to avoid
 * build failures when environment variables are only available at runtime.
 */
export function getSupabaseCredentials(): { url: string; key: string } {
  const envUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
  const envKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY
  const hasValidPair = Boolean(
    envUrl && envKey && envUrl.trim() !== "" && envKey.trim() !== ""
  )

  if (!hasValidPair) {
    const isProduction = process.env.NODE_ENV === "production"
    const isBuildTime =
      typeof window === "undefined" &&
      (process.env.NEXT_PHASE === "phase-production-build" ||
        process.env.NEXT_PHASE === "phase-development-build")

    const message =
      "Missing required Supabase configuration: " +
      "NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY must be set."

    if (isProduction && !isBuildTime) {
      throw new Error(message)
    }

    // Development fallback or build-time placeholder - only for local testing/build without real Supabase
    if (isBuildTime) {
      console.warn(
        "[Supabase] " + message + " Using placeholder credentials for build."
      )
    } else {
      console.warn(
        "[Supabase] " + message + " Using placeholder credentials for development."
      )
    }
    return {
      url: "https://placeholder.supabase.co",
      key: "placeholder-anon-key",
    }
  }

  return {
    url: envUrl!.trim().replace(/\/$/, ""),
    key: envKey!.trim(),
  }
}