import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { BodyWeightHistoryList } from "@/components/body-weight-history-list";
import type { BodyWeightEntryData, DeleteStatus } from "@/types/body-weight";

const MOCK_ENTRIES: BodyWeightEntryData[] = [
  { entry_id: "e1", logged_date: "2026-07-12", weight_kg: "70.00" },
  { entry_id: "e2", logged_date: "2026-07-11", weight_kg: "71.00" },
];

function renderList(
  entries: BodyWeightEntryData[],
  historyStatus: "loading" | "available" | "empty" | "error",
  historyError: string | null = null,
  deleteStatus: DeleteStatus = "idle",
  deletingEntryId: string | null = null,
  onDelete = vi.fn(),
  onRetry = vi.fn()
) {
  return render(
    <BodyWeightHistoryList
      entries={entries}
      historyStatus={historyStatus}
      historyError={historyError}
      deleteStatus={deleteStatus}
      deletingEntryId={deletingEntryId}
      onDelete={onDelete}
      onRetry={onRetry}
    />
  );
}

describe("BodyWeightHistoryList", () => {
  it("shows loading state", () => {
    renderList([], "loading");
    expect(screen.getByRole("status", { name: /loading weight history/i })).toBeInTheDocument();
  });

  it("shows empty state", () => {
    renderList([], "empty");
    expect(screen.getByText(/no weight entries yet/i)).toBeInTheDocument();
  });

  it("shows error state", () => {
    renderList([], "error", "Failed to load");
    expect(screen.getByText(/failed to load weight history/i)).toBeInTheDocument();
  });

  it("shows retry button on error", () => {
    const onRetry = vi.fn();
    renderList([], "error", "Error", "idle", null, vi.fn(), onRetry);
    expect(screen.getByRole("button", { name: /retry/i })).toBeInTheDocument();
  });

  it("renders entries when available", () => {
    renderList(MOCK_ENTRIES, "available");
    expect(screen.getByText("12 July 2026")).toBeInTheDocument();
    expect(screen.getByText("11 July 2026")).toBeInTheDocument();
  });

  it("renders delete button for each entry", () => {
    renderList(MOCK_ENTRIES, "available");
    const deleteButtons = screen.getAllByRole("button", { name: /delete weight entry/i });
    expect(deleteButtons).toHaveLength(2);
  });

  it("no edit action", () => {
    renderList(MOCK_ENTRIES, "available");
    expect(screen.queryByRole("button", { name: /edit/i })).not.toBeInTheDocument();
  });
});
