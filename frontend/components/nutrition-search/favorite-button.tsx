"use client"

import { Star } from "lucide-react"
import { cn } from "@/lib/utils"

interface FavoriteButtonProps {
  active: boolean
  onToggle: () => void
  label: string
}

export function FavoriteButton({ active, onToggle, label }: FavoriteButtonProps) {
  return (
    <button
      type="button"
      onClick={onToggle}
      aria-label={label}
      aria-pressed={active}
      className={cn(
        "p-1.5 rounded-full backdrop-blur-md border border-white/10 transition-colors",
        active ? "text-brand bg-black/40" : "text-primary-muted/60 bg-black/40 hover:text-brand",
      )}
    >
      <Star className={cn("h-[18px] w-[18px]", active && "fill-current")} aria-hidden="true" />
    </button>
  )
}
