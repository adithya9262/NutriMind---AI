import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor, act } from "@testing-library/react";
import { useNutritionProfile } from "@/hooks/use-nutrition-profile";

const mockGetProfile = vi.fn();
const mockCreateProfile = vi.fn();
const mockUpdateProfile = vi.fn();
const mockGetCalculations = vi.fn();
const mockGetSummary = vi.fn();

vi.mock("@/services/api/nutrition-profile", () => ({
  getNutritionProfile: (...args: unknown[]) => mockGetProfile(...args),
  createNutritionProfile: (...args: unknown[]) => mockCreateProfile(...args),
  updateNutritionProfile: (...args: unknown[]) => mockUpdateProfile(...args),
  getNutritionCalculations: (...args: unknown[]) => mockGetCalculations(...args),
  getPersonalizedNutritionSummary: (...args: unknown[]) => mockGetSummary(...args),
}));

const MOCK_PROFILE = {
  id: "p1",
  user_id: "u1",
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
};

const MOCK_CALCULATIONS = {
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
};

const MOCK_SUMMARY = {
  overview: "Your nutrition profile indicates...",
  items: [
    { code: "BMI_SCREENING_CONTEXT", title: "BMI Context", message: "Your BMI is...", tone: "informational" },
    { code: "DAILY_ENERGY_ESTIMATE", title: "Daily Energy", message: "Your TDEE is...", tone: "informational" },
  ],
};

function makeSuccessProfileResponse() {
  return { success: true as const, message: "ok", data: { profile: MOCK_PROFILE } };
}

function makeSuccessCalculationsResponse() {
  return { success: true as const, message: "ok", data: MOCK_CALCULATIONS };
}

function makeSuccessSummaryResponse() {
  return { success: true as const, message: "ok", data: MOCK_SUMMARY };
}

function makeNotFoundResponse() {
  return {
    success: false as const,
    error: { code: "NUTRITION_PROFILE_NOT_FOUND", message: "Nutrition profile not found.", request_id: "r1" },
  };
}

function makeErrorResponse(message = "Server error") {
  return {
    success: false as const,
    error: { code: "HTTP_ERROR", message, request_id: "r1" },
  };
}

describe("useNutritionProfile", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("initial loading state has correct defaults", () => {
    const { result } = renderHook(() => useNutritionProfile());
    expect(result.current.profileStatus).toBe("loading");
    expect(result.current.profile).toBeNull();
    expect(result.current.profileError).toBeNull();
    expect(result.current.calculationsStatus).toBe("idle");
    expect(result.current.summaryStatus).toBe("idle");
  });

  it("transitions to missing when profile not found", async () => {
    mockGetProfile.mockResolvedValueOnce(makeNotFoundResponse());
    const { result } = renderHook(() => useNutritionProfile());
    act(() => { result.current.loadProfile(); });
    await waitFor(() => {
      expect(result.current.profileStatus).toBe("missing");
    });
    expect(result.current.profile).toBeNull();
  });

  it("transitions to available with profile data", async () => {
    mockGetProfile.mockResolvedValueOnce(makeSuccessProfileResponse());
    mockGetCalculations.mockResolvedValueOnce(makeSuccessCalculationsResponse());
    mockGetSummary.mockResolvedValueOnce(makeSuccessSummaryResponse());
    const { result } = renderHook(() => useNutritionProfile());
    act(() => { result.current.loadProfile(); });
    await waitFor(() => {
      expect(result.current.profileStatus).toBe("available");
    });
    expect(result.current.profile).toEqual(MOCK_PROFILE);
    expect(result.current.calculationsStatus).toBe("available");
    expect(result.current.summaryStatus).toBe("available");
  });

  it("transitions to read_error on failure after retry", async () => {
    // First call fails, triggers retry. Second call (retry) also fails -> read_error
    mockGetProfile
      .mockResolvedValueOnce(makeErrorResponse("Server error"))  // first call
      .mockResolvedValueOnce(makeErrorResponse("Server error")); // retry call
    const { result } = renderHook(() => useNutritionProfile());
    act(() => { result.current.loadProfile(); });
    // First failure schedules a retry
    await waitFor(() => {
      expect(result.current.profileStatus).toBe("loading"); // still loading due to retry
    });
    // Wait for retry to complete (500ms timeout + execution)
    await waitFor(() => {
      expect(result.current.profileStatus).toBe("read_error");
    }, { timeout: 2000 });
    expect(result.current.profileError).toBe("Server error");
  });

  it("successful creation returns true and sets profile", async () => {
    mockCreateProfile.mockResolvedValueOnce(makeSuccessProfileResponse());
    mockGetProfile.mockResolvedValueOnce(makeSuccessProfileResponse());
    mockGetCalculations.mockResolvedValueOnce(makeSuccessCalculationsResponse());
    mockGetSummary.mockResolvedValueOnce(makeSuccessSummaryResponse());
    const { result } = renderHook(() => useNutritionProfile());
    const payload = {
      date_of_birth: "1990-01-15",
      biological_sex: "male",
      height_cm: "180.00",
      weight_kg: "75.00",
      activity_level: "moderately_active",
      goal: "maintain_weight",
    };
    let success = false;
    await act(async () => {
      success = await result.current.createProfile(payload);
    });
    expect(success).toBe(true);
    expect(result.current.profileStatus).toBe("available");
    expect(result.current.profile).toEqual(MOCK_PROFILE);
  });

  it("creation failure returns false and sets error", async () => {
    mockCreateProfile.mockResolvedValueOnce(makeErrorResponse("Creation failed"));
    const { result } = renderHook(() => useNutritionProfile());
    const payload = {
      date_of_birth: "1990-01-15",
      biological_sex: "male",
      height_cm: "180.00",
      weight_kg: "75.00",
      activity_level: "moderately_active",
      goal: "maintain_weight",
    };
    let success = true;
    await act(async () => {
      success = await result.current.createProfile(payload);
    });
    expect(success).toBe(false);
    expect(result.current.profileStatus).toBe("create_error");
    expect(result.current.profileError).toBe("Creation failed");
  });

  it("successful update returns true and sets profile", async () => {
    mockUpdateProfile.mockResolvedValueOnce(makeSuccessProfileResponse());
    mockGetProfile.mockResolvedValueOnce(makeSuccessProfileResponse());
    mockGetCalculations.mockResolvedValueOnce(makeSuccessCalculationsResponse());
    mockGetSummary.mockResolvedValueOnce(makeSuccessSummaryResponse());
    const { result } = renderHook(() => useNutritionProfile());
    const payload = { weight_kg: "76.00" };
    let success = false;
    await act(async () => {
      success = await result.current.updateProfile(payload);
    });
    expect(success).toBe(true);
    expect(result.current.profileStatus).toBe("available");
  });

  it("profile values preserved after creation failure", async () => {
    mockGetProfile.mockResolvedValueOnce(makeSuccessProfileResponse());
    mockGetCalculations.mockResolvedValueOnce(makeSuccessCalculationsResponse());
    mockGetSummary.mockResolvedValueOnce(makeSuccessSummaryResponse());
    const { result } = renderHook(() => useNutritionProfile());
    act(() => { result.current.loadProfile(); });
    await waitFor(() => {
      expect(result.current.profileStatus).toBe("available");
    });
    const loadedProfile = result.current.profile;

    mockCreateProfile.mockResolvedValueOnce(makeErrorResponse("Update failed"));
    const payload = {
      date_of_birth: "1990-01-15",
      biological_sex: "male",
      height_cm: "180.00",
      weight_kg: "80.00",
      activity_level: "moderately_active",
      goal: "maintain_weight",
    };
    await act(async () => {
      await result.current.createProfile(payload);
    });
    expect(result.current.profile).toEqual(loadedProfile);
  });
});
