import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import RegisterPage from "@/app/(auth)/register/page";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
  useSearchParams: () => ({ get: vi.fn() }),
}));

vi.mock("@/contexts/auth-context", () => ({
  useAuth: () => ({
    state: "unauthenticated",
    user: null,
    login: vi.fn(),
    logout: vi.fn(),
  }),
}));

describe("RegisterPage", () => {
  it("renders all form fields", () => {
    render(<RegisterPage />);
    const inputs = screen.getAllByRole("textbox");
    expect(inputs.length).toBeGreaterThanOrEqual(1);
    const passwordInputs = screen.getAllByLabelText(/password/i);
    expect(passwordInputs.length).toBeGreaterThanOrEqual(2);
  });

  it("renders create account button", () => {
    render(<RegisterPage />);
    expect(screen.getByRole("button", { name: /Create Account/i })).toBeInTheDocument();
  });

  it("renders link to login", () => {
    render(<RegisterPage />);
    expect(screen.getByText(/Sign In/i)).toBeInTheDocument();
  });

  it("shows validation error for short password", async () => {
    const user = userEvent.setup();
    render(<RegisterPage />);
    const inputs = screen.getAllByRole("textbox");
    const passwordInputs = screen.getAllByLabelText(/password/i);

    await user.type(inputs[0], "test@example.com");
    await user.type(passwordInputs[0], "short");
    await user.type(passwordInputs[1], "short");
    await user.click(screen.getByRole("button", { name: /Create Account/i }));
    expect(screen.getByText("Password must be at least 8 characters.")).toBeInTheDocument();
  });

  it("shows validation error for mismatched passwords", async () => {
    const user = userEvent.setup();
    render(<RegisterPage />);
    const inputs = screen.getAllByRole("textbox");
    const passwordInputs = screen.getAllByLabelText(/password/i);

    await user.type(inputs[0], "test@example.com");
    await user.type(passwordInputs[0], "longenough123");
    await user.type(passwordInputs[1], "different");
    await user.click(screen.getByRole("button", { name: /Create Account/i }));
    expect(screen.getByText("Passwords do not match.")).toBeInTheDocument();
  });

  it("shows validation error when submitting empty form", async () => {
    const user = userEvent.setup();
    render(<RegisterPage />);
    await user.click(screen.getByRole("button", { name: /Create Account/i }));
    expect(screen.getByText("Email is required.")).toBeInTheDocument();
    expect(screen.getByText("Password is required.")).toBeInTheDocument();
  });
});
