import type { ReactNode } from "react"
import { cn } from "@/lib/utils"
import { Label } from "./label"

interface FormFieldProps {
  label?: string
  required?: boolean
  error?: string | null
  htmlFor?: string
  children: ReactNode
  className?: string
}

export function FormField({
  label,
  required = false,
  error,
  htmlFor,
  children,
  className = "",
}: FormFieldProps) {
  return (
    <div className={cn("space-y-1", className)}>
      {label && (
        <Label htmlFor={htmlFor} required={required}>
          {label}
        </Label>
      )}
      {children}
      {error && (
        <p className="text-xs text-error mt-1" role="alert">
          {error}
        </p>
      )}
    </div>
  )
}
