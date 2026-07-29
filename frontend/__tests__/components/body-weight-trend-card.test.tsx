import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { BodyWeightTrendCard } from "@/components/body-weight-trend-card";
import type { BodyWeightTrendData, TrendStatus } from "@/types/body-weight";

const MOCK_TREND: BodyWeightTrendData = {
  observation_count: 3,
  first_logged_date: "2026-07-01",
  latest_logged_date: "2026-07-12",
  starting_weight_kg: "71.00",
  latest_weight_kg: "70.00",
  absolute_change_kg: "-1.00",
  percentage_change: "-1.41",
  direction: "decreased",
};

function renderCard(
  trend: BodyWeightTrendData | null,
  trendStatus: TrendStatus,
  trendError: string | null = null,
  onRetry = vi.fn()
) {
  return render(
    <BodyWeightTrendCard
      trend={trend}
      trendStatus={trendStatus}
      trendError={trendError}
      onRetry={onRetry}
    />
  );
}

describe("BodyWeightTrendCard", () => {
  it("shows loading state", () => {
    renderCard(null, "loading");
    expect(screen.getByRole("status", { name: /loading weight trend/i })).toBeInTheDocument();
  });

  it("shows success state", () => {
    renderCard(MOCK_TREND, "available");
    expect(screen.getByText("3")).toBeInTheDocument();
    expect(screen.getByText(/decreased/i)).toBeInTheDocument();
    expect(screen.getByText(/-1\.0\s*kg/i)).toBeInTheDocument();
    expect(screen.getByText(/-1\.4%/i)).toBeInTheDocument();
  });

  it("shows insufficient-history state", () => {
    renderCard(null, "insufficient");
    expect(screen.getByText(/at least two body-weight entries/i)).toBeInTheDocument();
  });

  it("shows error state", () => {
    renderCard(null, "error", "Something went wrong");
    expect(screen.getByText(/something went wrong/i)).toBeInTheDocument();
  });

  it("shows retry button on error", () => {
    const onRetry = vi.fn();
    renderCard(null, "error", "Error", onRetry);
    expect(screen.getByRole("button", { name: /retry/i })).toBeInTheDocument();
  });

  it("shows observation count", () => {
    renderCard(MOCK_TREND, "available");
    expect(screen.getByText("3")).toBeInTheDocument();
  });

  it("shows starting weight", () => {
    renderCard(MOCK_TREND, "available");
    expect(screen.getByText(/71\.0\s*kg/i)).toBeInTheDocument();
  });

  it("shows latest weight", () => {
    renderCard(MOCK_TREND, "available");
    expect(screen.getByText(/70\.0\s*kg/i)).toBeInTheDocument();
  });

  it("shows direction label", () => {
    renderCard(MOCK_TREND, "available");
    expect(screen.getByText(/decreased/i)).toBeInTheDocument();
  });

  it("preserves positive change", () => {
    const inc = { ...MOCK_TREND, absolute_change_kg: "2.00", percentage_change: "2.82", direction: "increased" as const };
    renderCard(inc, "available");
    expect(screen.getByText(/2\.0\s*kg/i)).toBeInTheDocument();
  });

  it("preserves zero change", () => {
    const stable = { ...MOCK_TREND, absolute_change_kg: "0.00", percentage_change: "0.00", direction: "stable" as const };
    renderCard(stable, "available");
    expect(screen.getByText("0.0 kg")).toBeInTheDocument();
  });

  it("does not render when null and not loading/error/insufficient", () => {
    const { container } = renderCard(null, "idle");
    expect(container.innerHTML).toBe("");
  });

  it("no trend recalculation", async () => {
    const types = await import("@/types/body-weight");
    expect(typeof (types as Record<string, unknown>).calculateTrend).toBe("undefined");
  });

  it("no health interpretation", () => {
    renderCard(MOCK_TREND, "available");
    expect(screen.queryByText(/good/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/bad/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/healthy/i)).not.toBeInTheDocument();
  });

  it("no recommendation", () => {
    renderCard(MOCK_TREND, "available");
    expect(screen.queryByText(/should/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/recommend/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/try to/i)).not.toBeInTheDocument();
  });

  it("no prediction", () => {
    renderCard(MOCK_TREND, "available");
    expect(screen.queryByText(/will/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/predict/i)).not.toBeInTheDocument();
  });

  it("no fake chart", () => {
    renderCard(MOCK_TREND, "available");
    expect(screen.queryByRole("img")).not.toBeInTheDocument();
  });

  it("no reclassification of direction", async () => {
    const types = await import("@/types/body-weight");
    expect(typeof (types as Record<string, unknown>).reclassifyTrendDirection).toBe("undefined");
  });
});
