"use client";

import { Target } from "lucide-react";
import Link from "next/link";
import { Card } from "@/components/ui/card";
import { SectionHeader } from "@/components/ui/section-header";
import { ErrorState } from "@/components/ui/error-state";
import { EmptyState } from "@/components/ui/empty-state";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { formatDecimal } from "@/lib/format";
import {
  GOAL_DIRECTION_LABELS,
  GOAL_STATUS_LABELS,
} from "@/types/body-weight";
import type {
  BodyWeightGoalProgressData,
  GoalStatus,
} from "@/types/body-weight";

interface BodyWeightGoalProgressCardProps {
  goalProgress: BodyWeightGoalProgressData | null;
  goalStatus: GoalStatus;
  goalError: string | null;
  onRetry: () => void;
}

export function BodyWeightGoalProgressCard({
  goalProgress,
  goalStatus,
  goalError,
  onRetry,
}: BodyWeightGoalProgressCardProps) {
  if (goalStatus === "loading") {
    return (
      <Card>
        <SectionHeader title="Goal Progress" />
        <div className="space-y-3" role="status" aria-label="Loading goal progress">
          <div className="grid grid-cols-2 gap-3">
            {Array.from({ length: 4 }).map((_, i) => (
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

  if (goalStatus === "missing_profile") {
    return (
      <Card>
        <SectionHeader title="Goal Progress" />
        <EmptyState
          icon={<Target className="h-8 w-8" aria-hidden="true" />}
          title="Nutrition profile required"
          description="Set up your nutrition profile to track weight goal progress."
          action={
            <Link href="/nutrition">
              <Button variant="primary" size="sm">
                Go to Nutrition
              </Button>
            </Link>
          }
        />
      </Card>
    );
  }

  if (goalStatus === "missing_current_weight") {
    return (
      <Card>
        <SectionHeader title="Goal Progress" />
        <EmptyState
          icon={<Target className="h-8 w-8" aria-hidden="true" />}
          title="Current weight required"
          description="Add at least one body-weight entry to see goal progress."
        />
      </Card>
    );
  }

  if (goalStatus === "invalid_goal") {
    return (
      <Card>
        <SectionHeader title="Goal Progress" />
        <EmptyState
          icon={<Target className="h-8 w-8" aria-hidden="true" />}
          title="Goal configuration issue"
          description="Your starting and target weight are the same. Update your nutrition profile to set a target."
          action={
            <Link href="/nutrition">
              <Button variant="secondary" size="sm">
                Edit Nutrition Profile
              </Button>
            </Link>
          }
        />
      </Card>
    );
  }

  if (goalStatus === "error") {
    return (
      <Card>
        <SectionHeader title="Goal Progress" />
        <ErrorState
          title="Failed to load goal progress"
          message={goalError ?? "An unexpected error occurred."}
          action={
            <Button variant="secondary" size="sm" onClick={onRetry}>
              Retry
            </Button>
          }
        />
      </Card>
    );
  }

  if (!goalProgress) return null;

  const directionLabel = GOAL_DIRECTION_LABELS[goalProgress.direction];
  const statusLabel = GOAL_STATUS_LABELS[goalProgress.status];
  const percentage = Number(goalProgress.progress_percentage);

  const barWidth = Math.max(0, Math.min(100, percentage));

  return (
    <Card>
      <SectionHeader title="Goal Progress" />
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
        <div className="text-center">
          <p className="text-sm text-[var(--color-text-muted)]">Starting</p>
          <p className="mt-1 text-xl font-bold text-[var(--color-text-primary)]">
            {formatDecimal(goalProgress.starting_weight_kg)} kg
          </p>
        </div>
        <div className="text-center">
          <p className="text-sm text-[var(--color-text-muted)]">Current</p>
          <p className="mt-1 text-xl font-bold text-[var(--color-text-primary)]">
            {formatDecimal(goalProgress.current_weight_kg)} kg
          </p>
        </div>
        <div className="text-center">
          <p className="text-sm text-[var(--color-text-muted)]">Target</p>
          <p className="mt-1 text-xl font-bold text-[var(--color-text-primary)]">
            {formatDecimal(goalProgress.target_weight_kg)} kg
          </p>
        </div>
        <div className="text-center">
          <p className="text-sm text-[var(--color-text-muted)]">Direction</p>
          <p className="mt-1 text-sm font-medium text-[var(--color-text-primary)]">
            {directionLabel}
          </p>
        </div>
        <div className="text-center">
          <p className="text-sm text-[var(--color-text-muted)]">Status</p>
          <p className="mt-1 text-sm font-medium text-[var(--color-text-primary)]">
            {statusLabel}
          </p>
        </div>
        <div className="text-center">
          <p className="text-sm text-[var(--color-text-muted)]">Required</p>
          <p className="mt-1 text-xl font-bold text-[var(--color-text-primary)]">
            {formatDecimal(goalProgress.total_change_required_kg)} kg
          </p>
        </div>
        <div className="text-center">
          <p className="text-sm text-[var(--color-text-muted)]">Achieved</p>
          <p className="mt-1 text-xl font-bold text-[var(--color-text-primary)]">
            {formatDecimal(goalProgress.change_achieved_kg)} kg
          </p>
        </div>
        <div className="text-center">
          <p className="text-sm text-[var(--color-text-muted)]">Remaining</p>
          <p className="mt-1 text-xl font-bold text-[var(--color-text-primary)]">
            {formatDecimal(goalProgress.remaining_change_kg)} kg
          </p>
        </div>
        <div className="text-center">
          <p className="text-sm text-[var(--color-text-muted)]">Progress</p>
          <p className="mt-1 text-xl font-bold text-[var(--color-text-primary)]">
            {formatDecimal(goalProgress.progress_percentage)}%
          </p>
        </div>
      </div>

      <div className="mt-4">
        <div className="h-2.5 w-full rounded-full bg-[var(--color-border)] overflow-hidden">
          <div
            className="h-full rounded-full bg-[var(--color-brand)] transition-all duration-300"
            style={{ width: `${barWidth}%` }}
            role="progressbar"
            aria-valuenow={percentage}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-label={`${percentage.toFixed(1)}% progress toward goal`}
          />
        </div>
      </div>
    </Card>
  );
}
