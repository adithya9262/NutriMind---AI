import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { EmptyState } from "@/components/ui/empty-state";

describe("EmptyState", () => {
  it("renders title and description", () => {
    render(
      <EmptyState title="Nothing here" description="Add some data to get started." />
    );
    expect(screen.getByText("Nothing here")).toBeInTheDocument();
    expect(screen.getByText("Add some data to get started.")).toBeInTheDocument();
  });
});
