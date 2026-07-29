import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { BodyWeightGoalProgressCard } from "@/components/body-weight-goal-progress-card";
import type { BodyWeightGoalProgressData, GoalStatus } from "@/types/body-weight";

const MOCK_GOAL: BodyWeightGoalProgressData = {
  starting_weight_kg: "80.00",
  current_weight_kg: "75.00",
  target_weight_kg: "70.00",
  direction: "decrease",
  total_change_required_kg: "10.00",
  change_achieved_kg: "5.00",
  remaining_change_kg: "5.00",
  progress_percentage: "50.00",
  status: "in_progress",
};

function renderCard(
  goalProgress: BodyWeightGoalProgressData | null,
  goalStatus: GoalStatus,
  goalError: string | null = null,
  onRetry = vi.fn()
) {
  return render(
    <BodyWeightGoalProgressCard
      goalProgress={goalProgress}
      goalStatus={goalStatus}
      goalError={goalError}
      onRetry={onRetry}
    />
  );
}

describe("BodyWeightGoalProgressCard", () => {
  it("shows loading state", () => {
    renderCard(null, "loading");
    expect(screen.getByRole("status", { name: /loading goal progress/i })).toBeInTheDocument();
  });

  it("shows success state", () => {
    renderCard(MOCK_GOAL, "available");
    expect(screen.getByText(/80\.0\s*kg/i)).toBeInTheDocument();
    expect(screen.getByText(/75\.0\s*kg/i)).toBeInTheDocument();
    expect(screen.getByText(/70\.0\s*kg/i)).toBeInTheDocument();
    expect(screen.getByText(/decrease/i)).toBeInTheDocument();
    expect(screen.getByText(/in progress/i)).toBeInTheDocument();
  });

  it("shows error state", () => {
    renderCard(null, "error", "Goal error");
    expect(screen.getByText(/goal error/i)).toBeInTheDocument();
  });

  it("shows retry button on error", () => {
    const onRetry = vi.fn();
    renderCard(null, "error", "Error", onRetry);
    expect(screen.getByRole("button", { name: /retry/i })).toBeInTheDocument();
  });

  it("shows missing profile state", () => {
    renderCard(null, "missing_profile");
    expect(screen.getByText(/nutrition profile required/i)).toBeInTheDocument();
  });

  it("shows link to /nutrition when missing profile", () => {
    renderCard(null, "missing_profile");
    const link = screen.getByRole("link", { name: /go to nutrition/i });
    expect(link).toHaveAttribute("href", "/nutrition");
  });

  it("shows missing current weight state", () => {
    renderCard(null, "missing_current_weight");
    expect(screen.getByText(/current weight required/i)).toBeInTheDocument();
  });

  it("shows invalid/equal goal state", () => {
    renderCard(null, "invalid_goal");
    expect(screen.getByText(/goal configuration issue/i)).toBeInTheDocument();
  });

  it("shows starting weight", () => {
    renderCard(MOCK_GOAL, "available");
    expect(screen.getByText(/80\.0\s*kg/i)).toBeInTheDocument();
  });

  it("shows current weight", () => {
    renderCard(MOCK_GOAL, "available");
    expect(screen.getByText(/75\.0\s*kg/i)).toBeInTheDocument();
  });

  it("shows target weight", () => {
    renderCard(MOCK_GOAL, "available");
    expect(screen.getByText(/70\.0\s*kg/i)).toBeInTheDocument();
  });

  it("shows direction", () => {
    renderCard(MOCK_GOAL, "available");
    expect(screen.getByText("Decrease")).toBeInTheDocument();
  });

  it("shows status", () => {
    renderCard(MOCK_GOAL, "available");
    expect(screen.getByText("In Progress")).toBeInTheDocument();
  });

  it("preserves negative progress", () => {
    const neg = { ...MOCK_GOAL, change_achieved_kg: "-2.00", progress_percentage: "-20.00" };
    renderCard(neg, "available");
    expect(screen.getByText(/-20\.0%/i)).toBeInTheDocument();
  });

  it("preserves zero progress", () => {
    const zero = { ...MOCK_GOAL, change_achieved_kg: "0.00", progress_percentage: "0.00" };
    renderCard(zero, "available");
    expect(screen.getByText("0.0%")).toBeInTheDocument();
  });

  it("preserves exactly 100%", () => {
    const hundred = { ...MOCK_GOAL, change_achieved_kg: "10.00", progress_percentage: "100.00", status: "target_reached" as const };
    renderCard(hundred, "available");
    expect(screen.getByText(/100\.0%/i)).toBeInTheDocument();
  });

  it("preserves above 100% progress", () => {
    const above = { ...MOCK_GOAL, change_achieved_kg: "12.00", progress_percentage: "120.00", status: "target_passed" as const };
    renderCard(above, "available");
    expect(screen.getByText(/120\.0%/i)).toBeInTheDocument();
  });

  it("preserves negative remaining", () => {
    const neg = { ...MOCK_GOAL, change_achieved_kg: "12.00", remaining_change_kg: "-2.00", progress_percentage: "120.00", status: "target_passed" as const };
    renderCard(neg, "available");
    expect(screen.getByText(/-2\.0\s*kg/i)).toBeInTheDocument();
  });

  it("has progress bar with aria attributes", () => {
    renderCard(MOCK_GOAL, "available");
    const bar = screen.getByRole("progressbar");
    expect(bar).toHaveAttribute("aria-valuenow", "50");
    expect(bar).toHaveAttribute("aria-valuemin", "0");
    expect(bar).toHaveAttribute("aria-valuemax", "100");
  });

  it("does not cap displayed percentage", () => {
    const above = { ...MOCK_GOAL, change_achieved_kg: "15.00", progress_percentage: "150.00", status: "target_passed" as const };
    renderCard(above, "available");
    expect(screen.getByText(/150\.0%/i)).toBeInTheDocument();
  });

  it("no goal-progress calculation in frontend", async () => {
    const types = await import("@/types/body-weight");
    expect(typeof (types as Record<string, unknown>).calculateGoalProgress).toBe("undefined");
    expect(typeof (types as Record<string, unknown>).calculatePercentageProgress).toBe("undefined");
    expect(typeof (types as Record<string, unknown>).calculateRemainingChange).toBe("undefined");
  });

  it("no status reclassification", async () => {
    const types = await import("@/types/body-weight");
    expect(typeof (types as Record<string, unknown>).reclassifyStatus).toBe("undefined");
  });

  it("no goal-date estimate", () => {
    renderCard(MOCK_GOAL, "available");
    expect(screen.queryByText(/by date/i)).not.toBeInTheDocument();
  });

  it("no prediction", () => {
    renderCard(MOCK_GOAL, "available");
    expect(screen.queryByText(/predict/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/will reach/i)).not.toBeInTheDocument();
  });

  it("no recommendation", () => {
    renderCard(MOCK_GOAL, "available");
    expect(screen.queryByText(/should/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/recommend/i)).not.toBeInTheDocument();
  });

  it("no medical interpretation", () => {
    renderCard(MOCK_GOAL, "available");
    expect(screen.queryByText(/healthy/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/unhealthy/i)).not.toBeInTheDocument();
  });

  it("no reclassification of direction", async () => {
    const types = await import("@/types/body-weight");
    expect(typeof (types as Record<string, unknown>).reclassifyDirection).toBe("undefined");
  });

  it("does not render when null and not loading/error/info state", () => {
    const { container } = renderCard(null, "idle");
    expect(container.innerHTML).toBe("");
  });
});
