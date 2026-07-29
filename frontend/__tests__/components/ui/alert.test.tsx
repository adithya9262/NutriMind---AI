import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { Alert } from "@/components/ui/alert";

describe("Alert", () => {
  it("renders children", () => {
    render(<Alert>Message</Alert>);
    expect(screen.getByRole("alert")).toHaveTextContent("Message");
  });

  it("applies error variant", () => {
    render(<Alert variant="error">Error</Alert>);
    const alert = screen.getByRole("alert");
    expect(alert.className).toContain("bg-error-light");
  });
});
