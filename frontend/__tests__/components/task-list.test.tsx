import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { TaskList } from "@/components/task-list";
import type { TaskData } from "@/types/tasks";

const mockOnComplete = vi.fn();
const mockOnReopen = vi.fn();
const mockOnDelete = vi.fn();
const mockOnRetry = vi.fn();

const TASKS: TaskData[] = [
  {
    task_id: "t1",
    title: "Task 1",
    description: null,
    priority: "high",
    status: "pending",
    due_date: null,
    completed_at: null,
  },
  {
    task_id: "t2",
    title: "Task 2",
    description: "Desc",
    priority: "low",
    status: "completed",
    due_date: "2026-07-15",
    completed_at: "2026-07-14T10:00:00Z",
  },
];

function renderList(overrides: Record<string, unknown> = {}) {
  return render(
    <TaskList
      tasks={TASKS}
      listStatus="available"
      listError={null}
      actionStatus="idle"
      actionTaskId={null}
      onComplete={mockOnComplete}
      onReopen={mockOnReopen}
      onDelete={mockOnDelete}
      onRetry={mockOnRetry}
      {...overrides}
    />
  );
}

describe("TaskList", () => {
  it("renders loading state", () => {
    renderList({ listStatus: "loading" });
    expect(screen.getByRole("status", { name: /loading tasks/i })).toBeInTheDocument();
  });

  it("renders empty state", () => {
    renderList({ listStatus: "empty", tasks: [] });
    expect(screen.getByText("No tasks yet")).toBeInTheDocument();
  });

  it("renders error state with retry", async () => {
    const user = userEvent.setup();
    renderList({ listStatus: "error", listError: "Failed" });
    expect(screen.getByText("Failed to load tasks")).toBeInTheDocument();
    const retry = screen.getByRole("button", { name: /retry/i });
    await user.click(retry);
    expect(mockOnRetry).toHaveBeenCalled();
  });

  it("renders available tasks", () => {
    renderList();
    expect(screen.getByText("Task 1")).toBeInTheDocument();
    expect(screen.getByText("Task 2")).toBeInTheDocument();
  });

  it("preserves backend ordering", () => {
    renderList();
    const items = screen.getAllByRole("listitem");
    expect(items).toHaveLength(2);
  });
});
