import Link from "next/link"
import { Sparkles } from "lucide-react"
import { cn } from "@/lib/utils"

interface UpgradeCardProps {
  className?: string
}

export function UpgradeCard({ className }: UpgradeCardProps) {
  return (
    <Link
      href="/settings"
      className={cn(
        "group relative block overflow-hidden rounded-2xl border border-brand-primary/25 bg-gradient-to-br from-brand-primary/12 to-surface-high/40 p-4 transition-all duration-200 hover:border-brand-primary/45",
        className,
      )}
    >
      <div className="flex items-center gap-2">
        <span className="grid h-7 w-7 place-items-center rounded-lg bg-brand-primary/20">
          <Sparkles className="h-4 w-4 text-brand-primary" aria-hidden="true" />
        </span>
        <p className="text-sm font-semibold text-primary">Unlock Premium</p>
      </div>
      <p className="mt-2 text-xs leading-relaxed text-primary-muted">
        Advanced biometric insights, AI coaching & unlimited tracking.
      </p>
      <span className="mt-3 inline-flex items-center text-xs font-semibold text-brand-primary transition-transform duration-200 group-hover:translate-x-0.5">
        Upgrade plan →
      </span>
    </Link>
  )
}
