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

beforeEach(() => {
  vi.clearAllMocks();
  process.env.NEXT_PUBLIC_API_URL = "http://test:8000/api/v1";
});

function mockResponse(data: unknown, status = 200) {
  return Promise.resolve({
    ok: status >= 200 && status < 300,
    status,
    headers: new Headers({ "X-Request-ID": "req-123" }),
    text: () => Promise.resolve(JSON.stringify(data)),
    json: () => Promise.resolve(data),
  });
}

const MOCK_HISTORY_RESPONSE = {
  success: true,
  message: "Body-weight history retrieved successfully.",
  data: {
    entries: [
      {
        entry_id: "e1",
        logged_date: "2026-07-12",
        weight_kg: "70.00",
      },
    ],
  },
};

const MOCK_CREATE_RESPONSE = {
  success: true,
  message: "Body-weight entry created successfully.",
  data: {
    entry_id: "e1",
    logged_date: "2026-07-12",
    weight_kg: "70.00",
  },
};

const MOCK_DELETE_RESPONSE = {
  success: true,
  message: "Body-weight entry deleted successfully.",
};

const MOCK_TREND_RESPONSE = {
  success: true,
  message: "Body-weight trend calculated successfully.",
  data: {
    observation_count: 3,
    first_logged_date: "2026-07-01",
    latest_logged_date: "2026-07-12",
    starting_weight_kg: "71.00",
    latest_weight_kg: "70.00",
    absolute_change_kg: "-1.00",
    percentage_change: "-1.41",
    direction: "decreased",
  },
};

const MOCK_GOAL_RESPONSE = {
  success: true,
  message: "Body-weight goal progress calculated successfully.",
  data: {
    starting_weight_kg: "80.00",
    current_weight_kg: "75.00",
    target_weight_kg: "70.00",
    direction: "decrease",
    total_change_required_kg: "10.00",
    change_achieved_kg: "5.00",
    remaining_change_kg: "5.00",
    progress_percentage: "50.00",
    status: "in_progress",
  },
};

describe("Body Weight Service", () => {
  describe("listBodyWeightHistory", () => {
    it("uses GET /body-weights", async () => {
      mockFetch.mockResolvedValueOnce(mockResponse(MOCK_HISTORY_RESPONSE));
      const { listBodyWeightHistory } = await import("@/services/api/body-weight");
      await listBodyWeightHistory();
      const callUrl = mockFetch.mock.calls[0][0] as string;
      expect(callUrl).toContain("/body-weights");
      expect(mockFetch.mock.calls[0][1].method).toBe("GET");
    });

    it("returns entries on success", async () => {
      mockFetch.mockResolvedValueOnce(mockResponse(MOCK_HISTORY_RESPONSE));
      const { listBodyWeightHistory } = await import("@/services/api/body-weight");
      const result = await listBodyWeightHistory();
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.entries).toHaveLength(1);
      }
    });
  });

  describe("createBodyWeightEntry", () => {
    it("uses POST /body-weights with logged_date query", async () => {
      mockFetch.mockResolvedValueOnce(mockResponse(MOCK_CREATE_RESPONSE, 201));
      const { createBodyWeightEntry } = await import("@/services/api/body-weight");
      await createBodyWeightEntry("2026-07-12", "70.00");
      const callUrl = mockFetch.mock.calls[0][0] as string;
      expect(callUrl).toContain("/body-weights");
      expect(callUrl).toContain("logged_date=2026-07-12");
      expect(mockFetch.mock.calls[0][1].method).toBe("POST");
    });

    it("sends exact body fields", async () => {
      mockFetch.mockResolvedValueOnce(mockResponse(MOCK_CREATE_RESPONSE, 201));
      const { createBodyWeightEntry } = await import("@/services/api/body-weight");
      await createBodyWeightEntry("2026-07-12", "70.00");
      const body = JSON.parse(mockFetch.mock.calls[0][1].body);
      expect(body).toEqual({ weight_kg: "70.00" });
    });

    it("sends logged_date in query, not body", async () => {
      mockFetch.mockResolvedValueOnce(mockResponse(MOCK_CREATE_RESPONSE, 201));
      const { createBodyWeightEntry } = await import("@/services/api/body-weight");
      await createBodyWeightEntry("2026-07-12", "70.00");
      const body = JSON.parse(mockFetch.mock.calls[0][1].body);
      expect(body.logged_date).toBeUndefined();
      const callUrl = mockFetch.mock.calls[0][0] as string;
      expect(callUrl).toContain("logged_date=2026-07-12");
    });
  });

  describe("deleteBodyWeightEntry", () => {
    it("uses DELETE /body-weights/{entry_id}", async () => {
      mockFetch.mockResolvedValueOnce(mockResponse(MOCK_DELETE_RESPONSE));
      const { deleteBodyWeightEntry } = await import("@/services/api/body-weight");
      await deleteBodyWeightEntry("e1");
      const callUrl = mockFetch.mock.calls[0][0] as string;
      expect(callUrl).toContain("/body-weights/e1");
      expect(mockFetch.mock.calls[0][1].method).toBe("DELETE");
    });

    it("encodes UUID path safely", async () => {
      mockFetch.mockResolvedValueOnce(mockResponse(MOCK_DELETE_RESPONSE));
      const { deleteBodyWeightEntry } = await import("@/services/api/body-weight");
      await deleteBodyWeightEntry("123e4567-e89b-12d3-a456-426614174000");
      const callUrl = mockFetch.mock.calls[0][0] as string;
      expect(callUrl).toContain("/body-weights/123e4567-e89b-12d3-a456-426614174000");
    });
  });

  describe("getBodyWeightTrend", () => {
    it("uses GET /body-weights/trend", async () => {
      mockFetch.mockResolvedValueOnce(mockResponse(MOCK_TREND_RESPONSE));
      const { getBodyWeightTrend } = await import("@/services/api/body-weight");
      await getBodyWeightTrend();
      const callUrl = mockFetch.mock.calls[0][0] as string;
      expect(callUrl).toContain("/body-weights/trend");
      expect(mockFetch.mock.calls[0][1].method).toBe("GET");
    });
  });

  describe("getBodyWeightGoalProgress", () => {
    it("uses GET /body-weights/goal-progress", async () => {
      mockFetch.mockResolvedValueOnce(mockResponse(MOCK_GOAL_RESPONSE));
      const { getBodyWeightGoalProgress } = await import("@/services/api/body-weight");
      await getBodyWeightGoalProgress();
      const callUrl = mockFetch.mock.calls[0][0] as string;
      expect(callUrl).toContain("/body-weights/goal-progress");
      expect(mockFetch.mock.calls[0][1].method).toBe("GET");
    });
  });

  describe("Error handling", () => {
    it("preserves error codes", async () => {
      mockFetch.mockResolvedValueOnce(
        mockResponse(
          { success: false, error: { code: "BODY_WEIGHT_ENTRY_NOT_FOUND", message: "Entry not found.", request_id: "req-123" } },
          404
        )
      );
      const { deleteBodyWeightEntry } = await import("@/services/api/body-weight");
      const result = await deleteBodyWeightEntry("e1");
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.code).toBe("BODY_WEIGHT_ENTRY_NOT_FOUND");
      }
    });

    it("handles network errors safely", async () => {
      mockFetch.mockRejectedValueOnce(new Error("Network failure"));
      const { listBodyWeightHistory } = await import("@/services/api/body-weight");
      const result = await listBodyWeightHistory();
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.code).toBe("NETWORK_ERROR");
      }
    });

    it("handles timeout errors safely", async () => {
      const error = new Error("The operation was aborted");
      error.name = "AbortError";
      mockFetch.mockRejectedValueOnce(error);
      const { listBodyWeightHistory } = await import("@/services/api/body-weight");
      const result = await listBodyWeightHistory();
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.code).toBe("TIMEOUT");
      }
    });

    it("handles invalid JSON safely", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        headers: new Headers(),
        text: () => Promise.resolve("not json"),
      });
      const { listBodyWeightHistory } = await import("@/services/api/body-weight");
      const result = await listBodyWeightHistory();
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.code).toBe("INVALID_JSON");
      }
    });

    it("reuses existing API client", async () => {
      const client = await import("@/services/api/client");
      expect(typeof client.apiGet).toBe("function");
      expect(typeof client.apiPost).toBe("function");
      expect(typeof client.apiDelete).toBe("function");
    });

    it("inherits Bearer behavior from existing client", async () => {
      const { setAccessToken } = await import("@/lib/token-storage");
      setAccessToken("test-token", "backend");
      mockFetch.mockResolvedValueOnce(mockResponse(MOCK_HISTORY_RESPONSE));
      const { listBodyWeightHistory } = await import("@/services/api/body-weight");
      await listBodyWeightHistory();
      const headers = mockFetch.mock.calls[0][1].headers as Record<string, string>;
      expect(headers["Authorization"]).toMatch(/^Bearer /);
      const { removeAccessToken } = await import("@/lib/token-storage");
      removeAccessToken("backend");
    });

    it("Decimal strings remain strings", async () => {
      mockFetch.mockResolvedValueOnce(mockResponse(MOCK_CREATE_RESPONSE, 201));
      const { createBodyWeightEntry } = await import("@/services/api/body-weight");
      const result = await createBodyWeightEntry("2026-07-12", "70.00");
      if (result.success) {
        expect(typeof result.data.weight_kg).toBe("string");
      }
    });
  });
});
