import { LandingHeader } from "@/components/landing/landing-header"
import { Hero } from "@/components/landing/hero"
import { Features } from "@/components/landing/features"
import { HowItWorks } from "@/components/landing/how-it-works"
import { CoachDemo } from "@/components/landing/coach-demo"
import { CtaBand } from "@/components/landing/cta-band"
import { LandingFooter } from "@/components/landing/landing-footer"

export default function HomePage() {
  return (
    <div className="min-h-screen bg-background">
      <LandingHeader />
      <main>
        <Hero />
        <Features />
        <HowItWorks />
        <CoachDemo />
        <CtaBand />
      </main>
      <LandingFooter />
    </div>
  )
}

