import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import NutritionLogsPage from "@/app/(protected)/nutrition/logs/page";

const mockSetSelectedDate = vi.fn();
const mockReloadAll = vi.fn();
const mockRetryEntries = vi.fn();
const mockRetrySummary = vi.fn();
const mockRetryProgress = vi.fn();
const mockCreateEntry = vi.fn();
const mockRequestDelete = vi.fn();
const mockConfirmDelete = vi.fn();
const mockCancelDelete = vi.fn();
const mockClearCreateSuccess = vi.fn();
const mockClearDeleteSuccess = vi.fn();

function createMockHook(overrides: Record<string, unknown> = {}) {
  return {
    selectedDate: "2025-06-15",
    entriesStatus: "loading" as const,
    entries: [] as Array<Record<string, unknown>>,
    entriesError: null,
    summaryStatus: "loading" as const,
    summary: null,
    summaryError: null,
    progressStatus: "loading" as const,
    progress: null,
    progressError: null,
    createStatus: "idle" as const,
    createError: null,
    deleteStatus: "idle" as const,
    deletingEntryId: null,
    deleteError: null,
    setSelectedDate: mockSetSelectedDate,
    reloadAll: mockReloadAll,
    retryEntries: mockRetryEntries,
    retrySummary: mockRetrySummary,
    retryProgress: mockRetryProgress,
    createEntry: mockCreateEntry,
    requestDelete: mockRequestDelete,
    confirmDelete: mockConfirmDelete,
    cancelDelete: mockCancelDelete,
    clearCreateSuccess: mockClearCreateSuccess,
    clearDeleteSuccess: mockClearDeleteSuccess,
    ...overrides,
  };
}

vi.mock("@/hooks/use-daily-nutrition-logs", () => ({
  useDailyNutritionLogs: () => mockHook(),
}));

vi.mock("@/contexts/auth-context", () => ({
  useAuth: () => ({
    state: "authenticated",
    user: { email: "test@example.com" },
    login: vi.fn(),
    logout: vi.fn(),
  }),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn(), prefetch: vi.fn() }),
  useSearchParams: () => new URLSearchParams(),
}));

let mockHook: () => ReturnType<typeof createMockHook>;

beforeEach(() => {
  vi.clearAllMocks();
  mockHook = () => createMockHook();
});

describe("NutritionLogsPage", () => {
  it("renders one h1", () => {
    render(<NutritionLogsPage />);
    expect(screen.getByRole("heading", { level: 1 })).toBeInTheDocument();
    expect(screen.getAllByRole("heading", { level: 1 })).toHaveLength(1);
  });

  it("renders date selector", () => {
    render(<NutritionLogsPage />);
    expect(screen.getByLabelText(/date/i)).toBeInTheDocument();
  });

  it("renders initial loading state", () => {
    render(<NutritionLogsPage />);
    expect(screen.getByRole("status", { name: /loading entries/i })).toBeInTheDocument();
    expect(screen.getByRole("status", { name: /loading summary/i })).toBeInTheDocument();
    expect(screen.getByRole("status", { name: /loading progress/i })).toBeInTheDocument();
  });

  it("shows add entry form", () => {
    render(<NutritionLogsPage />);
    expect(screen.getByRole("form", { name: /add nutrition log entry/i })).toBeInTheDocument();
  });

  it("shows empty-day state", () => {
    mockHook = () => createMockHook({
      entriesStatus: "empty",
      summaryStatus: "available",
      summary: {
        entry_count: 0,
        totals: { calories_kcal: "0.00", protein_g: "0.00", carbohydrate_g: "0.00", fat_g: "0.00" },
        meals: [
          { meal_type: "breakfast", entry_count: 0, totals: { calories_kcal: "0.00", protein_g: "0.00", carbohydrate_g: "0.00", fat_g: "0.00" } },
          { meal_type: "lunch", entry_count: 0, totals: { calories_kcal: "0.00", protein_g: "0.00", carbohydrate_g: "0.00", fat_g: "0.00" } },
          { meal_type: "dinner", entry_count: 0, totals: { calories_kcal: "0.00", protein_g: "0.00", carbohydrate_g: "0.00", fat_g: "0.00" } },
          { meal_type: "snack", entry_count: 0, totals: { calories_kcal: "0.00", protein_g: "0.00", carbohydrate_g: "0.00", fat_g: "0.00" } },
        ],
      },
      progressStatus: "available",
      progress: {
        calories: { consumed: "0.00", target: "2500.00", remaining: "2500.00", percentage: "0.00", status: "below_target" },
        protein: { consumed: "0.00", target: "100.00", remaining: "100.00", percentage: "0.00", status: "below_target" },
        carbohydrate: { consumed: "0.00", target: "300.00", remaining: "300.00", percentage: "0.00", status: "below_target" },
        fat: { consumed: "0.00", target: "80.00", remaining: "80.00", percentage: "0.00", status: "below_target" },
      },
    });
    render(<NutritionLogsPage />);
    expect(screen.getByText(/no entries logged/i)).toBeInTheDocument();
  });

  it("shows success feedback after create", () => {
    mockHook = () => createMockHook({ createStatus: "success" });
    render(<NutritionLogsPage />);
    expect(screen.getByText(/entry added successfully/i)).toBeInTheDocument();
  });

  it("no edit action exists", () => {
    render(<NutritionLogsPage />);
    expect(screen.queryByRole("button", { name: /edit/i })).not.toBeInTheDocument();
  });

  it("renders page header with correct title", () => {
    render(<NutritionLogsPage />);
    expect(screen.getByText("Food Diary")).toBeInTheDocument();
  });
});
