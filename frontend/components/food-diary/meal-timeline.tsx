"use client";

import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Alert } from "@/components/ui/alert";
import { Spinner } from "@/components/ui/spinner";
import { EmptyState } from "@/components/ui/empty-state";
import { NutritionLogEntryCard } from "./meal-entry-card";
import { MEAL_TYPE_LABELS, MEAL_TYPE_ORDER } from "@/types/nutrition";
import type {
  NutritionLogEntryData,
  MealType,
  EntryReadStatus,
  DeleteStatus,
} from "@/types/nutrition";
import { Plus, Sunrise, Sun, Moon, Cookie, ClipboardList } from "lucide-react";
import { cn } from "@/lib/utils";

interface MealTimelineProps {
  entries: NutritionLogEntryData[];
  status: EntryReadStatus;
  error: string | null;
  deleteStatus: DeleteStatus;
  deletingEntryId: string | null;
  deleteError: string | null;
  onDelete: (entryId: string) => void;
  onCancelDelete: () => void;
  onConfirmDelete: () => Promise<void>;
  onRetry: () => void;
  onAddMeal?: (mealType: MealType) => void;
  onDuplicate?: (entry: NutritionLogEntryData) => void;
}

const MEAL_ICONS: Record<MealType, typeof Sunrise> = {
  breakfast: Sunrise,
  lunch: Sun,
  dinner: Moon,
  snack: Cookie,
};

export function MealTimeline({
  entries,
  status,
  error,
  deleteStatus,
  deletingEntryId,
  deleteError,
  onDelete,
  onCancelDelete,
  onConfirmDelete,
  onRetry,
  onAddMeal,
  onDuplicate,
}: MealTimelineProps) {
  if (status === "loading") {
    return (
      <div className="flex items-center justify-center py-8" role="status" aria-label="Loading entries">
        <Spinner size="lg" />
      </div>
    );
  }

  if (status === "error") {
    return (
      <Alert variant="error">
        <p>{error || "Failed to load entries."}</p>
        <Button variant="secondary" size="sm" className="mt-2" onClick={onRetry}>
          Retry
        </Button>
      </Alert>
    );
  }

  if (status === "empty") {
    return (
      <Card>
        <EmptyState
          icon={<ClipboardList className="h-8 w-8" aria-hidden="true" />}
          title="No entries logged"
          description="Add your first food entry for this date using the form above."
        />
      </Card>
    );
  }

  return (
    <div className="relative space-y-8">
      {MEAL_TYPE_ORDER.map((mealType) => {
        const Icon = MEAL_ICONS[mealType];
        const mealEntries = entries.filter((e) => e.meal_type === mealType);
        const isEmpty = mealEntries.length === 0;

        return (
          <div key={mealType} className="relative flex gap-4 items-start">
            <div
              className={cn(
                "z-10 grid h-10 w-10 flex-shrink-0 place-items-center rounded-full border",
                isEmpty
                  ? "border-border bg-surface-low opacity-50"
                  : "border-brand-primary/40 bg-brand-primary/15 text-brand-primary",
              )}
            >
              <Icon className="h-5 w-5" aria-hidden="true" />
            </div>

            <div className="flex-1">
              <div className="mb-3 flex items-center justify-between">
                <h3
                  className={cn(
                    "text-base font-semibold",
                    isEmpty ? "text-primary-muted" : "text-primary",
                  )}
                >
                  {MEAL_TYPE_LABELS[mealType]} Phase
                </h3>
                {onAddMeal && (
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-brand-primary"
                    onClick={() => onAddMeal(mealType)}
                  >
                    <Plus className="h-4 w-4" aria-hidden="true" />
                    Log Meal Protocol
                  </Button>
                )}
              </div>

              {isEmpty ? (
                <div className="flex flex-col items-center justify-center gap-2 rounded-2xl border border-dashed border-border bg-surface-low p-6 text-center">
                  <div className="grid h-12 w-12 place-items-center rounded-full bg-surface text-primary-muted">
                    <ClipboardList className="h-6 w-6" aria-hidden="true" />
                  </div>
                  <p className="text-sm text-primary-muted">Awaiting nutritional data input…</p>
                </div>
              ) : (
                <div className="space-y-3" role="list" aria-label={`${MEAL_TYPE_LABELS[mealType]} entries`}>
                  {mealEntries.map((entry) => (
                    <NutritionLogEntryCard
                      key={entry.entry_id}
                      entry={entry}
                      isDeleting={deleteStatus === "deleting" && deletingEntryId === entry.entry_id}
                      isConfirming={deleteStatus === "confirming" && deletingEntryId === entry.entry_id}
                      deleteError={
                        deleteStatus === "error" && deletingEntryId === entry.entry_id ? deleteError : null
                      }
                      onDelete={() => onDelete(entry.entry_id)}
                      onCancelDelete={onCancelDelete}
                      onConfirmDelete={onConfirmDelete}
                      onDuplicate={onDuplicate}
                    />
                  ))}
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
