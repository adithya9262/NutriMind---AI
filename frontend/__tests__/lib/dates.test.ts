import { describe, it, expect } from "vitest";
import { getLocalCalendarDate } from "@/lib/dates";

describe("getLocalCalendarDate", () => {
  it("returns YYYY-MM-DD format", () => {
    const result = getLocalCalendarDate(new Date(2025, 5, 15));
    expect(result).toBe("2025-06-15");
  });

  it("pads single-digit month and day", () => {
    const result = getLocalCalendarDate(new Date(2025, 0, 5));
    expect(result).toBe("2025-01-05");
  });

  it("handles December date", () => {
    const result = getLocalCalendarDate(new Date(2025, 11, 25));
    expect(result).toBe("2025-12-25");
  });

  it("returns local date, not UTC", () => {
    const d = new Date(2025, 5, 15);
    expect(getLocalCalendarDate(d)).toBe("2025-06-15");
  });
});
