import { type LabelHTMLAttributes } from "react"
import { cn } from "@/lib/utils"

interface LabelProps extends LabelHTMLAttributes<HTMLLabelElement> {
  required?: boolean
}

export function Label({
  className = "",
  required = false,
  children,
  ...props
}: LabelProps) {
  return (
    <label
      className={cn(
        "block text-sm font-medium text-primary mb-1.5",
        className,
      )}
      {...props}
    >
      {children}
      {required && (
        <span className="text-error ml-0.5" aria-hidden="true">*</span>
      )}
    </label>
  )
}
