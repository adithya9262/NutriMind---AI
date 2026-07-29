"use client"

import { Send, Paperclip, Mic } from "lucide-react"
import { cn } from "@/lib/utils"

interface ComposerProps {
  value: string
  onChange: (value: string) => void
  onSend: () => void
  disabled?: boolean
  placeholder?: string
}

export function Composer({ value, onChange, onSend, disabled, placeholder }: ComposerProps) {
  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      onSend()
    }
  }

  return (
    <div className="relative">
      <div className="relative flex items-center gap-1 rounded-3xl bg-surface-high/60 p-2 shadow-xl ring-1 ring-white/10 backdrop-blur-xl">
        <button
          type="button"
          aria-label="Attach bio-data"
          className="grid h-10 w-10 place-items-center rounded-2xl text-primary-muted transition-colors hover:bg-white/5 hover:text-brand-primary"
        >
          <Paperclip className="h-5 w-5" aria-hidden="true" />
        </button>

        <input
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder ?? "Ask NutriMind anything about your performance…"}
          disabled={disabled}
          aria-label="Chat message"
          className="flex-1 border-none bg-transparent px-2 py-3 text-base text-primary placeholder:text-primary-muted focus:outline-none focus:ring-0 disabled:opacity-50"
        />

        <div className="flex items-center gap-1 px-2">
          <button
            type="button"
            aria-label="Voice input"
            className="grid h-12 w-12 place-items-center rounded-2xl text-primary-muted transition-colors hover:bg-white/5 hover:text-brand-primary"
          >
            <Mic className="h-5 w-5" aria-hidden="true" />
          </button>
          <button
            type="button"
            onClick={onSend}
            disabled={disabled || !value.trim()}
            aria-label="Send message"
            className={cn(
              "grid h-12 w-12 place-items-center rounded-2xl bg-brand-primary text-[#003111] shadow-lg shadow-brand-primary/30 transition-all",
              "hover:brightness-110 active:scale-95 disabled:cursor-not-allowed disabled:opacity-40",
            )}
          >
            <Send className="h-5 w-5" aria-hidden="true" />
          </button>
        </div>
      </div>
    </div>
  )
}
