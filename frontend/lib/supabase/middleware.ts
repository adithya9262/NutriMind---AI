import { createServerClient } from "@supabase/ssr"
import { NextResponse, type NextRequest } from "next/server"

function getSupabaseCredentials() {
  const envUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
  const envKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY
  const hasValidPair = Boolean(envUrl && envKey && envUrl.trim() !== "" && envKey.trim() !== "")
  return {
    url: hasValidPair ? envUrl! : "https://placeholder.supabase.co",
    key: hasValidPair ? envKey! : "placeholder-anon-key",
  }
}

export function createClient(request: NextRequest) {
  let supabaseResponse = NextResponse.next({ request })
  const { url, key } = getSupabaseCredentials()

  const supabase = createServerClient(
    url,
    key,
    {
      cookies: {
        getAll() {
          return request.cookies.getAll()
        },
        setAll(cookiesToSet) {
          cookiesToSet.forEach(({ name, value }) => {
            request.cookies.set(name, value)
          })
          supabaseResponse = NextResponse.next({ request })
          cookiesToSet.forEach(({ name, value, options }) => {
            supabaseResponse.cookies.set(name, value, options)
          })
        },
      },
    }
  )

  return { supabase, response: supabaseResponse }
}
