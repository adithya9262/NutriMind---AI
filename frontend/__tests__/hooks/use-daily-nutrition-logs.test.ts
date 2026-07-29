import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act, waitFor } from "@testing-library/react";
import { useDailyNutritionLogs } from "@/hooks/use-daily-nutrition-logs";

const mockListEntries = vi.fn();
const mockCreateEntry = vi.fn();
const mockDeleteEntry = vi.fn();
const mockGetSummary = vi.fn();
const mockGetProgress = vi.fn();

vi.mock("@/services/api/nutrition-logs", () => ({
  listNutritionLogEntries: (...args: unknown[]) => mockListEntries(...args),
  createNutritionLogEntry: (...args: unknown[]) => mockCreateEntry(...args),
  deleteNutritionLogEntry: (...args: unknown[]) => mockDeleteEntry(...args),
  getDailyNutritionLogSummary: (...args: unknown[]) => mockGetSummary(...args),
  getDailyNutritionTargetProgress: (...args: unknown[]) => mockGetProgress(...args),
}));

function successResponse(data: unknown) {
  return { success: true as const, message: "Success", data };
}

function errorResponse(code: string, message: string) {
  return { success: false as const, error: { code, message, request_id: "req-1" } };
}

const MOCK_ENTRIES = [
  { entry_id: "e1", food_name: "Oatmeal", meal_type: "breakfast" as const, serving_description: "1 cup", calories_kcal: "350.00", protein_g: "12.00", carbohydrate_g: "55.00", fat_g: "5.00" },
];

const MOCK_SUMMARY = {
  entry_count: 1,
  totals: { calories_kcal: "350.00", protein_g: "12.00", carbohydrate_g: "55.00", fat_g: "5.00" },
  meals: [
    { meal_type: "breakfast" as const, entry_count: 1, totals: { calories_kcal: "350.00", protein_g: "12.00", carbohydrate_g: "55.00", fat_g: "5.00" } },
    { meal_type: "lunch" as const, entry_count: 0, totals: { calories_kcal: "0.00", protein_g: "0.00", carbohydrate_g: "0.00", fat_g: "0.00" } },
    { meal_type: "dinner" as const, entry_count: 0, totals: { calories_kcal: "0.00", protein_g: "0.00", carbohydrate_g: "0.00", fat_g: "0.00" } },
    { meal_type: "snack" as const, entry_count: 0, totals: { calories_kcal: "0.00", protein_g: "0.00", carbohydrate_g: "0.00", fat_g: "0.00" } },
  ],
};

const MOCK_PROGRESS = {
  calories: { consumed: "350.00", target: "2500.00", remaining: "2150.00", percentage: "14.00", status: "below_target" as const },
  protein: { consumed: "12.00", target: "100.00", remaining: "88.00", percentage: "12.00", status: "below_target" as const },
  carbohydrate: { consumed: "55.00", target: "300.00", remaining: "245.00", percentage: "18.33", status: "below_target" as const },
  fat: { consumed: "5.00", target: "80.00", remaining: "75.00", percentage: "6.25", status: "below_target" as const },
};

const CREATE_PAYLOAD = {
  entry_id: "new-e1",
  food_name: "Banana",
  meal_type: "snack" as const,
  serving_description: "1 medium",
  calories_kcal: "105.00",
  protein_g: "1.30",
  carbohydrate_g: "27.00",
  fat_g: "0.40",
};

beforeEach(() => {
  vi.clearAllMocks();
  mockListEntries.mockResolvedValue(successResponse({ logged_date: "2025-06-15", entries: MOCK_ENTRIES }));
  mockGetSummary.mockResolvedValue(successResponse(MOCK_SUMMARY));
  mockGetProgress.mockResolvedValue(successResponse(MOCK_PROGRESS));
  mockCreateEntry.mockResolvedValue(successResponse(MOCK_ENTRIES[0]));
  mockDeleteEntry.mockResolvedValue(successResponse(undefined));
});

function getHook() {
  return renderHook(() => useDailyNutritionLogs("2025-06-15"));
}

describe("useDailyNutritionLogs", () => {
  function mountHook() {
    const hook = getHook();
    act(() => { hook.result.current.reloadAll(); });
    return hook;
  }

  it("starts in loading state", async () => {
    mockListEntries.mockResolvedValue(new Promise(() => {}));
    mockGetSummary.mockResolvedValue(new Promise(() => {}));
    mockGetProgress.mockResolvedValue(new Promise(() => {}));
    const { result } = getHook();
    expect(result.current.entriesStatus).toBe("loading");
    expect(result.current.summaryStatus).toBe("loading");
    expect(result.current.progressStatus).toBe("loading");
  });

  it("loads entries successfully", async () => {
    const { result } = mountHook();
    await waitFor(() => {
      expect(result.current.entriesStatus).toBe("available");
    });
    expect(result.current.entries).toHaveLength(1);
    expect(result.current.entries[0].food_name).toBe("Oatmeal");
  });

  it("handles empty entries state", async () => {
    mockListEntries.mockResolvedValue(successResponse({ logged_date: "2025-06-15", entries: [] }));
    const { result } = mountHook();
    await waitFor(() => {
      expect(result.current.entriesStatus).toBe("empty");
    });
    expect(result.current.entries).toHaveLength(0);
  });

  it("handles entries read error", async () => {
    mockListEntries.mockResolvedValue(errorResponse("HTTP_ERROR", "Failed to load entries"));
    const { result } = mountHook();
    await waitFor(() => {
      expect(result.current.entriesStatus).toBe("error");
    });
    expect(result.current.entriesError).toBe("Failed to load entries");
  });

  it("loads summary successfully", async () => {
    const { result } = mountHook();
    await waitFor(() => {
      expect(result.current.summaryStatus).toBe("available");
    });
    expect(result.current.summary?.entry_count).toBe(1);
  });

  it("handles summary error", async () => {
    mockGetSummary.mockResolvedValue(errorResponse("HTTP_ERROR", "Summary error"));
    const { result } = mountHook();
    await waitFor(() => {
      expect(result.current.summaryStatus).toBe("error");
    });
    expect(result.current.summaryError).toBe("Summary error");
  });

  it("loads progress successfully", async () => {
    const { result } = mountHook();
    await waitFor(() => {
      expect(result.current.progressStatus).toBe("available");
    });
    expect(result.current.progress?.calories.status).toBe("below_target");
  });

  it("handles progress error", async () => {
    mockGetProgress.mockResolvedValue(errorResponse("HTTP_ERROR", "Progress error"));
    const { result } = mountHook();
    await waitFor(() => {
      expect(result.current.progressStatus).toBe("error");
    });
    expect(result.current.progressError).toBe("Progress error");
  });

  it("handles missing profile for progress", async () => {
    mockGetProgress.mockResolvedValue(errorResponse("NUTRITION_PROFILE_NOT_FOUND", "Nutrition profile not found."));
    const { result } = mountHook();
    await waitFor(() => {
      expect(result.current.progressStatus).toBe("missing_profile");
    });
  });

  it("date change reloads all three reads", async () => {
    const { result } = mountHook();
    await waitFor(() => {
      expect(result.current.entriesStatus).toBe("available");
    });

    mockListEntries.mockClear();
    mockGetSummary.mockClear();
    mockGetProgress.mockClear();

    act(() => {
      result.current.setSelectedDate("2025-06-16");
    });

    expect(mockListEntries).toHaveBeenCalledWith("2025-06-16", expect.any(AbortSignal));
    expect(mockGetSummary).toHaveBeenCalledWith("2025-06-16", expect.any(AbortSignal));
  });

  it("retry entries works", async () => {
    mockListEntries.mockResolvedValueOnce(errorResponse("HTTP_ERROR", "Fail"));
    const { result } = mountHook();
    await waitFor(() => {
      expect(result.current.entriesStatus).toBe("error");
    });

    mockListEntries.mockResolvedValue(successResponse({ logged_date: "2025-06-15", entries: MOCK_ENTRIES }));
    act(() => {
      result.current.retryEntries();
    });
    await waitFor(() => {
      expect(result.current.entriesStatus).toBe("available");
    });
  });

  it("successful create calls API and refreshes", async () => {
    const { result } = mountHook();
    await waitFor(() => {
      expect(result.current.entriesStatus).toBe("available");
    });

    mockListEntries.mockClear();
    mockGetSummary.mockClear();
    mockGetProgress.mockClear();

    let success = false;
    await act(async () => {
      success = await result.current.createEntry(CREATE_PAYLOAD);
    });

    expect(success).toBe(true);
    expect(mockCreateEntry).toHaveBeenCalledWith("2025-06-15", CREATE_PAYLOAD);
    expect(mockListEntries).toHaveBeenCalled();
    expect(mockGetSummary).toHaveBeenCalled();
    expect(mockGetProgress).toHaveBeenCalled();
  });

  it("create failure preserves form values (does not clear form state)", async () => {
    const { result } = mountHook();
    await waitFor(() => {
      expect(result.current.entriesStatus).toBe("available");
    });

    mockCreateEntry.mockResolvedValue(errorResponse("HTTP_ERROR", "Creation failed"));

    let success = true;
    await act(async () => {
      success = await result.current.createEntry(CREATE_PAYLOAD);
    });

    expect(success).toBe(false);
    expect(result.current.createError).toBe("Creation failed");
  });

  it("selected date remains after create", async () => {
    const { result } = mountHook();
    await waitFor(() => {
      expect(result.current.entriesStatus).toBe("available");
    });

    await act(async () => {
      await result.current.createEntry(CREATE_PAYLOAD);
    });

    expect(result.current.selectedDate).toBe("2025-06-15");
  });

  it("successful delete calls API and refreshes", async () => {
    const { result } = mountHook();
    await waitFor(() => {
      expect(result.current.entriesStatus).toBe("available");
    });

    act(() => {
      result.current.requestDelete("e1");
    });
    expect(result.current.deleteStatus).toBe("confirming");
    expect(result.current.deletingEntryId).toBe("e1");

    mockListEntries.mockClear();
    mockGetSummary.mockClear();
    mockGetProgress.mockClear();

    await act(async () => {
      await result.current.confirmDelete();
    });

    expect(mockDeleteEntry).toHaveBeenCalledWith("e1");
    expect(mockListEntries).toHaveBeenCalled();
    expect(mockGetSummary).toHaveBeenCalled();
    expect(mockGetProgress).toHaveBeenCalled();
  });

  it("delete failure preserves entry", async () => {
    const { result } = mountHook();
    await waitFor(() => {
      expect(result.current.entriesStatus).toBe("available");
    });

    mockDeleteEntry.mockResolvedValue(errorResponse("HTTP_ERROR", "Delete failed"));

    act(() => {
      result.current.requestDelete("e1");
    });

    await act(async () => {
      await result.current.confirmDelete();
    });

    expect(result.current.deleteStatus).toBe("error");
    expect(result.current.deleteError).toBe("Delete failed");
  });

  it("selected date remains after delete", async () => {
    const { result } = mountHook();
    await waitFor(() => {
      expect(result.current.entriesStatus).toBe("available");
    });

    act(() => {
      result.current.requestDelete("e1");
    });
    await act(async () => {
      await result.current.confirmDelete();
    });

    expect(result.current.selectedDate).toBe("2025-06-15");
  });

  it("cancel delete resets delete state", async () => {
    const { result } = mountHook();
    await waitFor(() => {
      expect(result.current.entriesStatus).toBe("available");
    });

    act(() => {
      result.current.requestDelete("e1");
    });
    expect(result.current.deleteStatus).toBe("confirming");

    act(() => {
      result.current.cancelDelete();
    });
    expect(result.current.deleteStatus).toBe("idle");
    expect(result.current.deletingEntryId).toBeNull();
  });
});
