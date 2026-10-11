import { beforeEach, describe, expect, it, vi } from "vitest"
import { NextRequest, NextResponse } from "next/server"

const getUser = vi.hoisted(() => vi.fn())
vi.mock("@/lib/supabase/middleware", () => ({
  createClient: (request: NextRequest) => ({
    supabase: { auth: { getUser } },
    response: NextResponse.next({ request }),
  }),
}))
vi.mock("@/lib/url", () => ({ getAppUrl: () => "https://app.example.test" }))

describe("protected route middleware", () => {
  beforeEach(() => getUser.mockReset())

  it("rejects the old forgeable constant session cookie", async () => {
    getUser.mockResolvedValue({ data: { user: null }, error: { message: "No session" } })
    const { middleware } = await import("@/middleware")
    const response = await middleware(new NextRequest("https://app.example.test/dashboard", {
      headers: { cookie: "nutrimind_session=1" },
    }))
    expect(response.status).toBe(307)
    expect(response.headers.get("location")).toContain("/login")
  })

  it("rejects missing or expired Supabase sessions", async () => {
    getUser.mockResolvedValue({ data: { user: null }, error: { message: "Session expired" } })
    const { middleware } = await import("@/middleware")
    const response = await middleware(new NextRequest("https://app.example.test/dashboard"))
    expect(response.status).toBe(307)
  })

  it("allows a session verified by Supabase Auth", async () => {
    getUser.mockResolvedValue({ data: { user: { id: "verified-user" } }, error: null })
    const { middleware } = await import("@/middleware")
    const response = await middleware(new NextRequest("https://app.example.test/dashboard"))
    expect(response.status).toBe(200)
    expect(response.headers.get("cache-control")).toContain("no-store")
  })
})
