import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import NutritionPage from "@/app/(protected)/nutrition/page";
import { useNutritionProfile } from "@/hooks/use-nutrition-profile";

const mockLoadProfile = vi.fn();
const mockCreateProfile = vi.fn();
const mockUpdateProfile = vi.fn();
const mockRetryCalculations = vi.fn();
const mockRetrySummary = vi.fn();
const mockClearProfileError = vi.fn();

function createMockHook(overrides: Record<string, unknown> = {}) {
  return {
    profileStatus: "loading",
    profile: null,
    profileError: null,
    calculationsStatus: "idle",
    calculations: null,
    calculationsError: null,
    summaryStatus: "idle",
    summary: null,
    summaryError: null,
    loadProfile: mockLoadProfile,
    createProfile: mockCreateProfile,
    updateProfile: mockUpdateProfile,
    retryCalculations: mockRetryCalculations,
    retrySummary: mockRetrySummary,
    clearProfileError: mockClearProfileError,
    ...overrides,
  };
}

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

const mockUseNutritionProfile = vi.fn(() => createMockHook());
vi.mock("@/hooks/use-nutrition-profile", () => ({
  useNutritionProfile: () => mockUseNutritionProfile(),
}));

vi.mock("@/contexts/auth-context", () => ({
  useAuth: () => ({
    state: "authenticated",
    user: { email: "test@example.com" },
    login: vi.fn(),
    logout: vi.fn(),
  }),
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
  ],
};

describe("NutritionPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseNutritionProfile.mockReturnValue(createMockHook());
  });

  it("renders loading spinner when profileStatus is loading", () => {
    mockUseNutritionProfile.mockReturnValue(
      createMockHook({ profileStatus: "loading" })
    );
    render(<NutritionPage />);
    expect(screen.getByRole("status", { name: /loading profile/i })).toBeInTheDocument();
  });

  it("renders setup form when profileStatus is missing", () => {
    mockUseNutritionProfile.mockReturnValue(
      createMockHook({ profileStatus: "missing" })
    );
    render(<NutritionPage />);
    expect(screen.getByText("Set Up Your Nutrition Profile")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /create profile/i })).toBeInTheDocument();
  });

  it("renders profile overview when profile is available", () => {
    mockUseNutritionProfile.mockReturnValue(
      createMockHook({
        profileStatus: "available",
        profile: MOCK_PROFILE,
        calculationsStatus: "available",
        calculations: MOCK_CALCULATIONS,
        summaryStatus: "available",
        summary: MOCK_SUMMARY,
      })
    );
    render(<NutritionPage />);
    expect(screen.getByText("Your Profile")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /edit/i })).toBeInTheDocument();
  });

  it("renders error state on read_error", () => {
    mockUseNutritionProfile.mockReturnValue(
      createMockHook({
        profileStatus: "read_error",
        profileError: "Failed to load",
      })
    );
    render(<NutritionPage />);
    expect(screen.getByText("Failed to load")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /retry/i })).toBeInTheDocument();
  });
});
