import Link from "next/link"
import { Button } from "@/components/ui/button"
import { ArrowRight } from "lucide-react"

export function Hero() {
  return (
    <section className="relative overflow-hidden py-16 sm:py-24 lg:py-32">
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute left-[-10%] top-10 h-96 w-96 rounded-full bg-brand-primary/10 blur-3xl" />
        <div className="absolute right-[-10%] top-40 h-[28rem] w-[28rem] rounded-full bg-accent/10 blur-3xl" />
      </div>
      <div className="mx-auto max-w-7xl px-5 sm:px-8">
        <div className="relative mx-auto max-w-3xl text-center">
          <h1
            id="hero-heading"
            className="text-balance text-4xl font-semibold leading-[1.1] tracking-[-0.04em] text-primary sm:text-5xl lg:text-6xl"
          >
            Understand Your Nutrition. Build Better Habits.
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-lg leading-relaxed text-primary-secondary">
            Track meals, nutrition goals, body weight and daily habits in one place — with tools
            designed to help you understand your progress.
          </p>
          <div className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row">
            <Link href="/register">
              <Button size="lg" pill className="w-full shadow-lg sm:w-auto">
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
      </div>
    </section>
  )
}
