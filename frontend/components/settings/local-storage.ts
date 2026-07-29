export function getLocalItem<T>(key: string, fallback: T): T {
  if (typeof window === "undefined") return fallback
  try {
    const v = localStorage.getItem(key)
    return v !== null ? (JSON.parse(v) as T) : fallback
  } catch {
    return fallback
  }
}

export function setLocalItem<T>(key: string, value: T) {
  try {
    localStorage.setItem(key, JSON.stringify(value))
  } catch { /* noop */ }
}

export function applyTheme(theme: "light" | "dark" | "system") {
  const d = document.documentElement
  if (theme === "system") {
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches
    d.setAttribute("data-theme", prefersDark ? "dark" : "light")
  } else {
    d.setAttribute("data-theme", theme)
  }
}

export function applyFontSize(size: "small" | "medium" | "large") {
  const d = document.documentElement
  d.removeAttribute("data-font-size")
  if (size !== "medium") {
    d.setAttribute("data-font-size", size)
  }
}
