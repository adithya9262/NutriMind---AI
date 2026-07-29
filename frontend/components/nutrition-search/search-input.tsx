"use client"

import { Search, X } from "lucide-react"
import { Input } from "@/components/ui/input"
import { cn } from "@/lib/utils"

interface SearchInputProps {
  value: string
  onChange: (value: string) => void
  onSubmit: (value: string) => void
  loading?: boolean
  className?: string
}

export function SearchInput({
  value,
  onChange,
  onSubmit,
  loading = false,
  className,
}: SearchInputProps) {
  return (
    <form
      className={cn(
        "relative w-full rounded-full transition-all duration-300 border border-border bg-surface-low overflow-hidden focus-within:border-brand focus-within:shadow-[0_0_20px_rgba(98,223,125,0.15)]",
        className,
      )}
      onSubmit={(e) => {
        e.preventDefault()
        onSubmit(value)
      }}
      role="search"
    >
      <Search
        className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-primary-muted"
        aria-hidden="true"
      />
      <Input
        type="search"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Search clinical-grade nutrition..."
        aria-label="Search nutrition"
        className="border-0 bg-transparent rounded-full py-3.5 pl-12 pr-12 text-primary placeholder:text-primary-muted/50 focus-visible:ring-0 focus-visible:border-0"
      />
      {value && (
        <button
          type="button"
          onClick={() => onChange("")}
          aria-label="Clear search"
          className="absolute right-4 top-1/2 -translate-y-1/2 text-primary-muted hover:text-primary transition-colors"
        >
          <X className="h-4 w-4" aria-hidden="true" />
        </button>
      )}
      {loading && (
        <span
          className="absolute right-4 top-1/2 -translate-y-1/2 h-4 w-4 animate-spin rounded-full border-2 border-border border-t-brand"
          aria-hidden="true"
        />
      )}
    </form>
  )
}
