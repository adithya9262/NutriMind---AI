import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act, waitFor } from "@testing-library/react";
import { useBodyWeight } from "@/hooks/use-body-weight";

const mockListHistory = vi.fn();
const mockCreateEntry = vi.fn();
const mockDeleteEntry = vi.fn();
const mockGetTrend = vi.fn();
const mockGetGoalProgress = vi.fn();

vi.mock("@/services/api/body-weight", () => ({
  listBodyWeightHistory: (...args: unknown[]) => mockListHistory(...args),
  createBodyWeightEntry: (...args: unknown[]) => mockCreateEntry(...args),
  deleteBodyWeightEntry: (...args: unknown[]) => mockDeleteEntry(...args),
  getBodyWeightTrend: (...args: unknown[]) => mockGetTrend(...args),
  getBodyWeightGoalProgress: (...args: unknown[]) => mockGetGoalProgress(...args),
}));

function successResponse(data: unknown) {
  return { success: true as const, message: "Success", data };
}

function errorResponse(code: string, message: string) {
  return { success: false as const, error: { code, message, request_id: "req-1" } };
}

const MOCK_ENTRIES = [
  { entry_id: "e1", logged_date: "2026-07-12", weight_kg: "70.00" },
];

const MOCK_TREND = {
  observation_count: 2,
  first_logged_date: "2026-07-01",
  latest_logged_date: "2026-07-12",
  starting_weight_kg: "71.00",
  latest_weight_kg: "70.00",
  absolute_change_kg: "-1.00",
  percentage_change: "-1.41",
  direction: "decreased" as const,
};

const MOCK_GOAL = {
  starting_weight_kg: "80.00",
  current_weight_kg: "75.00",
  target_weight_kg: "70.00",
  direction: "decrease" as const,
  total_change_required_kg: "10.00",
  change_achieved_kg: "5.00",
  remaining_change_kg: "5.00",
  progress_percentage: "50.00",
  status: "in_progress" as const,
};

beforeEach(() => {
  vi.clearAllMocks();
  mockListHistory.mockResolvedValue(successResponse({ entries: MOCK_ENTRIES }));
  mockGetTrend.mockResolvedValue(successResponse(MOCK_TREND));
  mockGetGoalProgress.mockResolvedValue(successResponse(MOCK_GOAL));
  mockCreateEntry.mockResolvedValue(successResponse(MOCK_ENTRIES[0]));
  mockDeleteEntry.mockResolvedValue(successResponse(undefined));
});

afterEach(() => {
});

function mountHook() {
  return renderHook(() => useBodyWeight());
}

describe("useBodyWeight", () => {
  it("starts in loading state", async () => {
    mockListHistory.mockResolvedValue(new Promise(() => {}));
    mockGetTrend.mockResolvedValue(new Promise(() => {}));
    mockGetGoalProgress.mockResolvedValue(new Promise(() => {}));
    const { result } = mountHook();
    expect(result.current.historyStatus).toBe("loading");
    expect(result.current.trendStatus).toBe("loading");
    expect(result.current.goalStatus).toBe("loading");
  });

  it("loads history successfully", async () => {
    const { result } = mountHook();
    act(() => { result.current.reloadAll(); });
    await waitFor(() => {
      expect(result.current.historyStatus).toBe("available");
    });
    expect(result.current.entries).toHaveLength(1);
  });

  it("handles empty history", async () => {
    mockListHistory.mockResolvedValue(successResponse({ entries: [] }));
    const { result } = mountHook();
    act(() => { result.current.reloadAll(); });
    await waitFor(() => {
      expect(result.current.historyStatus).toBe("empty");
    });
    expect(result.current.entries).toHaveLength(0);
  });

  it("handles history error", async () => {
    mockListHistory.mockResolvedValue(errorResponse("HTTP_ERROR", "Failed"));
    const { result } = mountHook();
    act(() => { result.current.reloadAll(); });
    await waitFor(() => {
      expect(result.current.historyStatus).toBe("error");
    });
    expect(result.current.historyError).toBe("Failed");
  });

  it("loads trend successfully", async () => {
    const { result } = mountHook();
    act(() => { result.current.reloadAll(); });
    await waitFor(() => {
      expect(result.current.trendStatus).toBe("available");
    });
    expect(result.current.trend?.direction).toBe("decreased");
  });

  it("handles insufficient history for trend", async () => {
    mockGetTrend.mockResolvedValue(errorResponse("BODY_WEIGHT_TREND_INSUFFICIENT_HISTORY", "Insufficient"));
    const { result } = mountHook();
    act(() => { result.current.reloadAll(); });
    await waitFor(() => {
      expect(result.current.trendStatus).toBe("insufficient");
    });
  });

  it("handles trend error", async () => {
    mockGetTrend.mockResolvedValue(errorResponse("HTTP_ERROR", "Trend fail"));
    const { result } = mountHook();
    act(() => { result.current.reloadAll(); });
    await waitFor(() => {
      expect(result.current.trendStatus).toBe("error");
    });
    expect(result.current.trendError).toBe("Trend fail");
  });

  it("loads goal progress successfully", async () => {
    const { result } = mountHook();
    act(() => { result.current.reloadAll(); });
    await waitFor(() => {
      expect(result.current.goalStatus).toBe("available");
    });
    expect(result.current.goalProgress?.status).toBe("in_progress");
  });

  it("handles missing profile for goal", async () => {
    mockGetGoalProgress.mockResolvedValue(errorResponse("NUTRITION_PROFILE_NOT_FOUND", "No profile"));
    const { result } = mountHook();
    act(() => { result.current.reloadAll(); });
    await waitFor(() => {
      expect(result.current.goalStatus).toBe("missing_profile");
    });
  });

  it("handles missing current weight for goal", async () => {
    mockGetGoalProgress.mockResolvedValue(errorResponse("BODY_WEIGHT_GOAL_CURRENT_WEIGHT_NOT_FOUND", "No weight"));
    const { result } = mountHook();
    act(() => { result.current.reloadAll(); });
    await waitFor(() => {
      expect(result.current.goalStatus).toBe("missing_current_weight");
    });
  });

  it("handles invalid goal", async () => {
    mockGetGoalProgress.mockResolvedValue(errorResponse("BODY_WEIGHT_GOAL_PROGRESS_INVALID", "Invalid"));
    const { result } = mountHook();
    act(() => { result.current.reloadAll(); });
    await waitFor(() => {
      expect(result.current.goalStatus).toBe("invalid_goal");
    });
  });

  it("handles goal error", async () => {
    mockGetGoalProgress.mockResolvedValue(errorResponse("HTTP_ERROR", "Goal fail"));
    const { result } = mountHook();
    act(() => { result.current.reloadAll(); });
    await waitFor(() => {
      expect(result.current.goalStatus).toBe("error");
    });
    expect(result.current.goalError).toBe("Goal fail");
  });

  it("retry history works", async () => {
    mockListHistory.mockResolvedValueOnce(errorResponse("HTTP_ERROR", "Fail"));
    const { result } = mountHook();
    act(() => { result.current.reloadAll(); });
    await waitFor(() => {
      expect(result.current.historyStatus).toBe("error");
    });

    mockListHistory.mockResolvedValue(successResponse({ entries: MOCK_ENTRIES }));
    act(() => { result.current.retryHistory(); });
    await waitFor(() => {
      expect(result.current.historyStatus).toBe("available");
    });
  });

  it("retry trend works", async () => {
    mockGetTrend.mockResolvedValueOnce(errorResponse("HTTP_ERROR", "Fail"));
    const { result } = mountHook();
    act(() => { result.current.reloadAll(); });
    await waitFor(() => {
      expect(result.current.trendStatus).toBe("error");
    });

    mockGetTrend.mockResolvedValue(successResponse(MOCK_TREND));
    act(() => { result.current.retryTrend(); });
    await waitFor(() => {
      expect(result.current.trendStatus).toBe("available");
    });
  });

  it("retry goal progress works", async () => {
    mockGetGoalProgress.mockResolvedValueOnce(errorResponse("HTTP_ERROR", "Fail"));
    const { result } = mountHook();
    act(() => { result.current.reloadAll(); });
    await waitFor(() => {
      expect(result.current.goalStatus).toBe("error");
    });

    mockGetGoalProgress.mockResolvedValue(successResponse(MOCK_GOAL));
    act(() => { result.current.retryGoalProgress(); });
    await waitFor(() => {
      expect(result.current.goalStatus).toBe("available");
    });
  });

  it("successful create calls API and refreshes", async () => {
    const { result } = mountHook();
    act(() => { result.current.reloadAll(); });
    await waitFor(() => {
      expect(result.current.historyStatus).toBe("available");
    });

    mockListHistory.mockClear();
    mockGetTrend.mockClear();
    mockGetGoalProgress.mockClear();

    let ok = false;
    await act(async () => {
      ok = await result.current.createEntry("2026-07-13", "71.00");
    });
    expect(ok).toBe(true);
    expect(mockCreateEntry).toHaveBeenCalledWith("2026-07-13", "71.00");
    expect(mockListHistory).toHaveBeenCalled();
    expect(mockGetTrend).toHaveBeenCalled();
    expect(mockGetGoalProgress).toHaveBeenCalled();
  });

  it("create failure preserves error", async () => {
    const { result } = mountHook();
    act(() => { result.current.reloadAll(); });
    await waitFor(() => {
      expect(result.current.historyStatus).toBe("available");
    });

    mockCreateEntry.mockResolvedValue(errorResponse("HTTP_ERROR", "Create failed"));

    let ok = true;
    await act(async () => {
      ok = await result.current.createEntry("2026-07-13", "71.00");
    });
    expect(ok).toBe(false);
    expect(result.current.createError).toBe("Create failed");
  });

  it("successful delete calls API and refreshes", async () => {
    const { result } = mountHook();
    act(() => { result.current.reloadAll(); });
    await waitFor(() => {
      expect(result.current.historyStatus).toBe("available");
    });

    act(() => { result.current.requestDelete("e1"); });
    expect(result.current.deleteStatus).toBe("confirming");
    expect(result.current.deletingEntryId).toBe("e1");

    mockListHistory.mockClear();
    mockGetTrend.mockClear();
    mockGetGoalProgress.mockClear();

    await act(async () => {
      await result.current.confirmDelete();
    });
    expect(mockDeleteEntry).toHaveBeenCalledWith("e1");
    expect(mockListHistory).toHaveBeenCalled();
    expect(mockGetTrend).toHaveBeenCalled();
    expect(mockGetGoalProgress).toHaveBeenCalled();
  });

  it("delete failure preserves entry", async () => {
    const { result } = mountHook();
    act(() => { result.current.reloadAll(); });
    await waitFor(() => {
      expect(result.current.historyStatus).toBe("available");
    });

    mockDeleteEntry.mockResolvedValue(errorResponse("HTTP_ERROR", "Delete failed"));
    act(() => { result.current.requestDelete("e1"); });
    await act(async () => {
      await result.current.confirmDelete();
    });
    expect(result.current.deleteStatus).toBe("error");
    expect(result.current.deleteError).toBe("Delete failed");
  });

  it("cancel delete resets state", async () => {
    const { result } = mountHook();
    act(() => { result.current.reloadAll(); });
    await waitFor(() => {
      expect(result.current.historyStatus).toBe("available");
    });

    act(() => { result.current.requestDelete("e1"); });
    expect(result.current.deleteStatus).toBe("confirming");

    act(() => { result.current.cancelDelete(); });
    expect(result.current.deleteStatus).toBe("idle");
    expect(result.current.deletingEntryId).toBeNull();
  });

  it("duplicate create prevented by submitting state", async () => {
    const { result } = mountHook();
    act(() => { result.current.reloadAll(); });
    await waitFor(() => {
      expect(result.current.historyStatus).toBe("available");
    });

    mockCreateEntry.mockImplementation(() => new Promise(() => {}));
    act(() => { result.current.createEntry("2026-07-13", "71.00"); });

    expect(mockCreateEntry).toHaveBeenCalledTimes(1);
    expect(result.current.createStatus).toBe("submitting");
  });

  it("duplicate delete prevented by deleting state", async () => {
    const { result } = mountHook();
    act(() => { result.current.reloadAll(); });
    await waitFor(() => {
      expect(result.current.historyStatus).toBe("available");
    });

    mockDeleteEntry.mockImplementation(() => new Promise(() => {}));
    act(() => { result.current.requestDelete("e1"); });
    act(() => {
      result.current.confirmDelete();
    });

    act(() => {
      result.current.confirmDelete();
    });
    expect(mockDeleteEntry).toHaveBeenCalledTimes(1);
  });

  it("clearCreateSuccess resets create state", async () => {
    const { result } = mountHook();
    act(() => { result.current.reloadAll(); });
    await waitFor(() => {
      expect(result.current.historyStatus).toBe("available");
    });

    mockCreateEntry.mockResolvedValue(successResponse(MOCK_ENTRIES[0]));
    await act(async () => {
      await result.current.createEntry("2026-07-13", "71.00");
    });
    expect(result.current.createStatus).toBe("success");

    act(() => { result.current.clearCreateSuccess(); });
    expect(result.current.createStatus).toBe("idle");
  });
});
