import { forwardRef, type TextareaHTMLAttributes } from "react"
import { cn } from "@/lib/utils"

interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  "aria-label"?: string
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className = "", ...props }, ref) => {
    return (
      <textarea
        ref={ref}
        className={cn(
          "block w-full rounded-[0.5rem] border border-[var(--color-border)] bg-bg px-4 py-2.5 text-sm text-primary resize-y min-h-[80px]",
          "placeholder:text-primary-muted",
          "transition-all duration-200",
          "hover:border-brand-primary/30",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary/30 focus-visible:border-brand-primary",
          "disabled:cursor-not-allowed disabled:opacity-50",
          className,
        )}
        {...props}
      />
    )
  }
)
Textarea.displayName = "Textarea"
