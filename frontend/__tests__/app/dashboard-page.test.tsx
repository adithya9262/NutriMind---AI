import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, waitFor, act } from "@testing-library/react"
import DashboardPage from "@/app/(protected)/dashboard/page"

const mockLoadProfile = vi.fn()
const mockRetryCalculations = vi.fn()

function createMockProfileHook(overrides: Record<string, unknown> = {}) {
  return {
    profileStatus: "available",
    profile: { email: "test@example.com", daily_calorie_goal: 2000, daily_protein_goal_g: 150, daily_carb_goal_g: 200, daily_fat_goal_g: 70, water_goal_ml: 2000, sleep_goal_hours: 8 },
    calculationsStatus: "available",
    calculations: {
      metrics: { bmi: "22.5", bmi_category: "normal", bmr_kcal_per_day: "1500", tdee_kcal_per_day: "2200" },
      targets: { calorie_target_kcal_per_day: "2200", protein_g_per_day: "165", carbohydrate_g_per_day: "275", fat_g_per_day: "73" }
    },
    calculationsError: null,
    summaryStatus: "available",
    summary: { entry_count: 0, totals: { calories_kcal: "0", protein_g: "0", carbohydrate_g: "0", fat_g: "0" }, meals: [] },
    loadProfile: mockLoadProfile,
    retryCalculations: mockRetryCalculations,
    ...overrides,
  }
}

function createMockLogsHook(overrides: Record<string, unknown> = {}) {
  return {
    selectedDate: "2025-06-15",
    entriesStatus: "available",
    entries: [],
    summaryStatus: "available",
    summary: { entry_count: 0, totals: { calories_kcal: "0", protein_g: "0", carbohydrate_g: "0", fat_g: "0" }, meals: [] },
    progressStatus: "available",
    progress: null,
    setSelectedDate: vi.fn(),
    reloadAll: vi.fn(),
    createEntry: vi.fn(),
    requestDelete: vi.fn(),
    confirmDelete: vi.fn(),
    cancelDelete: vi.fn(),
    clearCreateSuccess: vi.fn(),
    clearDeleteSuccess: vi.fn(),
    ...overrides,
  }
}

function createMockWeightHook(overrides: Record<string, unknown> = {}) {
  return {
    historyStatus: "available",
    entries: [],
    trendStatus: "idle",
    trend: null,
    goalStatus: "idle",
    goalProgress: null,
    createStatus: "idle",
    deleteStatus: "idle",
    createEntry: vi.fn(),
    requestDelete: vi.fn(),
    confirmDelete: vi.fn(),
    cancelDelete: vi.fn(),
    reloadAll: vi.fn(),
    clearCreateSuccess: vi.fn(),
    ...overrides,
  }
}

const mockUseAuth = vi.fn(() => ({
  state: "authenticated",
  user: { email: "test@example.com" },
  login: vi.fn(),
  logout: vi.fn(),
}))

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}))

const mockUseNutritionProfile = vi.fn(() => createMockProfileHook())
vi.mock("@/hooks/use-nutrition-profile", () => ({
  useNutritionProfile: () => mockUseNutritionProfile(),
}))

const mockUseDailyNutritionLogs = vi.fn(() => createMockLogsHook())
vi.mock("@/hooks/use-daily-nutrition-logs", () => ({
  useDailyNutritionLogs: () => mockUseDailyNutritionLogs(),
}))

const mockUseBodyWeight = vi.fn(() => createMockWeightHook())
vi.mock("@/hooks/use-body-weight", () => ({
  useBodyWeight: () => mockUseBodyWeight(),
}))

vi.mock("@/contexts/auth-context", () => ({
  useAuth: () => mockUseAuth(),
}))

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
}

describe("DashboardPage", () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockUseNutritionProfile.mockReturnValue(createMockProfileHook())
    mockUseDailyNutritionLogs.mockReturnValue(createMockLogsHook())
    mockUseBodyWeight.mockReturnValue(createMockWeightHook())
    mockUseAuth.mockReturnValue({
      state: "authenticated",
      user: { email: "test@example.com" },
      login: vi.fn(),
      logout: vi.fn(),
    })
  })

  it("renders user greeting", async () => {
    render(<DashboardPage />)
    await waitFor(() => {
      expect(screen.getByText(/test/i)).toBeInTheDocument()
    })
  })

  it("renders stat cards after initial load", async () => {
    mockUseNutritionProfile.mockReturnValue(
      createMockProfileHook({ profileStatus: "available", calculationsStatus: "available", calculations: MOCK_CALCULATIONS })
    )
    mockUseDailyNutritionLogs.mockReturnValue(createMockLogsHook({ summaryStatus: "available", summary: { entry_count: 0, totals: { calories_kcal: "0", protein_g: "0", carbohydrate_g: "0", fat_g: "0" }, meals: [] } }))
    render(<DashboardPage />)
    await waitFor(() => {
      expect(screen.getAllByText("Calories").length).toBeGreaterThanOrEqual(1)
      expect(screen.getByText("Protein Target")).toBeInTheDocument()
      expect(screen.getByText("Hydration")).toBeInTheDocument()
      expect(screen.getByText("Weight")).toBeInTheDocument()
    })
  })

  it("shows AI Insight section", async () => {
    mockUseNutritionProfile.mockReturnValue(
      createMockProfileHook({ profileStatus: "missing" })
    )
    render(<DashboardPage />)
    await waitFor(() => {
      expect(screen.getByText("AI Insights")).toBeInTheDocument()
    })
    await waitFor(() => {
      expect(screen.getByText("Set up your nutrition profile")).toBeInTheDocument()
    })
  })
})
