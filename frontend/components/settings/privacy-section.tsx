"use client"

import { useEffect, useState } from "react"
import { Card } from "@/components/ui/card"
import { Toggle } from "@/components/settings/toggle"
import { getLocalItem, setLocalItem } from "@/components/settings/local-storage"

export function PrivacySection() {
  const [dataSharing, setDataSharing] = useState(() => getLocalItem("privacy_data_sharing", false))
  const [profileVisibility, setProfileVisibility] = useState(() => getLocalItem("privacy_profile_visibility", true))

  useEffect(() => { setLocalItem("privacy_data_sharing", dataSharing) }, [dataSharing])
  useEffect(() => { setLocalItem("privacy_profile_visibility", profileVisibility) }, [profileVisibility])

  return (
    <Card className="p-6 space-y-5">
      <div>
        <h3 className="text-base font-semibold text-primary">Privacy Settings</h3>
        <p className="text-sm text-primary-secondary mt-0.5">Control your data and visibility</p>
      </div>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-primary">Data Sharing</p>
          <p className="text-xs text-primary-secondary">Share anonymous usage data to improve Nutrimind AI</p>
        </div>
        <Toggle checked={dataSharing} onChange={setDataSharing} id="privacy-data" />
      </div>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-primary">Profile Visibility</p>
          <p className="text-xs text-primary-secondary">Allow others to see your profile</p>
        </div>
        <Toggle checked={profileVisibility} onChange={setProfileVisibility} id="privacy-visibility" />
      </div>
      <p className="text-xs text-primary-muted pt-2">
        Your data is stored securely and never shared without your consent.
      </p>
    </Card>
  )
}
