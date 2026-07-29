const cache = new Map<string, { data: unknown; timestamp: number }>()
const TTL = 30000

export function getCached<T>(key: string): T | null {
  const entry = cache.get(key)
  if (!entry) return null
  if (Date.now() - entry.timestamp > TTL) {
    cache.delete(key)
    return null
  }
  return entry.data as T
}

export function setCache(key: string, data: unknown): void {
  cache.set(key, { data, timestamp: Date.now() })
  if (cache.size > 100) {
    const first = cache.keys().next().value
    if (first) cache.delete(first)
  }
}

export function clearCache(): void {
  cache.clear()
}
