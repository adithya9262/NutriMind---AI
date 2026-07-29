import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act, waitFor } from "@testing-library/react";
import { useTasks } from "@/hooks/use-tasks";

const mockListTasks = vi.fn();
const mockCreateTask = vi.fn();
const mockCompleteTask = vi.fn();
const mockReopenTask = vi.fn();
const mockDeleteTask = vi.fn();

vi.mock("@/services/api/tasks", () => ({
  listTasks: (...args: unknown[]) => mockListTasks(...args),
  createTask: (...args: unknown[]) => mockCreateTask(...args),
  completeTask: (...args: unknown[]) => mockCompleteTask(...args),
  reopenTask: (...args: unknown[]) => mockReopenTask(...args),
  deleteTask: (...args: unknown[]) => mockDeleteTask(...args),
}));

function successResponse(data: unknown) {
  return { success: true as const, message: "Success", data };
}

function errorResponse(code: string, message: string) {
  return { success: false as const, error: { code, message, request_id: "req-1" } };
}

const MOCK_TASKS = [
  {
    task_id: "t1",
    title: "Task 1",
    description: "Description 1",
    priority: "high" as const,
    status: "pending" as const,
    due_date: "2026-07-15",
    completed_at: null,
  },
  {
    task_id: "t2",
    title: "Task 2",
    description: null,
    priority: "low" as const,
    status: "completed" as const,
    due_date: null,
    completed_at: "2026-07-14T10:00:00Z",
  },
];

beforeEach(() => {
  vi.clearAllMocks();
  mockListTasks.mockResolvedValue(successResponse({ tasks: MOCK_TASKS }));
  mockCreateTask.mockResolvedValue(successResponse(MOCK_TASKS[0]));
  mockCompleteTask.mockResolvedValue(successResponse({ ...MOCK_TASKS[0], status: "completed", completed_at: "2026-07-15T10:00:00Z" }));
  mockReopenTask.mockResolvedValue(successResponse({ ...MOCK_TASKS[1], status: "pending", completed_at: null }));
  mockDeleteTask.mockResolvedValue(successResponse(undefined));
});

afterEach(() => {
});

function mountHook() {
  return renderHook(() => useTasks());
}

describe("useTasks", () => {
  it("starts in loading state", async () => {
    mockListTasks.mockResolvedValue(new Promise(() => {}));
    const { result } = mountHook();
    expect(result.current.listStatus).toBe("loading");
  });

  it("loads tasks successfully", async () => {
    const { result } = mountHook();
    act(() => { result.current.reloadTasks(); });
    await waitFor(() => {
      expect(result.current.listStatus).toBe("available");
    });
    expect(result.current.tasks).toHaveLength(2);
  });

  it("handles empty list", async () => {
    mockListTasks.mockResolvedValue(successResponse({ tasks: [] }));
    const { result } = mountHook();
    act(() => { result.current.reloadTasks(); });
    await waitFor(() => {
      expect(result.current.listStatus).toBe("empty");
    });
    expect(result.current.tasks).toHaveLength(0);
  });

  it("handles read failure", async () => {
    mockListTasks.mockResolvedValue(errorResponse("HTTP_ERROR", "Failed"));
    const { result } = mountHook();
    act(() => { result.current.reloadTasks(); });
    await waitFor(() => {
      expect(result.current.listStatus).toBe("error");
    });
    expect(result.current.listError).toBe("Failed");
  });

  it("retry works", async () => {
    mockListTasks.mockResolvedValueOnce(errorResponse("HTTP_ERROR", "Fail"));
    const { result } = mountHook();
    act(() => { result.current.reloadTasks(); });
    await waitFor(() => {
      expect(result.current.listStatus).toBe("error");
    });

    mockListTasks.mockResolvedValue(successResponse({ tasks: MOCK_TASKS }));
    act(() => { result.current.retryTasks(); });
    await waitFor(() => {
      expect(result.current.listStatus).toBe("available");
    });
  });

  it("successful create calls API and refreshes", async () => {
    const { result } = mountHook();
    act(() => { result.current.reloadTasks(); });
    await waitFor(() => {
      expect(result.current.listStatus).toBe("available");
    });

    mockListTasks.mockClear();

    let ok = false;
    await act(async () => {
      ok = await result.current.createTask({ title: "New task" });
    });
    expect(ok).toBe(true);
    expect(mockCreateTask).toHaveBeenCalledWith({ title: "New task" });
    expect(mockListTasks).toHaveBeenCalled();
  });

  it("create failure preserves form state", async () => {
    const { result } = mountHook();
    act(() => { result.current.reloadTasks(); });
    await waitFor(() => {
      expect(result.current.listStatus).toBe("available");
    });

    mockCreateTask.mockResolvedValue(errorResponse("HTTP_ERROR", "Create failed"));

    let ok = true;
    await act(async () => {
      ok = await result.current.createTask({ title: "New task" });
    });
    expect(ok).toBe(false);
    expect(result.current.createError).toBe("Create failed");
  });

  it("duplicate create prevented by submitting state", async () => {
    const { result } = mountHook();
    act(() => { result.current.reloadTasks(); });
    await waitFor(() => {
      expect(result.current.listStatus).toBe("available");
    });

    mockCreateTask.mockImplementation(() => new Promise(() => {}));
    act(() => { result.current.createTask({ title: "New task" }); });

    expect(mockCreateTask).toHaveBeenCalledTimes(1);
    expect(result.current.createStatus).toBe("submitting");
  });

  it("successful completion calls API and refreshes", async () => {
    const { result } = mountHook();
    act(() => { result.current.reloadTasks(); });
    await waitFor(() => {
      expect(result.current.listStatus).toBe("available");
    });

    mockListTasks.mockClear();

    let ok = false;
    await act(async () => {
      ok = await result.current.completeTask("t1");
    });
    expect(ok).toBe(true);
    expect(mockCompleteTask).toHaveBeenCalled();
    expect(mockListTasks).toHaveBeenCalled();
  });

  it("completion failure preserves task state", async () => {
    const { result } = mountHook();
    act(() => { result.current.reloadTasks(); });
    await waitFor(() => {
      expect(result.current.listStatus).toBe("available");
    });

    mockCompleteTask.mockResolvedValue(errorResponse("HTTP_ERROR", "Complete failed"));

    let ok = true;
    await act(async () => {
      ok = await result.current.completeTask("t1");
    });
    expect(ok).toBe(false);
    expect(result.current.actionError).toBe("Complete failed");
  });

  it("duplicate complete prevented", async () => {
    const { result } = mountHook();
    act(() => { result.current.reloadTasks(); });
    await waitFor(() => {
      expect(result.current.listStatus).toBe("available");
    });

    mockCompleteTask.mockImplementation(() => new Promise(() => {}));
    act(() => { result.current.completeTask("t1"); });
    act(() => { result.current.completeTask("t1"); });
    expect(mockCompleteTask).toHaveBeenCalledTimes(1);
  });

  it("successful reopen calls API and refreshes", async () => {
    const { result } = mountHook();
    act(() => { result.current.reloadTasks(); });
    await waitFor(() => {
      expect(result.current.listStatus).toBe("available");
    });

    mockListTasks.mockClear();

    let ok = false;
    await act(async () => {
      ok = await result.current.reopenTask("t2");
    });
    expect(ok).toBe(true);
    expect(mockReopenTask).toHaveBeenCalledWith("t2");
    expect(mockListTasks).toHaveBeenCalled();
  });

  it("reopen failure preserves task state", async () => {
    const { result } = mountHook();
    act(() => { result.current.reloadTasks(); });
    await waitFor(() => {
      expect(result.current.listStatus).toBe("available");
    });

    mockReopenTask.mockResolvedValue(errorResponse("HTTP_ERROR", "Reopen failed"));

    let ok = true;
    await act(async () => {
      ok = await result.current.reopenTask("t2");
    });
    expect(ok).toBe(false);
    expect(result.current.actionError).toBe("Reopen failed");
  });

  it("duplicate reopen prevented", async () => {
    const { result } = mountHook();
    act(() => { result.current.reloadTasks(); });
    await waitFor(() => {
      expect(result.current.listStatus).toBe("available");
    });

    mockReopenTask.mockImplementation(() => new Promise(() => {}));
    act(() => { result.current.reopenTask("t2"); });
    act(() => { result.current.reopenTask("t2"); });
    expect(mockReopenTask).toHaveBeenCalledTimes(1);
  });

  it("delete requested sets confirm state", async () => {
    const { result } = mountHook();
    act(() => { result.current.reloadTasks(); });
    await waitFor(() => {
      expect(result.current.listStatus).toBe("available");
    });

    act(() => { result.current.requestDelete("t1"); });
    expect(result.current.deleteConfirmTaskId).toBe("t1");
  });

  it("delete cancel resets state", async () => {
    const { result } = mountHook();
    act(() => { result.current.reloadTasks(); });
    await waitFor(() => {
      expect(result.current.listStatus).toBe("available");
    });

    act(() => { result.current.requestDelete("t1"); });
    expect(result.current.deleteConfirmTaskId).toBe("t1");

    act(() => { result.current.cancelDelete(); });
    expect(result.current.deleteConfirmTaskId).toBeNull();
  });

  it("successful delete calls API and refreshes", async () => {
    const { result } = mountHook();
    act(() => { result.current.reloadTasks(); });
    await waitFor(() => {
      expect(result.current.listStatus).toBe("available");
    });

    act(() => { result.current.requestDelete("t1"); });
    expect(result.current.deleteConfirmTaskId).toBe("t1");

    mockListTasks.mockClear();
    await act(async () => {
      await result.current.confirmDelete();
    });
    expect(mockDeleteTask).toHaveBeenCalledWith("t1");
    expect(mockListTasks).toHaveBeenCalled();
  });

  it("delete failure preserves task", async () => {
    const { result } = mountHook();
    act(() => { result.current.reloadTasks(); });
    await waitFor(() => {
      expect(result.current.listStatus).toBe("available");
    });

    mockDeleteTask.mockResolvedValue(errorResponse("HTTP_ERROR", "Delete failed"));
    act(() => { result.current.requestDelete("t1"); });
    await act(async () => {
      await result.current.confirmDelete();
    });
    expect(result.current.actionError).toBe("Delete failed");
  });

  it("duplicate delete prevented", async () => {
    const { result } = mountHook();
    act(() => { result.current.reloadTasks(); });
    await waitFor(() => {
      expect(result.current.listStatus).toBe("available");
    });

    mockDeleteTask.mockImplementation(() => new Promise(() => {}));
    act(() => { result.current.requestDelete("t1"); });
    act(() => { result.current.confirmDelete(); });
    act(() => { result.current.confirmDelete(); });
    expect(mockDeleteTask).toHaveBeenCalledTimes(1);
  });

  it("clearCreateSuccess resets create state", async () => {
    const { result } = mountHook();
    act(() => { result.current.reloadTasks(); });
    await waitFor(() => {
      expect(result.current.listStatus).toBe("available");
    });

    mockCreateTask.mockResolvedValue(successResponse(MOCK_TASKS[0]));
    await act(async () => {
      await result.current.createTask({ title: "New" });
    });
    expect(result.current.createStatus).toBe("success");

    act(() => { result.current.clearCreateSuccess(); });
    expect(result.current.createStatus).toBe("idle");
  });
});
