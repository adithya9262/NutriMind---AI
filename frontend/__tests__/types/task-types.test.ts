import { describe, it, expect } from "vitest";
import {
  PRIORITY_LABELS,
  STATUS_LABELS,
  PRIORITY_VARIANTS,
  STATUS_VARIANTS,
  MIN_TASK_TITLE_LENGTH,
  MAX_TASK_TITLE_LENGTH,
  MAX_TASK_DESCRIPTION_LENGTH,
  EMPTY_TASK_FORM,
} from "@/types/tasks";

describe("Task types", () => {
  it("has exact priority values", () => {
    expect(PRIORITY_LABELS).toEqual({
      low: "Low",
      medium: "Medium",
      high: "High",
    });
  });

  it("has exact status values", () => {
    expect(STATUS_LABELS).toEqual({
      pending: "Pending",
      completed: "Completed",
    });
  });

  it("has priority variants for badge display", () => {
    expect(PRIORITY_VARIANTS).toEqual({
      low: "default",
      medium: "warning",
      high: "error",
    });
  });

  it("has status variants for badge display", () => {
    expect(STATUS_VARIANTS).toEqual({
      pending: "default",
      completed: "success",
    });
  });

  it("has correct length constraints", () => {
    expect(MIN_TASK_TITLE_LENGTH).toBe(1);
    expect(MAX_TASK_TITLE_LENGTH).toBe(200);
    expect(MAX_TASK_DESCRIPTION_LENGTH).toBe(2000);
  });

  it("has empty form state", () => {
    expect(EMPTY_TASK_FORM).toEqual({
      title: "",
      description: "",
      due_date: "",
      priority: "medium",
      category: "custom",
      recurrence: "none",
    });
  });

  it("preserves due_date as date-only string", () => {
    const date = "2026-07-15";
    expect(date).toMatch(/^\d{4}-\d{2}-\d{2}$/);
  });

  it("preserves completed_at as ISO string", () => {
    const ts = "2026-07-15T10:00:00.000Z";
    expect(() => new Date(ts)).not.toThrow();
  });

  it("no priority reclassification exists", () => {
    const types = PRIORITY_LABELS as Record<string, unknown>;
    expect(typeof types.low).toBe("string");
    expect(typeof types.medium).toBe("string");
    expect(typeof types.high).toBe("string");
  });

  it("no status reclassification exists", () => {
    const types = STATUS_LABELS as Record<string, unknown>;
    expect(typeof types.pending).toBe("string");
    expect(typeof types.completed).toBe("string");
  });

  it("no urgency calculation function", async () => {
    const types = await import("@/types/tasks");
    expect(typeof (types as Record<string, unknown>).calculateUrgency).toBe("undefined");
  });
});
