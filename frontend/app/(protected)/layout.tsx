"use client"

import { useState, type ReactNode } from "react"
import { Sidebar } from "@/components/layout/sidebar"
import { Header } from "@/components/layout/header"
import { MobileNav } from "@/components/layout/mobile-nav"
import { MobileBottomNav } from "@/components/layout/mobile-bottom-nav"
import { ProtectedRoute } from "@/components/protected-route"
import { usePathname } from "next/navigation"

const pageTitles: Record<string, string> = {
  "/dashboard": "Dashboard",
  "/nutrition": "Nutrition",
  "/nutrition/logs": "Food Diary",
  "/body-weight": "Body Weight",
  "/tasks": "Tasks",
  "/ai-coach": "AI Coach",
  "/settings": "Settings",
}

export default function ProtectedLayout({ children }: { children: ReactNode }) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const pathname = usePathname()

  const currentTitle = pageTitles[pathname] || "NutriMind AI"

  return (
    <ProtectedRoute>
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:top-2 focus:left-2 focus:z-50 focus:px-4 focus:py-2 focus:bg-brand focus:text-white focus:rounded-lg focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-brand"
      >
        Skip to main content
      </a>

      <div className="min-h-screen bg-background">
        <Sidebar />

        <MobileNav
          open={mobileMenuOpen}
          onClose={() => setMobileMenuOpen(false)}
        />

        <div className="lg:pl-64 flex flex-col min-h-screen">
          <Header
            onMenuClick={() => setMobileMenuOpen(true)}
            title={currentTitle}
          />

          <main id="main-content" className="flex-1 px-5 pb-24 sm:px-8 lg:px-16 lg:pb-8 py-6 lg:py-8 max-w-[1440px] w-full mx-auto animate-fade-in">
            {children}
          </main>
          <MobileBottomNav />
        </div>
      </div>
    </ProtectedRoute>
  )
}
