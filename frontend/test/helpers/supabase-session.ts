import type { Page } from '@playwright/test'

/** Read the access token from the current Supabase SSR cookie session. */
export async function getSupabaseAccessToken(page: Page): Promise<string> {
  const cookies = await page.context().cookies()
  const groups = new Map<string, Array<{ name: string; value: string; index: number | null }>>()

  for (const cookie of cookies) {
    const match = /^(sb-.+-auth-token)(?:\.(\d+))?$/.exec(cookie.name)
    if (!match) continue

    const group = groups.get(match[1]) ?? []
    group.push({ name: cookie.name, value: cookie.value, index: match[2] ? Number(match[2]) : null })
    groups.set(match[1], group)
  }

  for (const chunks of groups.values()) {
    const ordered = [...chunks].sort((left, right) => {
      if (left.index === null) return -1
      if (right.index === null) return 1
      return left.index - right.index
    })
    const encoded = ordered.map((chunk) => chunk.value).join('')
    try {
      const decoded = encoded.startsWith('base64-')
        ? Buffer.from(encoded.slice('base64-'.length), 'base64url').toString('utf8')
        : decodeURIComponent(encoded)
      const session: unknown = JSON.parse(decoded)
      if (typeof session === 'object' && session !== null && 'access_token' in session) {
        const token = session.access_token
        if (typeof token === 'string' && token.length > 0) return token
      }
    } catch {
      // Ignore unrelated or partially refreshed cookie groups; try the next session cookie.
    }
  }

  throw new Error('No valid Supabase access token found in the browser cookie session')
}
