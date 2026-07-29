import { createServerClient } from "@supabase/ssr"
import { cookies } from "next/headers"
import type { NextResponse } from "next/server"

export async function createClient() {
  const cookieStore = await cookies()

  return createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return cookieStore.getAll()
        },
        setAll(cookiesToSet) {
          try {
            cookiesToSet.forEach(({ name, value, options }) =>
              cookieStore.set(name, value, options)
            )
          } catch {
            /* middleware will refresh on next request */
          }
        },
      },
    }
  )
}

export function createRouteHandlerClient(
  request: Request,
  response: NextResponse
) {
  const cookieHeader = request.headers.get("cookie") ?? ""

  return createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          const pairs: { name: string; value: string }[] = []
          for (const part of cookieHeader.split(";")) {
            const eq = part.indexOf("=")
            if (eq !== -1) {
              pairs.push({
                name: part.slice(0, eq).trim(),
                value: part.slice(eq + 1).trim(),
              })
            }
          }
          return pairs
        },
        setAll(cookiesToSet) {
          cookiesToSet.forEach(({ name, value, options }) => {
            response.cookies.set(name, value, options)
          })
        },
      },
    }
  )
}
