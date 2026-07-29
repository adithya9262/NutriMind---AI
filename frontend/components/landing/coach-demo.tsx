import { Card } from "@/components/ui/card"
import { Chip } from "@/components/ui/chip"
import { Button } from "@/components/ui/button"
import { Bot, Send, Keyboard, CheckCircle2, Sparkles } from "lucide-react"

export function CoachDemo() {
  return (
    <section className="py-16 sm:py-20">
      <div className="mx-auto grid max-w-7xl items-center gap-10 px-5 sm:px-8 lg:grid-cols-2">
        <div>
          <Chip variant="accent" className="mb-5">
            <Sparkles className="h-3.5 w-3.5" />
            AI Nutrition Coach
          </Chip>
          <h2 className="text-balance text-2xl font-semibold tracking-tight text-primary sm:text-3xl">
            Your Nutrition Assistant
          </h2>
          <p className="mt-4 max-w-xl leading-relaxed text-primary-secondary">
            Get answers to nutrition questions, meal planning help, and goal guidance from an AI coach
            that understands your profile and tracked data.
          </p>
          <ul className="mt-6 space-y-3">
            <Feature icon={<CheckCircle2 className="h-4 w-4" />} label="Nutrition Q&A" />
            <Feature icon={<CheckCircle2 className="h-4 w-4" />} label="Meal suggestions" />
            <Feature icon={<CheckCircle2 className="h-4 w-4" />} label="Goal coaching" />
            <Feature icon={<CheckCircle2 className="h-4 w-4" />} label="Profile-aware responses" />
          </ul>
        </div>

        <Card variant="elevated" className="p-0">
          <div className="flex items-center justify-between border-b border-[var(--color-border)] p-5">
            <div className="flex items-center gap-2.5">
              <span className="flex h-9 w-9 items-center justify-center rounded-full gradient-brand text-white">
                <Bot className="h-4 w-4" />
              </span>
              <div>
                <p className="text-sm font-medium text-primary">NutriMind AI Coach</p>
                <p className="text-xs text-primary-secondary">Ready to help</p>
              </div>
            </div>
          </div>

          <div className="space-y-4 p-5">
            <Bubble>
              Hi! I can help with meal planning, macro questions, or goal adjustments. What would you like to work on?
            </Bubble>
            <Bubble self>
              What&apos;s a good high-protein breakfast under 400 calories?
            </Bubble>
            <Bubble>
              Greek yogurt (170g) with berries and a tablespoon of chia seeds: ~30g protein, 300 calories.
              Or try 3 eggs with spinach and 1 slice of whole grain toast: ~25g protein, 350 calories.
            </Bubble>
          </div>

          <div className="flex items-center gap-2 border-t border-[var(--color-border)] p-4">
            <div className="flex flex-1 items-center gap-2 rounded-xl border border-[var(--color-border)] bg-bg px-3 py-2.5">
              <Keyboard className="h-4 w-4 text-primary-muted" />
              <span className="text-sm text-primary-muted">Ask about nutrition, meals, or goals...</span>
            </div>
            <Button size="sm" pill aria-label="Send">
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </Card>
      </div>
    </section>
  )
}

function Feature({ icon, label }: { icon: React.ReactNode; label: string }) {
  return (
    <li className="flex items-center gap-3 text-sm text-primary-secondary">
      <span className="text-brand-primary">{icon}</span>
      {label}
    </li>
  )
}

function Bubble({ children, self }: { children: React.ReactNode; self?: boolean }) {
  return (
    <div className={self ? "flex justify-end" : "flex justify-start"}>
      <p
        className={
          self
            ? "max-w-[85%] rounded-2xl rounded-br-md bg-brand text-white px-4 py-2.5 text-sm"
            : "max-w-[85%] rounded-2xl rounded-bl-md bg-surface-high px-4 py-2.5 text-sm text-primary-secondary"
        }
      >
        {children}
      </p>
    </div>
  )
}
