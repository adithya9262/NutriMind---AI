"use client";

import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { Spinner } from "@/components/ui/spinner";
import { Alert } from "@/components/ui/alert";
import { SectionHeader } from "@/components/ui/section-header";
import { ClipboardList } from "lucide-react";
import { NutritionLogEntryCard } from "@/components/food-diary/meal-entry-card";
import type { NutritionLogEntryData, EntryReadStatus, DeleteStatus } from "@/types/nutrition";

interface NutritionLogEntryListProps {
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
}

export function NutritionLogEntryList({
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
}: NutritionLogEntryListProps) {
  return (
    <section aria-labelledby="entries-heading">
      <SectionHeader
        title="Daily Entries"
        description="Your logged food entries for the selected date."
      />

      {status === "loading" && (
        <div className="flex items-center justify-center py-8" role="status" aria-label="Loading entries">
          <Spinner size="lg" />
        </div>
      )}

      {status === "error" && (
        <Alert variant="error">
          <p>{error || "Failed to load entries."}</p>
          <Button variant="secondary" size="sm" className="mt-2" onClick={onRetry}>
            Retry
          </Button>
        </Alert>
      )}

      {status === "empty" && (
        <Card>
          <EmptyState
            icon={<ClipboardList className="h-8 w-8" aria-hidden="true" />}
            title="No entries logged"
            description="Add your first food entry for this date using the form above."
          />
        </Card>
      )}

      {status === "available" && (
        <div className="space-y-3" role="list" aria-label="Nutrition log entries">
          {entries.map((entry) => (
            <NutritionLogEntryCard
              key={entry.entry_id}
              entry={entry}
              isDeleting={deleteStatus === "deleting" && deletingEntryId === entry.entry_id}
              isConfirming={deleteStatus === "confirming" && deletingEntryId === entry.entry_id}
              deleteError={deleteStatus === "error" && deletingEntryId === entry.entry_id ? deleteError : null}
              onDelete={() => onDelete(entry.entry_id)}
              onCancelDelete={onCancelDelete}
              onConfirmDelete={onConfirmDelete}
            />
          ))}
        </div>
      )}
    </section>
  );
}

