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

function mockResponse(data: unknown, status = 200) {
  return Promise.resolve({
    ok: status >= 200 && status < 300,
    status,
    headers: new Headers({ "X-Request-ID": "req-123" }),
    text: () => Promise.resolve(JSON.stringify(data)),
    json: () => Promise.resolve(data),
  });
}

const MOCK_TASK = {
  task_id: "t1",
  title: "Test task",
  description: "A description",
  priority: "medium" as const,
  status: "pending" as const,
  due_date: "2026-07-15",
  completed_at: null,
};

const MOCK_LIST_RESPONSE = {
  success: true,
  message: "Tasks retrieved successfully.",
  data: {
    tasks: [MOCK_TASK],
  },
};

const MOCK_CREATE_RESPONSE = {
  success: true,
  message: "Task created successfully.",
  data: MOCK_TASK,
};

const MOCK_COMPLETE_RESPONSE = {
  success: true,
  message: "Task completed successfully.",
  data: { ...MOCK_TASK, status: "completed", completed_at: "2026-07-15T10:00:00Z" },
};

const MOCK_REOPEN_RESPONSE = {
  success: true,
  message: "Task reopened successfully.",
  data: { ...MOCK_TASK, status: "pending", completed_at: null },
};

const MOCK_DELETE_RESPONSE = {
  success: true,
  message: "Task deleted successfully.",
};

describe("Task Service", () => {
  describe("listTasks", () => {
    it("uses GET /tasks", async () => {
      mockFetch.mockResolvedValueOnce(mockResponse(MOCK_LIST_RESPONSE));
      const { listTasks } = await import("@/services/api/tasks");
      await listTasks();
      const callUrl = mockFetch.mock.calls[0][0] as string;
      expect(callUrl).toContain("/tasks");
      expect(mockFetch.mock.calls[0][1].method).toBe("GET");
    });

    it("returns tasks on success", async () => {
      mockFetch.mockResolvedValueOnce(mockResponse(MOCK_LIST_RESPONSE));
      const { listTasks } = await import("@/services/api/tasks");
      const result = await listTasks();
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.tasks).toHaveLength(1);
      }
    });
  });

  describe("getTask", () => {
    it("uses GET /tasks/{task_id}", async () => {
      mockFetch.mockResolvedValueOnce(mockResponse(MOCK_CREATE_RESPONSE));
      const { getTask } = await import("@/services/api/tasks");
      await getTask("t1");
      const callUrl = mockFetch.mock.calls[0][0] as string;
      expect(callUrl).toContain("/tasks/t1");
      expect(mockFetch.mock.calls[0][1].method).toBe("GET");
    });

    it("encodes UUID path safely", async () => {
      mockFetch.mockResolvedValueOnce(mockResponse(MOCK_CREATE_RESPONSE));
      const { getTask } = await import("@/services/api/tasks");
      await getTask("123e4567-e89b-12d3-a456-426614174000");
      const callUrl = mockFetch.mock.calls[0][0] as string;
      expect(callUrl).toContain("/tasks/123e4567-e89b-12d3-a456-426614174000");
    });
  });

  describe("createTask", () => {
    it("uses POST /tasks", async () => {
      mockFetch.mockResolvedValueOnce(mockResponse(MOCK_CREATE_RESPONSE, 201));
      const { createTask } = await import("@/services/api/tasks");
      await createTask({ title: "Test" });
      const callUrl = mockFetch.mock.calls[0][0] as string;
      expect(callUrl).toContain("/tasks");
      expect(mockFetch.mock.calls[0][1].method).toBe("POST");
    });

    it("sends exact body fields", async () => {
      mockFetch.mockResolvedValueOnce(mockResponse(MOCK_CREATE_RESPONSE, 201));
      const { createTask } = await import("@/services/api/tasks");
      await createTask({ title: "Task", priority: "high", description: "desc", due_date: "2026-07-15" });
      const body = JSON.parse(mockFetch.mock.calls[0][1].body);
      expect(body).toEqual({ title: "Task", priority: "high", description: "desc", due_date: "2026-07-15" });
    });

    it("omits optional fields when not provided", async () => {
      mockFetch.mockResolvedValueOnce(mockResponse(MOCK_CREATE_RESPONSE, 201));
      const { createTask } = await import("@/services/api/tasks");
      await createTask({ title: "Minimal" });
      const body = JSON.parse(mockFetch.mock.calls[0][1].body);
      expect(body).toEqual({ title: "Minimal" });
    });
  });

  describe("completeTask", () => {
    it("uses POST /tasks/{task_id}/complete", async () => {
      mockFetch.mockResolvedValueOnce(mockResponse(MOCK_COMPLETE_RESPONSE));
      const { completeTask } = await import("@/services/api/tasks");
      await completeTask("t1", "2026-07-15T10:00:00Z");
      const callUrl = mockFetch.mock.calls[0][0] as string;
      expect(callUrl).toContain("/tasks/t1/complete");
      expect(mockFetch.mock.calls[0][1].method).toBe("POST");
    });

    it("sends completed_at", async () => {
      mockFetch.mockResolvedValueOnce(mockResponse(MOCK_COMPLETE_RESPONSE));
      const { completeTask } = await import("@/services/api/tasks");
      await completeTask("t1", "2026-07-15T10:00:00Z");
      const body = JSON.parse(mockFetch.mock.calls[0][1].body);
      expect(body).toEqual({ completed_at: "2026-07-15T10:00:00Z" });
    });
  });

  describe("reopenTask", () => {
    it("uses POST /tasks/{task_id}/reopen", async () => {
      mockFetch.mockResolvedValueOnce(mockResponse(MOCK_REOPEN_RESPONSE));
      const { reopenTask } = await import("@/services/api/tasks");
      await reopenTask("t1");
      const callUrl = mockFetch.mock.calls[0][0] as string;
      expect(callUrl).toContain("/tasks/t1/reopen");
      expect(mockFetch.mock.calls[0][1].method).toBe("POST");
    });

    it("sends no body", async () => {
      mockFetch.mockResolvedValueOnce(mockResponse(MOCK_REOPEN_RESPONSE));
      const { reopenTask } = await import("@/services/api/tasks");
      await reopenTask("t1");
      expect(mockFetch.mock.calls[0][1].body).toBeUndefined();
    });
  });

  describe("deleteTask", () => {
    it("uses DELETE /tasks/{task_id}", async () => {
      mockFetch.mockResolvedValueOnce(mockResponse(MOCK_DELETE_RESPONSE));
      const { deleteTask } = await import("@/services/api/tasks");
      await deleteTask("t1");
      const callUrl = mockFetch.mock.calls[0][0] as string;
      expect(callUrl).toContain("/tasks/t1");
      expect(mockFetch.mock.calls[0][1].method).toBe("DELETE");
    });

    it("encodes UUID path safely", async () => {
      mockFetch.mockResolvedValueOnce(mockResponse(MOCK_DELETE_RESPONSE));
      const { deleteTask } = await import("@/services/api/tasks");
      await deleteTask("123e4567-e89b-12d3-a456-426614174000");
      const callUrl = mockFetch.mock.calls[0][0] as string;
      expect(callUrl).toContain("/tasks/123e4567-e89b-12d3-a456-426614174000");
    });
  });

  describe("Error handling", () => {
    it("preserves error codes", async () => {
      mockFetch.mockResolvedValueOnce(
        mockResponse(
          { success: false, error: { code: "TASK_NOT_FOUND", message: "Task was not found.", request_id: "req-123" } },
          404
        )
      );
      const { getTask } = await import("@/services/api/tasks");
      const result = await getTask("t1");
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.code).toBe("TASK_NOT_FOUND");
      }
    });

    it("handles network errors safely", async () => {
      mockFetch.mockRejectedValueOnce(new Error("Network failure"));
      const { listTasks } = await import("@/services/api/tasks");
      const result = await listTasks();
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.code).toBe("NETWORK_ERROR");
      }
    });

    it("handles timeout errors safely", async () => {
      const error = new Error("The operation was aborted");
      error.name = "AbortError";
      mockFetch.mockRejectedValueOnce(error);
      const { listTasks } = await import("@/services/api/tasks");
      const result = await listTasks();
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.code).toBe("TIMEOUT");
      }
    });

    it("handles invalid JSON safely", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        headers: new Headers(),
        text: () => Promise.resolve("not json"),
      });
      const { listTasks } = await import("@/services/api/tasks");
      const result = await listTasks();
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.code).toBe("INVALID_JSON");
      }
    });

    it("reuses existing API client", async () => {
      const client = await import("@/services/api/client");
      expect(typeof client.apiGet).toBe("function");
      expect(typeof client.apiPost).toBe("function");
      expect(typeof client.apiDelete).toBe("function");
    });

    it("inherits Bearer behavior from existing client", async () => {
      const { setAccessToken } = await import("@/lib/token-storage");
      setAccessToken("test-token", "backend");
      mockFetch.mockResolvedValueOnce(mockResponse(MOCK_LIST_RESPONSE));
      const { listTasks } = await import("@/services/api/tasks");
      await listTasks();
      const headers = mockFetch.mock.calls[0][1].headers as Record<string, string>;
      expect(headers["Authorization"]).toMatch(/^Bearer /);
      const { removeAccessToken } = await import("@/lib/token-storage");
      removeAccessToken("backend");
    });
  });
});
