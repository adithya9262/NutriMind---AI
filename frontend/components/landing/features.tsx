import { Card } from "@/components/ui/card"
import { Utensils, Target, Scale, Flame, Bot, FileText, Search, Upload } from "lucide-react"

const features = [
  {
    icon: Utensils,
    title: "Nutrition Tracking",
    description: "Log meals and review daily calorie and macronutrient intake with a clean food diary.",
  },
  {
    icon: Search,
    title: "Nutrition Search",
    description: "Search a nutrition database for foods and view their complete macro profile.",
  },
  {
    icon: Scale,
    title: "Weight Tracking",
    description: "Record body weight and follow progress over time with visual trends.",
  },
  {
    icon: Target,
    title: "Goals",
    description: "Create and manage nutrition or health goals supported by the application.",
  },
  {
    icon: Flame,
    title: "Daily Tasks",
    description: "Create, complete and manage daily wellness tasks and habits.",
  },
  {
    icon: Bot,
    title: "AI Coach",
    description: "Get nutrition-related assistance from NutriMind's AI Coach.",
  },
]

export function Features() {
  return (
    <section id="features" className="py-16 sm:py-20">
      <div className="mx-auto max-w-7xl px-5 sm:px-8">
        <div className="mb-12 flex flex-col items-start justify-between gap-4 sm:flex-row sm:items-end">
          <div>
            <h2 className="text-2xl font-semibold tracking-tight text-primary sm:text-3xl">
              Everything You Need to Stay on Track
            </h2>
            <p className="mt-3 max-w-xl text-primary-secondary">
              Practical tools to help you understand your nutrition, build habits, and see progress.
            </p>
          </div>
        </div>

        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {features.map((f) => (
            <Card key={f.title} variant="elevated" className="card-hover p-6">
              <div className="mb-4 inline-flex rounded-xl bg-brand-primary/10 p-3 text-brand-primary">
                <f.icon className="h-5 w-5" />
              </div>
              <h3 className="font-semibold text-primary">{f.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-primary-secondary">{f.description}</p>
            </Card>
          ))}
        </div>
      </div>
    </section>
  )
}