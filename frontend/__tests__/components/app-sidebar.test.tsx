import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { Sidebar } from "@/components/layout/sidebar";

vi.mock("next/navigation", () => ({
  usePathname: () => "/dashboard",
}));

vi.mock("@/contexts/auth-context", () => ({
  useAuth: () => ({
    user: { email: "test@example.com" },
    logout: vi.fn(),
  }),
}));

describe("AppSidebar", () => {
  it("renders navigation links", () => {
    render(<Sidebar />);
    expect(screen.getByText("Dashboard")).toBeInTheDocument();
    expect(screen.getByText("Food Diary")).toBeInTheDocument();
    expect(screen.getByText("AI Coach")).toBeInTheDocument();
    expect(screen.getByText("Weight Tracker")).toBeInTheDocument();
    expect(screen.getByText("Tasks")).toBeInTheDocument();
    expect(screen.getByText("Settings")).toBeInTheDocument();
  });

  it("renders brand name", () => {
    render(<Sidebar />);
    expect(screen.getByText("NutriMind")).toBeInTheDocument();
  });

  it("marks active route", () => {
    render(<Sidebar />);
    const dashboardLink = screen.getByText("Dashboard").closest("a");
    expect(dashboardLink).toHaveAttribute("aria-current", "page");
  });
});
