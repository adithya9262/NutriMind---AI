import { createBrowserClient } from "@supabase/ssr"
import { supabaseCookieOptions } from "./cookie-options"
import { getSupabaseCredentials } from "./credentials"

let client: ReturnType<typeof createBrowserClient> | null = null

export function createClient() {
  if (client) return client
  const { url, key } = getSupabaseCredentials()
  client = createBrowserClient(url, key, { cookieOptions: supabaseCookieOptions })
  return client
}
