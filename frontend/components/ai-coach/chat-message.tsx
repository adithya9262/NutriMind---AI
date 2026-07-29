import { Avatar } from "@/components/ui/avatar"
import { cn } from "@/lib/utils"

export interface ChatMessageData {
  id: string
  role: "user" | "assistant"
  content: string
  timestamp?: string
}

interface ChatMessageProps {
  message: ChatMessageData
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === "user"
  return (
    <div className={cn("flex gap-3 max-w-5xl", isUser ? "self-end flex-row-reverse" : "self-start")}>
      {isUser ? (
        <div className="h-9 w-9 flex-shrink-0 self-start rounded-full border-2 border-brand-primary/40">
          <Avatar initials="U" size="sm" alt="You" className="h-full w-full" />
        </div>
      ) : (
        <div className="grid h-9 w-9 flex-shrink-0 self-start place-items-center rounded-2xl border border-brand-primary/20 bg-brand-primary/10 text-brand-primary">
          <span className="text-base font-bold">N</span>
        </div>
      )}

      <div className={cn("flex flex-col gap-1", isUser && "items-end")}>
        <div
          className={cn(
            "rounded-3xl px-4 py-3 text-sm leading-relaxed sm:text-[15px]",
            isUser
              ? "rounded-tr-md bg-gradient-to-br from-brand-primary to-[#14803b] text-[#003111]"
              : "chat-bubble-ai rounded-tl-md border border-white/5 text-primary",
          )}
        >
          {message.content}
        </div>
        {message.timestamp && (
          <span className="px-2 text-[10px] font-bold uppercase tracking-widest text-primary-muted">
            {isUser ? "Sent" : "NutriMind Core"} • {message.timestamp}
          </span>
        )}
      </div>
    </div>
  )
}
