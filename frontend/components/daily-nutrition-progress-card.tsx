"use client";

import Link from "next/link";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Alert } from "@/components/ui/alert";
import { SectionHeader } from "@/components/ui/section-header";
import { Spinner } from "@/components/ui/spinner";
import { Badge } from "@/components/ui/badge";
import { formatDecimalWhole } from "@/lib/format";
import { PROGRESS_STATUS_LABELS } from "@/types/nutrition";
import type {
  DailyNutritionProgressData,
  NutrientProgressData,
  ProgressReadStatus,
  NutritionProgressStatus,
} from "@/types/nutrition";

const statusBadgeVariants: Record<NutritionProgressStatus, "success" | "warning" | "info"> = {
  below_target: "info",
  target_met: "success",
  above_target: "warning",
};

interface DailyNutritionProgressCardProps {
  progress: DailyNutritionProgressData | null;
  status: ProgressReadStatus;
  error: string | null;
  onRetry: () => void;
}

const NUTRIENT_SECTIONS: { key: keyof DailyNutritionProgressData; label: string; unit: string }[] = [
  { key: "calories", label: "Calories", unit: "kcal" },
  { key: "protein", label: "Protein", unit: "g" },
  { key: "carbohydrate", label: "Carbohydrates", unit: "g" },
  { key: "fat", label: "Fat", unit: "g" },
];

export function DailyNutritionProgressCard({
  progress,
  status,
  error,
  onRetry,
}: DailyNutritionProgressCardProps) {
  return (
    <section aria-labelledby="progress-heading">
      <SectionHeader
        title="Daily Target Progress"
        description="Your progress toward daily nutrition targets."
      />

      {status === "loading" && (
        <div className="flex items-center justify-center py-8" role="status" aria-label="Loading progress">
          <Spinner size="lg" />
        </div>
      )}

      {status === "missing_profile" && (
        <Card>
          <div className="text-center py-4">
            <p className="text-sm text-[var(--color-text-secondary)]">
              Set up your nutrition profile to see daily target progress.
            </p>
            <Link href="/nutrition">
              <Button size="sm" className="mt-3">
                Create Profile
              </Button>
            </Link>
          </div>
        </Card>
      )}

      {status === "error" && (
        <Alert variant="error">
          <p>{error || "Failed to load progress."}</p>
          <Button variant="secondary" size="sm" className="mt-2" onClick={onRetry}>
            Retry
          </Button>
        </Alert>
      )}

      {status === "available" && progress && (
        <div className="space-y-4">
          {NUTRIENT_SECTIONS.map((section) => {
            const nutrient = progress[section.key];
            return (
              <NutrientProgressCard
                key={section.key}
                label={section.label}
                unit={section.unit}
                nutrient={nutrient}
              />
            );
          })}
        </div>
      )}
    </section>
  );
}

interface NutrientProgressCardProps {
  label: string;
  unit: string;
  nutrient: NutrientProgressData;
}

function NutrientProgressCard({ label, unit, nutrient }: NutrientProgressCardProps) {
  const badgeVariant = statusBadgeVariants[nutrient.status] || "info";
  const percentageNum = parseFloat(nutrient.percentage);
  const barWidth = isNaN(percentageNum) ? 0 : Math.min(percentageNum, 100);

  return (
    <Card>
      <div className="flex items-center justify-between gap-2 flex-wrap">
        <p className="font-medium text-[var(--color-text-primary)]">{label}</p>
        <Badge variant={badgeVariant}>{PROGRESS_STATUS_LABELS[nutrient.status]}</Badge>
      </div>

      <div className="mt-3 grid grid-cols-2 sm:grid-cols-4 gap-2 text-sm">
        <div>
          <p className="text-xs text-[var(--color-text-muted)]">Consumed</p>
          <p className="font-medium text-[var(--color-text-primary)]">
            {formatDecimalWhole(nutrient.consumed)} {unit}
          </p>
        </div>
        <div>
          <p className="text-xs text-[var(--color-text-muted)]">Target</p>
          <p className="font-medium text-[var(--color-text-primary)]">
            {formatDecimalWhole(nutrient.target)} {unit}
          </p>
        </div>
        <div>
          <p className="text-xs text-[var(--color-text-muted)]">Remaining</p>
          <p className="font-medium text-[var(--color-text-primary)]">
            {formatDecimalWhole(nutrient.remaining)} {unit}
          </p>
        </div>
        <div>
          <p className="text-xs text-[var(--color-text-muted)]">Progress</p>
          <p className="font-medium text-[var(--color-text-primary)]">
            {nutrient.percentage}%
          </p>
        </div>
      </div>

      <div className="mt-3 h-2 w-full rounded-full bg-[var(--color-border)] overflow-hidden" role="progressbar" aria-valuenow={barWidth} aria-valuemin={0} aria-valuemax={100} aria-label={`${label} progress`}>
        <div
          className="h-full rounded-full bg-[var(--color-brand)] transition-all"
          style={{ width: `${barWidth}%` }}
        />
      </div>
    </Card>
  );
}
