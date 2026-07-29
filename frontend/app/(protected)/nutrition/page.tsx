"use client"

import { useEffect, useState } from "react"
import { motion } from "framer-motion"
import { PageHeader } from "@/components/ui/page-header"
import { SectionHeader } from "@/components/ui/section-header"
import { Card } from "@/components/ui/card"
import { Alert } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { Spinner } from "@/components/ui/spinner"
import { NutritionProfileForm } from "@/components/nutrition-profile-form"
import { NutritionProfileOverview } from "@/components/nutrition-profile-overview"
import { NutritionCalculationsCard } from "@/components/nutrition-calculations-card"
import { PersonalizedNutritionSummary } from "@/components/personalized-nutrition-summary"
import { useNutritionProfile } from "@/hooks/use-nutrition-profile"
import type { NutritionProfileCreateRequest, NutritionProfileUpdateRequest } from "@/types/nutrition"
import { Edit3, User } from "lucide-react"

export default function NutritionPage() {
  const {
    profileStatus,
    profile,
    profileError,
    calculationsStatus,
    calculations,
    calculationsError,
    summaryStatus,
    summary,
    summaryError,
    loadProfile,
    createProfile,
    updateProfile,
    retryCalculations,
    retrySummary,
    clearProfileError,
  } = useNutritionProfile()

  const [editing, setEditing] = useState(false)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)

  useEffect(() => {
    loadProfile()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  function handleStartEditing() {
    setEditing(true)
    clearProfileError()
    setSuccessMessage(null)
  }

  function handleCancelEditing() {
    setEditing(false)
    clearProfileError()
  }

  async function handleCreateSubmit(payload: NutritionProfileCreateRequest | NutritionProfileUpdateRequest) {
    const success = await createProfile(payload as NutritionProfileCreateRequest)
    if (success) {
      setSuccessMessage("Nutrition profile created successfully.")
      setEditing(false)
    }
    return success
  }

  async function handleUpdateSubmit(payload: NutritionProfileCreateRequest | NutritionProfileUpdateRequest) {
    const success = await updateProfile(payload as NutritionProfileUpdateRequest)
    if (success) {
      setSuccessMessage("Nutrition profile updated successfully.")
      setEditing(false)
    }
    return success
  }

  if (profileStatus === "loading") {
    return (
      <div className="space-y-6">
        <PageHeader title="Nutrition" description="Manage your nutrition profile and view personalized targets." />
        <div className="flex items-center justify-center py-16" role="status" aria-label="Loading profile">
          <Spinner size="lg" />
        </div>
      </div>
    )
  }

  if (profileStatus === "read_error") {
    return (
      <div className="space-y-6">
        <PageHeader title="Nutrition" description="Manage your nutrition profile and view personalized targets." />
        <Alert variant="error">
          <p>{profileError || "Unable to load nutrition profile."}</p>
          <Button variant="secondary" size="sm" className="mt-2" onClick={loadProfile}>Retry</Button>
        </Alert>
      </div>
    )
  }

  const isCreatingOrUpdating = profileStatus === "creating" || profileStatus === "updating"

  return (
    <div className="space-y-6">
      <PageHeader
        title="Nutrition"
        description="Manage your nutrition profile and view personalized targets."
      />

      {successMessage && (
        <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
          <Alert variant="success" dismissible onDismiss={() => setSuccessMessage(null)}>
            {successMessage}
          </Alert>
        </motion.div>
      )}

      {profileStatus === "missing" && !editing && (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
          <SectionHeader
            title="Set Up Your Nutrition Profile"
            description="Your profile information is used to calculate personalized nutrition targets."
          />
          <Card className="p-6">
            <div className="flex items-center gap-3 mb-5">
              <div className="p-2.5 rounded-xl bg-brand-light">
                <User className="h-5 w-5 text-brand" />
              </div>
              <div>
                <p className="text-sm font-semibold text-primary">Create Profile</p>
                <p className="text-xs text-primary-secondary">Fill in your details to get started</p>
              </div>
            </div>
            <NutritionProfileForm
              loading={isCreatingOrUpdating}
              error={profileError}
              onSubmit={handleCreateSubmit}
              isUpdate={false}
            />
          </Card>
        </motion.div>
      )}

      {profile && !editing && (
        <>
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
            <SectionHeader
              title="Your Profile"
              description="Your nutrition profile details."
              action={
                <Button variant="secondary" size="sm" onClick={handleStartEditing}>
                  <Edit3 className="h-3.5 w-3.5" />
                  Edit
                </Button>
              }
            />
            <Card className="p-5">
              <NutritionProfileOverview profile={profile} />
            </Card>
          </motion.div>

          {calculationsStatus !== "idle" && (
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
              <SectionHeader
                title="Nutrition Calculations"
                description="Your calculated nutrition metrics and targets."
              />
              <NutritionCalculationsCard
                metrics={calculations?.metrics ?? null}
                targets={calculations?.targets ?? null}
                status={calculationsStatus}
                error={calculationsError}
                onRetry={retryCalculations}
              />
            </motion.div>
          )}

          {summaryStatus !== "idle" && (
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }}>
              <SectionHeader
                title="Personalized Summary"
                description="An overview of your nutrition profile and targets."
              />
              <PersonalizedNutritionSummary
                summary={summary}
                status={summaryStatus}
                error={summaryError}
                onRetry={retrySummary}
              />
            </motion.div>
          )}
        </>
      )}

      {profile && editing && (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
          <SectionHeader
            title="Edit Profile"
            description="Update your nutrition profile information."
          />
          <Card className="p-6">
            <NutritionProfileForm
              initial={profile}
              loading={isCreatingOrUpdating}
              error={profileError}
              onSubmit={handleUpdateSubmit}
              onCancel={handleCancelEditing}
              isUpdate={true}
            />
          </Card>
        </motion.div>
      )}
    </div>
  )
}
