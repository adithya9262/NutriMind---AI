import { cn } from "@/lib/utils"

interface ProgressProps {
  value: number
  max?: number
  variant?: "default" | "success" | "warning" | "error" | "accent"
  size?: "sm" | "md" | "lg"
  showLabel?: boolean
  className?: string
}

export function Progress({
  value,
  max = 100,
  variant = "default",
  size = "md",
  showLabel = false,
  className = "",
}: ProgressProps) {
  const percentage = Math.min(Math.round((value / max) * 100), 100)

  const sizeClasses = {
    sm: "h-1.5",
    md: "h-2.5",
    lg: "h-4",
  }

  const variantClasses = {
    default: "bg-brand",
    success: "bg-success",
    warning: "bg-warning",
    error: "bg-error",
    accent: "bg-accent",
  }

  return (
    <div className={cn("w-full", className)}>
      {showLabel && (
        <div className="flex justify-between mb-1.5">
          <span className="text-xs text-primary-secondary">{Math.round(value)}</span>
          <span className="text-xs text-primary-muted">{max}</span>
        </div>
      )}
      <div
        className={cn("w-full rounded-full bg-brand-primary/10 overflow-hidden", sizeClasses[size])}
        role="progressbar"
        aria-valuenow={value}
        aria-valuemin={0}
        aria-valuemax={max}
        aria-label={`${percentage}% complete`}
      >
        <div
          className={cn(
            "h-full rounded-full transition-all duration-500 ease-out",
            variantClasses[variant],
            sizeClasses[size],
          )}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  )
}
