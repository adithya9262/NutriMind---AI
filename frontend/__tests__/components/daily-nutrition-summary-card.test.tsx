import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { DailyNutritionSummaryCard } from "@/components/daily-nutrition-summary-card";

const MOCK_SUMMARY = {
  entry_count: 2,
  totals: { calories_kcal: "800.00", protein_g: "47.00", carbohydrate_g: "75.00", fat_g: "27.00" },
  meals: [
    { meal_type: "breakfast" as const, entry_count: 1, totals: { calories_kcal: "350.00", protein_g: "12.00", carbohydrate_g: "55.00", fat_g: "5.00" } },
    { meal_type: "lunch" as const, entry_count: 1, totals: { calories_kcal: "450.00", protein_g: "35.00", carbohydrate_g: "20.00", fat_g: "22.00" } },
    { meal_type: "dinner" as const, entry_count: 0, totals: { calories_kcal: "0.00", protein_g: "0.00", carbohydrate_g: "0.00", fat_g: "0.00" } },
    { meal_type: "snack" as const, entry_count: 0, totals: { calories_kcal: "0.00", protein_g: "0.00", carbohydrate_g: "0.00", fat_g: "0.00" } },
  ],
};

const defaultProps = {
  summary: null,
  status: "loading" as const,
  error: null,
  onRetry: vi.fn(),
};

describe("DailyNutritionSummaryCard", () => {
  it("shows loading state", () => {
    render(<DailyNutritionSummaryCard {...defaultProps} />);
    expect(screen.getByRole("status", { name: /loading summary/i })).toBeInTheDocument();
  });

  it("shows success state with totals", () => {
    render(<DailyNutritionSummaryCard {...defaultProps} status="available" summary={MOCK_SUMMARY} />);
    expect(screen.getByText("800")).toBeInTheDocument();
    expect(screen.getByText("47.0")).toBeInTheDocument();
    expect(screen.getByText("75.0")).toBeInTheDocument();
    expect(screen.getByText("27.0")).toBeInTheDocument();
  });

  it("shows zero totals for empty day", () => {
    const zeroSummary = {
      entry_count: 0,
      totals: { calories_kcal: "0.00", protein_g: "0.00", carbohydrate_g: "0.00", fat_g: "0.00" },
      meals: [
        { meal_type: "breakfast" as const, entry_count: 0, totals: { calories_kcal: "0.00", protein_g: "0.00", carbohydrate_g: "0.00", fat_g: "0.00" } },
        { meal_type: "lunch" as const, entry_count: 0, totals: { calories_kcal: "0.00", protein_g: "0.00", carbohydrate_g: "0.00", fat_g: "0.00" } },
        { meal_type: "dinner" as const, entry_count: 0, totals: { calories_kcal: "0.00", protein_g: "0.00", carbohydrate_g: "0.00", fat_g: "0.00" } },
        { meal_type: "snack" as const, entry_count: 0, totals: { calories_kcal: "0.00", protein_g: "0.00", carbohydrate_g: "0.00", fat_g: "0.00" } },
      ],
    };
    render(<DailyNutritionSummaryCard {...defaultProps} status="available" summary={zeroSummary} />);
    expect(screen.getByText("0")).toBeInTheDocument();
  });

  it("shows error state with retry", () => {
    render(<DailyNutritionSummaryCard {...defaultProps} status="error" error="Summary error" />);
    expect(screen.getByText("Summary error")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /retry/i })).toBeInTheDocument();
  });

  it("displays exact backend totals", () => {
    render(<DailyNutritionSummaryCard {...defaultProps} status="available" summary={MOCK_SUMMARY} />);
    expect(screen.getByText("800")).toBeInTheDocument();
  });

  it("shows correct units", () => {
    render(<DailyNutritionSummaryCard {...defaultProps} status="available" summary={MOCK_SUMMARY} />);
    expect(screen.getAllByText("kcal").length).toBeGreaterThan(0);
    expect(screen.getAllByText("g").length).toBeGreaterThan(0);
  });

  it("no unsupported metric", () => {
    render(<DailyNutritionSummaryCard {...defaultProps} status="available" summary={MOCK_SUMMARY} />);
    expect(screen.queryByText(/fiber|sugar|sodium|cholesterol/i)).not.toBeInTheDocument();
  });

  it("no recommendation", () => {
    render(<DailyNutritionSummaryCard {...defaultProps} status="available" summary={MOCK_SUMMARY} />);
    expect(screen.queryByText(/should|recommend|consider/i)).not.toBeInTheDocument();
  });

  it("no medical interpretation", () => {
    render(<DailyNutritionSummaryCard {...defaultProps} status="available" summary={MOCK_SUMMARY} />);
    expect(screen.queryByText(/healthy|unhealthy|good|bad|risk|disease/i)).not.toBeInTheDocument();
  });
});
