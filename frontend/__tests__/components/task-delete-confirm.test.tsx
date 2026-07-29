import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { TaskDeleteConfirm } from "@/components/task-delete-confirm";
import type { TaskData } from "@/types/tasks";

const mockOnConfirm = vi.fn();
const mockOnCancel = vi.fn();

function renderConfirm(task: TaskData, deleting = false) {
  return render(
    <TaskDeleteConfirm
      task={task}
      deleting={deleting}
      onConfirm={mockOnConfirm}
      onCancel={mockOnCancel}
    />
  );
}

const TEST_TASK: TaskData = {
  task_id: "t1",
  title: "Task to delete",
  description: null,
  priority: "medium",
  status: "pending",
  due_date: null,
  completed_at: null,
};

describe("TaskDeleteConfirm", () => {
  it("renders task title in confirmation", () => {
    renderConfirm(TEST_TASK);
    expect(screen.getByText(/Task to delete/)).toBeInTheDocument();
  });

  it("shows explanation message", () => {
    renderConfirm(TEST_TASK);
    expect(screen.getByText(/cannot be undone/i)).toBeInTheDocument();
  });

  it("renders Cancel and Delete buttons", () => {
    renderConfirm(TEST_TASK);
    expect(screen.getByRole("button", { name: /cancel/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /delete/i })).toBeInTheDocument();
  });

  it("calls onCancel when Cancel clicked", async () => {
    const user = userEvent.setup();
    renderConfirm(TEST_TASK);
    await user.click(screen.getByRole("button", { name: /cancel/i }));
    expect(mockOnCancel).toHaveBeenCalled();
  });

  it("calls onConfirm when Delete clicked", async () => {
    const user = userEvent.setup();
    renderConfirm(TEST_TASK);
    await user.click(screen.getByRole("button", { name: /delete/i }));
    expect(mockOnConfirm).toHaveBeenCalled();
  });

  it("disables buttons during deletion", () => {
    renderConfirm(TEST_TASK, true);
    expect(screen.getByRole("button", { name: /cancel/i })).toBeDisabled();
    expect(screen.getByRole("button", { name: /deleting/i })).toBeDisabled();
  });

  it("has dialog role", () => {
    renderConfirm(TEST_TASK);
    expect(screen.getByRole("dialog")).toBeInTheDocument();
  });
});
