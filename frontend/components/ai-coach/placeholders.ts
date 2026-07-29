export interface DemoConversation {
  id: string
  title: string
  preview: string
  meta: string
  active?: boolean
}

export const AI_COACH_PLACEHOLDERS = {
  assistantName: "NutriMind Core v3",
  statusLabel: "Analyzing Vitals…",
  demoBanner:
    "Demo interface — the AI coaching backend is not yet connected. Messages are stored locally and no assistant reply is generated.",
  conversations: [
    {
      id: "c1",
      title: "Intermittent Fasting Strategy",
      preview: "Optimizing cortisol levels during the window…",
      meta: "Active",
      active: true,
    },
    {
      id: "c2",
      title: "Keto Adaptation Phase",
      preview: "Reviewing macro balance for elite…",
      meta: "1d",
    },
    {
      id: "c3",
      title: "Magnesium Protocol",
      preview: "Discussion on Glycinate vs L-Threonate…",
      meta: "3d",
    },
  ] as DemoConversation[],
  suggestedPrompts: [
    "Adjust recovery for endurance",
    "Analyze last night's REM",
    "Update micronutrient stack",
    "Design a macro plan for my next workout",
  ],
  welcomeMessage:
    "Hello! I'm your AI nutrition coach. I can help you with meal planning, nutrition advice, and goal setting. What would you like to explore today?",
} as const

export const AI_COACH_PLACEHOLDER_NOTE =
  "Demo content only: conversation history and suggested prompts are illustrative placeholders (no AI/chat backend). Easy to replace via AI_COACH_PLACEHOLDERS."
