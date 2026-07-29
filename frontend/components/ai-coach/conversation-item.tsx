"use client"

import { cn } from "@/lib/utils"
import type { DemoConversation } from "./placeholders"

interface ConversationItemProps {
  conversation: DemoConversation
  onSelect?: (id: string) => void
}

export function ConversationItem({ conversation, onSelect }: ConversationItemProps) {
  return (
    <button
      type="button"
      onClick={() => onSelect?.(conversation.id)}
      className={cn(
        "w-full rounded-2xl border p-4 text-left transition-all",
        conversation.active
          ? "border-brand-primary/20 bg-brand-primary/5"
          : "border-transparent hover:bg-white/5",
      )}
    >
      <div className="mb-1 flex items-start justify-between gap-2">
        <span className={cn("text-sm font-semibold", conversation.active ? "text-brand-primary" : "text-primary/80")}>
          {conversation.title}
        </span>
        <span className="text-[10px] font-bold uppercase tracking-tighter text-primary-muted">
          {conversation.active ? "Active" : conversation.meta}
        </span>
      </div>
      <p className="truncate text-sm text-primary-muted">{conversation.preview}</p>
    </button>
  )
}
