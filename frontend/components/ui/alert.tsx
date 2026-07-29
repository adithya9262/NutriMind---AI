import { type HTMLAttributes } from "react"
import { cn } from "@/lib/utils"
import { AlertCircle, CheckCircle2, Info, AlertTriangle, X } from "lucide-react"

interface AlertProps extends HTMLAttributes<HTMLDivElement> {
  variant?: "info" | "success" | "warning" | "error"
  dismissible?: boolean
  onDismiss?: () => void
}

const variantStyles = {
  info: {
    container: "bg-info-light border-info/20 text-info",
    icon: Info,
  },
  success: {
    container: "bg-success-light border-success/20 text-success",
    icon: CheckCircle2,
  },
  warning: {
    container: "bg-warning-light border-warning/20 text-warning",
    icon: AlertTriangle,
  },
  error: {
    container: "bg-error-light border-error/20 text-error",
    icon: AlertCircle,
  },
}

export function Alert({
  className = "",
  variant = "info",
  dismissible = false,
  onDismiss,
  children,
  ...props
}: AlertProps) {
  const Icon = variantStyles[variant].icon

  return (
    <div
      className={cn(
        "flex items-start gap-3 rounded-xl border p-4 text-sm",
        variantStyles[variant].container,
        className,
      )}
      role="alert"
      {...props}
    >
      <Icon className="h-5 w-5 flex-shrink-0 mt-0.5" aria-hidden="true" />
      <div className="flex-1">{children}</div>
      {dismissible && onDismiss && (
        <button
          type="button"
          onClick={onDismiss}
          className="flex-shrink-0 p-0.5 rounded hover:opacity-70 transition-opacity"
          aria-label="Dismiss"
        >
          <X className="h-4 w-4" />
        </button>
      )}
    </div>
  )
}
