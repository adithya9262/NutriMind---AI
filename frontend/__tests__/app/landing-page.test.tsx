import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import HomePage from "@/app/page";

describe("LandingPage", () => {
  it("renders the hero heading", () => {
    render(<HomePage />);
    expect(
      screen.getByRole("heading", {
        level: 1,
        name: /Understand Your Nutrition\. Build Better Habits\./i,
      }),
    ).toBeInTheDocument();
  });

  it("renders Get started button", () => {
    render(<HomePage />);
    expect(screen.getAllByRole("link", { name: /Get Started/i }).length).toBeGreaterThan(0);
  });

  it("renders Sign in button", () => {
    render(<HomePage />);
    const signInButtons = screen.getAllByText("Sign in");
    expect(signInButtons.length).toBeGreaterThanOrEqual(1);
  });

  it("does not contain medical claims", () => {
    render(<HomePage />);
    const text = document.body.textContent || "";
    expect(text.toLowerCase()).not.toContain("diagnosis");
    expect(text.toLowerCase()).not.toContain("guaranteed");
    expect(text.toLowerCase()).not.toContain("disease");
  });

  it("has semantic heading hierarchy", () => {
    render(<HomePage />);
    expect(screen.getByRole("heading", { level: 1 })).toBeInTheDocument();
  });

  it("renders the product description", () => {
    render(<HomePage />);
    expect(screen.getByText(/Track meals, nutrition goals, body weight and daily habits/i)).toBeInTheDocument();
  });
});
