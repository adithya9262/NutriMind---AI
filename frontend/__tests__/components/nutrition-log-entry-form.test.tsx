import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { NutritionLogEntryForm } from "@/components/nutrition-log-entry-form";

const mockOnSubmit = vi.fn();

function renderForm(overrides: Record<string, unknown> = {}) {
  return render(
    <NutritionLogEntryForm
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

describe("NutritionLogEntryForm", () => {
  it("renders all required fields", () => {
    renderForm();
    expect(screen.getByLabelText(/food name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/meal/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/serving description/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/calories/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/protein/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/carbohydrates/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/fat/i)).toBeInTheDocument();
  });

  it("renders all meal options", () => {
    renderForm();
    const select = screen.getByLabelText(/meal/i);
    expect(select).toContainHTML("Breakfast");
    expect(select).toContainHTML("Lunch");
    expect(select).toContainHTML("Dinner");
    expect(select).toContainHTML("Snack");
  });

  it("renders required labels", () => {
    renderForm();
    const form = screen.getByRole("form", { name: /add nutrition log entry/i });
    expect(form).toBeInTheDocument();
  });

  it("validates required fields", async () => {
    const user = userEvent.setup();
    renderForm();

    const addButton = screen.getByRole("button", { name: /add entry/i });
    await user.click(addButton);

    await waitFor(() => {
      expect(screen.getByText(/food name is required/i)).toBeInTheDocument();
      expect(screen.getByText(/serving description is required/i)).toBeInTheDocument();
      expect(screen.getByText(/calories is required/i)).toBeInTheDocument();
    });
  });

  it("shows aria-invalid on invalid fields", async () => {
    const user = userEvent.setup();
    renderForm();

    await user.click(screen.getByRole("button", { name: /add entry/i }));

    await waitFor(() => {
      const foodInput = screen.getByLabelText(/food name/i);
      expect(foodInput).toHaveAttribute("aria-invalid", "true");
    });
  });

  it("calls onSubmit with correct payload on valid submission", async () => {
    const user = userEvent.setup();
    mockOnSubmit.mockResolvedValueOnce(true);
    renderForm();

    await user.type(screen.getByLabelText(/food name/i), "Apple");
    await user.type(screen.getByLabelText(/serving description/i), "1 medium");
    await user.type(screen.getByLabelText(/^calories/i), "95");
    await user.type(screen.getByLabelText(/^protein/i), "0.5");
    await user.type(screen.getByLabelText(/^carbohydrates/i), "25");
    await user.type(screen.getByLabelText(/^fat/i), "0.3");

    await user.click(screen.getByRole("button", { name: /add entry/i }));

    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledTimes(1);
      const payload = mockOnSubmit.mock.calls[0][0];
      expect(payload.food_name).toBe("Apple");
      expect(payload.serving_description).toBe("1 medium");
      expect(payload.calories_kcal).toBe("95");
      expect(payload.protein_g).toBe("0.5");
      expect(payload.carbohydrate_g).toBe("25");
      expect(payload.fat_g).toBe("0.3");
      expect(payload.meal_type).toBe("breakfast");
      expect(payload.entry_id).toBeTruthy();
      expect(payload.entry_id.length).toBeGreaterThan(0);
    });
  });

  it("does not include logged_date in body (query-only)", async () => {
    const user = userEvent.setup();
    mockOnSubmit.mockResolvedValueOnce(true);
    renderForm();

    await user.type(screen.getByLabelText(/food name/i), "Apple");
    await user.type(screen.getByLabelText(/serving description/i), "1");
    await user.type(screen.getByLabelText(/^calories/i), "95");
    await user.type(screen.getByLabelText(/^protein/i), "0.5");
    await user.type(screen.getByLabelText(/^carbohydrates/i), "25");
    await user.type(screen.getByLabelText(/^fat/i), "0.3");

    await user.click(screen.getByRole("button", { name: /add entry/i }));

    await waitFor(() => {
      const payload = mockOnSubmit.mock.calls[0][0];
      expect(payload.logged_date).toBeUndefined();
    });
  });

  it("does not include user_id in payload", async () => {
    const user = userEvent.setup();
    mockOnSubmit.mockResolvedValueOnce(true);
    renderForm();

    await user.type(screen.getByLabelText(/food name/i), "Apple");
    await user.type(screen.getByLabelText(/serving description/i), "1");
    await user.type(screen.getByLabelText(/^calories/i), "95");
    await user.type(screen.getByLabelText(/^protein/i), "0.5");
    await user.type(screen.getByLabelText(/^carbohydrates/i), "25");
    await user.type(screen.getByLabelText(/^fat/i), "0.3");

    await user.click(screen.getByRole("button", { name: /add entry/i }));

    await waitFor(() => {
      const payload = mockOnSubmit.mock.calls[0][0];
      expect(payload.user_id).toBeUndefined();
    });
  });

  it("does not include unsupported fields", async () => {
    const user = userEvent.setup();
    mockOnSubmit.mockResolvedValueOnce(true);
    renderForm();

    await user.type(screen.getByLabelText(/food name/i), "Apple");
    await user.type(screen.getByLabelText(/serving description/i), "1");
    await user.type(screen.getByLabelText(/^calories/i), "95");
    await user.type(screen.getByLabelText(/^protein/i), "0.5");
    await user.type(screen.getByLabelText(/^carbohydrates/i), "25");
    await user.type(screen.getByLabelText(/^fat/i), "0.3");

    await user.click(screen.getByRole("button", { name: /add entry/i }));

    await waitFor(() => {
      const payload = mockOnSubmit.mock.calls[0][0];
      expect(payload.fiber_g).toBeUndefined();
      expect(payload.sugar_g).toBeUndefined();
      expect(payload.sodium_mg).toBeUndefined();
      expect(payload.created_at).toBeUndefined();
      expect(payload.updated_at).toBeUndefined();
    });
  });

  it("shows loading state", () => {
    renderForm({ loading: true });
    expect(screen.getByRole("button", { name: /adding/i })).toBeDisabled();
  });

  it("prevents duplicate submit while loading", () => {
    renderForm({ loading: true });
    const button = screen.getByRole("button", { name: /adding/i });
    expect(button).toBeDisabled();
  });

  it("shows cancel button when onCancel provided", () => {
    render(
      <NutritionLogEntryForm
        onSubmit={mockOnSubmit}
        loading={false}
        error={null}
        onCancel={vi.fn()}
      />
    );
    expect(screen.getByRole("button", { name: /cancel/i })).toBeInTheDocument();
  });

  it("resets form after successful submit", async () => {
    const user = userEvent.setup();
    mockOnSubmit.mockResolvedValueOnce(true);
    renderForm();

    await user.type(screen.getByLabelText(/food name/i), "Apple");
    await user.type(screen.getByLabelText(/serving description/i), "1");
    await user.type(screen.getByLabelText(/^calories/i), "95");
    await user.type(screen.getByLabelText(/^protein/i), "0.5");
    await user.type(screen.getByLabelText(/^carbohydrates/i), "25");
    await user.type(screen.getByLabelText(/^fat/i), "0.3");

    await user.click(screen.getByRole("button", { name: /add entry/i }));

    await waitFor(() => {
      const foodInput = screen.getByLabelText(/food name/i) as HTMLInputElement;
      expect(foodInput.value).toBe("");
    });
  });

  it("shows backend validation error", () => {
    renderForm({ error: "Entry already exists." });
    expect(screen.getByText("Entry already exists.")).toBeInTheDocument();
  });

  it("has correct button types", () => {
    renderForm();
    expect(screen.getByRole("button", { name: /add entry/i })).toHaveAttribute("type", "submit");
  });
});
