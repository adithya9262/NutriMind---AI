import { cn } from "@/lib/utils"

interface SkeletonProps {
  className?: string
  variant?: "text" | "circular" | "rectangular"
}

const variantStyles: Record<string, string> = {
  text: "h-4 w-full rounded-lg",
  circular: "h-10 w-10 rounded-full",
  rectangular: "h-24 w-full rounded-2xl",
}

export function Skeleton({
  className = "",
  variant = "text",
}: SkeletonProps) {
  return (
    <div
      role="status"
      aria-label="Loading"
      className={cn(
        "animate-shimmer rounded-lg",
        variantStyles[variant],
        className,
      )}
    />
  )
}
