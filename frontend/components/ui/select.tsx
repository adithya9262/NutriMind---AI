import { forwardRef, type SelectHTMLAttributes } from "react"
import { cn } from "@/lib/utils"
import { ChevronDown } from "lucide-react"

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  "aria-label"?: string
  "aria-invalid"?: boolean | "true" | "false"
  "aria-describedby"?: string
  error?: string | null
}

export const Select = forwardRef<HTMLSelectElement, SelectProps>(
  ({ className = "", children, "aria-invalid": ariaInvalid, "aria-describedby": ariaDescribedby, error: _error, ...props }, ref) => {
    return (
      <div className="relative">
        <select
          ref={ref}
          aria-invalid={ariaInvalid}
          aria-describedby={ariaDescribedby}
          className={cn(
            "block w-full rounded-[0.5rem] border bg-bg px-4 py-2.5 pr-10 text-sm text-primary appearance-none",
            "transition-all duration-200",
            "hover:border-brand-primary/30",
            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary/30 focus-visible:border-brand-primary",
            "disabled:cursor-not-allowed disabled:opacity-50",
            ariaInvalid && ariaInvalid !== "false" ? "border-error focus-visible:ring-error/30 focus-visible:border-error" : "border-[var(--color-border)]",
            className,
          )}
          {...props}
        >
          {children}
        </select>
        <ChevronDown className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-primary-muted" aria-hidden="true" />
      </div>
    )
  }
)
Select.displayName = "Select"
