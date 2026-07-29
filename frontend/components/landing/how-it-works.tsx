import { Card } from "@/components/ui/card"
import { UserPlus, Utensils, BarChart3, ArrowRight } from "lucide-react"

const steps = [
  {
    icon: UserPlus,
    title: "Create Your Profile",
    description: "Enter your information to calculate personalized nutrition targets including calories, protein, carbs, and fat goals.",
  },
  {
    icon: Utensils,
    title: "Track Your Day",
    description: "Log meals using search or food recognition, record weight, set goals, and complete daily tasks.",
  },
  {
    icon: BarChart3,
    title: "Understand Your Progress",
    description: "Review your dashboard, nutrition summary, and goal progress to see how you're doing over time.",
  },
]

export function HowItWorks() {
  return (
    <section id="how-it-works" className="py-16 sm:py-20 bg-surface/30">
      <div className="mx-auto max-w-7xl px-5 sm:px-8">
        <div className="mx-auto mb-12 max-w-2xl text-center">
          <h2 className="text-2xl font-semibold tracking-tight text-primary sm:text-3xl">
            How It Works
          </h2>
          <p className="mt-3 text-primary-secondary">
            Get started in three simple steps.
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-3">
          {steps.map((step, index) => (
            <Card key={step.title} variant="elevated" className="p-6">
              <div className="mb-4 flex items-center gap-2">
                <span className="text-3xl font-semibold text-brand-primary/30">{index + 1}</span>
                <div className="inline-flex rounded-xl bg-brand-primary/10 p-2.5 text-brand-primary">
                  <step.icon className="h-5 w-5" />
                </div>
              </div>
              <h3 className="font-semibold text-primary">{step.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-primary-secondary">{step.description}</p>
            </Card>
          ))}
        </div>
      </div>
    </section>
  )
}