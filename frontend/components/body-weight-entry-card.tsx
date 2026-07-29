"use client";

import { Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { formatDate } from "@/lib/format";
import { formatDecimal } from "@/lib/format";
import type { BodyWeightEntryData } from "@/types/body-weight";

interface BodyWeightEntryCardProps {
  entry: BodyWeightEntryData;
  onDelete: (entryId: string) => void;
  deleting?: boolean;
}

export function BodyWeightEntryCard({
  entry,
  onDelete,
  deleting,
}: BodyWeightEntryCardProps) {
  return (
    <div className="flex items-center justify-between py-3 px-4 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)]">
      <div className="flex flex-col sm:flex-row sm:items-center sm:gap-4">
        <span className="text-sm font-medium text-[var(--color-text-primary)]">
          {formatDate(entry.logged_date)}
        </span>
        <span className="text-sm text-[var(--color-text-secondary)]">
          {formatDecimal(entry.weight_kg)} kg
        </span>
      </div>
      <Button
        variant="ghost"
        size="sm"
        onClick={() => onDelete(entry.entry_id)}
        disabled={deleting}
        aria-label={`Delete weight entry for ${formatDate(entry.logged_date)}`}
      >
        <Trash2 className="h-4 w-4" aria-hidden="true" />
      </Button>
    </div>
  );
}
