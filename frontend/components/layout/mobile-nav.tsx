"use client"

import { useEffect, useRef } from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { X, Leaf, LayoutDashboard, UtensilsCrossed, Bot, Weight, CheckSquare, Settings, Search, Camera } from "lucide-react"
import { SidebarItem } from "./sidebar-item"
import { UserProfileCard } from "./user-profile-card"
import { UpgradeCard } from "./upgrade-card"
import { cn } from "@/lib/utils"

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/nutrition/logs", label: "Food Diary", icon: UtensilsCrossed },
  { href: "/nutrition/search", label: "Nutrition Search", icon: Search },
  { href: "/nutrition/recognize", label: "Food Recognition", icon: Camera },
  { href: "/ai-coach", label: "AI Coach", icon: Bot },
  { href: "/body-weight", label: "Weight Tracker", icon: Weight },
  { href: "/tasks", label: "Tasks", icon: CheckSquare },
  { href: "/settings", label: "Settings", icon: Settings },
]

interface MobileNavProps {
  open: boolean
  onClose: () => void
}

export function MobileNav({ open, onClose }: MobileNavProps) {
  const pathname = usePathname()
  const closeButtonRef = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    if (open) {
      closeButtonRef.current?.focus()
      document.body.style.overflow = "hidden"
    } else {
      document.body.style.overflow = ""
    }
    return () => { document.body.style.overflow = "" }
  }, [open])

  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape" && open) onClose()
    }
    document.addEventListener("keydown", handleKeyDown)
    return () => document.removeEventListener("keydown", handleKeyDown)
  }, [open, onClose])

  function isActive(href: string) {
    if (href === "/dashboard") return pathname === href
    return pathname.startsWith(href + "/") || pathname === href
  }

  return (
    <>
      {open && (
        <div
          className="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm lg:hidden"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      <div
        role="dialog"
        aria-modal="true"
        aria-label="Navigation menu"
        className={cn(
          "fixed inset-y-0 left-0 z-50 flex w-72 flex-col glass border-r border-border transform transition-transform duration-300 ease-[cubic-bezier(0.16,1,0.3,1)] lg:hidden",
          open ? "translate-x-0" : "-translate-x-full",
        )}
      >
        <div className="flex items-center justify-between px-5 h-16 border-b border-border">
          <Link href="/dashboard" className="flex items-center gap-2.5" onClick={onClose}>
            <span className="grid h-8 w-8 place-items-center rounded-xl gradient-brand">
              <Leaf className="h-4 w-4 text-white" aria-hidden="true" />
            </span>
            <span className="font-bold text-sm text-primary leading-tight">NutriMind</span>
          </Link>
          <button
            ref={closeButtonRef}
            type="button"
            className="rounded-xl p-2 text-primary-secondary hover:bg-white/5 transition-colors"
            onClick={onClose}
            aria-label="Close navigation menu"
          >
            <X className="h-5 w-5" aria-hidden="true" />
          </button>
        </div>

        <nav className="flex-1 px-3 py-5 space-y-1" aria-label="Mobile navigation">
          {navItems.map((item) => (
            <SidebarItem
              key={item.href}
              href={item.href}
              label={item.label}
              icon={item.icon}
              active={isActive(item.href)}
              onNavigate={onClose}
            />
          ))}
        </nav>

        <div className="space-y-3 px-3 pb-5">
          <UpgradeCard />
          <UserProfileCard />
        </div>
      </div>
    </>
  )
}
