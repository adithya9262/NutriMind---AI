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

const MOCK_LIST_RESPONSE = {
  success: true,
  message: "Nutrition log entries retrieved successfully.",
  data: {
    logged_date: "2025-06-15",
    entries: [
      {
        entry_id: "e1",
        food_name: "Oatmeal",
        meal_type: "breakfast",
        serving_description: "1 cup",
        calories_kcal: "350.00",
        protein_g: "12.00",
        carbohydrate_g: "55.00",
        fat_g: "5.00",
      },
    ],
  },
};

const MOCK_CREATE_RESPONSE = {
  success: true,
  message: "Nutrition log entry created successfully.",
  data: {
    entry_id: "e1",
    food_name: "Oatmeal",
    meal_type: "breakfast",
    serving_description: "1 cup",
    calories_kcal: "350.00",
    protein_g: "12.00",
    carbohydrate_g: "55.00",
    fat_g: "5.00",
  },
};

const MOCK_DELETE_RESPONSE = {
  success: true,
  message: "Nutrition log entry deleted successfully.",
};

const MOCK_SUMMARY_RESPONSE = {
  success: true,
  message: "Daily nutrition log summarized successfully.",
  data: {
    entry_count: 1,
    totals: { calories_kcal: "350.00", protein_g: "12.00", carbohydrate_g: "55.00", fat_g: "5.00" },
    meals: [
      { meal_type: "breakfast", entry_count: 1, totals: { calories_kcal: "350.00", protein_g: "12.00", carbohydrate_g: "55.00", fat_g: "5.00" } },
      { meal_type: "lunch", entry_count: 0, totals: { calories_kcal: "0.00", protein_g: "0.00", carbohydrate_g: "0.00", fat_g: "0.00" } },
      { meal_type: "dinner", entry_count: 0, totals: { calories_kcal: "0.00", protein_g: "0.00", carbohydrate_g: "0.00", fat_g: "0.00" } },
      { meal_type: "snack", entry_count: 0, totals: { calories_kcal: "0.00", protein_g: "0.00", carbohydrate_g: "0.00", fat_g: "0.00" } },
    ],
  },
};

const MOCK_PROGRESS_RESPONSE = {
  success: true,
  message: "Daily nutrition target progress calculated successfully.",
  data: {
    calories: { consumed: "350.00", target: "2500.00", remaining: "2150.00", percentage: "14.00", status: "below_target" },
    protein: { consumed: "12.00", target: "100.00", remaining: "88.00", percentage: "12.00", status: "below_target" },
    carbohydrate: { consumed: "55.00", target: "300.00", remaining: "245.00", percentage: "18.33", status: "below_target" },
    fat: { consumed: "5.00", target: "80.00", remaining: "75.00", percentage: "6.25", status: "below_target" },
  },
};

describe("Nutrition Logs Service", () => {
  describe("listNutritionLogEntries", () => {
    it("uses GET /nutrition-logs with logged_date", async () => {
      mockFetch.mockResolvedValueOnce(mockResponse(MOCK_LIST_RESPONSE));
      const { listNutritionLogEntries } = await import("@/services/api/nutrition-logs");
      await listNutritionLogEntries("2025-06-15");
      const callUrl = mockFetch.mock.calls[0][0] as string;
      expect(callUrl).toContain("/nutrition-logs");
      expect(callUrl).toContain("logged_date=2025-06-15");
      expect(mockFetch.mock.calls[0][1].method).toBe("GET");
    });

    it("returns entries list on success", async () => {
      mockFetch.mockResolvedValueOnce(mockResponse(MOCK_LIST_RESPONSE));
      const { listNutritionLogEntries } = await import("@/services/api/nutrition-logs");
      const result = await listNutritionLogEntries("2025-06-15");
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.entries).toHaveLength(1);
        expect(result.data.entries[0].food_name).toBe("Oatmeal");
      }
    });

    it("preserves Decimal strings", async () => {
      mockFetch.mockResolvedValueOnce(mockResponse(MOCK_LIST_RESPONSE));
      const { listNutritionLogEntries } = await import("@/services/api/nutrition-logs");
      const result = await listNutritionLogEntries("2025-06-15");
      if (result.success) {
        expect(typeof result.data.entries[0].calories_kcal).toBe("string");
        expect(result.data.entries[0].calories_kcal).toBe("350.00");
      }
    });
  });

  describe("createNutritionLogEntry", () => {
    it("uses POST /nutrition-logs with logged_date query", async () => {
      mockFetch.mockResolvedValueOnce(mockResponse(MOCK_CREATE_RESPONSE, 201));
      const { createNutritionLogEntry } = await import("@/services/api/nutrition-logs");
      const payload = {
        entry_id: "e1",
        food_name: "Oatmeal",
        meal_type: "breakfast" as const,
        serving_description: "1 cup",
        calories_kcal: "350.00",
        protein_g: "12.00",
        carbohydrate_g: "55.00",
        fat_g: "5.00",
      };
      await createNutritionLogEntry("2025-06-15", payload);
      const callUrl = mockFetch.mock.calls[0][0] as string;
      expect(callUrl).toContain("/nutrition-logs");
      expect(callUrl).toContain("logged_date=2025-06-15");
      expect(mockFetch.mock.calls[0][1].method).toBe("POST");
    });

    it("sends exact body fields", async () => {
      mockFetch.mockResolvedValueOnce(mockResponse(MOCK_CREATE_RESPONSE, 201));
      const { createNutritionLogEntry } = await import("@/services/api/nutrition-logs");
      const payload = {
        entry_id: "e1",
        food_name: "Oatmeal",
        meal_type: "breakfast" as const,
        serving_description: "1 cup",
        calories_kcal: "350.00",
        protein_g: "12.00",
        carbohydrate_g: "55.00",
        fat_g: "5.00",
      };
      await createNutritionLogEntry("2025-06-15", payload);
      const body = JSON.parse(mockFetch.mock.calls[0][1].body);
      expect(body).toEqual(payload);
    });
  });

  describe("deleteNutritionLogEntry", () => {
    it("uses DELETE /nutrition-logs/{entry_id}", async () => {
      mockFetch.mockResolvedValueOnce(mockResponse(MOCK_DELETE_RESPONSE));
      const { deleteNutritionLogEntry } = await import("@/services/api/nutrition-logs");
      await deleteNutritionLogEntry("e1");
      const callUrl = mockFetch.mock.calls[0][0] as string;
      expect(callUrl).toContain("/nutrition-logs/e1");
      expect(mockFetch.mock.calls[0][1].method).toBe("DELETE");
    });

    it("encodes UUID path safely", async () => {
      mockFetch.mockResolvedValueOnce(mockResponse(MOCK_DELETE_RESPONSE));
      const { deleteNutritionLogEntry } = await import("@/services/api/nutrition-logs");
      await deleteNutritionLogEntry("123e4567-e89b-12d3-a456-426614174000");
      const callUrl = mockFetch.mock.calls[0][0] as string;
      expect(callUrl).toContain("/nutrition-logs/123e4567-e89b-12d3-a456-426614174000");
    });
  });

  describe("getDailyNutritionLogSummary", () => {
    it("uses GET /nutrition-logs/summary with logged_date", async () => {
      mockFetch.mockResolvedValueOnce(mockResponse(MOCK_SUMMARY_RESPONSE));
      const { getDailyNutritionLogSummary } = await import("@/services/api/nutrition-logs");
      await getDailyNutritionLogSummary("2025-06-15");
      const callUrl = mockFetch.mock.calls[0][0] as string;
      expect(callUrl).toContain("/nutrition-logs/summary");
      expect(callUrl).toContain("logged_date=2025-06-15");
      expect(mockFetch.mock.calls[0][1].method).toBe("GET");
    });
  });

  describe("getDailyNutritionTargetProgress", () => {
    it("uses GET /nutrition-logs/progress with logged_date and reference_date", async () => {
      mockFetch.mockResolvedValueOnce(mockResponse(MOCK_PROGRESS_RESPONSE));
      const { getDailyNutritionTargetProgress } = await import("@/services/api/nutrition-logs");
      await getDailyNutritionTargetProgress("2025-06-15", "2025-06-15");
      const callUrl = mockFetch.mock.calls[0][0] as string;
      expect(callUrl).toContain("/nutrition-logs/progress");
      expect(callUrl).toContain("logged_date=2025-06-15");
      expect(callUrl).toContain("reference_date=2025-06-15");
      expect(mockFetch.mock.calls[0][1].method).toBe("GET");
    });
  });

  describe("Error handling", () => {
    it("preserves error codes", async () => {
      mockFetch.mockResolvedValueOnce(
        mockResponse(
          { success: false, error: { code: "NUTRITION_LOG_ENTRY_NOT_FOUND", message: "Entry not found.", request_id: "req-123" } },
          404
        )
      );
      const { deleteNutritionLogEntry } = await import("@/services/api/nutrition-logs");
      const result = await deleteNutritionLogEntry("e1");
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.code).toBe("NUTRITION_LOG_ENTRY_NOT_FOUND");
      }
    });

    it("handles network errors safely", async () => {
      mockFetch.mockRejectedValueOnce(new Error("Network failure"));
      const { listNutritionLogEntries } = await import("@/services/api/nutrition-logs");
      const result = await listNutritionLogEntries("2025-06-15");
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.code).toBe("NETWORK_ERROR");
      }
    });

    it("handles timeout errors safely", async () => {
      const error = new Error("The operation was aborted");
      error.name = "AbortError";
      mockFetch.mockRejectedValueOnce(error);
      const { listNutritionLogEntries } = await import("@/services/api/nutrition-logs");
      const result = await listNutritionLogEntries("2025-06-15");
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
      const { listNutritionLogEntries } = await import("@/services/api/nutrition-logs");
      const result = await listNutritionLogEntries("2025-06-15");
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
      mockFetch.mockResolvedValueOnce(mockResponse(MOCK_LIST_RESPONSE));
      const { listNutritionLogEntries } = await import("@/services/api/nutrition-logs");
      await listNutritionLogEntries("2025-06-15");
      const headers = mockFetch.mock.calls[0][1].headers as Record<string, string>;
      expect(headers["Authorization"]).toMatch(/^Bearer /);
      const { removeAccessToken } = await import("@/lib/token-storage");
      removeAccessToken("backend");
    });
  });
});
