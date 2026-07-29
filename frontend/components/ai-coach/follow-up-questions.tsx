import React from "react"
import { MessageCircleQuestion } from "lucide-react"

interface FollowUpData {
  type: string
  questions: string[]
}

export function FollowUpQuestions({ data, onSelect }: { data: FollowUpData, onSelect: (q: string) => void }) {
  if (!data.questions || data.questions.length === 0) return null

  return (
    <div className="my-4 space-y-2">
      <div className="flex items-center gap-2 text-xs font-medium text-primary-secondary uppercase tracking-wider pl-1">
        <MessageCircleQuestion className="h-3.5 w-3.5" />
        <span>Suggested Questions</span>
      </div>
      <div className="flex flex-wrap gap-2">
        {data.questions.map((q, idx) => (
          <button
            key={idx}
            onClick={() => onSelect(q)}
            className="rounded-full border border-brand/30 bg-brand/5 px-3 py-1.5 text-xs text-brand transition-colors hover:bg-brand hover:text-white"
          >
            {q}
          </button>
        ))}
      </div>
    </div>
  )
}
