import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { Skeleton } from "@/components/ui/skeleton";

describe("Skeleton", () => {
  it("renders with loading label", () => {
    render(<Skeleton />);
    expect(screen.getByLabelText("Loading")).toBeInTheDocument();
  });

  it("applies variant classes", () => {
    render(<Skeleton variant="circular" />);
    const skeleton = screen.getByRole("status");
    expect(skeleton.className).toContain("rounded-full");
  });
});
