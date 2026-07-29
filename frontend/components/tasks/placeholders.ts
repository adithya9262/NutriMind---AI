export const TASKS_DEMO_LABEL = "Demo preview"

export interface TodayOptimization {
  id: string
  label: string
  done: boolean
  isDemo: boolean
}

// Demo-only content shown in the "Today's Optimization" panel.
// These do NOT reflect backend task state and are clearly labeled as demo.
export const TODAY_OPTIMIZATION_DEMO: TodayOptimization[] = [
  { id: "demo-opt-1", label: "Log a mindful nutrition entry", done: true, isDemo: true },
  { id: "demo-opt-2", label: "Complete one high-priority task", done: false, isDemo: true },
  { id: "demo-opt-3", label: "Hit your hydration target", done: false, isDemo: true },
  { id: "demo-opt-4", label: "10-minute recovery mobility", done: false, isDemo: true },
]

export const TASK_EMPTY_STATE = {
  title: "No tasks yet",
  description: "Create your first task to get started.",
  isDemo: false,
}
