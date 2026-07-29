import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { NutritionProfileForm } from "@/components/nutrition-profile-form";

describe("NutritionProfileForm", () => {
  const mockOnSubmit = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    mockOnSubmit.mockResolvedValue(true);
  });

  it("renders all required fields", () => {
    render(<NutritionProfileForm loading={false} error={null} onSubmit={mockOnSubmit} />);
    expect(screen.getByLabelText(/date of birth/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/biological sex/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/e\.g\. 170/)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/e\.g\. 70/)).toBeInTheDocument();
    expect(screen.getByLabelText(/activity level/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/goal/i)).toBeInTheDocument();
  });

  it("renders optional fields", () => {
    render(<NutritionProfileForm loading={false} error={null} onSubmit={mockOnSubmit} />);
    expect(screen.getByLabelText(/target weight/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/dietary preference/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/allergies/i)).toBeInTheDocument();
  });

  it("renders submit button with Create Profile text for new profile", () => {
    render(<NutritionProfileForm loading={false} error={null} onSubmit={mockOnSubmit} />);
    expect(screen.getByRole("button", { name: "Create Profile" })).toBeInTheDocument();
  });

  it("renders submit button with Save Changes text for update", () => {
    render(
      <NutritionProfileForm
        loading={false}
        error={null}
        onSubmit={mockOnSubmit}
        isUpdate={true}
      />
    );
    expect(screen.getByRole("button", { name: "Save Changes" })).toBeInTheDocument();
  });

  it("renders cancel button when onCancel provided", () => {
    render(
      <NutritionProfileForm
        loading={false}
        error={null}
        onSubmit={mockOnSubmit}
        onCancel={vi.fn()}
      />
    );
    expect(screen.getByRole("button", { name: "Cancel" })).toBeInTheDocument();
  });

  it("shows validation errors when submitting empty form", async () => {
    const user = userEvent.setup();
    render(<NutritionProfileForm loading={false} error={null} onSubmit={mockOnSubmit} />);
    await user.click(screen.getByRole("button", { name: "Create Profile" }));
    expect(screen.getByText("Date of birth is required.")).toBeInTheDocument();
    expect(screen.getByText("Biological sex is required.")).toBeInTheDocument();
    expect(screen.getByText("Height is required.")).toBeInTheDocument();
    expect(screen.getByText("Weight is required.")).toBeInTheDocument();
    expect(screen.getByText("Activity level is required.")).toBeInTheDocument();
    expect(screen.getByText("Goal is required.")).toBeInTheDocument();
  });

  it("shows height validation error for out-of-range value", async () => {
    const user = userEvent.setup();
    render(<NutritionProfileForm loading={false} error={null} onSubmit={mockOnSubmit} />);
    const heightInput = screen.getByPlaceholderText(/e\.g\. 170/);
    await user.type(heightInput, "10");
    await user.click(screen.getByRole("button", { name: "Create Profile" }));
    expect(screen.getByText("Height must be between 50 and 300 cm.")).toBeInTheDocument();
  });

  it("shows weight validation error for out-of-range value", async () => {
    const user = userEvent.setup();
    render(<NutritionProfileForm loading={false} error={null} onSubmit={mockOnSubmit} />);
    const weightInput = screen.getByPlaceholderText(/e\.g\. 70/);
    await user.type(weightInput, "5");
    await user.click(screen.getByRole("button", { name: "Create Profile" }));
    expect(screen.getByText("Weight must be between 10 and 700 kg.")).toBeInTheDocument();
  });

  it("displays error alert when error prop is set", () => {
    render(
      <NutritionProfileForm
        loading={false}
        error="Something went wrong"
        onSubmit={mockOnSubmit}
      />
    );
    expect(screen.getByText("Something went wrong")).toBeInTheDocument();
  });

  it("submit button is disabled when loading", () => {
    render(<NutritionProfileForm loading={true} error={null} onSubmit={mockOnSubmit} />);
    expect(screen.getByRole("button", { name: /creating/i })).toBeDisabled();
  });

  it("calls onSubmit with valid payload", async () => {
    const user = userEvent.setup();
    render(<NutritionProfileForm loading={false} error={null} onSubmit={mockOnSubmit} />);
    await user.type(screen.getByLabelText(/date of birth/i), "1990-01-15");
    await user.selectOptions(screen.getByLabelText(/biological sex/i), "male");
    await user.type(screen.getByPlaceholderText(/e\.g\. 170/), "180");
    await user.type(screen.getByPlaceholderText(/e\.g\. 70/), "75");
    await user.selectOptions(screen.getByLabelText(/activity level/i), "moderately_active");
    await user.selectOptions(screen.getByLabelText(/goal/i), "maintain_weight");
    await user.click(screen.getByRole("button", { name: "Create Profile" }));
    expect(mockOnSubmit).toHaveBeenCalledTimes(1);
  });
});
