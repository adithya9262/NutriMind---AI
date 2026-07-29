import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { NutritionLogEntryList } from "@/components/nutrition-log-entry-list";

const MOCK_ENTRIES = [
  { entry_id: "e1", food_name: "Oatmeal", meal_type: "breakfast" as const, serving_description: "1 cup", calories_kcal: "350.00", protein_g: "12.00", carbohydrate_g: "55.00", fat_g: "5.00" },
  { entry_id: "e2", food_name: "Chicken Salad", meal_type: "lunch" as const, serving_description: "1 bowl", calories_kcal: "450.00", protein_g: "35.00", carbohydrate_g: "20.00", fat_g: "22.00" },
];

const defaultProps = {
  entries: MOCK_ENTRIES,
  status: "available" as const,
  error: null,
  deleteStatus: "idle" as const,
  deletingEntryId: null,
  deleteError: null,
  onDelete: vi.fn(),
  onCancelDelete: vi.fn(),
  onConfirmDelete: vi.fn(),
  onRetry: vi.fn(),
};

describe("NutritionLogEntryList", () => {
  it("shows loading state", () => {
    render(<NutritionLogEntryList {...defaultProps} status="loading" entries={[]} />);
    expect(screen.getByRole("status", { name: /loading entries/i })).toBeInTheDocument();
  });

  it("shows empty state when no entries", () => {
    render(<NutritionLogEntryList {...defaultProps} status="empty" entries={[]} />);
    expect(screen.getByText(/no entries logged/i)).toBeInTheDocument();
  });

  it("shows error state with retry", () => {
    render(<NutritionLogEntryList {...defaultProps} status="error" entries={[]} error="Failed to load" />);
    expect(screen.getByText("Failed to load")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /retry/i })).toBeInTheDocument();
  });

  it("renders entries when available", () => {
    render(<NutritionLogEntryList {...defaultProps} />);
    expect(screen.getByText("Oatmeal")).toBeInTheDocument();
    expect(screen.getByText("Chicken Salad")).toBeInTheDocument();
    expect(screen.getByText("Breakfast")).toBeInTheDocument();
    expect(screen.getByText("Lunch")).toBeInTheDocument();
  });

  it("preserves backend order", () => {
    render(<NutritionLogEntryList {...defaultProps} />);
    const entries = screen.getAllByRole("listitem");
    expect(entries[0]).toHaveTextContent("Oatmeal");
    expect(entries[1]).toHaveTextContent("Chicken Salad");
  });

  it("has delete action with accessible name", () => {
    render(<NutritionLogEntryList {...defaultProps} />);
    expect(screen.getByRole("button", { name: /delete oatmeal/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /delete chicken salad/i })).toBeInTheDocument();
  });

  it("shows confirmation on delete click", async () => {
    const user = userEvent.setup();
    const onDelete = vi.fn();
    render(<NutritionLogEntryList {...defaultProps} onDelete={onDelete} />);

    await user.click(screen.getByRole("button", { name: /delete oatmeal/i }));
    expect(onDelete).toHaveBeenCalledWith("e1");
  });

  it("shows deletion inline confirmation", () => {
    render(
      <NutritionLogEntryList
        {...defaultProps}
        deleteStatus="confirming"
        deletingEntryId="e1"
      />
    );
    expect(screen.getByRole("button", { name: /cancel/i })).toBeInTheDocument();
    const deleteButtons = screen.getAllByRole("button", { name: /delete/i });
    expect(deleteButtons.length).toBe(2);
  });

  it("shows loading state during deletion", () => {
    render(
      <NutritionLogEntryList
        {...defaultProps}
        deleteStatus="deleting"
        deletingEntryId="e1"
      />
    );
    const deleteButton = screen.getByRole("button", { name: /delete oatmeal/i });
    expect(deleteButton).toBeDisabled();
  });

  it("shows delete error", () => {
    render(
      <NutritionLogEntryList
        {...defaultProps}
        deleteStatus="error"
        deletingEntryId="e1"
        deleteError="Delete failed"
      />
    );
    expect(screen.getByText("Delete failed")).toBeInTheDocument();
  });

  it("no edit action exists", () => {
    render(<NutritionLogEntryList {...defaultProps} />);
    expect(screen.queryByRole("button", { name: /edit/i })).not.toBeInTheDocument();
  });

  it("does not expose user_id", () => {
    render(<NutritionLogEntryList {...defaultProps} />);
    expect(screen.queryByText(/u1|user/i)).not.toBeInTheDocument();
  });
});
