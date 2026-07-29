import type { ReactNode } from "react"
import { AlertCircle } from "lucide-react"
import { cn } from "@/lib/utils"

interface ErrorStateProps {
  title: string
  message?: string
  action?: ReactNode
  className?: string
}

export function ErrorState({
  title,
  message,
  action,
  className = "",
}: ErrorStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center py-12 text-center",
        className,
      )}
    >
      <div className="mb-4 p-3 rounded-full bg-error-light">
        <AlertCircle className="h-6 w-6 text-error" aria-hidden="true" />
      </div>
      <h3 className="text-base font-semibold text-primary">{title}</h3>
      {message && (
        <p className="mt-1 text-sm text-primary-secondary max-w-md">
          {message}
        </p>
      )}
      {action && <div className="mt-4">{action}</div>}
    </div>
  )
}
