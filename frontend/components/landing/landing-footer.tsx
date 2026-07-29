import { Logo } from "@/components/logo"

export function LandingFooter() {
  return (
    <footer className="border-t border-[var(--color-border)] py-12">
      <div className="mx-auto max-w-7xl px-5 sm:px-8">
        <div className="flex flex-col items-start justify-between gap-8 sm:flex-row sm:items-center">
          <div>
            <Logo />
            <p className="mt-3 max-w-sm text-sm text-primary-secondary">
              Nutrition and wellness tracking tools designed to help you understand your daily
              habits and progress.
            </p>
          </div>
          <nav className="flex flex-wrap gap-x-6 gap-y-3 text-sm" aria-label="Footer">
            <a href="#features" className="text-primary-secondary transition-colors hover:text-primary">
              Features
            </a>
            <a href="#how-it-works" className="text-primary-secondary transition-colors hover:text-primary">
              How It Works
            </a>
            <a href="/login" className="text-primary-secondary transition-colors hover:text-primary">
              Sign In
            </a>
            <a href="/register" className="text-primary-secondary transition-colors hover:text-primary">
              Get Started
            </a>
          </nav>
        </div>
        <div className="mt-10 flex flex-col items-start justify-between gap-3 border-t border-[var(--color-border)] pt-6 text-xs text-primary-muted sm:flex-row sm:items-center">
          <p>© 2026 NutriMind AI</p>
          <p>
            NutriMind provides informational wellness tools and is not a substitute for professional
            medical advice.
          </p>
        </div>
      </div>
    </footer>
  )
}
