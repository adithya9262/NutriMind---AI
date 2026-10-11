import { describe, it, expect, vi } from "vitest"

const { getSession } = vi.hoisted(() => ({ getSession: vi.fn() }))
vi.mock("@/lib/supabase/client", () => ({
  createClient: () => ({ auth: { getSession } }),
}))

describe("Supabase session token access", () => {
  it("reads the active token from the Supabase-managed session", async () => {
    getSession.mockResolvedValueOnce({ data: { session: { access_token: "session-token" } }, error: null })
    const { getAccessToken } = await import("@/lib/token-storage")
    await expect(getAccessToken()).resolves.toBe("session-token")
  })

  it("returns null without a valid session", async () => {
    getSession.mockResolvedValueOnce({ data: { session: null }, error: null })
    const { getAccessToken } = await import("@/lib/token-storage")
    await expect(getAccessToken()).resolves.toBeNull()
  })

  it("does not expose custom token mutation or localStorage APIs", async () => {
    const storage = await import("@/lib/token-storage")
    expect(Object.keys(storage)).toEqual(["getAccessToken"])
  })
})
