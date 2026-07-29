import { type HTMLAttributes } from "react"
import Image from "next/image"
import { cn } from "@/lib/utils"

interface AvatarProps extends HTMLAttributes<HTMLDivElement> {
  initials?: string
  size?: "sm" | "md" | "lg"
  src?: string
  alt?: string
}

export function Avatar({
  className = "",
  initials,
  size = "md",
  src,
  alt = "",
  ...props
}: AvatarProps) {
  const sizeClasses = {
    sm: "h-8 w-8 text-xs",
    md: "h-10 w-10 text-sm",
    lg: "h-12 w-12 text-base",
  }

  if (src) {
    return (
      <div
        className={cn("rounded-full overflow-hidden flex-shrink-0", sizeClasses[size], className)}
        {...props}
      >
        <Image src={src} alt={alt} width={128} height={128} className="h-full w-full object-cover" unoptimized />
      </div>
    )
  }

  return (
    <div
      className={cn(
        "rounded-full flex items-center justify-center font-semibold flex-shrink-0",
        "gradient-brand text-white",
        sizeClasses[size],
        className,
      )}
      aria-label={alt || initials || "Avatar"}
      {...props}
    >
      {initials || "?"}
    </div>
  )
}
