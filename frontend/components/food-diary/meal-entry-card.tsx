"use client";

import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Alert } from "@/components/ui/alert";
import { Copy, Trash2 } from "lucide-react";
import { formatDecimal } from "@/lib/format";
import { MEAL_TYPE_LABELS } from "@/types/nutrition";
import type { NutritionLogEntryData } from "@/types/nutrition";

interface NutritionLogEntryCardProps {
  entry: NutritionLogEntryData;
  isDeleting: boolean;
  isConfirming: boolean;
  deleteError: string | null;
  onDelete: () => void;
  onCancelDelete: () => void;
  onConfirmDelete: () => Promise<void>;
  onDuplicate?: (entry: NutritionLogEntryData) => void;
}

export function NutritionLogEntryCard({
  entry,
  isDeleting,
  isConfirming,
  deleteError,
  onDelete,
  onCancelDelete,
  onConfirmDelete,
  onDuplicate,
}: NutritionLogEntryCardProps) {
  return (
    <Card role="listitem" className={isDeleting ? "opacity-50" : ""}>
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <p className="font-medium text-primary truncate">
              {entry.food_name}
            </p>
            <Badge variant="info">{MEAL_TYPE_LABELS[entry.meal_type]}</Badge>
          </div>
          {entry.serving_description && (
            <p className="mt-0.5 text-sm text-primary-muted truncate">
              {entry.serving_description}
            </p>
          )}
          <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-sm text-primary-secondary">
            <span>{formatDecimal(entry.calories_kcal)} kcal</span>
            <span>P: {formatDecimal(entry.protein_g)}g</span>
            <span>C: {formatDecimal(entry.carbohydrate_g)}g</span>
            <span>F: {formatDecimal(entry.fat_g)}g</span>
          </div>
        </div>

        <div className="flex-shrink-0 flex items-center gap-1">
          {isConfirming ? (
            <div className="flex items-center gap-2">
              <Button
                size="sm"
                variant="secondary"
                onClick={onCancelDelete}
                disabled={isDeleting}
              >
                Cancel
              </Button>
              <Button
                size="sm"
                variant="primary"
                onClick={onConfirmDelete}
                disabled={isDeleting}
              >
                {isDeleting ? "Deleting..." : "Delete"}
              </Button>
            </div>
          ) : (
            <>
              {onDuplicate && (
                <Button
                  size="sm"
                  variant="ghost"
                  aria-label={`Duplicate ${entry.food_name}`}
                  onClick={() => onDuplicate(entry)}
                  disabled={isDeleting}
                >
                  <Copy className="h-4 w-4" aria-hidden="true" />
                </Button>
              )}
              <Button
                size="sm"
                variant="ghost"
                aria-label={`Delete ${entry.food_name}`}
                onClick={onDelete}
                disabled={isDeleting}
              >
                <Trash2 className="h-4 w-4" aria-hidden="true" />
              </Button>
            </>
          )}
        </div>
      </div>

      {deleteError && (
        <Alert variant="error" className="mt-3">
          {deleteError}
        </Alert>
      )}

      {isConfirming && (
        <p className="mt-2 text-xs text-primary-muted">
          This action cannot be undone.
        </p>
      )}
    </Card>
  );
}
