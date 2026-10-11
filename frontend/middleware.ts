import { type NextRequest, NextResponse } from "next/server"
import { createClient } from "@/lib/supabase/middleware"
import { getAppUrl } from "@/lib/url"

const PUBLIC_PATHS = new Set([
  "/", "/login", "/register", "/forgot-password", "/reset-password",
  "/auth/callback", "/privacy", "/terms",
])

const PUBLIC_PREFIXES = ["/_next", "/api", "/favicon", "/images", "/fonts"]

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl

  if (PUBLIC_PREFIXES.some((p) => pathname.startsWith(p))) {
    return NextResponse.next()
  }

  if (PUBLIC_PATHS.has(pathname)) {
    return NextResponse.next()
  }

  // Validate the Supabase cookie with Auth; cookie presence alone is not proof.
  const { supabase, response } = createClient(request)
  const { data: { user }, error } = await supabase.auth.getUser()

  if (error || !user) {
    const appUrl = getAppUrl()
    const loginUrl = new URL("/login", appUrl)
    loginUrl.searchParams.set("redirect", pathname)
    return NextResponse.redirect(loginUrl)
  }

  if (user && (pathname === "/login" || pathname === "/register")) {
    return NextResponse.redirect(new URL("/dashboard", getAppUrl()))
  }

  response.headers.set("X-Frame-Options", "DENY")
  response.headers.set("X-Content-Type-Options", "nosniff")
  response.headers.set("Referrer-Policy", "strict-origin-when-cross-origin")
  response.headers.set("Cache-Control", "private, no-store, max-age=0")

  return response
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
}
