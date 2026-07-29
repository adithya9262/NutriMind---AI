import { forwardRef, type InputHTMLAttributes } from "react"
import { cn } from "@/lib/utils"

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  "aria-label"?: string
  "aria-invalid"?: boolean | "true" | "false"
  "aria-describedby"?: string
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className = "", "aria-label": ariaLabel, "aria-invalid": ariaInvalid, "aria-describedby": ariaDescribedby, ...props }, ref) => {
    return (
      <input
        ref={ref}
        aria-label={ariaLabel}
        aria-invalid={ariaInvalid}
        aria-describedby={ariaDescribedby}
        className={cn(
          "block w-full rounded-[0.5rem] border bg-bg px-4 py-2.5 text-sm text-primary",
          "placeholder:text-primary-muted",
          "transition-all duration-200",
          "hover:border-brand-primary/30",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary/30 focus-visible:border-brand-primary",
          "disabled:cursor-not-allowed disabled:opacity-50 disabled:bg-surface-low",
          ariaInvalid && ariaInvalid !== "false" && "border-error focus-visible:ring-error/30 focus-visible:border-error",
          !ariaInvalid || ariaInvalid === "false" ? "border-[var(--color-border)]" : "",
          className,
        )}
        {...props}
      />
    )
  }
)
Input.displayName = "Input"
