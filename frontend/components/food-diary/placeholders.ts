export const FOOD_DIARY_PLACEHOLDERS = {
  burnedKcal: 320,
  hydration: { currentL: 1.2, targetL: 3.5 },
  fiber: { currentG: 14, targetG: 30 },
  insight: {
    label: "AI Strategic Insight",
    body: "Protocol deviation detected: Protein intake is 15% below target. Optimal recovery window closing. Add 25g whey protein or 150g greek yogurt within 60 mins.",
  },
  mealPhaseLabels: {
    breakfast: "Breakfast Phase",
    lunch: "Lunch Phase",
    dinner: "Dinner Phase",
    snack: "Snack Phase",
  },
} as const

export const FOOD_DIARY_PLACEHOLDER_NOTE =
  "Demo values: calories burned, hydration, fiber, and AI insight are illustrative placeholders (no backend endpoint). Easy to replace via FOOD_DIARY_PLACEHOLDERS."
