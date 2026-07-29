export interface WeightMilestone {
  id: string
  title: string
  description: string
  icon: "streak" | "metabolic" | "fat" | "lean"
  unlocked: boolean
}

export const weightMilestones: WeightMilestone[] = [
  {
    id: "demo-streak",
    title: "10-Day Streak",
    description: "Achieved perfect logging precision for 240 consecutive hours.",
    icon: "streak",
    unlocked: true,
  },
  {
    id: "demo-pivot",
    title: "Metabolic Pivot",
    description: "Basal Metabolic Rate increased by 12% through lean mass growth.",
    icon: "metabolic",
    unlocked: true,
  },
  {
    id: "demo-fat",
    title: "Fat Burner",
    description: "Target: Maintain caloric deficit for 30 consecutive days.",
    icon: "fat",
    unlocked: false,
  },
  {
    id: "demo-lean",
    title: "Lean Master",
    description: "Locked: Achieve 15% body fat target for 2 weeks.",
    icon: "lean",
    unlocked: false,
  },
]
