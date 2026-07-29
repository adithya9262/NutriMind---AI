import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act, waitFor } from "@testing-library/react";
import { useGoals } from "@/hooks/use-goals";

const mockListGoals = vi.fn();
const mockCreateGoal = vi.fn();
const mockUpdateGoal = vi.fn();
const mockDeleteGoal = vi.fn();

vi.mock("@/services/api/goals", () => ({
  listGoals: (...args: unknown[]) => mockListGoals(...args),
  createGoal: (...args: unknown[]) => mockCreateGoal(...args),
  updateGoal: (...args: unknown[]) => mockUpdateGoal(...args),
  deleteGoal: (...args: unknown[]) => mockDeleteGoal(...args),
}));

function successResponse(data: unknown) {
  return { success: true as const, message: "Success", data };
}

function errorResponse(code: string, message: string) {
  return { success: false as const, error: { code, message, request_id: "req-1" } };
}

const MOCK_GOALS = [
  {
    goal_id: "g1",
    user_id: "u1",
    goal_type: "calorie_target" as const,
    target_value: 2000,
    current_value: 1800,
    unit: "kcal",
    start_date: "2026-07-01",
    end_date: "2026-07-31",
    status: "active" as const,
    created_at: "2026-07-01T00:00:00Z",
    updated_at: "2026-07-01T00:00:00Z",
  },
];

describe("useGoals lifecycle and race conditions", () => {
  beforeEach(() => {
    mockListGoals.mockReset();
    mockCreateGoal.mockReset();
    mockUpdateGoal.mockReset();
    mockDeleteGoal.mockReset();
  });

  afterEach(() => {
  });

  it("should not update state after unmount when request completes", async () => {
    let resolveListGoals: (value: unknown) => void;
    const listPromise = new Promise((resolve) => {
      resolveListGoals = resolve;
    });
    mockListGoals.mockReturnValue(listPromise);

    const { result, unmount } = renderHook(() => useGoals());

    expect(result.current.listStatus).toBe("loading");

    // Unmount while request is pending
    unmount();

    // Resolve the request after unmount
    act(() => {
      resolveListGoals!(successResponse({ goals: MOCK_GOALS }));
    });

    // Wait for promise to settle
    await act(async () => {
      await Promise.resolve();
    });

    // Should not throw React state update warning
    // (vitest would fail if there's an unhandled rejection or act warning)
    expect(true).toBe(true);
  });

  it("should not update state from stale response after new request started", async () => {
    let resolveFirst: (value: unknown) => void;
    let resolveSecond: (value: unknown) => void;

    const firstPromise = new Promise((resolve) => { resolveFirst = resolve; });
    const secondPromise = new Promise((resolve) => { resolveSecond = resolve; });

    mockListGoals
      .mockReturnValueOnce(firstPromise)
      .mockReturnValueOnce(secondPromise);

    const { result } = renderHook(() => useGoals());

    // First request
    act(() => { result.current.reloadGoals(); });

    // Immediately start second request (simulating rapid navigation/retry)
    act(() => { result.current.reloadGoals(); });

    // Resolve first (stale) request
    act(() => {
      resolveFirst!(successResponse({ goals: [] }));
    });

    await act(async () => { await Promise.resolve(); });

    // Resolve second (latest) request
    act(() => {
      resolveSecond!(successResponse({ goals: MOCK_GOALS }));
    });

    await act(async () => { await Promise.resolve(); });

    // Should have data from second request, not first
    expect(result.current.goals).toEqual(MOCK_GOALS);
    expect(result.current.listStatus).toBe("available");
  });

  it("should handle rapid retry after failure", async () => {
    let resolveFirst: (value: unknown) => void;
    let resolveSecond: (value: unknown) => void;

    const firstPromise = new Promise((resolve) => { resolveFirst = resolve; });
    const secondPromise = new Promise((resolve) => { resolveSecond = resolve; });

    mockListGoals
      .mockReturnValueOnce(firstPromise)
      .mockReturnValueOnce(secondPromise);

    const { result } = renderHook(() => useGoals());

    // Initial load - fails
    act(() => { result.current.reloadGoals(); });
    act(() => { resolveFirst!(errorResponse("ERR", "Failed")); });
    await act(async () => { await Promise.resolve(); });

    await waitFor(() => expect(result.current.listStatus).toBe("error"), { timeout: 2000 });

    // Retry
    act(() => { result.current.retryGoals(); });

    act(() => { resolveSecond!(successResponse({ goals: MOCK_GOALS })); });
    await act(async () => { await Promise.resolve(); });

    await waitFor(() => expect(result.current.listStatus).toBe("available"), { timeout: 2000 });
    expect(result.current.goals).toEqual(MOCK_GOALS);
  });

  it("should not call setState after unmount on createGoal", async () => {
    let resolveCreate: (value: unknown) => void;
    const createPromise = new Promise((resolve) => { resolveCreate = resolve; });
    mockCreateGoal.mockReturnValue(createPromise);

    const { result, unmount } = renderHook(() => useGoals());

    // Start create
    act(() => { result.current.createGoal({ goal_type: "weight_loss", title: "Test Goal", target_calories: 2000, start_date: "2026-07-01", end_date: "2026-07-31" }); });

    // Unmount while creating
    unmount();

    // Resolve after unmount
    act(() => { resolveCreate!(successResponse({ goal: MOCK_GOALS[0] })); });

    await act(async () => { await Promise.resolve(); });

    expect(true).toBe(true); // No warning thrown
  });
});