import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { GlobalSearch } from "@/components/dashboard/global-search";
import { globalSearch } from "@/services/api/search";

vi.mock("@/services/api/search", () => ({
  globalSearch: vi.fn(),
}));

const mockGlobalSearch = vi.mocked(globalSearch);

beforeEach(() => {
  vi.clearAllMocks();
});

describe("GlobalSearch", () => {
  it("renders search input with placeholder", () => {
    render(<GlobalSearch />);
    expect(screen.getByPlaceholderText("Search meals, tasks...")).toBeInTheDocument();
  });

  it("shows loading indicator when searching", async () => {
    let resolveSearch: (value: any) => void;
    mockGlobalSearch.mockImplementation(() => new Promise((resolve) => { resolveSearch = resolve; }));

    render(<GlobalSearch />);
    const input = screen.getByPlaceholderText("Search meals, tasks...");

    fireEvent.change(input, { target: { value: "chicken" } });

    // Wait for debounce and search to start
    await waitFor(() => {
      expect(screen.getByLabelText("Searching")).toBeInTheDocument();
    });
  });

  it("displays food results when search returns foods", async () => {
    mockGlobalSearch.mockResolvedValueOnce({
      success: true,
      message: "Search completed.",
      data: {
        foods: [
          { id: "1", food_name: "Grilled Chicken", meal_type: "lunch", logged_date: "2024-01-15", calories_kcal: "350" },
        ],
        tasks: [],
      },
    });

    render(<GlobalSearch />);
    const input = screen.getByPlaceholderText("Search meals, tasks...");

    fireEvent.change(input, { target: { value: "chicken" } });

    await waitFor(() => {
      expect(screen.getByText("Grilled Chicken")).toBeInTheDocument();
    });
  });

  it("displays task results when search returns tasks", async () => {
    mockGlobalSearch.mockResolvedValueOnce({
      success: true,
      message: "Search completed.",
      data: {
        foods: [],
        tasks: [
          { id: "1", task_id: "task-1", title: "Meal prep chicken", status: "pending", due_date: "2024-01-16" },
        ],
      },
    });

    render(<GlobalSearch />);
    const input = screen.getByPlaceholderText("Search meals, tasks...");

    fireEvent.change(input, { target: { value: "meal prep" } });

    await waitFor(() => {
      expect(screen.getByText("Meal prep chicken")).toBeInTheDocument();
    });
  });

  it("shows empty state when no results found", async () => {
    mockGlobalSearch.mockResolvedValueOnce({
      success: true,
      message: "Search completed.",
      data: { foods: [], tasks: [] },
    });

    render(<GlobalSearch />);
    const input = screen.getByPlaceholderText("Search meals, tasks...");

    fireEvent.change(input, { target: { value: "nonexistent" } });

    await waitFor(() => {
      expect(screen.getByText(/No results found for/i)).toBeInTheDocument();
    });
  });

  it("does not search on empty query", async () => {
    render(<GlobalSearch />);
    const input = screen.getByPlaceholderText("Search meals, tasks...");

    fireEvent.change(input, { target: { value: "" } });

    // Wait a bit to ensure debounce would have fired
    await new Promise(resolve => setTimeout(resolve, 350));

    expect(mockGlobalSearch).not.toHaveBeenCalled();
  });

  it("handles API error gracefully", async () => {
    mockGlobalSearch.mockResolvedValueOnce({
      success: false,
      error: { code: "HTTP_ERROR", message: "Search failed", request_id: "123" },
    });

    render(<GlobalSearch />);
    const input = screen.getByPlaceholderText("Search meals, tasks...");

    fireEvent.change(input, { target: { value: "chicken" } });

    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });
    expect(screen.getByText("Search failed")).toBeInTheDocument();
  });

  it("clears results when query is cleared", async () => {
    mockGlobalSearch.mockResolvedValueOnce({
      success: true,
      message: "Search completed.",
      data: {
        foods: [{ id: "1", food_name: "Chicken", meal_type: "lunch", logged_date: "2024-01-15", calories_kcal: "350" }],
        tasks: [],
      },
    });

    render(<GlobalSearch />);
    const input = screen.getByPlaceholderText("Search meals, tasks...");

    fireEvent.change(input, { target: { value: "chicken" } });

    await waitFor(() => {
      expect(screen.getByText("Chicken")).toBeInTheDocument();
    });

    // Clear the input
    fireEvent.change(input, { target: { value: "" } });

    await waitFor(() => {
      expect(screen.queryByText("Chicken")).not.toBeInTheDocument();
    });
  });

  it("debounces rapid queries", async () => {
    mockGlobalSearch.mockResolvedValue({
      success: true,
      message: "Search completed.",
      data: { foods: [], tasks: [] },
    });

    render(<GlobalSearch />);
    const input = screen.getByPlaceholderText("Search meals, tasks...");

    fireEvent.change(input, { target: { value: "c" } });
    await new Promise(resolve => setTimeout(resolve, 50));
    fireEvent.change(input, { target: { value: "ch" } });
    await new Promise(resolve => setTimeout(resolve, 50));
    fireEvent.change(input, { target: { value: "chi" } });
    await new Promise(resolve => setTimeout(resolve, 50));
    fireEvent.change(input, { target: { value: "chic" } });
    await new Promise(resolve => setTimeout(resolve, 50));
    fireEvent.change(input, { target: { value: "chick" } });
    await new Promise(resolve => setTimeout(resolve, 50));
    fireEvent.change(input, { target: { value: "chicken" } });

    await new Promise(resolve => setTimeout(resolve, 350));

    // Should only call search once (for the final value)
    expect(mockGlobalSearch).toHaveBeenCalledTimes(1);
    expect(mockGlobalSearch).toHaveBeenCalledWith("chicken");
  });

  it("does not show stale results from previous query", async () => {
    // First search - slow response
    let resolveFirst: (value: any) => void;
    mockGlobalSearch.mockImplementationOnce(() => new Promise((resolve) => { resolveFirst = resolve; }));

    render(<GlobalSearch />);
    const input = screen.getByPlaceholderText("Search meals, tasks...");

    fireEvent.change(input, { target: { value: "chicken" } });
    await new Promise(resolve => setTimeout(resolve, 350));

    // Second search - fast response
    mockGlobalSearch.mockResolvedValueOnce({
      success: true,
      message: "Search completed.",
      data: { foods: [{ id: "2", food_name: "Beef", meal_type: "dinner", logged_date: "2024-01-15", calories_kcal: "400" }], tasks: [] },
    });

    fireEvent.change(input, { target: { value: "beef" } });
    await new Promise(resolve => setTimeout(resolve, 350));

    // Resolve first search (should be ignored due to query change)
    resolveFirst!({
      success: true,
      message: "Search completed.",
      data: { foods: [{ id: "1", food_name: "Chicken", meal_type: "lunch", logged_date: "2024-01-15", calories_kcal: "350" }], tasks: [] },
    });

    await waitFor(() => {
      expect(screen.getByText("Beef")).toBeInTheDocument();
    });
    expect(screen.queryByText("Chicken")).not.toBeInTheDocument();
  });
});