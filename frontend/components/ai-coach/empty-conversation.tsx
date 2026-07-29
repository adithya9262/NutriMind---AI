"use client"

import { Sparkles, Activity, Apple } from "lucide-react"

interface EmptyConversationProps {
  onPrompt?: (prompt: string) => void
}

export function EmptyConversation({ onPrompt }: EmptyConversationProps) {
  const tiles = [
    { icon: Activity, title: "Daily Bio-Sync", desc: "Analyze sleep and heart rate variability data." },
    { icon: Apple, title: "Meal Protocol", desc: "Design a macro plan for your next workout." },
  ]

  return (
    <div className="flex flex-col items-center justify-center p-8 text-center">
      <div className="relative mb-6 grid h-24 w-24 place-items-center rounded-3xl bg-brand-primary/5">
        <div className="absolute inset-0 rounded-full bg-brand-primary/20 blur-2xl" />
        <Sparkles className="relative z-10 h-10 w-10 text-brand-primary" aria-hidden="true" />
      </div>
      <h2 className="mb-2 text-2xl font-bold text-primary">Peak Performance Starts Here</h2>
      <p className="mb-10 max-w-sm text-primary-muted">
        Your biology is unique. Let&apos;s optimize your day based on your latest biometric sync.
      </p>
      <div className="grid max-w-xl grid-cols-1 gap-4 sm:grid-cols-2">
        {tiles.map((tile) => (
          <button
            key={tile.title}
            type="button"
            onClick={() => onPrompt?.(tile.title)}
            className="rounded-2xl border border-border bg-white/5 p-6 text-left transition-all hover:bg-white/10"
          >
            <tile.icon className="mb-3 h-5 w-5 text-brand-primary" aria-hidden="true" />
            <h4 className="font-bold text-primary">{tile.title}</h4>
            <p className="mt-1 text-xs text-primary-muted">{tile.desc}</p>
          </button>
        ))}
      </div>
    </div>
  )
}
