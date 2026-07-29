import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import TasksPage from "@/app/(protected)/tasks/page";

const mockReloadTasks = vi.fn();
const mockRetryTasks = vi.fn();
const mockCreateTask = vi.fn();
const mockCompleteTask = vi.fn();
const mockReopenTask = vi.fn();
const mockRequestDelete = vi.fn();
const mockConfirmDelete = vi.fn();
const mockCancelDelete = vi.fn();
const mockClearCreateSuccess = vi.fn();

vi.mock("@/hooks/use-tasks", () => ({
  useTasks: vi.fn(() => ({
    listStatus: "empty",
    tasks: [],
    listError: null,
    createStatus: "idle",
    createError: null,
    actionStatus: "idle",
    actionError: null,
    actionTaskId: null,
    deleteConfirmTaskId: null,
    reloadTasks: mockReloadTasks,
    retryTasks: mockRetryTasks,
    createTask: mockCreateTask,
    completeTask: mockCompleteTask,
    reopenTask: mockReopenTask,
    requestDelete: mockRequestDelete,
    confirmDelete: mockConfirmDelete,
    cancelDelete: mockCancelDelete,
    clearCreateSuccess: mockClearCreateSuccess,
  })),
}));

vi.mock("@/contexts/auth-context", () => ({
  useAuth: () => ({ state: "authenticated", user: { id: "u1", email: "test@test.com" } }),
  AuthProvider: ({ children }: { children: React.ReactNode }) => children,
}));

beforeEach(() => {
  vi.clearAllMocks();
});

function renderPage() {
  return render(<TasksPage />);
}

describe("TasksPage", () => {
  it("renders exactly one h1", () => {
    renderPage();
    const headings = screen.getAllByRole("heading", { level: 1 });
    expect(headings).toHaveLength(1);
    expect(headings[0]).toHaveTextContent("Tasks");
  });

  it("shows Add Task action", () => {
    renderPage();
    expect(screen.getByRole("button", { name: /add task/i })).toBeInTheDocument();
  });

  it("opens form on Add Task click", async () => {
    const user = userEvent.setup();
    renderPage();
    await user.click(screen.getByRole("button", { name: /add task/i }));
    expect(screen.getByText("Create Task")).toBeInTheDocument();
  });

  it("renders empty state when no tasks", () => {
    renderPage();
    expect(screen.getByText("No tasks yet")).toBeInTheDocument();
  });

  it("renders available tasks", async () => {
    const { useTasks } = await import("@/hooks/use-tasks");
    (useTasks as ReturnType<typeof vi.fn>).mockReturnValue({
      listStatus: "available",
      tasks: [
        {
          task_id: "t1",
          title: "Task 1",
          description: null,
          priority: "high" as const,
          status: "pending" as const,
          due_date: null,
          completed_at: null,
        },
      ],
      listError: null,
      createStatus: "idle",
      createError: null,
      actionStatus: "idle",
      actionError: null,
      actionTaskId: null,
      deleteConfirmTaskId: null,
      reloadTasks: mockReloadTasks,
      retryTasks: mockRetryTasks,
      createTask: mockCreateTask,
      completeTask: mockCompleteTask,
      reopenTask: mockReopenTask,
      requestDelete: mockRequestDelete,
      confirmDelete: mockConfirmDelete,
      cancelDelete: mockCancelDelete,
      clearCreateSuccess: mockClearCreateSuccess,
    });
    renderPage();
    expect(screen.getByText("Task 1")).toBeInTheDocument();
  });

  it("shows success feedback on create success", async () => {
    const { useTasks } = await import("@/hooks/use-tasks");
    (useTasks as ReturnType<typeof vi.fn>).mockReturnValue({
      listStatus: "empty",
      tasks: [],
      listError: null,
      createStatus: "success",
      createError: null,
      actionStatus: "idle",
      actionError: null,
      actionTaskId: null,
      deleteConfirmTaskId: null,
      reloadTasks: mockReloadTasks,
      retryTasks: mockRetryTasks,
      createTask: mockCreateTask,
      completeTask: mockCompleteTask,
      reopenTask: mockReopenTask,
      requestDelete: mockRequestDelete,
      confirmDelete: mockConfirmDelete,
      cancelDelete: mockCancelDelete,
      clearCreateSuccess: mockClearCreateSuccess,
    });
    renderPage();
    expect(screen.getByText("Task created successfully.")).toBeInTheDocument();
  });

  it("shows error feedback on action error", async () => {
    const { useTasks } = await import("@/hooks/use-tasks");
    (useTasks as ReturnType<typeof vi.fn>).mockReturnValue({
      listStatus: "available",
      tasks: [
        {
          task_id: "t1",
          title: "Task 1",
          description: null,
          priority: "medium" as const,
          status: "pending" as const,
          due_date: null,
          completed_at: null,
        },
      ],
      listError: null,
      createStatus: "idle",
      createError: null,
      actionStatus: "error",
      actionError: "Task is already completed.",
      actionTaskId: "t1",
      deleteConfirmTaskId: null,
      reloadTasks: mockReloadTasks,
      retryTasks: mockRetryTasks,
      createTask: mockCreateTask,
      completeTask: mockCompleteTask,
      reopenTask: mockReopenTask,
      requestDelete: mockRequestDelete,
      confirmDelete: mockConfirmDelete,
      cancelDelete: mockCancelDelete,
      clearCreateSuccess: mockClearCreateSuccess,
    });
    renderPage();
    expect(screen.getByText("Task is already completed.")).toBeInTheDocument();
  });

  it("shows retry on error state", async () => {
    const { useTasks } = await import("@/hooks/use-tasks");
    (useTasks as ReturnType<typeof vi.fn>).mockReturnValue({
      listStatus: "error",
      tasks: [],
      listError: "Failed to load",
      createStatus: "idle",
      createError: null,
      actionStatus: "idle",
      actionError: null,
      actionTaskId: null,
      deleteConfirmTaskId: null,
      reloadTasks: mockReloadTasks,
      retryTasks: mockRetryTasks,
      createTask: mockCreateTask,
      completeTask: mockCompleteTask,
      reopenTask: mockReopenTask,
      requestDelete: mockRequestDelete,
      confirmDelete: mockConfirmDelete,
      cancelDelete: mockCancelDelete,
      clearCreateSuccess: mockClearCreateSuccess,
    });
    renderPage();
    expect(screen.getByText("Failed to load tasks")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /retry/i })).toBeInTheDocument();
  });

  it("form cancels correctly", async () => {
    const user = userEvent.setup();
    renderPage();
    await user.click(screen.getByRole("button", { name: /add task/i }));
    expect(screen.getByText("Create Task")).toBeInTheDocument();
    const cancelButton = screen.getByRole("button", { name: /cancel/i });
    await user.click(cancelButton);
    await waitFor(() => {
      expect(screen.queryByText("Create Task")).not.toBeInTheDocument();
    });
  });
});
