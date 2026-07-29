import { getAccessToken, setAccessToken } from "./token-storage"
import type { PublicUser } from "@/types/auth"

interface SyncResult {
  success: boolean
  data?: { access_token: string; user: PublicUser }
  error?: string
}

// Maximum time we wait for the backend sync before giving up.
// Auth state is already resolved by this point — this is just enrichment.
const SYNC_REQUEST_TIMEOUT_MS = 8000

export async function syncSupabaseUser(): Promise<SyncResult> {
  const supabaseToken = getAccessToken("supabase")
  if (!supabaseToken) {
    return { success: false, error: "No Supabase session found." }
  }

  const baseUrl = process.env.NEXT_PUBLIC_API_URL?.replace(/\/+$/, "") || ""
  if (!baseUrl) {
    return { success: false, error: "API URL is not configured." }
  }

  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), SYNC_REQUEST_TIMEOUT_MS)

  try {
    const response = await fetch(`${baseUrl}/auth/supabase-sync`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${supabaseToken}`,
      },
      body: JSON.stringify({ access_token: supabaseToken }),
      signal: controller.signal,
    })

    clearTimeout(timeoutId)

    if (!response.ok) {
      return { success: false, error: `Sync failed with status ${response.status}.` }
    }

    const result = await response.json()

    if (result.success && result.data) {
      setAccessToken(result.data.access_token, "backend")
      return {
        success: true,
        data: {
          access_token: result.data.access_token,
          user: result.data.user,
        },
      }
    }

    return {
      success: false,
      error: result.error?.message || "Failed to sync with backend.",
    }
  } catch (err) {
    clearTimeout(timeoutId)
    if (err instanceof Error && err.name === "AbortError") {
      return { success: false, error: "Backend sync timed out." }
    }
    return { success: false, error: "Failed to connect to backend." }
  }
}
