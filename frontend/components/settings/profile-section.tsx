"use client"

import { useState, useEffect, useRef, type FormEvent } from "react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Select } from "@/components/ui/select"
import { FormField } from "@/components/ui/form-field"
import { Avatar } from "@/components/ui/avatar"
import { Alert } from "@/components/ui/alert"
import { Spinner } from "@/components/ui/spinner"
import { AlertTriangle, LogOut, Save, Upload } from "lucide-react"
import type { PublicUser } from "@/types/auth"
import type { NutritionProfileCreateRequest, NutritionProfileUpdateRequest, NutritionProfilePublic } from "@/types/nutrition"
import type { CalculatedNutritionData } from "@/types/nutrition"

interface ProfileSectionProps {
  user: PublicUser | null
  profile: NutritionProfilePublic | null
  profileStatus: string
  calculations: CalculatedNutritionData | null
  calculationsStatus: string
  onSave: (payload: NutritionProfileCreateRequest | NutritionProfileUpdateRequest) => Promise<boolean>
  onLoadProfile: () => void
  onLogout: () => void
}

export function ProfileSection({
  user,
  profile,
  profileStatus,
  calculations,
  calculationsStatus,
  onSave,
  onLoadProfile,
  onLogout,
}: ProfileSectionProps) {
  const [saved, setSaved] = useState(false)
  const [saveError, setSaveError] = useState<string | null>(null)
  const avatarUrlRef = useRef<string | null>(null)

  // Profile fields
  const [fullName, setFullName] = useState("")
  const [phone, setPhone] = useState("")
  const [dateOfBirth, setDateOfBirth] = useState("")
  const [biologicalSex, setBiologicalSex] = useState("")
  const [heightCm, setHeightCm] = useState("")
  const [weightKg, setWeightKg] = useState("")
  const [activityLevel, setActivityLevel] = useState("")
  const [goal, setGoal] = useState("")
  const [targetWeightKg, setTargetWeightKg] = useState("")
  const [dietaryPreference, setDietaryPreference] = useState("")
  const [allergies, setAllergies] = useState("")
  const [fitnessGoal, setFitnessGoal] = useState("")
  const [medicalConditions, setMedicalConditions] = useState("")
  const [waterGoalMl, setWaterGoalMl] = useState("")
  const [sleepGoalHours, setSleepGoalHours] = useState("")
  const [dailyCalorieGoal, setDailyCalorieGoal] = useState("")
  const [dailyProteinGoalG, setDailyProteinGoalG] = useState("")
  const [dailyCarbGoalG, setDailyCarbGoalG] = useState("")
  const [dailyFatGoalG, setDailyFatGoalG] = useState("")
  const [avatarUrl, setAvatarUrl] = useState("")

  useEffect(() => {
    if (profile) {
      setFullName(profile.full_name || "")
      setPhone(profile.phone || "")
      setDateOfBirth(profile.date_of_birth || "")
      setBiologicalSex(profile.biological_sex || "")
      setHeightCm(profile.height_cm || "")
      setWeightKg(profile.weight_kg || "")
      setActivityLevel(profile.activity_level || "")
      setGoal(profile.goal || "")
      setTargetWeightKg(profile.target_weight_kg || "")
      setDietaryPreference(profile.dietary_preference || "")
      setAllergies((profile.allergies || []).join(", "))
      setFitnessGoal(profile.fitness_goal || "")
      setMedicalConditions((profile.medical_conditions || []).join(", "))
      setWaterGoalMl(profile.water_goal_ml ? String(profile.water_goal_ml) : "")
      setSleepGoalHours(profile.sleep_goal_hours || "")
      setDailyCalorieGoal(profile.daily_calorie_goal ? String(profile.daily_calorie_goal) : "")
      setDailyProteinGoalG(profile.daily_protein_goal_g ? String(profile.daily_protein_goal_g) : "")
      setDailyCarbGoalG(profile.daily_carb_goal_g ? String(profile.daily_carb_goal_g) : "")
      setDailyFatGoalG(profile.daily_fat_goal_g ? String(profile.daily_fat_goal_g) : "")
      setAvatarUrl(profile.avatar_url || "")
    }
  }, [profile])

  useEffect(() => {
    return () => {
      if (avatarUrlRef.current) {
        URL.revokeObjectURL(avatarUrlRef.current)
      }
    }
  }, [])

  function handleAvatarSelect(file: File) {
    if (avatarUrlRef.current) {
      URL.revokeObjectURL(avatarUrlRef.current)
    }
    const url = URL.createObjectURL(file)
    avatarUrlRef.current = url
    setAvatarUrl(url)
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setSaveError(null)
    setSaved(false)

    const allergiesList = allergies ? allergies.split(",").map((a) => a.trim()).filter(Boolean) : []
    const medicalList = medicalConditions ? medicalConditions.split(",").map((a) => a.trim()).filter(Boolean) : []

    let result: boolean
    if (profile) {
      const payload: NutritionProfileUpdateRequest = {
        full_name: fullName || null,
        phone: phone || null,
        date_of_birth: dateOfBirth,
        biological_sex: biologicalSex,
        height_cm: heightCm,
        weight_kg: weightKg,
        activity_level: activityLevel,
        goal: goal,
        target_weight_kg: targetWeightKg || null,
        dietary_preference: dietaryPreference || null,
        allergies: allergiesList,
        fitness_goal: fitnessGoal || null,
        medical_conditions: medicalList,
        water_goal_ml: waterGoalMl ? Number(waterGoalMl) : null,
        sleep_goal_hours: sleepGoalHours || null,
        daily_calorie_goal: dailyCalorieGoal ? Number(dailyCalorieGoal) : null,
        daily_protein_goal_g: dailyProteinGoalG ? Number(dailyProteinGoalG) : null,
        daily_carb_goal_g: dailyCarbGoalG ? Number(dailyCarbGoalG) : null,
        daily_fat_goal_g: dailyFatGoalG ? Number(dailyFatGoalG) : null,
        avatar_url: avatarUrl || null,
      }
      result = await onSave(payload)
    } else {
      const payload: NutritionProfileCreateRequest = {
        full_name: fullName || null,
        phone: phone || null,
        date_of_birth: dateOfBirth,
        biological_sex: biologicalSex,
        height_cm: heightCm,
        weight_kg: weightKg,
        activity_level: activityLevel,
        goal: goal,
        target_weight_kg: targetWeightKg || null,
        dietary_preference: dietaryPreference || null,
        allergies: allergiesList,
        fitness_goal: fitnessGoal || null,
        medical_conditions: medicalList,
        water_goal_ml: waterGoalMl ? Number(waterGoalMl) : null,
        sleep_goal_hours: sleepGoalHours || null,
        daily_calorie_goal: dailyCalorieGoal ? Number(dailyCalorieGoal) : null,
        daily_protein_goal_g: dailyProteinGoalG ? Number(dailyProteinGoalG) : null,
        daily_carb_goal_g: dailyCarbGoalG ? Number(dailyCarbGoalG) : null,
        daily_fat_goal_g: dailyFatGoalG ? Number(dailyFatGoalG) : null,
        avatar_url: avatarUrl || null,
      }
      result = await onSave(payload)
    }

    if (result) {
      setSaved(true)
      setTimeout(() => setSaved(false), 3000)
    } else {
      setSaveError("Failed to save profile. Please try again.")
    }
  }

  const initials = user?.email?.[0]?.toUpperCase() || "U"

  if (profileStatus === "loading") {
    return (
      <Card className="p-6">
        <div className="flex items-center justify-center py-12">
          <Spinner size="lg" />
        </div>
      </Card>
    )
  }

  if (profileStatus === "read_error") {
    return (
      <Card className="p-6">
        <div className="flex flex-col items-center justify-center py-12 gap-4 text-center">
          <AlertTriangle className="h-10 w-10 text-error" />
          <div>
            <p className="text-base font-semibold text-primary">Could not load profile</p>
            <p className="text-sm text-primary-secondary mt-1">
              The backend may be unavailable. Check your connection and try again.
            </p>
          </div>
          <Button variant="secondary" onClick={onLoadProfile}>Retry</Button>
        </div>
      </Card>
    )
  }

  return (
    <Card className="p-6">
      {saved && (
        <Alert variant="success" className="mb-4" dismissible onDismiss={() => setSaved(false)}>
          Settings saved successfully.
        </Alert>
      )}
      {saveError && (
        <Alert variant="error" className="mb-4" dismissible onDismiss={() => setSaveError(null)}>
          {saveError}
        </Alert>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="flex items-center gap-4">
          <Avatar initials={initials} size="lg" src={avatarUrl || undefined} alt={user?.email || "User"} />
          <div className="flex-1">
            <p className="text-base font-semibold text-primary">{user?.email}</p>
            <p className="text-sm text-primary-secondary">
              {user?.is_verified ? "Verified account" : "Unverified account"}
            </p>
          </div>
          <label className="cursor-pointer">
            <input
              type="file"
              accept="image/*"
              className="hidden"
              onChange={(e) => {
                const file = e.target.files?.[0]
                if (file) handleAvatarSelect(file)
              }}
            />
            <Button type="button" variant="secondary" size="sm" onClick={() => document.querySelector<HTMLInputElement>('input[accept="image/*"]')?.click()}>
              <Upload className="h-4 w-4" />
              Upload
            </Button>
          </label>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <FormField label="Full Name" htmlFor="settings-fullname">
            <Input id="settings-fullname" placeholder="Your full name" value={fullName} onChange={(e) => setFullName(e.target.value)} />
          </FormField>
          <FormField label="Phone" htmlFor="settings-phone">
            <Input id="settings-phone" type="tel" placeholder="+1 (555) 000-0000" value={phone} onChange={(e) => setPhone(e.target.value)} />
          </FormField>
        </div>

        <FormField label="Email" htmlFor="settings-email">
          <Input id="settings-email" type="email" value={user?.email || ""} disabled />
        </FormField>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <FormField label="Date of Birth" htmlFor="settings-dob">
            <Input id="settings-dob" type="date" value={dateOfBirth} onChange={(e) => setDateOfBirth(e.target.value)} />
          </FormField>
          <FormField label="Biological Sex" htmlFor="settings-sex">
            <Select id="settings-sex" value={biologicalSex} onChange={(e) => setBiologicalSex(e.target.value)}>
              <option value="">Select...</option>
              <option value="male">Male</option>
              <option value="female">Female</option>
              <option value="other">Other</option>
              <option value="prefer_not_to_say">Prefer not to say</option>
            </Select>
          </FormField>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <FormField label="Height (cm)" htmlFor="settings-height">
            <Input id="settings-height" type="number" step="0.01" placeholder="e.g. 175" value={heightCm} onChange={(e) => setHeightCm(e.target.value)} />
          </FormField>
          <FormField label="Weight (kg)" htmlFor="settings-weight">
            <Input id="settings-weight" type="number" step="0.01" placeholder="e.g. 70" value={weightKg} onChange={(e) => setWeightKg(e.target.value)} />
          </FormField>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <FormField label="Activity Level" htmlFor="settings-activity">
            <Select id="settings-activity" value={activityLevel} onChange={(e) => setActivityLevel(e.target.value)}>
              <option value="">Select...</option>
              <option value="sedentary">Sedentary</option>
              <option value="lightly_active">Lightly Active</option>
              <option value="moderately_active">Moderately Active</option>
              <option value="very_active">Very Active</option>
              <option value="extra_active">Extra Active</option>
            </Select>
          </FormField>
          <FormField label="Nutrition Goal" htmlFor="settings-goal">
            <Select id="settings-goal" value={goal} onChange={(e) => setGoal(e.target.value)}>
              <option value="">Select...</option>
              <option value="lose_weight">Lose Weight</option>
              <option value="maintain_weight">Maintain Weight</option>
              <option value="gain_weight">Gain Weight</option>
              <option value="gain_muscle">Gain Muscle</option>
            </Select>
          </FormField>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <FormField label="Target Weight (kg)" htmlFor="settings-target-weight">
            <Input id="settings-target-weight" type="number" step="0.01" placeholder="e.g. 65" value={targetWeightKg} onChange={(e) => setTargetWeightKg(e.target.value)} />
          </FormField>
          <FormField label="Dietary Preference" htmlFor="settings-diet">
            <Select id="settings-diet" value={dietaryPreference} onChange={(e) => setDietaryPreference(e.target.value)}>
              <option value="">None specified</option>
              <option value="no_preference">No Preference</option>
              <option value="vegetarian">Vegetarian</option>
              <option value="vegan">Vegan</option>
              <option value="pescatarian">Pescatarian</option>
              <option value="eggetarian">Eggetarian</option>
            </Select>
          </FormField>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <FormField label="Fitness Goal" htmlFor="settings-fitness-goal">
            <Select id="settings-fitness-goal" value={fitnessGoal} onChange={(e) => setFitnessGoal(e.target.value)}>
              <option value="">Select...</option>
              <option value="weight_loss">Weight Loss</option>
              <option value="weight_gain">Weight Gain</option>
              <option value="maintain_weight">Maintain Weight</option>
              <option value="muscle_gain">Muscle Gain</option>
              <option value="fat_loss">Fat Loss</option>
              <option value="custom">Custom</option>
              <option value="general_fitness">General Fitness</option>
            </Select>
          </FormField>
          <FormField label="Medical Conditions" htmlFor="settings-medical">
            <Input id="settings-medical" placeholder="e.g. diabetes, hypertension" value={medicalConditions} onChange={(e) => setMedicalConditions(e.target.value)} />
          </FormField>
        </div>

        <FormField label="Allergies (comma separated)" htmlFor="settings-allergies">
          <Input id="settings-allergies" placeholder="e.g. peanuts, gluten, dairy" value={allergies} onChange={(e) => setAllergies(e.target.value)} />
        </FormField>

        <div className="border-t border-border pt-4">
          <h4 className="text-sm font-semibold text-primary mb-3">Custom Daily Targets</h4>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <FormField label="Water Goal (ml)" htmlFor="settings-water">
              <Input id="settings-water" type="number" placeholder="e.g. 2000" value={waterGoalMl} onChange={(e) => setWaterGoalMl(e.target.value)} />
            </FormField>
            <FormField label="Sleep Goal (hrs)" htmlFor="settings-sleep">
              <Input id="settings-sleep" type="number" step="0.5" placeholder="e.g. 8" value={sleepGoalHours} onChange={(e) => setSleepGoalHours(e.target.value)} />
            </FormField>
            <FormField label="Calorie Goal" htmlFor="settings-cals">
              <Input id="settings-cals" type="number" placeholder="kcal" value={dailyCalorieGoal} onChange={(e) => setDailyCalorieGoal(e.target.value)} />
            </FormField>
            <FormField label="Protein Goal (g)" htmlFor="settings-protein">
              <Input id="settings-protein" type="number" placeholder="g" value={dailyProteinGoalG} onChange={(e) => setDailyProteinGoalG(e.target.value)} />
            </FormField>
            <FormField label="Carbs Goal (g)" htmlFor="settings-carbs">
              <Input id="settings-carbs" type="number" placeholder="g" value={dailyCarbGoalG} onChange={(e) => setDailyCarbGoalG(e.target.value)} />
            </FormField>
            <FormField label="Fat Goal (g)" htmlFor="settings-fat">
              <Input id="settings-fat" type="number" placeholder="g" value={dailyFatGoalG} onChange={(e) => setDailyFatGoalG(e.target.value)} />
            </FormField>
          </div>
        </div>

        {calculationsStatus === "available" && calculations && (
          <div className="rounded-xl border border-border bg-bg p-4 space-y-2">
            <h4 className="text-sm font-semibold text-primary">Calculated Targets</h4>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
              <div>
                <span className="text-primary-secondary">Daily Calories:</span>{" "}
                <span className="font-medium text-primary">
                  {Math.round(Number(calculations.targets.calorie_target_kcal_per_day))} kcal
                </span>
              </div>
              <div>
                <span className="text-primary-secondary">Protein:</span>{" "}
                <span className="font-medium text-primary">
                  {Math.round(Number(calculations.targets.protein_g_per_day))} g
                </span>
              </div>
              <div>
                <span className="text-primary-secondary">Carbs:</span>{" "}
                <span className="font-medium text-primary">
                  {Math.round(Number(calculations.targets.carbohydrate_g_per_day))} g
                </span>
              </div>
              <div>
                <span className="text-primary-secondary">Fat:</span>{" "}
                <span className="font-medium text-primary">
                  {Math.round(Number(calculations.targets.fat_g_per_day))} g
                </span>
              </div>
            </div>
          </div>
        )}

        <div className="flex gap-3 flex-wrap">
          <Button type="submit" disabled={profileStatus === "creating" || profileStatus === "updating"}>
            <Save className="h-4 w-4" />
            {profile ? "Save Changes" : "Create Profile"}
          </Button>
          <Button variant="danger" type="button" onClick={onLogout}>
            <LogOut className="h-4 w-4" />
            Log out
          </Button>
        </div>
      </form>
    </Card>
  )
}
