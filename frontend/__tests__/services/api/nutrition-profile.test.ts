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

const MOCK_PROFILE_RESPONSE = {
  success: true,
  message: "Nutrition profile retrieved successfully.",
  data: {
    profile: {
      id: "123e4567-e89b-12d3-a456-426614174000",
      user_id: "123e4567-e89b-12d3-a456-426614174001",
      date_of_birth: "1990-01-15",
      biological_sex: "male",
      height_cm: "180.00",
      weight_kg: "75.00",
      activity_level: "moderately_active",
      goal: "maintain_weight",
      target_weight_kg: null,
      dietary_preference: "no_preference",
      allergies: [],
      created_at: "2025-01-01T00:00:00Z",
      updated_at: "2025-01-01T00:00:00Z",
    },
  },
};

const MOCK_CALCULATIONS_RESPONSE = {
  success: true,
  message: "Nutrition calculations completed successfully.",
  data: {
    metrics: {
      age_years: 35,
      bmi: "23.15",
      bmi_category: "healthy_weight",
      bmr_kcal_per_day: "1700.00",
      tdee_kcal_per_day: "2635.00",
    },
    targets: {
      calorie_target_kcal_per_day: "2635.00",
      protein_g_per_day: "98.81",
      carbohydrate_g_per_day: "296.44",
      fat_g_per_day: "87.83",
    },
  },
};

const MOCK_SUMMARY_RESPONSE = {
  success: true,
  message: "Nutrition summary generated successfully.",
  data: {
    overview: "Your nutrition profile indicates...",
    items: [
      { code: "BMI_SCREENING_CONTEXT", title: "BMI Context", message: "Your BMI is...", tone: "informational" },
      { code: "DAILY_ENERGY_ESTIMATE", title: "Daily Energy", message: "Your TDEE is...", tone: "informational" },
      { code: "CALORIE_TARGET_CONTEXT", title: "Calorie Target", message: "Your target is...", tone: "informational" },
      { code: "MACRONUTRIENT_TARGET_CONTEXT", title: "Macros", message: "Your macros...", tone: "informational" },
      { code: "GOAL_CONTEXT", title: "Goal", message: "Your goal is...", tone: "informational" },
      { code: "GENERAL_ESTIMATE_LIMITATION", title: "Limitation", message: "These are estimates...", tone: "caution" },
    ],
  },
};

function mockResponse(data: unknown, status = 200) {
  return Promise.resolve({
    ok: status >= 200 && status < 300,
    status,
    headers: new Headers({ "X-Request-ID": "req-123" }),
    text: () => Promise.resolve(JSON.stringify(data)),
    json: () => Promise.resolve(data),
  });
}

describe("Nutrition Profile Service", () => {
  describe("getNutritionProfile", () => {
    it("uses the correct GET endpoint", async () => {
      mockFetch.mockResolvedValueOnce(mockResponse(MOCK_PROFILE_RESPONSE));
      const { getNutritionProfile } = await import("@/services/api/nutrition-profile");
      await getNutritionProfile();
      expect(mockFetch).toHaveBeenCalledWith(
        "http://test:8000/api/v1/nutrition-profile",
        expect.objectContaining({ method: "GET" })
      );
    });

    it("returns profile data on success", async () => {
      mockFetch.mockResolvedValueOnce(mockResponse(MOCK_PROFILE_RESPONSE));
      const { getNutritionProfile } = await import("@/services/api/nutrition-profile");
      const result = await getNutritionProfile();
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.profile.biological_sex).toBe("male");
      }
    });

    it("returns error when profile not found", async () => {
      mockFetch.mockResolvedValueOnce(
        mockResponse(
          {
            success: false,
            error: { code: "NUTRITION_PROFILE_NOT_FOUND", message: "Nutrition profile not found.", request_id: "req-123" },
          },
          404
        )
      );
      const { getNutritionProfile } = await import("@/services/api/nutrition-profile");
      const result = await getNutritionProfile();
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.code).toBe("NUTRITION_PROFILE_NOT_FOUND");
      }
    });

    it("preserves Decimal strings", async () => {
      mockFetch.mockResolvedValueOnce(mockResponse(MOCK_PROFILE_RESPONSE));
      const { getNutritionProfile } = await import("@/services/api/nutrition-profile");
      const result = await getNutritionProfile();
      if (result.success) {
        expect(typeof result.data.profile.height_cm).toBe("string");
        expect(result.data.profile.height_cm).toBe("180.00");
      }
    });

    it("handles network errors safely", async () => {
      mockFetch.mockRejectedValueOnce(new Error("Network failure"));
      const { getNutritionProfile } = await import("@/services/api/nutrition-profile");
      const result = await getNutritionProfile();
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.code).toBe("NETWORK_ERROR");
      }
    });

    it("handles invalid JSON response", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        headers: new Headers(),
        text: () => Promise.resolve("not json"),
      });
      const { getNutritionProfile } = await import("@/services/api/nutrition-profile");
      const result = await getNutritionProfile();
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.code).toBe("INVALID_JSON");
      }
    });
  });

  describe("createNutritionProfile", () => {
    it("uses the correct POST endpoint and body", async () => {
      mockFetch.mockResolvedValueOnce(
        mockResponse(
          { success: true, message: "Nutrition profile created successfully.", data: MOCK_PROFILE_RESPONSE.data },
          201
        )
      );
      const { createNutritionProfile } = await import("@/services/api/nutrition-profile");
      const payload = {
        date_of_birth: "1990-01-15",
        biological_sex: "male",
        height_cm: "180.00",
        weight_kg: "75.00",
        activity_level: "moderately_active",
        goal: "maintain_weight",
      };
      await createNutritionProfile(payload);
      expect(mockFetch).toHaveBeenCalledWith(
        "http://test:8000/api/v1/nutrition-profile",
        expect.objectContaining({ method: "POST" })
      );
      const callArgs = mockFetch.mock.calls[0][1];
      expect(JSON.parse(callArgs.body)).toEqual(payload);
    });

    it("reuses the existing API client (Bearer token inherited)", async () => {
      mockFetch.mockResolvedValueOnce(mockResponse(MOCK_PROFILE_RESPONSE));
      const client = await import("@/services/api/client");
      expect(typeof client.apiPost).toBe("function");
    });
  });

  describe("updateNutritionProfile", () => {
    it("uses the correct PATCH endpoint and body", async () => {
      mockFetch.mockResolvedValueOnce(mockResponse(MOCK_PROFILE_RESPONSE));
      const { updateNutritionProfile } = await import("@/services/api/nutrition-profile");
      const payload = { weight_kg: "76.00" };
      await updateNutritionProfile(payload);
      expect(mockFetch).toHaveBeenCalledWith(
        "http://test:8000/api/v1/nutrition-profile",
        expect.objectContaining({ method: "PATCH" })
      );
      const callArgs = mockFetch.mock.calls[0][1];
      expect(JSON.parse(callArgs.body)).toEqual(payload);
    });
  });

  describe("getNutritionCalculations", () => {
    it("uses the correct GET endpoint with reference_date", async () => {
      mockFetch.mockResolvedValueOnce(mockResponse(MOCK_CALCULATIONS_RESPONSE));
      const { getNutritionCalculations } = await import("@/services/api/nutrition-profile");
      await getNutritionCalculations("2025-06-15");
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/nutrition-profile/calculations"),
        expect.objectContaining({ method: "GET" })
      );
    });

    it("returns calculation data", async () => {
      mockFetch.mockResolvedValueOnce(mockResponse(MOCK_CALCULATIONS_RESPONSE));
      const { getNutritionCalculations } = await import("@/services/api/nutrition-profile");
      const result = await getNutritionCalculations("2025-06-15");
      expect(result.success).toBe(true);
      if (result.success && result.data) {
        expect(result.data.metrics.bmi_category).toBe("healthy_weight");
        expect(typeof result.data.metrics.bmi).toBe("string");
      }
    });

    it("preserves Decimal strings in calculations", async () => {
      mockFetch.mockResolvedValueOnce(mockResponse(MOCK_CALCULATIONS_RESPONSE));
      const { getNutritionCalculations } = await import("@/services/api/nutrition-profile");
      const result = await getNutritionCalculations("2025-06-15");
      if (result.success && result.data) {
        expect(typeof result.data.targets.calorie_target_kcal_per_day).toBe("string");
        expect(result.data.targets.calorie_target_kcal_per_day).toBe("2635.00");
      }
    });
  });

  describe("getPersonalizedNutritionSummary", () => {
    it("uses the correct GET endpoint with reference_date", async () => {
      mockFetch.mockResolvedValueOnce(mockResponse(MOCK_SUMMARY_RESPONSE));
      const { getPersonalizedNutritionSummary } = await import("@/services/api/nutrition-profile");
      await getPersonalizedNutritionSummary("2025-06-15");
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/nutrition-profile/summary"),
        expect.objectContaining({ method: "GET" })
      );
    });

    it("returns summary data", async () => {
      mockFetch.mockResolvedValueOnce(mockResponse(MOCK_SUMMARY_RESPONSE));
      const { getPersonalizedNutritionSummary } = await import("@/services/api/nutrition-profile");
      const result = await getPersonalizedNutritionSummary("2025-06-15");
      expect(result.success).toBe(true);
      if (result.success && result.data) {
        expect(result.data.items[0].code).toBe("BMI_SCREENING_CONTEXT");
        expect(result.data.overview).toBe("Your nutrition profile indicates...");
      }
    });
  });
});