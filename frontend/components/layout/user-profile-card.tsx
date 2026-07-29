import { useAuth } from "@/contexts/auth-context"
import { Avatar } from "@/components/ui/avatar"
import { cn } from "@/lib/utils"

function deriveName(email: string | undefined): string {
  if (!email) return "Member"
  const local = email.split("@")[0]
  const parts = local.split(/[._-]/).filter(Boolean)
  if (parts.length === 0) return "Member"
  return parts
    .map((p) => p.charAt(0).toUpperCase() + p.slice(1))
    .join(" ")
}

interface UserProfileCardProps {
  className?: string
}

export function UserProfileCard({ className }: UserProfileCardProps) {
  const { user } = useAuth()
  const name = deriveName(user?.email)
  const initials = name.charAt(0).toUpperCase()

  return (
    <div className={cn("flex items-center gap-3 rounded-2xl border border-border bg-surface-high/40 p-3", className)}>
      <div className="relative">
        <Avatar initials={initials} size="md" alt={name} />
        <span
          aria-hidden="true"
          className="absolute -bottom-0.5 -right-0.5 h-3 w-3 rounded-full border-2 border-[#0c1a14] bg-brand-primary"
        />
      </div>
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-semibold text-primary">{name}</p>
        <div className="mt-0.5 flex items-center gap-1.5">
          <span className="rounded-full bg-brand-primary/15 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-brand-primary">
            Pro
          </span>
          <span className="text-[11px] text-primary-muted">Lv. 12</span>
        </div>
      </div>
    </div>
  )
}
