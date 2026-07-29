import { Card } from "@/components/ui/card";
import { DataField } from "@/components/data-field";
import { formatDate, formatDecimal } from "@/lib/format";
import {
  BIOLOGICAL_SEX_LABELS,
  ACTIVITY_LEVEL_LABELS,
  NUTRITION_GOAL_LABELS,
  DIETARY_PREFERENCE_LABELS,
} from "@/types/nutrition";
import type { NutritionProfilePublic } from "@/types/nutrition";

interface NutritionProfileOverviewProps {
  profile: NutritionProfilePublic;
}

export function NutritionProfileOverview({ profile }: NutritionProfileOverviewProps) {
  const sexLabel = profile.biological_sex ? (BIOLOGICAL_SEX_LABELS[profile.biological_sex] || profile.biological_sex) : null;
  const activityLabel = profile.activity_level ? (ACTIVITY_LEVEL_LABELS[profile.activity_level] || profile.activity_level) : null;
  const goalLabel = profile.goal ? (NUTRITION_GOAL_LABELS[profile.goal] || profile.goal) : null;
  const dietLabel = profile.dietary_preference
    ? DIETARY_PREFERENCE_LABELS[profile.dietary_preference] || profile.dietary_preference
    : null;

  return (
    <Card>
      <dl className="grid gap-4 sm:grid-cols-2">
        <DataField label="Date of Birth" value={formatDate(profile.date_of_birth)} />
        <DataField label="Biological Sex" value={sexLabel} />
        <DataField label="Height" value={`${formatDecimal(profile.height_cm)} cm`} />
        <DataField label="Weight" value={`${formatDecimal(profile.weight_kg)} kg`} />
        <DataField label="Activity Level" value={activityLabel} />
        <DataField label="Goal" value={goalLabel} />
        {profile.target_weight_kg && (
          <DataField label="Target Weight" value={`${formatDecimal(profile.target_weight_kg)} kg`} />
        )}
        {dietLabel && (
          <DataField label="Dietary Preference" value={dietLabel} />
        )}
        {profile.allergies && profile.allergies.length > 0 && (
          <DataField label="Allergies" value={profile.allergies.join(", ")} />
        )}
      </dl>
    </Card>
  );
}