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

let dispatchSpy: any;

beforeEach(() => {
  vi.clearAllMocks();
  dispatchSpy = vi.spyOn(window, "dispatchEvent");
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

  describe("401 Interceptor and Timeouts", () => {
    it("DOES NOT dispatch nutrimind:session-expired on 401 when useToken is false (e.g. /auth/login)", async () => {
      process.env.NEXT_PUBLIC_API_URL = "http://test:8000/api/v1";
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        headers: new Headers(),
        json: () => Promise.resolve({ error: { message: "Invalid credentials" } }),
      });

      const { apiPost } = await getClient();
      const result = await apiPost("/auth/login", {}, { token: false });

      expect(result.success).toBe(false);
      expect(dispatchSpy).not.toHaveBeenCalled();
      if (!result.success) {
        expect(result.error.message).toBe("Invalid credentials");
        expect(result.error.code).toBe("HTTP_ERROR");
      }
    });

    it("DOES NOT dispatch nutrimind:session-expired on 400 when useToken is false (e.g. /auth/register)", async () => {
      process.env.NEXT_PUBLIC_API_URL = "http://test:8000/api/v1";
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        headers: new Headers(),
        json: () => Promise.resolve({ error: { message: "Email already exists" } }),
      });

      const { apiPost } = await getClient();
      const result = await apiPost("/auth/register", {}, { token: false });

      expect(result.success).toBe(false);
      expect(dispatchSpy).not.toHaveBeenCalled();
    });

    it("DOES dispatch nutrimind:session-expired on 401 when useToken is true (authenticated endpoint)", async () => {
      process.env.NEXT_PUBLIC_API_URL = "http://test:8000/api/v1";
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        headers: new Headers(),
        json: () => Promise.resolve({ error: { message: "Token expired" } }),
      });

      const { apiGet } = await getClient();
      const result = await apiGet("/protected-route", { token: true });

      expect(result.success).toBe(false);
      expect(dispatchSpy).toHaveBeenCalledTimes(1);
      const event = dispatchSpy.mock.calls[0][0];
      expect(event.type).toBe("nutrimind:session-expired");
    });

    it("Returns Request timed out for AbortError", async () => {
      process.env.NEXT_PUBLIC_API_URL = "http://test:8000/api/v1";
      const abortError = new Error("The operation was aborted");
      abortError.name = "AbortError";
      mockFetch.mockRejectedValueOnce(abortError);

      const { apiGet } = await getClient();
      const result = await apiGet("/timeout-route");

      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.code).toBe("TIMEOUT");
        expect(result.error.message).toBe("Request timed out. The server may be unreachable.");
      }
    });
  });
});
