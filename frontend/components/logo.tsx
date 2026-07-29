import { cn } from "@/lib/utils"

interface LogoProps {
  className?: string
  showWordmark?: boolean
  size?: number
}

export function Logo({ className = "", showWordmark = true, size = 28 }: LogoProps) {
  return (
    <span className={cn("inline-flex items-center gap-2.5", className)}>
      <svg
        width={size}
        height={size}
        viewBox="0 0 32 32"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        aria-hidden="true"
        className="flex-shrink-0"
      >
        <defs>
          <linearGradient id="nm-grad" x1="0" y1="0" x2="32" y2="32" gradientUnits="userSpaceOnUse">
            <stop stopColor="#62df7d" />
            <stop offset="1" stopColor="#16a34a" />
          </linearGradient>
        </defs>
        <rect x="1" y="1" width="30" height="30" rx="9" stroke="url(#nm-grad)" strokeWidth="1.5" fill="#0d1f17" />
        {/* Leaf / molecule mark */}
        <path
          d="M16 7c-4.5 1-7 4.5-7 9 0 2 .6 3.8 1.7 5.3M16 7c4.5 1 7 4.5 7 9 0 2-.6 3.8-1.7 5.3"
          stroke="url(#nm-grad)"
          strokeWidth="1.8"
          strokeLinecap="round"
        />
        <path d="M16 7v15" stroke="url(#nm-grad)" strokeWidth="1.8" strokeLinecap="round" />
        <circle cx="16" cy="14.5" r="1.6" fill="#62df7d" />
        <circle cx="12.4" cy="18.5" r="1.2" fill="#94de2d" />
        <circle cx="19.6" cy="18.5" r="1.2" fill="#94de2d" />
      </svg>
      {showWordmark && (
        <span className="font-semibold text-primary text-lg tracking-tight leading-none">
          NutriMind <span className="text-primary/70 font-normal">AI</span>
        </span>
      )}
    </span>
  )
}
