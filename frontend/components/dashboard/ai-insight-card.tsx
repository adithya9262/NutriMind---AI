"use client"

import { motion } from "framer-motion"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Sparkles, ArrowRight } from "lucide-react"
import Link from "next/link"

interface AIInsightCardProps {
  profileStatus?: string
  hasWeight?: boolean
}

export function AIInsightCard({
  profileStatus,
  hasWeight,
}: AIInsightCardProps) {
  const insights: { badge: string; title: string; description: string; href: string; label: string }[] = []

  if (!profileStatus || profileStatus === "missing") {
    insights.push({
      badge: "Get Started",
      title: "Set up your nutrition profile",
      description: "Complete your profile to receive personalized nutrition targets and AI-powered recommendations.",
      href: "/nutrition",
      label: "Set up profile",
    })
  }

  if (profileStatus === "available") {
    insights.push({
      badge: "Track",
      title: "Log your meals today",
      description: "Start tracking your daily food intake to get real-time nutrition feedback and progress insights.",
      href: "/nutrition/logs",
      label: "Log meals",
    })
  }

  if (!hasWeight) {
    insights.push({
      badge: "Monitor",
      title: "Track your body weight",
      description: "Regular weight tracking helps you monitor progress toward your health goals with clear trends.",
      href: "/body-weight",
      label: "Track weight",
    })
  }

  if (insights.length === 0) {
    insights.push({
      badge: "AI Insight",
      title: "You're on a great track!",
      description: "Keep up the consistent tracking. Your nutrition data helps our AI provide increasingly personalized advice.",
      href: "/ai-coach",
      label: "Ask AI Coach",
    })
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: 0.3 }}
    >
      <Card className="p-5 card-hover border-brand-primary/10 bg-gradient-to-br from-[var(--color-surface)] to-[var(--color-surface-low)]">
        <div className="flex items-center gap-2 mb-4">
          <div className="p-1.5 rounded-lg bg-brand-light">
            <Sparkles className="h-4 w-4 text-brand" aria-hidden="true" />
          </div>
          <span className="text-xs font-semibold text-brand uppercase tracking-wider">
            AI Insights
          </span>
        </div>

        <div className="space-y-2">
          {insights.map((insight, i) => (
            <Link
              key={i}
              href={insight.href}
              className="block p-3 rounded-xl border border-border hover:border-brand-primary/20 hover:bg-brand-subtle transition-all duration-200 group"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <Badge variant="brand" size="sm" className="mb-1.5">{insight.badge}</Badge>
                  <p className="text-sm font-semibold text-primary group-hover:text-brand transition-colors">
                    {insight.title}
                  </p>
                  <p className="text-xs text-primary-secondary mt-0.5 leading-relaxed">
                    {insight.description}
                  </p>
                </div>
                <ArrowRight className="h-4 w-4 text-primary-muted group-hover:text-brand transition-colors shrink-0 mt-1" />
              </div>
            </Link>
          ))}
        </div>
      </Card>
    </motion.div>
  )
}
