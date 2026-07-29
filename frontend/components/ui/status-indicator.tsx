import { cn } from "@/lib/utils"

interface StatusIndicatorProps {
  status: "healthy" | "unhealthy" | "checking" | "unavailable"
  label?: string
  className?: string
}

const statusStyles = {
  healthy: "bg-success",
  unhealthy: "bg-error",
  checking: "bg-warning animate-pulse-soft",
  unavailable: "bg-primary-muted",
}

export function StatusIndicator({
  status,
  label,
  className = "",
}: StatusIndicatorProps) {
  return (
    <div className={cn("flex items-center gap-2", className)}>
      <span
        className={cn(
          "h-2.5 w-2.5 rounded-full",
          statusStyles[status],
        )}
        aria-hidden="true"
      />
      {label && (
        <span className="text-xs text-primary-secondary">{label}</span>
      )}
    </div>
  )
}
