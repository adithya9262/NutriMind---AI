import { createBrowserClient } from "@supabase/ssr"

let client: ReturnType<typeof createBrowserClient> | null = null

function getSupabaseCredentials() {
  const envUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
  const envKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY
  const hasValidPair = Boolean(envUrl && envKey && envUrl.trim() !== "" && envKey.trim() !== "")
  return {
    url: hasValidPair ? envUrl! : "https://placeholder.supabase.co",
    key: hasValidPair ? envKey! : "placeholder-anon-key",
  }
}

export function createClient() {
  if (client) return client
  const { url, key } = getSupabaseCredentials()
  client = createBrowserClient(url, key)
  return client
}
