"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { LayoutDashboard, UtensilsCrossed, Bot, LineChart, Settings } from "lucide-react"
import { cn } from "@/lib/utils"

const bottomNav = [
  { href: "/dashboard", label: "Home", icon: LayoutDashboard },
  { href: "/nutrition/logs", label: "Diary", icon: UtensilsCrossed },
  { href: "/ai-coach", label: "Coach", icon: Bot },
  { href: "/body-weight", label: "Track", icon: LineChart },
  { href: "/settings", label: "Settings", icon: Settings },
]

export function MobileBottomNav() {
  const pathname = usePathname()

  function isActive(href: string) {
    if (href === "/dashboard") return pathname === href
    return pathname.startsWith(href + "/") || pathname === href
  }

  return (
    <nav
      aria-label="Bottom navigation"
      className="fixed inset-x-0 bottom-0 z-30 flex h-16 items-stretch border-t border-border bg-[#0c1a14]/90 backdrop-blur-xl lg:hidden pb-safe"
    >
      {bottomNav.map((item) => {
        const active = isActive(item.href)
        return (
          <Link
            key={item.href}
            href={item.href}
            aria-current={active ? "page" : undefined}
            aria-label={item.label}
            className="relative flex flex-1 flex-col items-center justify-center gap-0.5 min-h-[44px] min-w-[44px]"
          >
            {active && (
              <span
                aria-hidden="true"
                className="absolute top-0 h-0.5 w-8 rounded-full bg-brand-primary"
              />
            )}
            <item.icon
              className={cn(
                "h-5 w-5 transition-colors duration-200",
                active ? "text-brand-primary" : "text-primary-muted",
              )}
              aria-hidden="true"
            />
            <span
              className={cn(
                "text-[10px] font-medium transition-colors duration-200 leading-tight",
                active ? "text-brand-primary" : "text-primary-muted",
              )}
            >
              {item.label}
            </span>
          </Link>
        )
      })}
    </nav>
  )
}
