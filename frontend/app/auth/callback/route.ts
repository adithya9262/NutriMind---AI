import { type NextRequest, NextResponse } from "next/server"
import { createClient } from "@/lib/supabase/server"
import { getAppUrl } from "@/lib/url"

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url)
  const code = searchParams.get("code")
  const error = searchParams.get("error")
  const appUrl = getAppUrl()

  if (error) {
    return NextResponse.redirect(`${appUrl}/login?error=auth_callback_error`)
  }

  if (code) {
    const supabase = await createClient()
    const { error: exchangeError } = await supabase.auth.exchangeCodeForSession(code)
    if (!exchangeError) {
      return NextResponse.redirect(`${appUrl}/dashboard`)
    }
  }

  return NextResponse.redirect(`${appUrl}/login?error=auth_callback_error`)
}
