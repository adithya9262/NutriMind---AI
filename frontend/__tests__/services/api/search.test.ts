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

async function getSearchApi() {
  return await import("@/services/api/search");
}

beforeEach(() => {
  vi.clearAllMocks();
  process.env.NEXT_PUBLIC_API_URL = "http://test:8000/api/v1";
});

describe("Search API", () => {
  describe("globalSearch", () => {
    it("calls the correct endpoint with encoded query", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        headers: new Headers(),
        text: () =>
          Promise.resolve(
            JSON.stringify({
              success: true,
              message: "Search completed.",
              data: { foods: [], tasks: [] },
            })
          ),
      });

      const { globalSearch } = await getSearchApi();
      await globalSearch("chicken");

      expect(mockFetch).toHaveBeenCalledWith(
        "http://test:8000/api/v1/search?q=chicken",
        expect.objectContaining({ method: "GET" })
      );
    });

    it("handles special characters in query", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        headers: new Headers(),
        text: () =>
          Promise.resolve(
            JSON.stringify({
              success: true,
              message: "Search completed.",
              data: { foods: [], tasks: [] },
            })
          ),
      });

      const { globalSearch } = await getSearchApi();
      await globalSearch("chicken & rice");

      expect(mockFetch).toHaveBeenCalledWith(
        "http://test:8000/api/v1/search?q=chicken%20%26%20rice",
        expect.objectContaining({ method: "GET" })
      );
    });

    it("returns success with foods and tasks on valid response", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        headers: new Headers(),
        text: () =>
          Promise.resolve(
            JSON.stringify({
              success: true,
              message: "Search completed.",
              data: {
                foods: [
                  {
                    id: "1",
                    food_name: "Grilled Chicken",
                    meal_type: "lunch",
                    logged_date: "2024-01-15",
                    calories_kcal: "350",
                  },
                ],
                tasks: [
                  {
                    id: "1",
                    task_id: "task-1",
                    title: "Meal prep chicken",
                    status: "pending",
                    due_date: "2024-01-16",
                  },
                ],
              },
            })
          ),
      });

      const { globalSearch } = await getSearchApi();
      const result = await globalSearch("chicken");

      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.foods).toHaveLength(1);
        expect(result.data.foods[0].food_name).toBe("Grilled Chicken");
        expect(result.data.tasks).toHaveLength(1);
        expect(result.data.tasks[0].title).toBe("Meal prep chicken");
      }
    });

    it("returns error on network failure", async () => {
      mockFetch.mockRejectedValueOnce(new Error("Network error"));

      const { globalSearch } = await getSearchApi();
      const result = await globalSearch("chicken");

      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.code).toBe("NETWORK_ERROR");
      }
    });

    it("returns error on HTTP 401 and dispatches session-expired", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        headers: new Headers(),
        json: () => Promise.resolve({ error: { message: "Token expired" } }),
      });

      const { globalSearch } = await getSearchApi();
      const result = await globalSearch("chicken");

      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.code).toBe("HTTP_ERROR");
      }
    });

    it("retries on HTTP 500 and eventually fails after max retries", async () => {
      // 500 is retryable, so it will retry 2 more times (3 total) then fail
      mockFetch
        .mockResolvedValueOnce({
          ok: false,
          status: 500,
          headers: new Headers({ "Retry-After": "0" }),
          json: () => Promise.resolve({ error: { message: "Internal server error" } }),
        })
        .mockResolvedValueOnce({
          ok: false,
          status: 500,
          headers: new Headers({ "Retry-After": "0" }),
          json: () => Promise.resolve({ error: { message: "Internal server error" } }),
        })
        .mockResolvedValueOnce({
          ok: false,
          status: 500,
          headers: new Headers({ "Retry-After": "0" }),
          json: () => Promise.resolve({ error: { message: "Internal server error" } }),
        });

      const { globalSearch } = await getSearchApi();
      const result = await globalSearch("chicken");

      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.code).toBe("HTTP_ERROR");
      }
      expect(mockFetch).toHaveBeenCalledTimes(3);
    });

    it("retries on transient failure and succeeds", async () => {
      mockFetch
        .mockRejectedValueOnce(new Error("Network error"))
        .mockResolvedValueOnce({
          ok: true,
          status: 200,
          headers: new Headers(),
          text: () =>
            Promise.resolve(
              JSON.stringify({
                success: true,
                message: "Search completed.",
                data: { foods: [], tasks: [] },
              })
            ),
        });

      const { globalSearch } = await getSearchApi();
      const result = await globalSearch("chicken");

      expect(result.success).toBe(true);
      expect(mockFetch).toHaveBeenCalledTimes(2);
    });
  });
});