import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Logo } from "@/components/logo"

export function LandingHeader() {
  return (
    <header className="sticky top-0 z-50 border-b border-[var(--color-border)] glass">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-5 py-3.5 sm:px-8">
        <Link href="/" aria-label="NutriMind AI home">
          <Logo />
        </Link>
        <nav className="hidden items-center gap-8 md:flex" aria-label="Primary">
          <a href="#features" className="text-sm font-medium text-primary-secondary transition-colors hover:text-primary">
            Features
          </a>
          <a href="#how-it-works" className="text-sm font-medium text-primary-secondary transition-colors hover:text-primary">
            How It Works
          </a>
        </nav>
        <div className="flex items-center gap-3">
          <Link href="/login">
            <Button variant="ghost" size="sm">Sign in</Button>
          </Link>
          <Link href="/register">
            <Button size="sm" pill>Get Started</Button>
          </Link>
        </div>
      </div>
    </header>
  )
}
