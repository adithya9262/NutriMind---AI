import { apiGet, apiPost, apiPut, apiDelete } from "./client";

// ── Types ─────────────────────────────────────────────────────────────────────

export interface ChatSession {
  id: string;
  title: string;
  pinned?: boolean;
  archived?: boolean;
  message_count: number;
  last_active_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  response_time_ms: number | null;
  is_helpful?: boolean;
  is_not_helpful?: boolean;
  was_regenerated?: boolean;
  was_copied?: boolean;
  created_at: string;
}

export interface AIUsage {
  messages_used: number;
  images_used: number;
  meal_plans_used: number;
  tokens_used: number;
  usage_date: string;
  messages_limit: number;
  images_limit: number;
  reset_at: string;
}

export interface AIUsageHistoryEntry {
  usage_date: string;
  messages_used: number;
  images_used: number;
}

export interface AIUsageHistory {
  entries: AIUsageHistoryEntry[];
  total_messages: number;
  total_sessions: number;
  avg_response_time_ms: number | null;
}

export interface ChatResponseData {
  response: string;
  session_id: string;
  response_time_ms: number;
  timestamp: string;
}

export type UsagePeriod = "today" | "yesterday" | "7d" | "30d" | "all";

// ── Session endpoints ─────────────────────────────────────────────────────────

/** List all sessions sorted by latest activity. Optionally filter by title. */
export async function getSessions(search?: string) {
  const path = search?.trim()
    ? `/ai-coach/sessions?search=${encodeURIComponent(search.trim())}`
    : "/ai-coach/sessions";
  return apiGet<ChatSession[]>(path);
}

export async function createSession(title: string) {
  return apiPost<ChatSession>("/ai-coach/sessions", { title });
}

export async function renameSession(id: string, title: string) {
  return apiPut<ChatSession>(`/ai-coach/sessions/${id}`, { title });
}

export async function togglePinSession(id: string, pinned: boolean) {
  return apiPut<ChatSession>(`/ai-coach/sessions/${id}`, { pinned });
}

export async function deleteSession(id: string) {
  return apiDelete<{ success: boolean }>(`/ai-coach/sessions/${id}`);
}

export async function getSessionMessages(id: string) {
  return apiGet<ChatMessage[]>(`/ai-coach/sessions/${id}/messages`);
}

// ── Usage endpoints ───────────────────────────────────────────────────────────

/** Get today's usage. A fresh row is auto-created if none exists (= daily reset). */
export async function getAIUsage() {
  return apiGet<AIUsage>("/ai-coach/usage");
}

/** Get usage history for a given period. */
export async function getAIUsageHistory(period: UsagePeriod = "7d") {
  return apiGet<AIUsageHistory>(`/ai-coach/usage/history?period=${period}`);
}

// ── Chat ──────────────────────────────────────────────────────────────────────

export async function sendChatMessage(payload: {
  message: string;
  session_id?: string;
  stream?: boolean;
}) {
  return apiPost<ChatResponseData>("/ai-coach/chat", payload);
}

export async function submitMessageFeedback(
  sessionId: string,
  messageId: string,
  feedback: {
    is_helpful?: boolean;
    is_not_helpful?: boolean;
    was_copied?: boolean;
    was_regenerated?: boolean;
  }
) {
  return apiPost<ChatMessage>(`/ai-coach/sessions/${sessionId}/messages/${messageId}/feedback`, feedback);
}
