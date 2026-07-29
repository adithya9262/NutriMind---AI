"use client"

import { Plus } from "lucide-react"
import { ConversationItem } from "./conversation-item"
import type { DemoConversation } from "./placeholders"

interface ConversationSidebarProps {
  conversations: DemoConversation[]
  onSelect?: (id: string) => void
  onNew?: () => void
}

export function ConversationSidebar({ conversations, onSelect, onNew }: ConversationSidebarProps) {
  return (
    <aside className="glass hidden w-72 flex-col border-r border-border md:flex">
      <div className="flex items-center justify-between border-b border-border p-4">
        <h2 className="text-lg font-semibold text-primary">History</h2>
        <button
          type="button"
          onClick={onNew}
          aria-label="New conversation"
          className="grid h-9 w-9 place-items-center rounded-xl bg-white/5 text-primary-muted transition-colors hover:bg-brand-primary/10 hover:text-brand-primary"
        >
          <Plus className="h-5 w-5" aria-hidden="true" />
        </button>
      </div>

      <div className="flex flex-1 flex-col gap-2 overflow-y-auto chat-scroll p-3">
        {conversations.map((c) => (
          <ConversationItem key={c.id} conversation={c} onSelect={onSelect} />
        ))}
      </div>
    </aside>
  )
}
