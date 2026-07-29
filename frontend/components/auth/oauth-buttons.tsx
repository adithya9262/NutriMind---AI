import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

interface OAuthButtonsProps {
  onGoogle?: () => void
  onApple?: () => void
  disabled?: boolean
  className?: string
}

export function OAuthButtons({ onGoogle, onApple, disabled, className = "" }: OAuthButtonsProps) {
  return (
    <div className={cn("grid grid-cols-2 gap-3", className)}>
      <Button
        type="button"
        variant="secondary"
        className="w-full"
        onClick={onGoogle}
        disabled={disabled}
        aria-label="Continue with Google"
      >
        <GoogleIcon className="h-4 w-4" />
        Google
      </Button>
      <Button
        type="button"
        variant="secondary"
        className="w-full"
        onClick={onApple}
        disabled={disabled}
        aria-label="Continue with Apple"
      >
        <AppleIcon className="h-4 w-4" />
        Apple
      </Button>
    </div>
  )
}

function GoogleIcon({ className = "" }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" className={className} aria-hidden="true" fill="none">
      <path d="M21.35 12.08c0-.68-.06-1.34-.18-1.97H12v3.72h5.27a4.5 4.5 0 0 1-1.95 2.95v2.45h3.15c1.85-1.7 2.88-4.2 2.88-7.15Z" fill="#4285F4" />
      <path d="M12 22c2.7 0 4.96-.9 6.62-2.43l-3.15-2.45c-.87.59-1.99.94-3.47.94-2.67 0-4.93-1.8-5.74-4.22H3.03v2.65A10 10 0 0 0 12 22Z" fill="#34A853" />
      <path d="M6.26 13.84A6 6 0 0 1 5.9 12c0-.64.11-1.26.27-1.84V7.51H3.03A10 10 0 0 0 2 12c0 1.61.39 3.14 1.03 4.49l3.23-2.65Z" fill="#FBBC05" />
      <path d="M12 5.98c1.51 0 2.86.52 3.93 1.54l2.94-2.94A10 10 0 0 0 12 2 10 10 0 0 0 3.03 7.51l3.23 2.65C7.07 7.78 9.33 5.98 12 5.98Z" fill="#EA4335" />
    </svg>
  )
}

function AppleIcon({ className = "" }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" className={className} aria-hidden="true" fill="currentColor">
      <path d="M16.37 12.78c.03 2.83 2.47 3.77 2.5 3.78-.02.06-.39 1.34-1.29 2.66-.78 1.14-1.59 2.28-2.87 2.3-1.26.03-1.66-.74-3.1-.74-1.43 0-1.88.72-3.06.77-1.23.05-2.17-1.25-2.96-2.5-1.62-2.34-2.86-6.62-1.2-9.5.83-1.43 2.32-2.36 3.93-2.38 1.27-.02 2.47.85 3.1.85.62 0 1.79-.84 3.02-.72 1.64.13 2.88.94 3.2 2.39-2.66 1.62-2.22 6.02-1.27 7.59Zm-3.24-7.2c.68-.83 1.14-1.98.98-3.12-.97.04-2.18.66-2.88 1.49-.56.72-1.08 1.9-.94 3.01.53.04 2.16-.68 2.84-1.38Z" />
    </svg>
  )
}
