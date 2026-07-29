"use client";

import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Alert } from "@/components/ui/alert";
import { SectionHeader } from "@/components/ui/section-header";
import { Spinner } from "@/components/ui/spinner";
import { MetricCard } from "@/components/metric-card";
import { formatDecimal, formatDecimalWhole } from "@/lib/format";
import { MEAL_TYPE_LABELS } from "@/types/nutrition";
import type {
  DailyNutritionLogSummaryData,
  SummaryReadStatus,
  MealNutritionSummaryData,
} from "@/types/nutrition";

interface DailyNutritionSummaryCardProps {
  summary: DailyNutritionLogSummaryData | null;
  status: SummaryReadStatus;
  error: string | null;
  onRetry: () => void;
}

export function DailyNutritionSummaryCard({
  summary,
  status,
  error,
  onRetry,
}: DailyNutritionSummaryCardProps) {
  return (
    <section aria-labelledby="summary-heading">
      <SectionHeader
        title="Daily Summary"
        description="Your total nutrient intake for the selected date."
      />

      {status === "loading" && (
        <div className="flex items-center justify-center py-8" role="status" aria-label="Loading summary">
          <Spinner size="lg" />
        </div>
      )}

      {status === "error" && (
        <Alert variant="error">
          <p>{error || "Failed to load summary."}</p>
          <Button variant="secondary" size="sm" className="mt-2" onClick={onRetry}>
            Retry
          </Button>
        </Alert>
      )}

      {status === "available" && summary && (
        <div className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <MetricCard
              label="Calories"
              value={formatDecimalWhole(summary.totals.calories_kcal)}
              unit="kcal"
            />
            <MetricCard
              label="Protein"
              value={formatDecimal(summary.totals.protein_g)}
              unit="g"
            />
            <MetricCard
              label="Carbohydrates"
              value={formatDecimal(summary.totals.carbohydrate_g)}
              unit="g"
            />
            <MetricCard
              label="Fat"
              value={formatDecimal(summary.totals.fat_g)}
              unit="g"
            />
          </div>

          {summary.meals && summary.meals.length > 0 && (
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              {summary.meals.map((meal) => (
                <MealSummaryCard key={meal.meal_type} meal={meal} />
              ))}
            </div>
          )}
        </div>
      )}
    </section>
  );
}

interface MealSummaryCardProps {
  meal: MealNutritionSummaryData;
}

function MealSummaryCard({ meal }: MealSummaryCardProps) {
  const label = MEAL_TYPE_LABELS[meal.meal_type] || meal.meal_type;
  return (
    <Card>
      <p className="text-sm font-medium text-[var(--color-text-primary)]">
        {label}
      </p>
      <p className="text-xs text-[var(--color-text-muted)]">
        {meal.entry_count} {meal.entry_count === 1 ? "entry" : "entries"}
      </p>
      <div className="mt-2 space-y-0.5 text-xs text-[var(--color-text-secondary)]">
        <p>{formatDecimalWhole(meal.totals.calories_kcal)} kcal</p>
        <p>P: {formatDecimal(meal.totals.protein_g)}g</p>
        <p>C: {formatDecimal(meal.totals.carbohydrate_g)}g</p>
        <p>F: {formatDecimal(meal.totals.fat_g)}g</p>
      </div>
    </Card>
  );
}
