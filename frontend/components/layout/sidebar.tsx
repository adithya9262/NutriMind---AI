"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import {
  LayoutDashboard,
  UtensilsCrossed,
  Bot,
  Weight,
  CheckSquare,
  Settings,
  Leaf,
  Search,
  Target,
  Camera,
} from "lucide-react"
import { SidebarItem } from "./sidebar-item"
import { UserProfileCard } from "./user-profile-card"
import { UpgradeCard } from "./upgrade-card"

const primaryNav = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/goals", label: "Goals", icon: Target },
  { href: "/nutrition/logs", label: "Food Diary", icon: UtensilsCrossed },
  { href: "/nutrition/search", label: "Nutrition Search", icon: Search },
  { href: "/nutrition/recognize", label: "Food Recognition", icon: Camera },
  { href: "/ai-coach", label: "AI Coach", icon: Bot },
  { href: "/body-weight", label: "Weight Tracker", icon: Weight },
  { href: "/tasks", label: "Tasks", icon: CheckSquare },
  { href: "/settings", label: "Settings", icon: Settings },
]

export function Sidebar() {
  const pathname = usePathname()

  function isActive(href: string) {
    if (href === "/dashboard") return pathname === href
    return pathname.startsWith(href + "/") || pathname === href
  }

  return (
    <aside
      aria-label="Sidebar navigation"
      className="fixed inset-y-0 left-0 z-30 hidden w-64 flex-col glass border-r border-border lg:flex"
    >
      <div className="flex items-center gap-3 px-5 h-16 border-b border-border">
        <Link href="/dashboard" className="flex items-center gap-3" aria-label="NutriMind home">
          <span className="grid h-9 w-9 place-items-center rounded-xl gradient-brand glow">
            <Leaf className="h-5 w-5 text-white" aria-hidden="true" />
          </span>
          <span className="block font-bold text-base text-primary leading-tight">
            NutriMind
          </span>
        </Link>
      </div>

      <nav aria-label="Main navigation" className="flex-1 overflow-y-auto scrollbar-thin px-3 py-5 space-y-1">
        {primaryNav.map((item) => (
          <SidebarItem
            key={item.href}
            href={item.href}
            label={item.label}
            icon={item.icon}
            active={isActive(item.href)}
          />
        ))}
      </nav>

      <div className="space-y-3 px-3 pb-4">
        <UpgradeCard />
        <UserProfileCard />
      </div>
    </aside>
  )
}
