import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";

vi.mock("@/contexts/auth-context", () => ({
  useAuth: () => ({ state: "authenticated" as const, user: { id: "u1", email: "test@test.com" }, logout: vi.fn() }),
  AuthProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

const mockReloadAll = vi.fn();
const mockRetryHistory = vi.fn();
const mockRetryTrend = vi.fn();
const mockRetryGoalProgress = vi.fn();
const mockCreateEntry = vi.fn();
const mockRequestDelete = vi.fn();
const mockConfirmDelete = vi.fn();
const mockCancelDelete = vi.fn();
const mockClearCreateSuccess = vi.fn();

import BodyWeightPage from "@/app/(protected)/body-weight/page";

vi.mock("@/hooks/use-body-weight", () => ({
  useBodyWeight: () => ({
    historyStatus: "empty",
    entries: [],
    historyError: null,
    trendStatus: "insufficient",
    trend: null,
    trendError: null,
    goalStatus: "missing_current_weight",
    goalProgress: null,
    goalError: null,
    createStatus: "idle",
    createError: null,
    deleteStatus: "idle",
    deletingEntryId: null,
    deleteError: null,
    reloadAll: mockReloadAll,
    retryHistory: mockRetryHistory,
    retryTrend: mockRetryTrend,
    retryGoalProgress: mockRetryGoalProgress,
    createEntry: mockCreateEntry,
    requestDelete: mockRequestDelete,
    confirmDelete: mockConfirmDelete,
    cancelDelete: mockCancelDelete,
    clearCreateSuccess: mockClearCreateSuccess,
  }),
}));

beforeEach(() => {
  vi.clearAllMocks();
});

function loadPage() {
  return render(<BodyWeightPage />);
}

describe("BodyWeightPage", () => {
  it("renders the page header with exactly one h1", async () => {
    const { container } = await loadPage();
    const headings = container.querySelectorAll("h1");
    expect(headings).toHaveLength(1);
    expect(headings[0]).toHaveTextContent("Body Weight");
  }, 10000);

  it("renders add weight heading", async () => {
    await loadPage();
    const headings = screen.getAllByRole("heading", { name: /add weight/i });
    expect(headings.length).toBeGreaterThanOrEqual(1);
  });

  it("renders weight history heading", async () => {
    await loadPage();
    expect(screen.getByRole("heading", { name: /^weight history$/i })).toBeInTheDocument();
  });

  it("renders weight trend heading", async () => {
    await loadPage();
    expect(screen.getByRole("heading", { name: /^weight trend$/i })).toBeInTheDocument();
  });

  it("renders goal progress heading", async () => {
    await loadPage();
    expect(screen.getByRole("heading", { name: /^goal progress$/i })).toBeInTheDocument();
  });

  it("renders empty state when no entries exist", async () => {
    await loadPage();
    expect(screen.getByText(/no weight entries yet/i)).toBeInTheDocument();
  });

  it("no edit action exists", async () => {
    await loadPage();
    expect(screen.queryByRole("button", { name: /edit/i })).not.toBeInTheDocument();
  });
});
