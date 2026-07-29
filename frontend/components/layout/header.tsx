"use client"

import { useState, useRef, useEffect } from "react"
import { useAuth } from "@/contexts/auth-context"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { Menu, LogOut, Bell, Search, User, ChevronDown, Leaf } from "lucide-react"
import { Avatar } from "@/components/ui/avatar"
import { ThemeToggle } from "@/components/theme-toggle"
import { cn } from "@/lib/utils"

function deriveName(email: string | undefined): string {
  if (!email) return "Member"
  const local = email.split("@")[0]
  const parts = local.split(/[._-]/).filter(Boolean)
  if (parts.length === 0) return "Member"
  return parts.map((p) => p.charAt(0).toUpperCase() + p.slice(1)).join(" ")
}

interface HeaderProps {
  onMenuClick: () => void
  title?: string
}

export function Header({ onMenuClick, title }: HeaderProps) {
  const { user, logout } = useAuth()
  const router = useRouter()
  const [showUserMenu, setShowUserMenu] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setShowUserMenu(false)
      }
    }
    document.addEventListener("mousedown", handleClickOutside)
    return () => document.removeEventListener("mousedown", handleClickOutside)
  }, [])

  function handleLogout() {
    setShowUserMenu(false)
    logout()
    router.push("/login")
  }

  const name = deriveName(user?.email)
  const initials = name.charAt(0).toUpperCase()

  return (
    <header className="sticky top-0 z-20 glass border-b border-border">
      <div className="flex items-center justify-between gap-3 h-16 px-4 lg:px-6">
        <div className="flex items-center gap-3">
          <button
            type="button"
            className="rounded-xl p-2 text-primary-secondary hover:bg-white/5 transition-all duration-200 lg:hidden"
            onClick={onMenuClick}
            aria-label="Open navigation menu"
          >
            <Menu className="h-5 w-5" aria-hidden="true" />
          </button>
          <Link href="/dashboard" className="flex items-center gap-2 lg:hidden" aria-label="NutriMind home">
            <span className="grid h-7 w-7 place-items-center rounded-lg gradient-brand">
              <Leaf className="h-4 w-4 text-white" aria-hidden="true" />
            </span>
            <span className="font-bold text-sm text-primary">NutriMind</span>
          </Link>
          {title && (
            <h1 className="hidden text-lg font-bold text-primary sm:block lg:ml-0">{title}</h1>
          )}
        </div>

        <div className="flex items-center gap-2 sm:gap-3">
          <button
            type="button"
            onClick={() => router.push("/nutrition/search")}
            aria-label="Search nutrition database"
            className="hidden items-center gap-2 rounded-xl border border-border bg-surface-high/40 px-3 py-2 text-sm text-primary-muted transition-colors hover:border-brand-primary/40 hover:text-primary sm:flex"
          >
            <Search className="h-4 w-4" aria-hidden="true" />
            <span>Search foods, meals…</span>
            <kbd className="ml-2 rounded border border-border bg-surface px-1.5 text-[10px] text-primary-muted">/</kbd>
          </button>

          <button
            type="button"
            className="rounded-xl p-2 text-primary-muted hover:bg-white/5 hover:text-primary transition-all duration-200"
            aria-label="Search"
          >
            <Search className="h-4 w-4 sm:hidden" aria-hidden="true" />
          </button>

          <ThemeToggle />

          <button
            type="button"
            className="relative rounded-xl p-2 text-primary-muted hover:bg-white/5 hover:text-primary transition-all duration-200"
            aria-label="Notifications"
          >
            <Bell className="h-4 w-4" aria-hidden="true" />
            <span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-error ring-2 ring-[#0c1a14]" />
          </button>

          <div className="relative" ref={menuRef}>
            <button
              type="button"
              className={cn(
                "flex items-center gap-2.5 rounded-xl p-1 pr-2.5 transition-all duration-200 hover:bg-white/5",
                showUserMenu && "bg-white/5",
              )}
              onClick={() => setShowUserMenu(!showUserMenu)}
              aria-label="User menu"
              aria-expanded={showUserMenu}
            >
              <Avatar initials={initials} size="sm" alt={name} />
              <span className="hidden text-sm font-medium text-primary max-w-[120px] truncate sm:block">
                {name}
              </span>
              <ChevronDown
                className={cn("h-3.5 w-3.5 text-primary-muted transition-transform duration-200", showUserMenu && "rotate-180")}
                aria-hidden="true"
              />
            </button>

            {showUserMenu && (
              <div className="absolute right-0 top-full mt-2 w-56 origin-top-right rounded-xl border border-border bg-surface-high py-1.5 shadow-xl animate-scale">
                <div className="border-b border-border px-3.5 py-2.5">
                  <p className="truncate text-sm font-medium text-primary">{name}</p>
                  <p className="mt-0.5 text-xs text-primary-muted">{user?.email}</p>
                </div>
                <button
                  type="button"
                  className="flex w-full items-center gap-2.5 px-3.5 py-2.5 text-sm text-primary-secondary transition-colors hover:bg-white/5 hover:text-primary"
                  onClick={() => { setShowUserMenu(false); router.push("/settings") }}
                >
                  <User className="h-4 w-4" aria-hidden="true" />
                  Settings
                </button>
                <div className="mt-1 border-t border-border pt-1">
                  <button
                    type="button"
                    className="flex w-full items-center gap-2.5 px-3.5 py-2.5 text-sm text-error transition-colors hover:bg-error-light"
                    onClick={handleLogout}
                  >
                    <LogOut className="h-4 w-4" aria-hidden="true" />
                    Log out
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  )
}
