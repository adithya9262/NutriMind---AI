import { forwardRef, type ButtonHTMLAttributes } from "react"
import { cn } from "@/lib/utils"

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost" | "danger" | "glass"
  size?: "sm" | "md" | "lg"
  pill?: boolean
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className = "", variant = "primary", size = "md", type = "button", pill = false, disabled, children, ...props }, ref) => {
    return (
      <button
        ref={ref}
        type={type}
        disabled={disabled}
        aria-disabled={disabled || undefined}
        className={cn(
          "inline-flex items-center justify-center font-semibold transition-all duration-200",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--color-bg)]",
          "disabled:opacity-50 disabled:pointer-events-none",
          "active:scale-[0.97]",
          variant === "primary" && [
            "bg-brand text-white shadow-md",
            "hover:bg-brand-hover hover:shadow-lg",
            "focus-visible:ring-brand-primary",
          ],
          variant === "secondary" && [
            "bg-surface-high/60 text-primary border border-[var(--color-border)]",
            "hover:bg-surface-highest/60 hover:border-[var(--color-border-light)]",
            "focus-visible:ring-brand-primary",
          ],
          variant === "ghost" && [
            "text-primary-secondary hover:text-primary",
            "hover:bg-brand-primary/10",
            "focus-visible:ring-brand-primary",
          ],
          variant === "danger" && [
            "bg-error text-[#690005] shadow-md",
            "hover:bg-red-300 hover:shadow-lg",
            "focus-visible:ring-error",
          ],
          variant === "glass" && [
            "glass text-primary",
            "hover:bg-white/5 hover:shadow-lg",
            "focus-visible:ring-white/40",
          ],
          size === "sm" && "min-h-[36px] h-9 px-3.5 text-xs gap-1.5",
          size === "md" && "min-h-[40px] h-10 px-5 text-sm gap-2",
          size === "lg" && "min-h-[48px] h-12 px-7 text-base gap-2.5",
          pill ? "rounded-full" : "rounded-[1rem]",
          className,
        )}
        {...props}
      >
        {children}
      </button>
    )
  }
)
Button.displayName = "Button"
