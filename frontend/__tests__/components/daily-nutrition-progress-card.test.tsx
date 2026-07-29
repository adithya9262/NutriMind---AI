import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { DailyNutritionProgressCard } from "@/components/daily-nutrition-progress-card";

const MOCK_PROGRESS = {
  calories: { consumed: "2000.00", target: "2500.00", remaining: "500.00", percentage: "80.00", status: "below_target" as const },
  protein: { consumed: "100.00", target: "100.00", remaining: "0.00", percentage: "100.00", status: "target_met" as const },
  carbohydrate: { consumed: "350.00", target: "300.00", remaining: "-50.00", percentage: "116.67", status: "above_target" as const },
  fat: { consumed: "40.00", target: "80.00", remaining: "40.00", percentage: "50.00", status: "below_target" as const },
};

const defaultProps = {
  progress: null,
  status: "loading" as const,
  error: null,
  onRetry: vi.fn(),
};

describe("DailyNutritionProgressCard", () => {
  it("shows loading state", () => {
    render(<DailyNutritionProgressCard {...defaultProps} />);
    expect(screen.getByRole("status", { name: /loading progress/i })).toBeInTheDocument();
  });

  it("shows success state with all nutrients", () => {
    render(<DailyNutritionProgressCard {...defaultProps} status="available" progress={MOCK_PROGRESS} />);
    expect(screen.getByText("Calories")).toBeInTheDocument();
    expect(screen.getByText("Protein")).toBeInTheDocument();
    expect(screen.getByText("Carbohydrates")).toBeInTheDocument();
    expect(screen.getByText("Fat")).toBeInTheDocument();
  });

  it("shows error state with retry", () => {
    render(<DailyNutritionProgressCard {...defaultProps} status="error" error="Progress error" />);
    expect(screen.getByText("Progress error")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /retry/i })).toBeInTheDocument();
  });

  it("shows missing-profile state with link to /nutrition", () => {
    render(<DailyNutritionProgressCard {...defaultProps} status="missing_profile" />);
    expect(screen.getByText(/set up your nutrition profile/i)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /create profile/i })).toHaveAttribute("href", "/nutrition");
  });

  it("displays consumed values", () => {
    render(<DailyNutritionProgressCard {...defaultProps} status="available" progress={MOCK_PROGRESS} />);
    expect(screen.getByText((content) => content.includes("2,000"))).toBeInTheDocument();
  });

  it("displays target values", () => {
    render(<DailyNutritionProgressCard {...defaultProps} status="available" progress={MOCK_PROGRESS} />);
    expect(screen.getByText((content) => content.includes("2,500"))).toBeInTheDocument();
  });

  it("displays remaining values", () => {
    render(<DailyNutritionProgressCard {...defaultProps} status="available" progress={MOCK_PROGRESS} />);
    const remainingElements = screen.getAllByText((content) => content.includes("500"));
    expect(remainingElements.length).toBeGreaterThan(0);
  });

  it("displays percentage values", () => {
    render(<DailyNutritionProgressCard {...defaultProps} status="available" progress={MOCK_PROGRESS} />);
    expect(screen.getByText("80.00%")).toBeInTheDocument();
    expect(screen.getByText("100.00%")).toBeInTheDocument();
    expect(screen.getByText("116.67%")).toBeInTheDocument();
    expect(screen.getByText("50.00%")).toBeInTheDocument();
  });

  it("displays status labels", () => {
    render(<DailyNutritionProgressCard {...defaultProps} status="available" progress={MOCK_PROGRESS} />);
    expect(screen.getAllByText("Below Target").length).toBeGreaterThan(0);
    expect(screen.getByText("Target Met")).toBeInTheDocument();
    expect(screen.getByText("Above Target")).toBeInTheDocument();
  });

  it("preserves negative remaining", () => {
    render(<DailyNutritionProgressCard {...defaultProps} status="available" progress={MOCK_PROGRESS} />);
    const remainingElements = screen.getAllByText((content) => content.includes("-50"));
    expect(remainingElements.length).toBeGreaterThan(0);
    expect(remainingElements[0].textContent).toContain("-");
  });

  it("preserves percentage above 100", () => {
    render(<DailyNutritionProgressCard {...defaultProps} status="available" progress={MOCK_PROGRESS} />);
    expect(screen.getByText("116.67%")).toBeInTheDocument();
  });

  it("exact status is preserved", () => {
    render(<DailyNutritionProgressCard {...defaultProps} status="available" progress={MOCK_PROGRESS} />);
    expect(MOCK_PROGRESS.carbohydrate.status).toBe("above_target");
    expect(MOCK_PROGRESS.protein.status).toBe("target_met");
  });

  it("no unsupported warning", () => {
    render(<DailyNutritionProgressCard {...defaultProps} status="available" progress={MOCK_PROGRESS} />);
    expect(screen.queryByText(/warning|caution|alert/i)).not.toBeInTheDocument();
  });

  it("no health interpretation", () => {
    render(<DailyNutritionProgressCard {...defaultProps} status="available" progress={MOCK_PROGRESS} />);
    expect(screen.queryByText(/healthy|unhealthy|good|bad|risk/i)).not.toBeInTheDocument();
  });

  it("has progressbar role with correct attributes", () => {
    render(<DailyNutritionProgressCard {...defaultProps} status="available" progress={MOCK_PROGRESS} />);
    const bars = screen.getAllByRole("progressbar");
    expect(bars.length).toBe(4);
  });
});
