"use client"

import {
  useState, useRef, useEffect, useCallback, useMemo,
  type KeyboardEvent,
} from "react"
import { motion, AnimatePresence } from "framer-motion"
import {
  Bot, Send, Sparkles, MessageSquare, Trash2, Menu, X, Plus,
  Pencil, Check, Search, BarChart2, Clock, User, Copy, RefreshCw, StopCircle, ThumbsUp, ThumbsDown, Download, Pin
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Spinner } from "@/components/ui/spinner"
import { Alert } from "@/components/ui/alert"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import {
  getSessions, deleteSession, renameSession, togglePinSession,
  getSessionMessages, submitMessageFeedback, type ChatSession, type UsagePeriod,
} from "@/services/api/ai-coach"
import { getProgressReport, getChatExport } from "@/services/api/reports"
import { useAIUsage, formatResetCountdown } from "@/hooks/use-ai-usage"
import { useNutritionProfile } from "@/hooks/use-nutrition-profile"
import { useBodyWeight } from "@/hooks/use-body-weight"
import { cn } from "@/lib/utils"
import { SmartNutritionCard } from "@/components/ai-coach/smart-nutrition-card"
import { FollowUpQuestions } from "@/components/ai-coach/follow-up-questions"

// ── Types ─────────────────────────────────────────────────────────────────────
interface Message { id?: string; role: "user" | "assistant"; content: string; created_at?: string; is_helpful?: boolean | null; is_not_helpful?: boolean | null; }

// ── Usage History Modal ───────────────────────────────────────────────────────
function UsageHistoryModal({
  onClose,
  period,
  history,
  historyLoading,
  loadHistory,
}: {
  onClose: () => void
  period: UsagePeriod
  history: ReturnType<typeof useAIUsage>["history"]
  historyLoading: boolean
  loadHistory: (p: UsagePeriod) => void
}) {
  const PERIODS: { label: string; value: UsagePeriod }[] = [
    { label: "Today", value: "today" },
    { label: "Yesterday", value: "yesterday" },
    { label: "7 Days", value: "7d" },
    { label: "30 Days", value: "30d" },
    { label: "All Time", value: "all" },
  ]

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4"
      onClick={onClose}
    >
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        transition={{ duration: 0.18 }}
        onClick={(e) => e.stopPropagation()}
        className="w-full max-w-md rounded-2xl border border-border bg-surface p-6 shadow-2xl"
      >
        <div className="flex items-center justify-between mb-5">
          <h3 className="text-base font-semibold text-primary flex items-center gap-2">
            <BarChart2 className="h-4 w-4 text-brand" />
            AI Usage History
          </h3>
          <button onClick={onClose} className="p-1 rounded-lg hover:bg-surface-high">
            <X className="h-4 w-4 text-primary-secondary" />
          </button>
        </div>

        {/* Period selector */}
        <div className="flex gap-2 mb-4 flex-wrap">
          {PERIODS.map((p) => (
            <button
              key={p.value}
              onClick={() => loadHistory(p.value)}
              className={cn(
                "px-3 py-1.5 rounded-lg text-xs font-medium border transition-all",
                period === p.value
                  ? "bg-brand text-white border-brand"
                  : "border-border text-primary-secondary hover:bg-surface-high",
              )}
            >
              {p.label}
            </button>
          ))}
        </div>

        {historyLoading ? (
          <div className="flex justify-center py-8"><Spinner size="md" /></div>
        ) : history ? (
          <div className="space-y-4">
            {/* Aggregates */}
            <div className="grid grid-cols-3 gap-3">
              {[
                { label: "Messages", value: history.total_messages },
                { label: "Sessions", value: history.total_sessions },
                {
                  label: "Avg Time",
                  value: history.avg_response_time_ms
                    ? `${(history.avg_response_time_ms / 1000).toFixed(1)}s`
                    : "—",
                },
              ].map((stat) => (
                <div key={stat.label} className="rounded-xl bg-surface-high p-3 text-center">
                  <p className="text-lg font-bold text-primary">{stat.value}</p>
                  <p className="text-xs text-primary-secondary">{stat.label}</p>
                </div>
              ))}
            </div>

            {/* Per-day rows */}
            {history.entries.length > 0 ? (
              <div className="space-y-1.5 max-h-52 overflow-y-auto pr-1">
                {history.entries.map((e) => (
                  <div key={e.usage_date} className="flex items-center justify-between rounded-lg px-3 py-2 bg-surface-high text-sm">
                    <span className="text-primary-secondary">{e.usage_date}</span>
                    <div className="flex gap-4">
                      <span className="text-primary font-medium">{e.messages_used} msgs</span>
                      {e.images_used > 0 && (
                        <span className="text-primary-secondary">{e.images_used} imgs</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-center text-sm text-primary-muted py-4">No usage in this period.</p>
            )}
          </div>
        ) : null}
      </motion.div>
    </div>
  )
}

// ── Sidebar session item ──────────────────────────────────────────────────────
function SessionItem({
  session,
  isActive,
  onSelect,
  onDelete,
  onRename,
  onPin,
}: {
  session: ChatSession
  isActive: boolean
  onSelect: () => void
  onDelete: () => void
  onRename: (title: string) => void
  onPin?: () => void
}) {
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState(session.title)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (editing) inputRef.current?.focus()
  }, [editing])

  function commitRename() {
    const trimmed = draft.trim()
    if (trimmed && trimmed !== session.title) onRename(trimmed)
    setEditing(false)
  }

  function handleKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter") commitRename()
    if (e.key === "Escape") { setDraft(session.title); setEditing(false) }
  }

  return (
    <div
      onClick={editing ? undefined : onSelect}
      className={cn(
        "group flex cursor-pointer items-center gap-2 rounded-xl px-3 py-2.5 text-sm transition-all",
        isActive
          ? "bg-brand/10 text-brand"
          : "text-primary-secondary hover:bg-surface-highest/60 hover:text-primary",
      )}
    >
      <MessageSquare className={cn("h-3.5 w-3.5 shrink-0 opacity-60", session.pinned && "fill-brand/20 text-brand opacity-100")} />

      {editing ? (
        <input
          ref={inputRef}
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={handleKeyDown}
          onBlur={commitRename}
          onClick={(e) => e.stopPropagation()}
          className="flex-1 min-w-0 bg-transparent text-sm outline-none border-b border-brand/50"
        />
      ) : (
        <span className="flex-1 truncate font-medium">{session.title}</span>
      )}

      <div className="flex shrink-0 items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
        {editing ? (
          <button
            onClick={(e) => { e.stopPropagation(); commitRename() }}
            className="rounded p-1 hover:bg-brand/10 text-brand"
          >
            <Check className="h-3 w-3" />
          </button>
        ) : (
          <button
            onClick={(e) => { e.stopPropagation(); setDraft(session.title); setEditing(true) }}
            className="rounded p-1 hover:bg-surface-high"
            title="Rename"
          >
            <Pencil className="h-3 w-3" />
          </button>
        )}
        {onPin && (
          <button
            onClick={(e) => { e.stopPropagation(); onPin() }}
            className={cn("rounded p-1 hover:bg-surface-high", session.pinned && "text-brand")}
            title={session.pinned ? "Unpin" : "Pin"}
          >
            <Pin className="h-3 w-3" />
          </button>
        )}
        <button
          onClick={(e) => { e.stopPropagation(); onDelete() }}
          className="rounded p-1 hover:bg-red-500/10 hover:text-red-500"
          title="Delete"
        >
          <Trash2 className="h-3 w-3" />
        </button>
      </div>
    </div>
  )
}

// ── Main Page ─────────────────────────────────────────────────────────────────
export default function AICoachPage() {
  // ── Chat state ──────────────────────────────────────────────────────────
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [isSending, setIsSending] = useState(false)
  const [isLoadingMessages, setIsLoadingMessages] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null)

  // ── Sidebar state ────────────────────────────────────────────────────────
  const [sessions, setSessions] = useState<ChatSession[]>([])
  const [sessionsLoading, setSessionsLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState("")
  const [isSidebarOpen, setIsSidebarOpen] = useState(false)

  // ── Usage ────────────────────────────────────────────────────────────────
  const {
    usage, usageLoading,
    history, historyLoading, historyPeriod,
    msUntilReset,
    refreshUsage, loadHistory, optimisticMessageIncrement,
  } = useAIUsage()
  const [showHistory, setShowHistory] = useState(false)

  // ── Profile data for contextual suggestions ──────────────────────────────
  const { profile, profileStatus, calculations, calculationsStatus } = useNutritionProfile()
  const { entries: weightEntries } = useBodyWeight()
  const hasProfile = profileStatus === "available" && profile
  const profileComplete = calculationsStatus === "available" && calculations !== null

  const suggestedPrompts = useMemo(() => {
    if (!hasProfile || !profileComplete) {
      return [
        "How do I set up my nutrition profile?",
        "What information do you need from me?",
        "Help me start tracking my nutrition",
        "How does the AI coach work?",
      ]
    }
    const prompts: string[] = []
    const goal = profile.fitness_goal || profile.goal
    if (goal) {
      if (goal.includes("weight") || goal.includes("lose") || goal.includes("loss")) {
        prompts.push("Help me lose weight effectively")
      } else if (goal.includes("muscle") || goal.includes("gain")) {
        prompts.push("How can I build more muscle?")
      } else {
        prompts.push("Help me reach my fitness goal")
      }
    }
    const latestWeight = weightEntries.length > 0 ? weightEntries[weightEntries.length - 1] : null
    if (latestWeight) {
      prompts.push("Is my current weight healthy for me?")
    }
    prompts.push("What should I eat today?")
    if (profile.dietary_preference && profile.dietary_preference !== "no_preference") {
      prompts.push(`Suggest a ${profile.dietary_preference} meal plan`)
    } else {
      prompts.push("Create a balanced meal plan for today")
    }
    prompts.push("How can I improve my nutrition?")
    return prompts.slice(0, 4)
  }, [hasProfile, profileComplete, profile, weightEntries])

  // ── Refs ─────────────────────────────────────────────────────────────────
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const abortRef = useRef<AbortController | null>(null)
  const isStreamingRef = useRef(false)

  const atLimit = (usage?.messages_used ?? 0) >= (usage?.messages_limit ?? 25)

  // ── Session loader ───────────────────────────────────────────────────────
  const loadSessions = useCallback(async (search?: string) => {
    setSessionsLoading(true)
    const res = await getSessions(search)
    if (res.success && res.data) setSessions(res.data)
    setSessionsLoading(false)
  }, [])

  useEffect(() => { loadSessions() }, [loadSessions])

  // Debounced search
  useEffect(() => {
    const t = setTimeout(() => loadSessions(searchQuery || undefined), 300)
    return () => clearTimeout(t)
  }, [searchQuery, loadSessions])

  const scrollToBottom = useCallback((behavior: ScrollBehavior = "smooth") => {
    messagesEndRef.current?.scrollIntoView({ behavior })
  }, [])

  // ── Load messages when session changes ───────────────────────────────────
  useEffect(() => {
    if (!currentSessionId) { setMessages([]); return }
    if (isStreamingRef.current) return
    let ignore = false
    setIsLoadingMessages(true)
    getSessionMessages(currentSessionId)
      .then((res) => {
        if (ignore) return
        if (res.success && res.data) {
          setMessages(res.data.map((m) => ({ id: m.id, role: m.role as "user" | "assistant", content: m.content, is_helpful: m.is_helpful, is_not_helpful: m.is_not_helpful })))
        }
      })
      .finally(() => {
        if (ignore) return
        setIsLoadingMessages(false)
        scrollToBottom("auto")
      })
    return () => { ignore = true }
  }, [currentSessionId, scrollToBottom])

  useEffect(() => { scrollToBottom() }, [messages, scrollToBottom])

  useEffect(() => { inputRef.current?.focus() }, [currentSessionId])

  // ── Send message ─────────────────────────────────────────────────────────
  const handleSend = useCallback(
    async (overrideText?: string) => {
      const text = (overrideText ?? input).trim()
      if (!text || isSending) return
      if (atLimit) { setError("You've reached today's AI limit. Resets tomorrow."); return }

      setMessages((prev) => [...prev, { role: "user", content: text }])
      setInput("")
      setError(null)
      setIsSending(true)
      isStreamingRef.current = true
      optimisticMessageIncrement()

      abortRef.current?.abort()
      abortRef.current = new AbortController()

      try {
        const { getAccessToken } = await import("@/lib/token-storage")
        const token = getAccessToken("backend") || getAccessToken("supabase")

        const baseUrl = process.env.NEXT_PUBLIC_API_URL?.replace(/\/+$/, "") || ""
        const res = await fetch(`${baseUrl}/ai-coach/chat`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
          body: JSON.stringify({ message: text, session_id: currentSessionId, stream: true }),
          signal: abortRef.current.signal,
        })

        if (!res.ok) {
          const errBody = await res.json().catch(() => ({}))
          const detail = errBody?.detail
          if (typeof detail === "object" && detail?.code === "DAILY_LIMIT_REACHED") {
            setError("You've reached today's AI limit. Your quota resets automatically tomorrow.")
          } else {
            throw new Error(errBody?.message || `HTTP ${res.status}`)
          }
          return
        }

        const reader = res.body?.getReader()
        if (!reader) throw new Error("No response stream")

        setMessages((prev) => [...prev, { role: "assistant", content: "" }])

        let localSessionId = currentSessionId
        const decoder = new TextDecoder()
        let buf = ""

        while (true) {
          const { done, value } = await reader.read()
          if (done) break
          buf += decoder.decode(value, { stream: true })
          const lines = buf.split("\n")
          buf = lines.pop() ?? ""

          for (const line of lines) {
            if (!line.startsWith("data: ")) continue
            const raw = line.slice(6)
            if (raw === "[DONE]") {
              refreshUsage()
              loadSessions()
              break
            }
            try {
              const data = JSON.parse(raw)
              if (data.session_id && !localSessionId) {
                localSessionId = data.session_id
                setCurrentSessionId(data.session_id)
              }
              if (data.content) {
                setMessages((prev) => {
                  const copy = prev.map((m, i) =>
                    i === prev.length - 1 && m.role === "assistant"
                      ? { ...m, content: m.content + data.content }
                      : m
                  )
                  return copy
                })
              }
              if (data.error) setError(data.error)
            } catch { /* ignore partial JSON */ }
          }
        }
      } catch (err) {
        if (err instanceof Error && err.name === "AbortError") return
        setError(err instanceof Error ? err.message : "An unexpected error occurred.")
      } finally {
        isStreamingRef.current = false
        setIsSending(false)
        inputRef.current?.focus()
      }
    },
    [input, isSending, atLimit, currentSessionId,
      optimisticMessageIncrement, refreshUsage, loadSessions],
  )

  const handleKeyDown = useCallback(
    (e: KeyboardEvent<HTMLInputElement>) => {
      if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend() }
    },
    [handleSend],
  )

  // ── Session actions ──────────────────────────────────────────────────────
  const handleNewChat = useCallback(() => {
    abortRef.current?.abort()
    setCurrentSessionId(null)
    setMessages([])
    setError(null)
    setInput("")
    setIsSidebarOpen(false)
    inputRef.current?.focus()
  }, [])

  const handleRegenerate = useCallback(() => {
    if (isSending || messages.length < 2) return
    const lastUserMsg = [...messages].reverse().find((m) => m.role === "user")
    if (lastUserMsg) {
      setMessages((prev) => {
        const copy = [...prev]
        while (copy.length > 0 && copy[copy.length - 1].role === "assistant") {
          copy.pop()
        }
        return copy
      })
      handleSend(lastUserMsg.content)
    }
  }, [messages, isSending, handleSend])

  const handleStop = useCallback(() => {
    abortRef.current?.abort()
    setIsSending(false)
  }, [])

  const handleFeedback = useCallback(async (msgId: string, type: 'helpful' | 'not_helpful') => {
    if (!currentSessionId) return
    const isHelpful = type === 'helpful'
    try {
      await submitMessageFeedback(currentSessionId, msgId, {
        is_helpful: isHelpful ? true : undefined,
        is_not_helpful: !isHelpful ? true : undefined,
      })
      setMessages(prev => prev.map(m => {
        if (m.id === msgId) {
          return { ...m, is_helpful: isHelpful, is_not_helpful: !isHelpful }
        }
        return m
      }))
    } catch (e) {
      console.error(e)
    }
  }, [currentSessionId])

  const handleCopy = useCallback((text: string) => {
    navigator.clipboard.writeText(text)
  }, [])

  const handleExportChat = useCallback(async () => {
    if (!currentSessionId) return
    try {
      const text = await getChatExport(currentSessionId)
      const blob = new Blob([text], { type: "text/markdown;charset=utf-8" })
      const url = URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = `chat-export-${currentSessionId.slice(0, 8)}.md`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch (e) {
      console.error(e)
    }
  }, [currentSessionId])

  const handleExportProgress = useCallback(async () => {
    try {
      const text = await getProgressReport("weekly")
      const blob = new Blob([text], { type: "text/markdown;charset=utf-8" })
      const url = URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = `weekly-progress.md`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch (e) {
      console.error(e)
    }
  }, [])

  const handleSelectSession = useCallback((id: string) => {
    if (id === currentSessionId) return
    abortRef.current?.abort()
    setCurrentSessionId(id)
    setError(null)
    setIsSidebarOpen(false)
  }, [currentSessionId])

  const handleDeleteSession = useCallback(async (id: string) => {
    try {
      await deleteSession(id)
      if (currentSessionId === id) { setCurrentSessionId(null); setMessages([]) }
    } catch { /* handled by API client */ }
    loadSessions(searchQuery || undefined)
  }, [currentSessionId, loadSessions, searchQuery])

  const handleRenameSession = useCallback(async (id: string, title: string) => {
    try {
      await renameSession(id, title)
    } catch { /* handled by API client */ }
    loadSessions(searchQuery || undefined)
  }, [loadSessions, searchQuery])

  const handlePinSession = useCallback(async (id: string, currentPinned: boolean) => {
    try {
      await togglePinSession(id, !currentPinned)
    } catch { /* handled by API client */ }
    loadSessions(searchQuery || undefined)
  }, [loadSessions, searchQuery])

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <div className="flex h-[calc(100vh-5.5rem)] overflow-hidden rounded-2xl border border-border bg-surface">

      {/* ── Mobile overlay ─────────────────────────────────────────────── */}
      {isSidebarOpen && (
        <div
          className="fixed inset-0 z-20 bg-black/40 md:hidden"
          onClick={() => setIsSidebarOpen(false)}
        />
      )}

      {/* ── Sidebar ────────────────────────────────────────────────────── */}
      <aside className={cn(
        "fixed inset-y-0 left-0 z-30 flex w-72 flex-col border-r border-border bg-surface transition-transform duration-300",
        "md:static md:z-auto md:translate-x-0 md:inset-auto",
        isSidebarOpen ? "translate-x-0" : "-translate-x-full",
      )}>
        {/* New chat + close (mobile) */}
        <div className="flex items-center gap-2 border-b border-border p-3">
          <Button variant="primary" size="sm" className="flex-1 gap-1.5" onClick={handleNewChat}>
            <Plus className="h-3.5 w-3.5" /> New Chat
          </Button>
          <button
            onClick={() => setIsSidebarOpen(false)}
            className="md:hidden rounded-lg p-2 hover:bg-surface-high"
          >
            <X className="h-4 w-4 text-primary-secondary" />
          </button>
        </div>

        {/* Search */}
        <div className="px-3 pt-2 pb-1">
          <div className="relative">
            <Search className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-primary-muted" />
            <input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search chats…"
              className="w-full rounded-lg border border-border bg-surface-high py-2 pl-8 pr-3 text-xs text-primary placeholder:text-primary-muted focus:outline-none focus:ring-1 focus:ring-brand/40"
            />
          </div>
        </div>

        {/* Session list */}
        <div className="flex-1 overflow-y-auto px-2 py-1 space-y-0.5">
          {sessionsLoading ? (
            <div className="flex justify-center py-6"><Spinner size="sm" /></div>
          ) : sessions.length === 0 ? (
            <p className="text-center text-xs text-primary-muted pt-8">
              {searchQuery ? "No chats match your search." : "No conversations yet."}
            </p>
          ) : (
            sessions.map((s) => (
              <SessionItem
                key={s.id}
                session={s}
                isActive={s.id === currentSessionId}
                onSelect={() => handleSelectSession(s.id)}
                onDelete={() => handleDeleteSession(s.id)}
                onRename={(title) => handleRenameSession(s.id, title)}
                onPin={() => handlePinSession(s.id, !!s.pinned)}
              />
            ))
          )}
        </div>

        {/* Usage panel */}
        <div className="border-t border-border p-3 space-y-2.5">
          {/* Messages bar */}
          <div>
            <div className="flex items-center justify-between text-xs mb-1">
              <span className="text-primary-secondary font-medium">Messages</span>
              <span className={cn("font-semibold", atLimit ? "text-red-500" : "text-primary")}>
                {usage?.messages_used ?? 0} / {usage?.messages_limit ?? 25}
              </span>
            </div>
            <div className="h-1.5 w-full overflow-hidden rounded-full bg-surface-high">
              <div
                className={cn("h-full rounded-full transition-all duration-500",
                  atLimit ? "bg-red-500" : "bg-brand")}
                style={{ width: `${Math.min(((usage?.messages_used ?? 0) / (usage?.messages_limit ?? 25)) * 100, 100)}%` }}
              />
            </div>
          </div>

          {/* Images bar */}
          <div>
            <div className="flex items-center justify-between text-xs mb-1">
              <span className="text-primary-secondary font-medium">Images</span>
              <span className="font-semibold text-primary">
                {usage?.images_used ?? 0} / {usage?.images_limit ?? 5}
              </span>
            </div>
            <div className="h-1.5 w-full overflow-hidden rounded-full bg-surface-high">
              <div
                className="h-full rounded-full bg-brand/60 transition-all duration-500"
                style={{ width: `${Math.min(((usage?.images_used ?? 0) / (usage?.images_limit ?? 5)) * 100, 100)}%` }}
              />
            </div>
          </div>

          {/* Reset countdown + history button */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1 text-xs text-primary-muted">
              <Clock className="h-3 w-3" />
              <span>{usageLoading ? "…" : formatResetCountdown(msUntilReset)}</span>
            </div>
            <button
              onClick={() => { setShowHistory(true); loadHistory(historyPeriod) }}
              className="flex items-center gap-1 text-xs text-brand hover:underline font-medium"
            >
              <BarChart2 className="h-3 w-3" /> History
            </button>
          </div>
        </div>
      </aside>

      {/* ── Main chat area ──────────────────────────────────────────────── */}
      <div className="flex flex-1 min-w-0 flex-col overflow-hidden">

        {/* Header */}
        <header className="flex items-center justify-between border-b border-border px-4 py-3">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setIsSidebarOpen(true)}
              className="md:hidden rounded-xl p-2 hover:bg-surface-high"
            >
              <Menu className="h-5 w-5 text-primary-secondary" />
            </button>
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-brand/10">
              <Bot className="h-5 w-5 text-brand" />
            </div>
            <div className="min-w-0">
              <h1 className="text-base font-semibold text-primary leading-tight">AI Coach</h1>
              <p className="text-xs text-primary-secondary truncate">
                {currentSessionId
                  ? sessions.find((s) => s.id === currentSessionId)?.title ?? "Session active"
                  : "Start a new conversation"}
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            <button onClick={handleExportProgress} title="Export Weekly Report" className="p-2 rounded-xl text-primary-secondary hover:text-primary hover:bg-surface-high transition-colors">
              <BarChart2 className="h-4 w-4" />
            </button>
            {currentSessionId && (
              <button onClick={handleExportChat} title="Export Chat" className="p-2 rounded-xl text-primary-secondary hover:text-primary hover:bg-surface-high transition-colors">
                <Download className="h-4 w-4" />
              </button>
            )}
          </div>
        </header>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-4 py-4">
          <div className="mx-auto max-w-2xl space-y-4">

            {/* Empty state */}
            {messages.length === 0 && !isLoadingMessages && !isSending && (
              <div className="flex min-h-[380px] flex-col items-center justify-center text-center">
                <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-brand/10">
                  <Sparkles className="h-8 w-8 text-brand" />
                </div>
                <h2 className="text-lg font-semibold text-primary">How can I help you?</h2>
                <p className="mt-1.5 max-w-xs text-sm text-primary-secondary leading-relaxed">
                  Ask me anything about nutrition, meals, supplements, or your health goals.
                </p>
                <div className="mt-6 grid w-full max-w-md gap-2 sm:grid-cols-2">
                  {suggestedPrompts.map((p) => (
                    <button
                      key={p}
                      type="button"
                      onClick={() => handleSend(p)}
                      disabled={isSending || atLimit}
                      className="rounded-xl border border-border bg-surface-high/50 px-4 py-3 text-left text-xs text-primary-secondary transition-all hover:border-brand/30 hover:bg-surface-high hover:text-primary disabled:opacity-50"
                    >
                      {p}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Loading messages */}
            {isLoadingMessages && (
              <div className="flex justify-center py-10"><Spinner size="md" /></div>
            )}

            {/* Message bubbles */}
            <AnimatePresence initial={false}>
              {messages.map((msg, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.2 }}
                  className={cn("flex", msg.role === "user" ? "justify-end" : "justify-start")}
                >
                  <div className={cn(
                    "flex max-w-[85%] items-end gap-2.5",
                    msg.role === "user" ? "flex-row-reverse" : "flex-row",
                  )}>
                    <div className={cn(
                      "flex h-7 w-7 shrink-0 items-center justify-center rounded-xl",
                      msg.role === "user" ? "bg-brand text-white" : "bg-surface-high text-brand",
                    )}>
                      {msg.role === "user"
                        ? <User className="h-3.5 w-3.5" />
                        : <Bot className="h-3.5 w-3.5" />}
                    </div>
                    <div className={cn(
                      "rounded-2xl px-4 py-3 text-sm leading-relaxed prose prose-sm max-w-none break-words relative group/msg",
                      msg.role === "user"
                        ? "bg-brand text-white prose-invert rounded-tr-sm"
                        : "bg-surface-high text-primary rounded-tl-sm",
                    )}>
                      <ReactMarkdown 
                        remarkPlugins={[remarkGfm]}
                        components={{
                          // eslint-disable-next-line @typescript-eslint/no-explicit-any
                          code({ inline, className, children }: any) {
                            const match = /language-(\w+)/.exec(className || '')
                            if (!inline && match && match[1] === 'json') {
                              const text = String(children).replace(/\n$/, '')
                              try {
                                const data = JSON.parse(text)
                                const cardTypes = ['NutritionCard', 'MealSuggestionCard', 'MacroProgressCard', 'ShoppingListCard', 'HydrationCard', 'MicronutrientCard']
                                if (cardTypes.includes(data.type)) {
                                  return <SmartNutritionCard data={data} />
                                }
                                if (data.type === 'FollowUpQuestions') {
                                  return <FollowUpQuestions data={data} onSelect={(q) => handleSend(q)} />
                                }
                              } catch {
                                // Fallback for invalid JSON
                              }
                            }
                            return <code className={className}>{children}</code>
                          }
                        }}
                      >
                        {msg.content}
                      </ReactMarkdown>
                      
                      {msg.role === "assistant" && (
                        <div className="absolute -bottom-6 left-0 opacity-0 group-hover/msg:opacity-100 transition-opacity flex gap-1">
                          {msg.id && (
                            <>
                              <button onClick={() => handleFeedback(msg.id!, 'helpful')} className={cn("p-1 rounded hover:bg-surface-high transition-colors", msg.is_helpful ? "text-brand" : "text-primary-muted hover:text-primary")} title="Helpful">
                                <ThumbsUp className="h-3.5 w-3.5" />
                              </button>
                              <button onClick={() => handleFeedback(msg.id!, 'not_helpful')} className={cn("p-1 rounded hover:bg-surface-high transition-colors", msg.is_not_helpful ? "text-red-500" : "text-primary-muted hover:text-primary")} title="Not Helpful">
                                <ThumbsDown className="h-3.5 w-3.5" />
                              </button>
                            </>
                          )}
                          <button onClick={() => handleCopy(msg.content)} className="p-1 rounded hover:bg-surface-high text-primary-muted hover:text-primary transition-colors" title="Copy">
                            <Copy className="h-3.5 w-3.5" />
                          </button>
                          {!isSending && i === messages.length - 1 && (
                            <button onClick={handleRegenerate} className="p-1 rounded hover:bg-surface-high text-primary-muted hover:text-primary transition-colors" title="Regenerate">
                              <RefreshCw className="h-3.5 w-3.5" />
                            </button>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>

            {/* Stop Generation Button */}
            <AnimatePresence>
              {isSending && (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="flex justify-center mt-2">
                  <Button variant="secondary" size="sm" onClick={handleStop} className="gap-1.5 h-8 text-xs rounded-full bg-surface/80 backdrop-blur shadow-sm">
                    <StopCircle className="h-3.5 w-3.5" /> Stop generating
                  </Button>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Typing indicator */}
            <AnimatePresence>
              {isSending && messages.at(-1)?.role === "user" && (
                <motion.div
                  initial={{ opacity: 0, y: 6 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  className="flex justify-start"
                >
                  <div className="flex items-end gap-2.5">
                    <div className="flex h-7 w-7 items-center justify-center rounded-xl bg-surface-high text-brand">
                      <Bot className="h-3.5 w-3.5" />
                    </div>
                    <div className="flex items-center gap-1.5 rounded-2xl rounded-tl-sm bg-surface-high px-4 py-3">
                      {[0, 150, 300].map((d) => (
                        <span
                          key={d}
                          className="h-1.5 w-1.5 animate-bounce rounded-full bg-brand/60"
                          style={{ animationDelay: `${d}ms` }}
                        />
                      ))}
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Error */}
        <AnimatePresence>
          {error && (
            <motion.div
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 6 }}
              className="px-4 pb-2"
            >
              <div className="mx-auto max-w-2xl">
                <Alert variant="error">
                  <div className="flex w-full items-center justify-between gap-2">
                    <span className="text-sm">{error}</span>
                    <button onClick={() => setError(null)} className="shrink-0 p-1 hover:opacity-70">
                      <X className="h-3.5 w-3.5" />
                    </button>
                  </div>
                </Alert>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Daily limit reached banner */}
        {atLimit && (
          <div className="mx-4 mb-2">
            <div className="mx-auto max-w-2xl rounded-xl border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-700 dark:text-amber-300">
              <p className="font-semibold">You&apos;ve reached today&apos;s AI limit.</p>
              <p className="text-xs mt-0.5 opacity-80">
                Your quota will automatically reset tomorrow. {formatResetCountdown(msUntilReset)}.
              </p>
            </div>
          </div>
        )}

        {/* Input */}
        <div className="border-t border-border px-4 py-3">
          <div className="mx-auto max-w-2xl">
            <div className="flex items-center gap-2">
              <Input
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={atLimit ? "Daily limit reached. Resets tomorrow." : "Ask your AI coach…"}
                disabled={isSending || atLimit}
                aria-label="Chat message"
                className="flex-1"
              />
              <Button
                onClick={() => handleSend()}
                disabled={!input.trim() || isSending || atLimit}
                size="md"
                aria-label="Send message"
              >
                {isSending ? <Spinner size="sm" /> : <Send className="h-4 w-4" />}
              </Button>
            </div>
            <p className="mt-1.5 flex justify-between text-xs text-primary-muted">
              <span>Personalised nutrition coaching powered by AI.</span>
              <span>{usage?.messages_used ?? 0} / {usage?.messages_limit ?? 25} messages today</span>
            </p>
          </div>
        </div>
      </div>

      {/* Usage history modal */}
      <AnimatePresence>
        {showHistory && (
          <UsageHistoryModal
            onClose={() => setShowHistory(false)}
            period={historyPeriod}
            history={history}
            historyLoading={historyLoading}
            loadHistory={(p) => loadHistory(p)}
          />
        )}
      </AnimatePresence>
    </div>
  )
}
