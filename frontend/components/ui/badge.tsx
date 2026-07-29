import { type HTMLAttributes } from "react"
import { cn } from "@/lib/utils"

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: "default" | "success" | "warning" | "error" | "info" | "brand"
  size?: "sm" | "md"
}

export function Badge({
  className = "",
  variant = "default",
  size = "sm",
  children,
  ...props
}: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center font-medium rounded-lg",
        size === "sm" && "px-2 py-0.5 text-xs",
        size === "md" && "px-2.5 py-1 text-xs",
        variant === "default" && "bg-background text-primary-secondary border border-border",
        variant === "success" && "bg-success-light text-success",
        variant === "warning" && "bg-warning-light text-warning",
        variant === "error" && "bg-error-light text-error",
        variant === "info" && "bg-info-light text-info",
        variant === "brand" && "bg-brand-light text-brand",
        className,
      )}
      {...props}
    >
      {children}
    </span>
  )
}
