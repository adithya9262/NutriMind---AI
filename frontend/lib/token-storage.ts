function isBrowser(): boolean {
  return typeof window !== "undefined" && typeof localStorage !== "undefined"
}

export function setAccessToken(token: string, type: "supabase" | "backend"): void {
  if (!isBrowser()) return
  try {
    localStorage.setItem(`${type}_access_token`, token)
  } catch {
    // Storage full or disabled
  }
}

export function getAccessToken(type: "supabase" | "backend"): string | null {
  if (!isBrowser()) return null
  try {
    return localStorage.getItem(`${type}_access_token`)
  } catch {
    return null
  }
}

export function removeAccessToken(type: "supabase" | "backend"): void {
  if (!isBrowser()) return
  try {
    localStorage.removeItem(`${type}_access_token`)
  } catch {
    // Ignore
  }
}

export function clearAllTokens(): void {
  if (!isBrowser()) return
  try {
    localStorage.removeItem("supabase_access_token")
    localStorage.removeItem("backend_access_token")
  } catch {
    // Ignore
  }
}
