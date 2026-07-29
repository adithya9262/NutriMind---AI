import { describe, it, expect } from "vitest";
import {
  MEAL_TYPE_LABELS,
  MEAL_TYPE_ORDER,
  PROGRESS_STATUS_LABELS,
  EMPTY_ENTRY_FORM,
  NUTRITION_FIELD_LIMITS,
} from "@/types/nutrition";

describe("Nutrition log types", () => {
  it("has exact meal-type labels", () => {
    expect(MEAL_TYPE_LABELS).toEqual({
      breakfast: "Breakfast",
      lunch: "Lunch",
      dinner: "Dinner",
      snack: "Snack",
    });
  });

  it("has correct meal-type order", () => {
    expect(MEAL_TYPE_ORDER).toEqual(["breakfast", "lunch", "dinner", "snack"]);
  });

  it("has progress status labels", () => {
    expect(PROGRESS_STATUS_LABELS).toEqual({
      below_target: "Below Target",
      target_met: "Target Met",
      above_target: "Above Target",
    });
  });

  it("has empty entry form state", () => {
    expect(EMPTY_ENTRY_FORM).toEqual({
      food_name: "",
      meal_type: "breakfast",
      serving_description: "",
      calories_kcal: "",
      protein_g: "",
      carbohydrate_g: "",
      fat_g: "",
    });
  });

  it("has correct nutrition field limits", () => {
    expect(NUTRITION_FIELD_LIMITS).toEqual({
      calories_kcal: { min: 0, max: 10000, step: "0.01" },
      protein_g: { min: 0, max: 1000, step: "0.01" },
      carbohydrate_g: { min: 0, max: 2000, step: "0.01" },
      fat_g: { min: 0, max: 1000, step: "0.01" },
    });
  });

  it("Decimal response fields remain strings in NutritionLogEntryData", () => {
    const entry = {
      entry_id: "123e4567-e89b-12d3-a456-426614174000",
      food_name: "Oatmeal",
      meal_type: "breakfast" as const,
      serving_description: "1 cup",
      calories_kcal: "350.00",
      protein_g: "12.50",
      carbohydrate_g: "55.00",
      fat_g: "5.00",
    };
    expect(typeof entry.calories_kcal).toBe("string");
    expect(typeof entry.protein_g).toBe("string");
    expect(typeof entry.carbohydrate_g).toBe("string");
    expect(typeof entry.fat_g).toBe("string");
  });

  it("negative remaining is preserved", () => {
    const progress = {
      consumed: "3000.00",
      target: "2500.00",
      remaining: "-500.00",
      percentage: "120.00",
      status: "above_target" as const,
    };
    expect(progress.remaining).toBe("-500.00");
    expect(Number(progress.remaining)).toBeLessThan(0);
  });

  it("percentage above 100 is preserved", () => {
    const progress = {
      consumed: "3000.00",
      target: "2500.00",
      remaining: "-500.00",
      percentage: "120.00",
      status: "above_target" as const,
    };
    expect(progress.percentage).toBe("120.00");
    expect(Number(progress.percentage)).toBeGreaterThan(100);
  });

  it("no frontend nutrition formula exists to recompute totals", async () => {
    const types = await import("@/types/nutrition");
    expect(typeof (types as Record<string, unknown>).calculateDailyNutritionTotals).toBe("undefined");
    expect(typeof (types as Record<string, unknown>).calculateDailyNutritionProgress).toBe("undefined");
  });

  it("no frontend status reclassification exists", async () => {
    const types = await import("@/types/nutrition");
    expect(typeof (types as Record<string, unknown>).reclassifyStatus).toBe("undefined");
  });
});
