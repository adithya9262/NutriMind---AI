import { createClient } from "@/lib/supabase/client"

/** Read the active Supabase session managed by @supabase/ssr. No parallel token store. */
export async function getAccessToken(): Promise<string | null> {
  const { data, error } = await createClient().auth.getSession()
  if (error) return null
  return data.session?.access_token ?? null
}
