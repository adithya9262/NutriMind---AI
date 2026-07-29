import { type HTMLAttributes } from "react"
import { cn } from "@/lib/utils"

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "elevated" | "glass" | "brand"
}

export function Card({
  className = "",
  variant = "default",
  children,
  ...props
}: CardProps) {
  return (
    <div
      className={cn(
        "rounded-xl transition-all duration-200",
        variant === "default" && "bg-surface border border-[var(--color-border)]",
        variant === "elevated" && "card-surface card-hover",
        variant === "glass" && "glass rounded-2xl",
        variant === "brand" && "gradient-brand text-white shadow-lg",
        className,
      )}
      {...props}
    >
      {children}
    </div>
  )
}
