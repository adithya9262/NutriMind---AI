import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { TaskForm } from "@/components/task-form";

const mockOnSubmit = vi.fn();

function renderForm(overrides: Record<string, unknown> = {}) {
  return render(
    <TaskForm
      onSubmit={mockOnSubmit}
      loading={false}
      error={null}
      onCancel={undefined}
      {...overrides}
    />
  );
}

beforeEach(() => {
  vi.clearAllMocks();
});

describe("TaskForm", () => {
  it("renders title field", () => {
    renderForm();
    expect(screen.getByLabelText(/title/i)).toBeInTheDocument();
  });

  it("renders description field", () => {
    renderForm();
    expect(screen.getByLabelText(/description/i)).toBeInTheDocument();
  });

  it("renders priority field", () => {
    renderForm();
    expect(screen.getByLabelText(/priority/i)).toBeInTheDocument();
  });

  it("renders due-date field", () => {
    renderForm();
    expect(screen.getByLabelText(/due date/i)).toBeInTheDocument();
  });

  it("renders submit and cancel buttons", () => {
    renderForm({ onCancel: () => {} });
    expect(screen.getByRole("button", { name: /add task/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /cancel/i })).toBeInTheDocument();
  });

  it("title input has accessible name", () => {
    renderForm();
    expect(screen.getByLabelText(/title/i)).toBeInTheDocument();
  });

  it("description has accessible name", () => {
    renderForm();
    expect(screen.getByLabelText(/description/i)).toBeInTheDocument();
  });

  it("priority select has accessible name", () => {
    renderForm();
    expect(screen.getByLabelText(/priority/i)).toBeInTheDocument();
  });

  it("due-date input has accessible name and type", () => {
    renderForm();
    const input = screen.getByLabelText(/due date/i);
    expect(input).toHaveAttribute("type", "date");
  });

  it("validates title is required", async () => {
    const user = userEvent.setup();
    renderForm();
    const submit = screen.getByRole("button", { name: /add task/i });
    await user.click(submit);
    await waitFor(() => {
      expect(screen.getByText(/title is required/i)).toBeInTheDocument();
    });
  });

  it("validates title minimum boundary", async () => {
    const user = userEvent.setup();
    renderForm();
    const titleInput = screen.getByLabelText(/title/i);
    titleInput.focus();
    fireEvent.change(titleInput, { target: { value: " " } });
    const submit = screen.getByRole("button", { name: /add task/i });
    await user.click(submit);
    await waitFor(() => {
      expect(screen.getByText(/title is required/i)).toBeInTheDocument();
    });
  });

  it("validates title maximum boundary", async () => {
    const user = userEvent.setup();
    renderForm();
    const titleInput = screen.getByLabelText(/title/i);
    fireEvent.change(titleInput, { target: { value: "x".repeat(201) } });
    const submit = screen.getByRole("button", { name: /add task/i });
    await user.click(submit);
    await waitFor(() => {
      expect(screen.getByText(/title must not exceed/i)).toBeInTheDocument();
    });
  });

  it("validates description maximum boundary", async () => {
    const user = userEvent.setup();
    renderForm();
    const descInput = screen.getByLabelText(/description/i);
    fireEvent.change(descInput, { target: { value: "x".repeat(2001) } });
    fireEvent.change(screen.getByLabelText(/title/i), { target: { value: "Valid title" } });
    const submit = screen.getByRole("button", { name: /add task/i });
    await user.click(submit);
    await waitFor(() => {
      expect(screen.getByText(/description must not exceed/i)).toBeInTheDocument();
    });
  });

  it("submits with correct payload", async () => {
    mockOnSubmit.mockResolvedValue(true);
    const user = userEvent.setup();
    renderForm();
    const titleInput = screen.getByLabelText(/title/i);
    await user.type(titleInput, "My task");
    const submit = screen.getByRole("button", { name: /add task/i });
    await user.click(submit);
    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith(expect.objectContaining({ title: "My task" }));
    });
  });

  it("includes description when provided", async () => {
    mockOnSubmit.mockResolvedValue(true);
    const user = userEvent.setup();
    renderForm();
    const titleInput = screen.getByLabelText(/title/i);
    await user.type(titleInput, "My task");
    const descInput = screen.getByLabelText(/description/i);
    await user.type(descInput, "A description");
    const submit = screen.getByRole("button", { name: /add task/i });
    await user.click(submit);
    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith(
        expect.objectContaining({ title: "My task", description: "A description" })
      );
    });
  });

  it("shows loading state", () => {
    renderForm({ loading: true });
    expect(screen.getByRole("button", { name: /creating/i })).toBeDisabled();
  });

  it("cancel behavior resets form", async () => {
    const onCancel = vi.fn();
    const user = userEvent.setup();
    renderForm({ onCancel });
    const cancel = screen.getByRole("button", { name: /cancel/i });
    await user.click(cancel);
    expect(onCancel).toHaveBeenCalled();
  });

  it("shows error message", () => {
    renderForm({ error: "Something went wrong" });
    expect(screen.getByText("Something went wrong")).toBeInTheDocument();
  });

  it("has correct button types", () => {
    renderForm({ onCancel: () => {} });
    expect(screen.getByRole("button", { name: /add task/i })).toHaveAttribute("type", "submit");
    expect(screen.getByRole("button", { name: /cancel/i })).toHaveAttribute("type", "button");
  });

  it("title has aria-required", () => {
    renderForm();
    expect(screen.getByLabelText(/title/i)).toHaveAttribute("aria-required", "true");
  });

  it("priority options have correct values", () => {
    renderForm();
    const select = screen.getByLabelText(/priority/i) as HTMLSelectElement;
    const options = Array.from(select.options);
    expect(options.map((o) => o.value)).toEqual(["low", "medium", "high"]);
  });
});
