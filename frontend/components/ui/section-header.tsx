import type { ReactNode } from "react"
import { cn } from "@/lib/utils"

interface SectionHeaderProps {
  title: string
  description?: string
  action?: ReactNode
  id?: string
  className?: string
}

export function SectionHeader({
  title,
  description,
  action,
  id,
  className = "",
}: SectionHeaderProps) {
  return (
    <div
      className={cn(
        "flex items-start justify-between gap-4 mb-4",
        className,
      )}
    >
      <div>
        <h2 id={id} className="text-lg font-semibold text-primary">
          {title}
        </h2>
        {description && (
          <p className="text-sm text-primary-secondary mt-0.5">
            {description}
          </p>
        )}
      </div>
      {action && <div className="flex-shrink-0">{action}</div>}
    </div>
  )
}
