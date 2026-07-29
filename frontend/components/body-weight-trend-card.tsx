"use client";

import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import { Card } from "@/components/ui/card";
import { SectionHeader } from "@/components/ui/section-header";
import { ErrorState } from "@/components/ui/error-state";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { formatDecimal, formatDateShort } from "@/lib/format";
import { TREND_DIRECTION_LABELS } from "@/types/body-weight";
import type {
  BodyWeightTrendData,
  TrendStatus,
} from "@/types/body-weight";

interface BodyWeightTrendCardProps {
  trend: BodyWeightTrendData | null;
  trendStatus: TrendStatus;
  trendError: string | null;
  onRetry: () => void;
}

export function BodyWeightTrendCard({
  trend,
  trendStatus,
  trendError,
  onRetry,
}: BodyWeightTrendCardProps) {
  if (trendStatus === "loading") {
    return (
      <Card>
        <SectionHeader title="Weight Trend" />
        <div className="space-y-3" role="status" aria-label="Loading weight trend">
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="space-y-2">
                <Skeleton variant="text" className="h-3 w-16" />
                <Skeleton variant="text" className="h-6 w-20" />
              </div>
            ))}
          </div>
        </div>
      </Card>
    );
  }

  if (trendStatus === "insufficient") {
    return (
      <Card>
        <SectionHeader title="Weight Trend" />
        <p className="text-sm text-[var(--color-text-secondary)]">
          At least two body-weight entries are required to calculate a trend.
        </p>
      </Card>
    );
  }

  if (trendStatus === "error") {
    return (
      <Card>
        <SectionHeader title="Weight Trend" />
        <ErrorState
          title="Failed to load trend"
          message={trendError ?? "An unexpected error occurred."}
          action={
            <Button variant="secondary" size="sm" onClick={onRetry}>
              Retry
            </Button>
          }
        />
      </Card>
    );
  }

  if (!trend) return null;

  const directionIcon = {
    decreased: <TrendingDown className="h-5 w-5" aria-hidden="true" />,
    stable: <Minus className="h-5 w-5" aria-hidden="true" />,
    increased: <TrendingUp className="h-5 w-5" aria-hidden="true" />,
  };

  const directionLabel = TREND_DIRECTION_LABELS[trend.direction];

  return (
    <Card>
      <SectionHeader title="Weight Trend" />
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
        <div className="text-center">
          <p className="text-sm text-[var(--color-text-muted)]">Observations</p>
          <p className="mt-1 text-xl font-bold text-[var(--color-text-primary)]">
            {trend.observation_count}
          </p>
        </div>
        <div className="text-center">
          <p className="text-sm text-[var(--color-text-muted)]">Date Range</p>
          <p className="mt-1 text-sm font-medium text-[var(--color-text-primary)]">
            {formatDateShort(trend.first_logged_date)}
            {" — "}
            {formatDateShort(trend.latest_logged_date)}
          </p>
        </div>
        <div className="text-center">
          <p className="text-sm text-[var(--color-text-muted)]">Starting</p>
          <p className="mt-1 text-xl font-bold text-[var(--color-text-primary)]">
            {formatDecimal(trend.starting_weight_kg)} kg
          </p>
        </div>
        <div className="text-center">
          <p className="text-sm text-[var(--color-text-muted)]">Latest</p>
          <p className="mt-1 text-xl font-bold text-[var(--color-text-primary)]">
            {formatDecimal(trend.latest_weight_kg)} kg
          </p>
        </div>
        <div className="text-center">
          <p className="text-sm text-[var(--color-text-muted)]">Change</p>
          <p className="mt-1 text-xl font-bold text-[var(--color-text-primary)]">
            {formatDecimal(trend.absolute_change_kg)} kg
          </p>
        </div>
        <div className="text-center">
          <p className="text-sm text-[var(--color-text-muted)]">% Change</p>
          <p className="mt-1 text-xl font-bold text-[var(--color-text-primary)]">
            {formatDecimal(trend.percentage_change)}%
          </p>
        </div>
      </div>
      <div className="mt-3 flex items-center justify-center gap-2 text-sm font-medium text-[var(--color-text-primary)]">
        {directionIcon[trend.direction]}
        <span>{directionLabel}</span>
      </div>
    </Card>
  );
}
