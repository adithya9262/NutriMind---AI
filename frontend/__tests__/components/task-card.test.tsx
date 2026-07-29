import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { TaskCard } from "@/components/task-card";
import type { TaskData } from "@/types/tasks";

const mockOnComplete = vi.fn();
const mockOnReopen = vi.fn();
const mockOnDelete = vi.fn();

function pendingTask(overrides: Partial<TaskData> = {}): TaskData {
  return {
    task_id: "t1",
    title: "Test task",
    description: "A description",
    priority: "medium",
    status: "pending",
    due_date: "2026-07-15",
    completed_at: null,
    ...overrides,
  };
}

function completedTask(overrides: Partial<TaskData> = {}): TaskData {
  return {
    task_id: "t2",
    title: "Done task",
    description: null,
    priority: "low",
    status: "completed",
    due_date: null,
    completed_at: "2026-07-14T10:00:00Z",
    ...overrides,
  };
}

function renderCard(task: TaskData, overrides: Record<string, unknown> = {}) {
  return render(
    <TaskCard
      task={task}
      onComplete={mockOnComplete}
      onReopen={mockOnReopen}
      onDelete={mockOnDelete}
      completing={false}
      reopening={false}
      deleting={false}
      isActionTarget={false}
      {...overrides}
    />
  );
}

describe("TaskCard", () => {
  it("renders task title", () => {
    renderCard(pendingTask());
    expect(screen.getByText("Test task")).toBeInTheDocument();
  });

  it("renders description when present", () => {
    renderCard(pendingTask());
    expect(screen.getByText("A description")).toBeInTheDocument();
  });

  it("does not render description when null", () => {
    renderCard(pendingTask({ description: null }));
    expect(screen.queryByText("A description")).not.toBeInTheDocument();
  });

  it("renders priority badge", () => {
    renderCard(pendingTask({ priority: "high" }));
    expect(screen.getByText("High")).toBeInTheDocument();
  });

  it("renders status badge", () => {
    renderCard(pendingTask());
    expect(screen.getByText("Pending")).toBeInTheDocument();
  });

  it("renders due date when present", () => {
    renderCard(pendingTask());
    expect(screen.getByText(/2026/)).toBeInTheDocument();
  });

  it("does not render due date when null", () => {
    renderCard(pendingTask({ due_date: null }));
    expect(screen.queryByText("2026")).not.toBeInTheDocument();
  });

  it("renders completed_at for completed tasks", () => {
    renderCard(completedTask());
    expect(screen.getByText(/Completed:/)).toBeInTheDocument();
  });

  it("shows complete action for pending tasks", () => {
    renderCard(pendingTask());
    expect(screen.getByRole("button", { name: /complete/i })).toBeInTheDocument();
  });

  it("does not show reopen for pending tasks", () => {
    renderCard(pendingTask());
    expect(screen.queryByRole("button", { name: /reopen/i })).not.toBeInTheDocument();
  });

  it("shows reopen for completed tasks", () => {
    renderCard(completedTask());
    expect(screen.getByRole("button", { name: /reopen/i })).toBeInTheDocument();
  });

  it("does not show complete for completed tasks", () => {
    renderCard(completedTask());
    expect(screen.queryByRole("button", { name: /complete/i })).not.toBeInTheDocument();
  });

  it("shows delete for all tasks", () => {
    renderCard(pendingTask());
    expect(screen.getByRole("button", { name: /delete/i })).toBeInTheDocument();
  });

  it("calls onComplete when complete clicked", async () => {
    const user = userEvent.setup();
    renderCard(pendingTask());
    await user.click(screen.getByRole("button", { name: /complete/i }));
    expect(mockOnComplete).toHaveBeenCalledWith("t1");
  });

  it("calls onReopen when reopen clicked", async () => {
    const user = userEvent.setup();
    renderCard(completedTask());
    await user.click(screen.getByRole("button", { name: /reopen/i }));
    expect(mockOnReopen).toHaveBeenCalledWith("t2");
  });

  it("calls onDelete when delete clicked", async () => {
    const user = userEvent.setup();
    renderCard(pendingTask());
    await user.click(screen.getByRole("button", { name: /delete/i }));
    expect(mockOnDelete).toHaveBeenCalledWith("t1");
  });

  it("disables buttons during action", () => {
    renderCard(pendingTask(), { isActionTarget: true, completing: true });
    expect(screen.getByRole("button", { name: /complete/i })).toBeDisabled();
  });

  it("long title wraps safely", () => {
    const long = "x".repeat(200);
    renderCard(pendingTask({ title: long }));
    const heading = screen.getByText(long);
    expect(heading).toBeInTheDocument();
  });

  it("multiline description remains readable", () => {
    const multiline = "line 1\nline 2\nline 3";
    renderCard(pendingTask({ description: multiline }));
    expect(screen.getByText(/line 1/)).toBeInTheDocument();
    expect(screen.getByText(/line 2/)).toBeInTheDocument();
    expect(screen.getByText(/line 3/)).toBeInTheDocument();
  });
});
