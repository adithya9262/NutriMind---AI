import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BodyWeightEntryForm } from "@/components/body-weight-entry-form";

const mockOnSubmit = vi.fn();

function renderForm(overrides: Record<string, unknown> = {}) {
  return render(
    <BodyWeightEntryForm
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

describe("BodyWeightEntryForm", () => {
  it("renders date and weight fields", () => {
    renderForm();
    expect(screen.getByLabelText(/date/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/weight/i)).toBeInTheDocument();
  });

  it("renders submit button", () => {
    renderForm();
    expect(screen.getByRole("button", { name: /add weight/i })).toBeInTheDocument();
  });

  it("renders cancel button when onCancel is provided", () => {
    render(
      <BodyWeightEntryForm
        onSubmit={mockOnSubmit}
        loading={false}
        error={null}
        onCancel={() => {}}
      />
    );
    expect(screen.getByRole("button", { name: /cancel/i })).toBeInTheDocument();
  });

  it("date input has accessible label", () => {
    renderForm();
    const dateInput = screen.getByLabelText(/date/i);
    expect(dateInput).toHaveAttribute("type", "date");
  });

  it("weight input has accessible label", () => {
    renderForm();
    const weightInput = screen.getByLabelText(/weight/i);
    expect(weightInput).toHaveAttribute("type", "number");
    expect(weightInput).toHaveAttribute("inputMode", "decimal");
  });

  it("validates required fields", async () => {
    const user = userEvent.setup();
    mockOnSubmit.mockResolvedValue(true);
    renderForm();

    const weightInput = screen.getByLabelText(/weight/i);
    await user.clear(weightInput);

    const addButton = screen.getByRole("button", { name: /add weight/i });
    await user.click(addButton);

    await waitFor(() => {
      expect(screen.getByText(/weight is required/i)).toBeInTheDocument();
    });
  });

  it("validates minimum boundary", async () => {
    const user = userEvent.setup();
    renderForm();

    const weightInput = screen.getByLabelText(/weight/i);
    await user.clear(weightInput);
    await user.type(weightInput, "5");

    const addButton = screen.getByRole("button", { name: /add weight/i });
    await user.click(addButton);

    await waitFor(() => {
      expect(screen.getByText(/must be between/i)).toBeInTheDocument();
    });
  });

  it("validates maximum boundary", async () => {
    const user = userEvent.setup();
    renderForm();

    const weightInput = screen.getByLabelText(/weight/i);
    await user.clear(weightInput);
    await user.type(weightInput, "800");

    const addButton = screen.getByRole("button", { name: /add weight/i });
    await user.click(addButton);

    await waitFor(() => {
      expect(screen.getByText(/must be between/i)).toBeInTheDocument();
    });
  });

  it("shows aria-invalid on invalid fields", async () => {
    const user = userEvent.setup();
    renderForm();

    const weightInput = screen.getByLabelText(/weight/i);
    await user.clear(weightInput);

    await user.click(screen.getByRole("button", { name: /add weight/i }));

    await waitFor(() => {
      expect(weightInput).toHaveAttribute("aria-invalid", "true");
    });
  });

  it("calls onSubmit with correct payload", async () => {
    const user = userEvent.setup();
    mockOnSubmit.mockResolvedValueOnce(true);

    const today = new Date();
    const y = today.getFullYear();
    const m = String(today.getMonth() + 1).padStart(2, "0");
    const d = String(today.getDate()).padStart(2, "0");
    const todayStr = `${y}-${m}-${d}`;

    renderForm();

    const weightInput = screen.getByLabelText(/weight/i);
    await user.clear(weightInput);
    await user.type(weightInput, "70.00");

    await user.click(screen.getByRole("button", { name: /add weight/i }));

    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith(todayStr, "70");
    });
  });

  it("shows loading state", () => {
    renderForm({ loading: true });
    expect(screen.getByRole("button", { name: /saving/i })).toBeDisabled();
  });

  it("prevents duplicate submission", async () => {
    const user = userEvent.setup();
    renderForm({ loading: true });

    const addButton = screen.getByRole("button", { name: /saving/i });
    expect(addButton).toBeDisabled();
  });

  it("shows API error", () => {
    renderForm({ error: "API error message" });
    expect(screen.getByText("API error message")).toBeInTheDocument();
  });

  it("cancel button triggers onCancel", async () => {
    const user = userEvent.setup();
    const onCancel = vi.fn();
    render(
      <BodyWeightEntryForm
        onSubmit={mockOnSubmit}
        loading={false}
        error={null}
        onCancel={onCancel}
      />
    );

    await user.click(screen.getByRole("button", { name: /cancel/i }));
    expect(onCancel).toHaveBeenCalledOnce();
  });

  it("has correct button types", () => {
    renderForm();
    const addButton = screen.getByRole("button", { name: /add weight/i });
    expect(addButton).toHaveAttribute("type", "submit");
  });

  it("user_id is not present in the form", () => {
    renderForm();
    expect(screen.queryByLabelText(/user id/i)).not.toBeInTheDocument();
  });

  it("entry_id is not present in the form", () => {
    renderForm();
    expect(screen.queryByLabelText(/entry id/i)).not.toBeInTheDocument();
  });

  it("weight input has correct min/max/step", () => {
    renderForm();
    const weightInput = screen.getByLabelText(/weight/i);
    expect(weightInput).toHaveAttribute("min", "10");
    expect(weightInput).toHaveAttribute("max", "700");
    expect(weightInput).toHaveAttribute("step", "0.01");
  });
});
