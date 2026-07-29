import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { Header } from "@/components/layout/header";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

vi.mock("@/contexts/auth-context", () => ({
  useAuth: () => ({
    user: { email: "test@example.com" },
    logout: vi.fn(),
  }),
}));

describe("AppHeader", () => {
  it("renders menu button for mobile", () => {
    render(<Header onMenuClick={vi.fn()} />);
    expect(screen.getByLabelText("Open navigation menu")).toBeInTheDocument();
  });

  it("shows user email after opening the user menu", () => {
    render(<Header onMenuClick={vi.fn()} />);
    expect(screen.queryByText("test@example.com")).not.toBeInTheDocument();
    fireEvent.click(screen.getByLabelText("User menu"));
    expect(screen.getByText("test@example.com")).toBeInTheDocument();
  });

  it("renders log out action in the user menu", () => {
    render(<Header onMenuClick={vi.fn()} />);
    fireEvent.click(screen.getByLabelText("User menu"));
    expect(screen.getByText("Log out")).toBeInTheDocument();
  });
});
