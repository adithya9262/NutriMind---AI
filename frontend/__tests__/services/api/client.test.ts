import { describe, it, expect, vi, beforeEach } from "vitest";

const mockFetch = vi.fn();
vi.stubGlobal("fetch", mockFetch);

vi.mock("@/lib/supabase/client", () => ({
  createClient: vi.fn(() => ({
    auth: {
      getSession: vi.fn().mockResolvedValue({
        data: { session: { access_token: "test-token" } },
        error: null,
      }),
    },
  })),
}));

// Reset modules to get fresh imports
async function getClient() {
  return await import("@/services/api/client");
}

beforeEach(() => {
  vi.clearAllMocks();
});

describe("API Client", () => {
  describe("apiGet", () => {
    it("uses NEXT_PUBLIC_API_URL as base URL", async () => {
      process.env.NEXT_PUBLIC_API_URL = "http://test:8000/api/v1";
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        headers: new Headers(),
        text: () => Promise.resolve(JSON.stringify({ success: true, message: "ok", data: {} })),
      });

      const { apiGet } = await getClient();
      await apiGet("/health");

      expect(mockFetch).toHaveBeenCalledWith(
        "http://test:8000/api/v1/health",
        expect.objectContaining({ method: "GET" })
      );
    });

    it("handles network errors safely", async () => {
      process.env.NEXT_PUBLIC_API_URL = "http://test:8000/api/v1";
      mockFetch.mockRejectedValueOnce(new Error("Network error"));

      const { apiGet } = await getClient();
      const result = await apiGet("/health");

      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.code).toBe("NETWORK_ERROR");
      }
    });
  });
});
