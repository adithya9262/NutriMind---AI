"use client";

import { Weight } from "lucide-react";
import { BodyWeightEntryCard } from "@/components/body-weight-entry-card";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import type { BodyWeightEntryData, DeleteStatus } from "@/types/body-weight";

interface BodyWeightHistoryListProps {
  entries: BodyWeightEntryData[];
  historyStatus: "loading" | "available" | "empty" | "error";
  historyError: string | null;
  deleteStatus: DeleteStatus;
  deletingEntryId: string | null;
  onDelete: (entryId: string) => void;
  onRetry: () => void;
}

export function BodyWeightHistoryList({
  entries,
  historyStatus,
  historyError,
  deleteStatus,
  deletingEntryId,
  onDelete,
  onRetry,
}: BodyWeightHistoryListProps) {
  if (historyStatus === "loading") {
    return (
      <div className="space-y-2" role="status" aria-label="Loading weight history">
        {Array.from({ length: 3 }).map((_, i) => (
          <Skeleton key={i} variant="rectangular" className="h-14" />
        ))}
      </div>
    );
  }

  if (historyStatus === "error") {
    return (
      <ErrorState
        title="Failed to load weight history"
        message={historyError ?? "An unexpected error occurred."}
        action={
          <Button variant="secondary" size="sm" onClick={onRetry}>
            Retry
          </Button>
        }
      />
    );
  }

  if (historyStatus === "empty") {
    return (
      <EmptyState
        icon={<Weight className="h-8 w-8" aria-hidden="true" />}
        title="No weight entries yet"
        description="Add your first weight entry using the form above."
      />
    );
  }

  return (
    <div className="space-y-2" role="list" aria-label="Weight history entries">
      {entries.map((entry) => (
        <BodyWeightEntryCard
          key={entry.entry_id}
          entry={entry}
          onDelete={onDelete}
          deleting={
            deleteStatus === "deleting" && deletingEntryId === entry.entry_id
          }
        />
      ))}
    </div>
  );
}
