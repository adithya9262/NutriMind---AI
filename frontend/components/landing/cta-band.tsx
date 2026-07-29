import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { ArrowRight, Target } from "lucide-react"

export function CtaBand() {
  return (
    <section className="py-16 sm:py-20">
      <div className="mx-auto max-w-7xl px-5 sm:px-8">
        <Card variant="brand" className="glow overflow-hidden p-10 text-center sm:p-16">
          <div className="mx-auto max-w-2xl">
            <div className="mb-4 inline-flex items-center justify-center gap-2 rounded-xl bg-white/15 px-4 py-2 text-sm font-medium text-white">
              <Target className="h-4 w-4" />
              Start Building Better Nutrition Habits
            </div>
            <h2 className="mx-auto max-w-2xl text-balance text-2xl font-semibold leading-tight tracking-tight text-white sm:text-4xl">
              Bring your nutrition, goals and progress tracking together.
            </h2>
            <p className="mx-auto mt-4 max-w-xl text-white/80">
              Create your NutriMind account and start understanding your daily nutrition and progress.
            </p>
            <div className="mt-8 flex flex-col items-center justify-center gap-4 sm:flex-row">
              <Link href="/register">
                <Button size="lg" variant="glass" pill className="text-white w-full sm:w-auto">
                  Get Started
                  <ArrowRight className="ml-2 h-4 w-4" aria-hidden="true" />
                </Button>
              </Link>
              <Link href="/login">
                <Button variant="secondary" size="lg" pill className="w-full sm:w-auto">
                  Sign In
                </Button>
              </Link>
            </div>
          </div>
        </Card>
      </div>
    </section>
  )
}
