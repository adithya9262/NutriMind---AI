import { cn } from "@/lib/utils"

interface ChipProps {
  children: React.ReactNode
  variant?: "primary" | "accent" | "neutral" | "success" | "warning"
  className?: string
  icon?: React.ReactNode
}

const variants = {
  primary: "bg-brand-primary/10 text-primary border-brand-primary/20",
  accent: "bg-accent/10 text-accent border-accent/20",
  neutral: "bg-white/5 text-primary-secondary border-[var(--color-border)]",
  success: "bg-success/10 text-success border-success/20",
  warning: "bg-warning/10 text-warning border-warning/20",
}

export function Chip({ children, variant = "primary", className = "", icon }: ChipProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-medium",
        variants[variant],
        className,
      )}
    >
      {icon}
      {children}
    </span>
  )
}
