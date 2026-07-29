import type { ReactNode } from "react"
import { cn } from "@/lib/utils"

interface PageHeaderProps {
  title: string
  description?: string
  actions?: ReactNode
  className?: string
}

export function PageHeader({
  title,
  description,
  actions,
  className = "",
}: PageHeaderProps) {
  return (
    <div
      className={cn(
        "flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between",
        className,
      )}
    >
      <div className="space-y-1">
        <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-primary">
          {title}
        </h1>
        {description && (
          <p className="text-sm sm:text-base text-primary-secondary">
            {description}
          </p>
        )}
      </div>
      {actions && <div className="flex items-center gap-3 mt-2 sm:mt-0">{actions}</div>}
    </div>
  )
}
