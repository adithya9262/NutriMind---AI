import { Card } from "@/components/ui/card";
import { MetricCard } from "@/components/metric-card";
import { Button } from "@/components/ui/button";
import { formatDecimal, formatDecimalWhole } from "@/lib/format";
import { BMI_CATEGORY_LABELS } from "@/types/nutrition";
import type { NutritionMetricsData, NutritionTargetsData } from "@/types/nutrition";

interface NutritionCalculationsCardProps {
  metrics: NutritionMetricsData | null;
  targets: NutritionTargetsData | null;
  status: "idle" | "loading" | "available" | "error";
  error: string | null;
  onRetry?: () => void;
}

export function NutritionCalculationsCard({
  metrics,
  targets,
  status,
  error,
  onRetry,
}: NutritionCalculationsCardProps) {
  if (status === "idle") return null;
  if (status === "loading") {
    return (
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Card key={i} className="text-center">
            <div className="h-4 w-20 mx-auto mb-2 rounded bg-[var(--color-border)] animate-pulse" />
            <div className="h-8 w-16 mx-auto rounded bg-[var(--color-border)] animate-pulse" />
          </Card>
        ))}
      </div>
    );
  }
  if (status === "error") {
    return (
      <Card>
        <div className="text-center py-4">
          <p className="text-sm text-[var(--color-error)]">{error || "Failed to load calculations."}</p>
          {onRetry && (
            <Button variant="secondary" size="sm" className="mt-2" onClick={onRetry}>
              Retry
            </Button>
          )}
        </div>
      </Card>
    );
  }
  if (!metrics || !targets) return null;
  const bmiLabel = BMI_CATEGORY_LABELS[metrics.bmi_category] || metrics.bmi_category;
  return (
    <div className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard label="BMI" value={formatDecimal(metrics.bmi)} unit={bmiLabel} />
        <MetricCard label="BMR" value={formatDecimalWhole(metrics.bmr_kcal_per_day)} unit="kcal/day" />
        <MetricCard label="TDEE" value={formatDecimalWhole(metrics.tdee_kcal_per_day)} unit="kcal/day" />
        <MetricCard label="Calorie Target" value={formatDecimalWhole(targets.calorie_target_kcal_per_day)} unit="kcal/day" />
      </div>
      <div className="grid gap-4 sm:grid-cols-3">
        <MetricCard label="Protein" value={formatDecimal(targets.protein_g_per_day)} unit="g/day" />
        <MetricCard label="Carbohydrates" value={formatDecimal(targets.carbohydrate_g_per_day)} unit="g/day" />
        <MetricCard label="Fat" value={formatDecimal(targets.fat_g_per_day)} unit="g/day" />
      </div>
    </div>
  );
}