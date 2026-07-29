import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { Textarea } from "@/components/ui/textarea";

describe("Textarea", () => {
  it("renders and accepts value", () => {
    render(<Textarea aria-label="Notes" defaultValue="Hello" />);
    const textarea = screen.getByRole("textbox");
    expect(textarea).toHaveValue("Hello");
  });

  it("supports disabled state", () => {
    render(<Textarea aria-label="Disabled" disabled />);
    expect(screen.getByRole("textbox")).toBeDisabled();
  });
});
