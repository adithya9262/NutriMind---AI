import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ErrorState } from "@/components/ui/error-state";

describe("ErrorState", () => {
  it("renders default error message", () => {
    render(<ErrorState title="Something went wrong" />);
    expect(screen.getByText("Something went wrong")).toBeInTheDocument();
    expect(screen.getByText("Something went wrong")).toBeInTheDocument();
  });

  it("renders custom message", () => {
    render(<ErrorState title="Oops" message="Custom error" />);
    expect(screen.getByText("Oops")).toBeInTheDocument();
    expect(screen.getByText("Custom error")).toBeInTheDocument();
  });
});
