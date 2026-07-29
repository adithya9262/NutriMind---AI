import { cn } from "@/lib/utils"

export function Divider({ children, className = "" }: { children?: React.ReactNode; className?: string }) {
  return (
    <div className={cn("flex items-center gap-4", className)}>
      <span className="h-px flex-1 bg-[var(--color-border)]" />
      {children && (
        <span className="text-xs font-medium uppercase tracking-wide text-primary-muted">
          {children}
        </span>
      )}
      <span className="h-px flex-1 bg-[var(--color-border)]" />
    </div>
  )
}
