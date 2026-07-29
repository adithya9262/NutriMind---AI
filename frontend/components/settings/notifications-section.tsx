"use client"

import { useState, useEffect } from "react"
import { Card } from "@/components/ui/card"
import { Toggle } from "@/components/settings/toggle"
import { getLocalItem, setLocalItem } from "@/components/settings/local-storage"

function useLocalStorage<T>(key: string, fallback: T): [T, (v: T) => void] {
  const [value, setValue] = useState<T>(() => getLocalItem(key, fallback))
  useEffect(() => { setLocalItem(key, value) }, [key, value])
  return [value, setValue]
}

export function NotificationsSection() {
  const [notifDaily, setNotifDaily] = useLocalStorage("notif_daily", true)
  const [notifWeekly, setNotifWeekly] = useLocalStorage("notif_weekly", true)
  const [notifGoals, setNotifGoals] = useLocalStorage("notif_goals", true)
  const [notifCoach, setNotifCoach] = useLocalStorage("notif_coach", false)
  const [notifMeals, setNotifMeals] = useLocalStorage("notif_meals", true)

  const items = [
    { key: "daily", label: "Daily reminders", desc: "Receive daily nutrition reminders", state: notifDaily, set: setNotifDaily },
    { key: "weekly", label: "Weekly summary", desc: "Weekly nutrition and progress summary", state: notifWeekly, set: setNotifWeekly },
    { key: "goals", label: "Goal achievements", desc: "Notify when you reach a goal", state: notifGoals, set: setNotifGoals },
    { key: "coach", label: "AI Coach insights", desc: "Personalized insights from AI Coach", state: notifCoach, set: setNotifCoach },
    { key: "meals", label: "Meal reminders", desc: "Reminders to log your meals", state: notifMeals, set: setNotifMeals },
  ]

  return (
    <Card className="p-6 space-y-5">
      <div>
        <h3 className="text-base font-semibold text-primary">Notification Preferences</h3>
        <p className="text-sm text-primary-secondary mt-0.5">Choose what notifications you receive</p>
      </div>
      {items.map((item) => (
        <div key={item.key} className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-primary">{item.label}</p>
            <p className="text-xs text-primary-secondary">{item.desc}</p>
          </div>
          <Toggle checked={item.state} onChange={item.set} id={`notif-${item.key}`} />
        </div>
      ))}
    </Card>
  )
}
