"use client"

import { useState, useCallback, useEffect } from "react"
import { motion } from "framer-motion"
import { PageHeader } from "@/components/ui/page-header"
import { User, Target, Bell, Eye, Database, Shield } from "lucide-react"
import { useAuth } from "@/contexts/auth-context"
import { useNutritionProfile } from "@/hooks/use-nutrition-profile"
import { useGoals } from "@/hooks/use-goals"
import { useRouter, useSearchParams } from "next/navigation"
import { TabNav, type Tab } from "@/components/settings/tab-nav"
import { ProfileSection } from "@/components/settings/profile-section"
import { GoalsSection } from "@/components/settings/goals-section"
import { NotificationsSection } from "@/components/settings/notifications-section"
import { DataCenterSection } from "@/components/settings/data-center-section"
import { PrivacySection } from "@/components/settings/privacy-section"
import { SecuritySection } from "@/components/settings/security-section"
import type { NutritionProfileCreateRequest, NutritionProfileUpdateRequest } from "@/types/nutrition"

const tabs: readonly Tab[] = [
  { id: "profile", label: "Profile", icon: User },
  { id: "goals", label: "Goals", icon: Target },
  { id: "notifications", label: "Notifications", icon: Bell },
  { id: "data-center", label: "Data Center", icon: Database },
  { id: "privacy", label: "Privacy", icon: Eye },
  { id: "security", label: "Security", icon: Shield },
] as const

type TabId = (typeof tabs)[number]["id"]

export default function SettingsPage() {
  const { user, logout, updatePassword: authUpdatePassword } = useAuth()
  const {
    profileStatus,
    profile,
    calculations,
    calculationsStatus,
    loadProfile,
    createProfile,
    updateProfile,
  } = useNutritionProfile()
  const { listStatus, goals, reloadGoals } = useGoals()
  const router = useRouter()
  const searchParams = useSearchParams()
  const [activeTab, setActiveTab] = useState<TabId>((searchParams.get("tab") as TabId) || "profile")

  useEffect(() => {
    loadProfile()
    reloadGoals()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const handleSaveProfile = useCallback(async (payload: NutritionProfileCreateRequest | NutritionProfileUpdateRequest): Promise<boolean> => {
    if (profile) {
      return await updateProfile(payload as NutritionProfileUpdateRequest)
    }
    return await createProfile(payload as NutritionProfileCreateRequest)
  }, [profile, createProfile, updateProfile])

  return (
    <div className="space-y-6">
      <PageHeader
        title="Settings"
        description="Manage your account and application preferences."
      />

      <div className="flex gap-6 flex-col lg:flex-row">
        <TabNav tabs={tabs} activeTab={activeTab} onTabChange={setActiveTab} />

        <div className="flex-1 min-w-0">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.2 }}
          >
            {activeTab === "profile" && (
              <ProfileSection
                user={user}
                profile={profile}
                profileStatus={profileStatus}
                calculations={calculations}
                calculationsStatus={calculationsStatus}
                onSave={handleSaveProfile}
                onLoadProfile={loadProfile}
                onLogout={() => { logout(); router.push("/login") }}
              />
            )}

            {activeTab === "goals" && (
              <GoalsSection
                goals={goals}
                listStatus={listStatus}
                onNavigateToGoal={() => router.push("/goals")}
              />
            )}

            {activeTab === "notifications" && <NotificationsSection />}
            {activeTab === "data-center" && <DataCenterSection />}
            {activeTab === "privacy" && <PrivacySection />}

            {activeTab === "security" && (
              <SecuritySection
                onUpdatePassword={authUpdatePassword}
                onLogout={logout}
                onNavigateToLogin={() => router.push("/login")}
              />
            )}
          </motion.div>
        </div>
      </div>
    </div>
  )
}
