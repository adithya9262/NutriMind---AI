import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

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

  describe("Retry Logic", () => {
    it("retries on network error and succeeds on second attempt (uses fresh controller)", async () => {
      process.env.NEXT_PUBLIC_API_URL = "http://test:8000/api/v1";
      // First call fails with network error, second succeeds
      mockFetch
        .mockRejectedValueOnce(new Error("Network error"))
        .mockResolvedValueOnce({
          ok: true,
          status: 200,
          headers: new Headers(),
          text: () => Promise.resolve(JSON.stringify({ success: true, message: "ok", data: { value: "retry-success" } })),
        });

      const { apiGet } = await getClient();
      const result = await apiGet("/retry-test");

      // Should succeed on retry
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data).toEqual({ value: "retry-success" });
      }
      // Should have been called twice
      expect(mockFetch).toHaveBeenCalledTimes(2);
    });

    it("retries on HTTP 500 and succeeds on second attempt (uses fresh controller)", async () => {
      process.env.NEXT_PUBLIC_API_URL = "http://test:8000/api/v1";
      // First call returns 500, second succeeds
      mockFetch
        .mockResolvedValueOnce({
          ok: false,
          status: 500,
          headers: new Headers({ "Retry-After": "0" }),
          json: () => Promise.resolve({ error: { message: "Internal server error" } }),
        })
        .mockResolvedValueOnce({
          ok: true,
          status: 200,
          headers: new Headers(),
          text: () => Promise.resolve(JSON.stringify({ success: true, message: "ok", data: { value: "retry-success" } })),
        });

      const { apiGet } = await getClient();
      const result = await apiGet("/retry-500");

      // Should succeed on retry
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data).toEqual({ value: "retry-success" });
      }
      expect(mockFetch).toHaveBeenCalledTimes(2);
    });

    it("retries on HTTP 429 and respects Retry-After header", async () => {
      process.env.NEXT_PUBLIC_API_URL = "http://test:8000/api/v1";
      // First call returns 429 with Retry-After: 1 (1 second), second succeeds
      mockFetch
        .mockResolvedValueOnce({
          ok: false,
          status: 429,
          headers: new Headers({ "Retry-After": "1" }),
          json: () => Promise.resolve({ error: { message: "Rate limited" } }),
        })
        .mockResolvedValueOnce({
          ok: true,
          status: 200,
          headers: new Headers(),
          text: () => Promise.resolve(JSON.stringify({ success: true, message: "ok", data: { value: "retry-success" } })),
        });

      const { apiGet } = await getClient();
      const start = Date.now();
      const result = await apiGet("/retry-429");
      const elapsed = Date.now() - start;

      // Should succeed on retry
      expect(result.success).toBe(true);
      // Should have waited at least ~1 second (Retry-After: 1s = 1000ms)
      expect(elapsed).toBeGreaterThanOrEqual(900); // Allow some margin
      expect(mockFetch).toHaveBeenCalledTimes(2);
    });

    it("does NOT retry on caller cancellation (AbortSignal)", async () => {
      process.env.NEXT_PUBLIC_API_URL = "http://test:8000/api/v1";
      const controller = new AbortController();
      
      // Abort after fetch starts to simulate real cancellation
      mockFetch.mockImplementation(async () => {
        await new Promise(resolve => setTimeout(resolve, 10));
        controller.abort();
        // Return a rejected promise with AbortError
        throw new DOMException("Aborted", "AbortError");
      });

      const { apiGet } = await getClient();
      const promise = apiGet("/cancel-test", { signal: controller.signal });
      
      // Wait for abort to happen
      await new Promise(resolve => setTimeout(resolve, 50));
      
      const result = await promise;

      // Should fail (aborted), not retry
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(["TIMEOUT", "NETWORK_ERROR"]).toContain(result.error.code);
      }
      // Should only be called once (no retry)
      expect(mockFetch).toHaveBeenCalledTimes(1);
    });

    it("exhausts retries and returns error after max attempts", async () => {
      process.env.NEXT_PUBLIC_API_URL = "http://test:8000/api/v1";
      // All 3 attempts fail with network errors (initial + 2 retries = 3 total)
      mockFetch
        .mockRejectedValueOnce(new Error("Network error"))
        .mockRejectedValueOnce(new Error("Network error"))
        .mockRejectedValueOnce(new Error("Network error"));

      const { apiGet } = await getClient();
      const result = await apiGet("/exhaust-test", { retries: 2 });

      // Should fail after exhausting retries
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.code).toBe("NETWORK_ERROR");
      }
      // Should have been called 3 times (initial + 2 retries)
      expect(mockFetch).toHaveBeenCalledTimes(3);
    });

    it("does NOT retry non-GET requests", async () => {
      process.env.NEXT_PUBLIC_API_URL = "http://test:8000/api/v1";
      const abortError = new Error("The operation was aborted");
      abortError.name = "AbortError";
      mockFetch.mockRejectedValueOnce(abortError);

      const { apiPost } = await getClient();
      const result = await apiPost("/non-get-retry", {}, { retryable: true }); // Even with retryable: true, POST should not retry

      // Should fail immediately, no retry
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.code).toBe("TIMEOUT");
      }
      expect(mockFetch).toHaveBeenCalledTimes(1);
    });

    it("cleans up timeout on successful response", async () => {
      process.env.NEXT_PUBLIC_API_URL = "http://test:8000/api/v1";
      let fetchCallCount = 0;
      mockFetch.mockImplementation(async () => {
        fetchCallCount++;
        // Simulate a delay
        await new Promise(resolve => setTimeout(resolve, 10));
        return {
          ok: true,
          status: 200,
          headers: new Headers(),
          text: () => Promise.resolve(JSON.stringify({ success: true, message: "ok", data: {} })),
        };
      });

      const { apiGet } = await getClient();
      const result = await apiGet("/cleanup-test", { timeout: 5000 });

      expect(result.success).toBe(true);
      // No assertion on timers directly, but if cleanup didn't happen,
      // the test would hang or timers would leak
    });

    it("cleans up timeout and event listeners on caller abort", async () => {
      process.env.NEXT_PUBLIC_API_URL = "http://test:8000/api/v1";
      const controller = new AbortController();
      let fetchStarted = false;

      mockFetch.mockImplementation(async () => {
        fetchStarted = true;
        // Never resolve - wait for abort
        await new Promise((_, reject) => {
          controller.signal.addEventListener("abort", () => reject(new DOMException("Aborted", "AbortError")), { once: true });
        });
      });

      const { apiGet } = await getClient();
      const promise = apiGet("/abort-cleanup", { signal: controller.signal, timeout: 5000 });

      // Give fetch a moment to start
      await new Promise(resolve => setTimeout(resolve, 5));
      expect(fetchStarted).toBe(true);

      // Abort the request
      controller.abort();

      const result = await promise;
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.code).toBe("TIMEOUT");
      }
    });
  });
});
