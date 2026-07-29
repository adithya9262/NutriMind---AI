import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { ProtectedRoute } from "@/components/protected-route";

const mockReplace = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: mockReplace }),
  usePathname: () => "/dashboard",
}));

vi.mock("@/contexts/auth-context", () => ({
  useAuth: () => ({
    state: "unauthenticated",
    user: null,
    login: vi.fn(),
    logout: vi.fn(),
  }),
}));

describe("ProtectedRoute", () => {
  it("redirects to login when unauthenticated", async () => {
    render(<ProtectedRoute>Content</ProtectedRoute>);
    await vi.waitFor(() => {
      expect(mockReplace).toHaveBeenCalledWith("/login?redirect=%2Fdashboard");
    });
  });

  it("does not render children when unauthenticated", () => {
    render(<ProtectedRoute>Visible</ProtectedRoute>);
    expect(screen.queryByText("Visible")).not.toBeInTheDocument();
  });
});
