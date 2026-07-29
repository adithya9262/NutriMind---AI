import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import type { NutritionSummaryData, NutritionSummaryItemData } from "@/types/nutrition";

const toneStyles: Record<string, string> = {
  informational: "text-[var(--color-text-primary)]",
  caution: "text-[var(--color-warning)]",
};

interface PersonalizedNutritionSummaryProps {
  summary: NutritionSummaryData | null;
  status: "idle" | "loading" | "available" | "error";
  error: string | null;
  onRetry?: () => void;
}

export function PersonalizedNutritionSummary({
  summary,
  status,
  error,
  onRetry,
}: PersonalizedNutritionSummaryProps) {
  if (status === "idle") return null;
  if (status === "loading") {
    return (
      <div className="space-y-3">
        <Skeleton variant="text" className="h-4 w-3/4" />
        <Skeleton variant="text" className="h-4 w-1/2" />
        <Skeleton variant="text" className="h-4 w-2/3" />
        <Skeleton variant="text" className="h-4 w-3/5" />
      </div>
    );
  }
  if (status === "error") {
    return (
      <Card>
        <div className="text-center py-4">
          <p className="text-sm text-[var(--color-error)]">{error || "Failed to load summary."}</p>
          {onRetry && (
            <Button variant="secondary" size="sm" className="mt-2" onClick={onRetry}>
              Retry
            </Button>
          )}
        </div>
      </Card>
    );
  }
  if (!summary) return null;
  return (
    <div className="space-y-4">
      <Card>
        <p className="text-sm text-[var(--color-text-primary)] leading-relaxed">
          {summary.overview}
        </p>
      </Card>
      <div className="grid gap-3">
        {summary.items.map((item) => (
          <NutritionSummaryItemCard key={item.code} item={item} />
        ))}
      </div>
    </div>
  );
}

interface NutritionSummaryItemCardProps {
  item: NutritionSummaryItemData;
}

function NutritionSummaryItemCard({ item }: NutritionSummaryItemCardProps) {
  const toneClass = toneStyles[item.tone] || "text-[var(--color-text-primary)]";
  return (
    <Card>
      <h3 className={`text-sm font-semibold ${toneClass}`}>{item.title}</h3>
      <p className="mt-1 text-sm text-[var(--color-text-secondary)] leading-relaxed">
        {item.message}
      </p>
    </Card>
  );
}