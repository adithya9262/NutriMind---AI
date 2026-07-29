"use client";

import { AlertCircle } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import type { TaskData } from "@/types/tasks";

interface TaskDeleteConfirmProps {
  task: TaskData;
  deleting: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

export function TaskDeleteConfirm({
  task,
  deleting,
  onConfirm,
  onCancel,
}: TaskDeleteConfirmProps) {
  return (
    <Card
      role="dialog"
      aria-modal="true"
      aria-label="Confirm delete"
      className="border-[var(--color-error)]"
    >
      <div className="flex items-start gap-3">
        <AlertCircle
          className="h-5 w-5 text-[var(--color-error)] mt-0.5 shrink-0"
          aria-hidden="true"
        />
        <div className="flex-1">
          <p className="text-sm font-medium text-[var(--color-text-primary)]">
            Delete task?
          </p>
          <p className="text-sm text-[var(--color-text-secondary)] mt-1">
            This will permanently delete &ldquo;{task.title}&rdquo;. This
            action cannot be undone.
          </p>
          <div className="flex gap-2 mt-3">
            <Button
              variant="secondary"
              size="sm"
              onClick={onCancel}
              disabled={deleting}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={onConfirm}
              disabled={deleting}
              className="bg-[var(--color-error)] hover:bg-[var(--color-error)]"
            >
              {deleting ? "Deleting..." : "Delete"}
            </Button>
          </div>
        </div>
      </div>
    </Card>
  );
}
