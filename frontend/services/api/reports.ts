import { getAccessToken } from "@/lib/token-storage"

const getBaseUrl = () => (process.env.NEXT_PUBLIC_API_URL || "").replace(/\/+$/, "")

async function fetchText(path: string): Promise<string> {
  const token = getAccessToken("supabase") || getAccessToken("backend")

  const res = await fetch(`${getBaseUrl()}${path}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  })

  if (!res.ok) throw new Error("Failed to fetch report")
  return res.text()
}

export async function getProgressReport(period: "weekly" | "monthly" = "weekly") {
  return fetchText(`/reports/progress?period=${period}`)
}

export async function getChatExport(sessionId: string) {
  return fetchText(`/reports/chat-export/${sessionId}`)
}
