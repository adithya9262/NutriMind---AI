import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { FormField } from "@/components/ui/form-field";
import { Input } from "@/components/ui/input";

describe("FormField", () => {
  it("renders label and children", () => {
    render(
      <FormField label="Email" htmlFor="email">
        <Input id="email" aria-label="Email" />
      </FormField>
    );
    expect(screen.getByText("Email")).toBeInTheDocument();
    expect(screen.getByRole("textbox")).toBeInTheDocument();
  });

  it("shows required indicator", () => {
    render(
      <FormField label="Email" required>
        <Input aria-label="Email" />
      </FormField>
    );
    expect(screen.getByText("*")).toBeInTheDocument();
  });

  it("displays error message", () => {
    render(
      <FormField label="Email" error="Email is required.">
        <Input aria-label="Email" />
      </FormField>
    );
    expect(screen.getByText("Email is required.")).toBeInTheDocument();
  });
});
