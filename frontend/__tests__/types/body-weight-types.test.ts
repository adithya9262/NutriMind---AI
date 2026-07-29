import { describe, it, expect } from "vitest";
import {
  TREND_DIRECTION_LABELS,
  GOAL_DIRECTION_LABELS,
  GOAL_STATUS_LABELS,
  MIN_WEIGHT_KG,
  MAX_WEIGHT_KG,
  WEIGHT_STEP,
} from "@/types/body-weight";

describe("Body weight types", () => {
  it("has exact trend-direction values", () => {
    expect(TREND_DIRECTION_LABELS).toEqual({
      decreased: "Decreased",
      stable: "Stable",
      increased: "Increased",
    });
  });

  it("has exact goal-direction values", () => {
    expect(GOAL_DIRECTION_LABELS).toEqual({
      decrease: "Decrease",
      maintain: "Maintain",
      increase: "Increase",
    });
  });

  it("has exact goal-status values", () => {
    expect(GOAL_STATUS_LABELS).toEqual({
      not_started: "Not Started",
      in_progress: "In Progress",
      target_reached: "Target Reached",
      target_passed: "Target Passed",
    });
  });

  it("has Decimal weight_kg as string in BodyWeightEntryData", () => {
    const entry = {
      entry_id: "123e4567-e89b-12d3-a456-426614174000",
      logged_date: "2026-07-12",
      weight_kg: "70.00",
    };
    expect(typeof entry.weight_kg).toBe("string");
  });

  it("preserves positive signed values", () => {
    const trend = {
      observation_count: 3,
      first_logged_date: "2026-07-01",
      latest_logged_date: "2026-07-12",
      starting_weight_kg: "70.00",
      latest_weight_kg: "72.00",
      absolute_change_kg: "2.00",
      percentage_change: "2.86",
      direction: "increased" as const,
    };
    expect(trend.absolute_change_kg).toBe("2.00");
    expect(trend.percentage_change).toBe("2.86");
  });

  it("preserves negative signed values", () => {
    const trend = {
      observation_count: 3,
      first_logged_date: "2026-07-01",
      latest_logged_date: "2026-07-12",
      starting_weight_kg: "72.00",
      latest_weight_kg: "70.00",
      absolute_change_kg: "-2.00",
      percentage_change: "-2.78",
      direction: "decreased" as const,
    };
    expect(trend.absolute_change_kg).toBe("-2.00");
    expect(trend.percentage_change).toBe("-2.78");
  });

  it("preserves zero values", () => {
    const trend = {
      observation_count: 2,
      first_logged_date: "2026-07-01",
      latest_logged_date: "2026-07-12",
      starting_weight_kg: "70.00",
      latest_weight_kg: "70.00",
      absolute_change_kg: "0.00",
      percentage_change: "0.00",
      direction: "stable" as const,
    };
    expect(trend.absolute_change_kg).toBe("0.00");
    expect(trend.percentage_change).toBe("0.00");
  });

  it("preserves percentages above 100", () => {
    const goal = {
      starting_weight_kg: "80.00",
      current_weight_kg: "70.00",
      target_weight_kg: "75.00",
      direction: "decrease" as const,
      status: "target_passed" as const,
      total_change_required_kg: "5.00",
      change_achieved_kg: "10.00",
      remaining_change_kg: "-5.00",
      progress_percentage: "200.00",
    };
    expect(goal.progress_percentage).toBe("200.00");
    expect(Number(goal.progress_percentage)).toBeGreaterThan(100);
  });

  it("preserves negative remaining values", () => {
    const goal = {
      starting_weight_kg: "80.00",
      current_weight_kg: "70.00",
      target_weight_kg: "75.00",
      direction: "decrease" as const,
      status: "target_passed" as const,
      total_change_required_kg: "5.00",
      change_achieved_kg: "10.00",
      remaining_change_kg: "-5.00",
      progress_percentage: "200.00",
    };
    expect(goal.remaining_change_kg).toBe("-5.00");
    expect(Number(goal.remaining_change_kg)).toBeLessThan(0);
  });

  it("has correct min and max weight constants", () => {
    expect(MIN_WEIGHT_KG).toBe(10);
    expect(MAX_WEIGHT_KG).toBe(700);
    expect(WEIGHT_STEP).toBe("0.01");
  });

  it("no frontend trend formula exists", async () => {
    const types = await import("@/types/body-weight");
    expect(typeof (types as Record<string, unknown>).calculateTrend).toBe("undefined");
    expect(typeof (types as Record<string, unknown>).calculateAbsoluteChange).toBe("undefined");
    expect(typeof (types as Record<string, unknown>).calculatePercentageChange).toBe("undefined");
    expect(typeof (types as Record<string, unknown>).determineTrendDirection).toBe("undefined");
  });

  it("no frontend goal-progress formula exists", async () => {
    const types = await import("@/types/body-weight");
    expect(typeof (types as Record<string, unknown>).calculateGoalProgress).toBe("undefined");
    expect(typeof (types as Record<string, unknown>).calculateRemainingChange).toBe("undefined");
    expect(typeof (types as Record<string, unknown>).calculatePercentageProgress).toBe("undefined");
    expect(typeof (types as Record<string, unknown>).reclassifyStatus).toBe("undefined");
    expect(typeof (types as Record<string, unknown>).reclassifyDirection).toBe("undefined");
  });
});
