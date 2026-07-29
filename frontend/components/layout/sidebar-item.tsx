import Link from "next/link"
import { type LucideIcon } from "lucide-react"
import { cn } from "@/lib/utils"

interface SidebarItemProps {
  href: string
  label: string
  icon: LucideIcon
  active: boolean
  onNavigate?: () => void
}

export function SidebarItem({ href, label, icon: Icon, active, onNavigate }: SidebarItemProps) {
  return (
    <Link
      href={href}
      onClick={onNavigate}
      aria-current={active ? "page" : undefined}
      className={cn(
        "group relative flex items-center gap-3 rounded-xl px-3.5 py-2.5 text-sm font-medium transition-all duration-200",
        active
          ? "bg-surface-high/70 text-primary"
          : "text-primary-secondary hover:bg-white/5 hover:text-primary",
      )}
    >
      {active && (
        <span
          aria-hidden="true"
          className="absolute left-0 top-1/2 h-6 w-1 -translate-y-1/2 rounded-full bg-brand-primary glow"
        />
      )}
      <Icon
        className={cn(
          "h-5 w-5 flex-shrink-0 transition-transform duration-200",
          active && "scale-110 text-brand-primary",
        )}
        aria-hidden="true"
      />
      {label}
    </Link>
  )
}
