"use client";

import { useState, type FormEvent } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { FormField } from "@/components/ui/form-field";
import { Alert } from "@/components/ui/alert";
import { Spinner } from "@/components/ui/spinner";
import {
  BIOLOGICAL_SEX_LABELS,
  ACTIVITY_LEVEL_LABELS,
  NUTRITION_GOAL_LABELS,
  DIETARY_PREFERENCE_LABELS,
} from "@/types/nutrition";
import type {
  NutritionProfilePublic,
  NutritionProfileCreateRequest,
  NutritionProfileUpdateRequest,
} from "@/types/nutrition";

interface NutritionProfileFormProps {
  initial?: NutritionProfilePublic | null;
  loading: boolean;
  error: string | null;
  onSubmit: (payload: NutritionProfileCreateRequest | NutritionProfileUpdateRequest) => Promise<boolean>;
  isCreate?: boolean;
  onCancel?: () => void;
  isUpdate?: boolean;
}

interface FormState {
  date_of_birth: string;
  biological_sex: string;
  height_cm: string;
  weight_kg: string;
  activity_level: string;
  goal: string;
  target_weight_kg: string;
  dietary_preference: string;
  allergies: string;
}

interface FormErrors {
  date_of_birth?: string;
  biological_sex?: string;
  height_cm?: string;
  weight_kg?: string;
  activity_level?: string;
  goal?: string;
}

function toFormState(profile: NutritionProfilePublic | null): FormState {
  if (!profile) {
    return {
      date_of_birth: "",
      biological_sex: "",
      height_cm: "",
      weight_kg: "",
      activity_level: "",
      goal: "",
      target_weight_kg: "",
      dietary_preference: "",
      allergies: "",
    };
  }
  return {
    date_of_birth: profile.date_of_birth ?? "",
    biological_sex: profile.biological_sex ?? "",
    height_cm: profile.height_cm ?? "",
    weight_kg: profile.weight_kg ?? "",
    activity_level: profile.activity_level ?? "",
    goal: profile.goal ?? "",
    target_weight_kg: profile.target_weight_kg ?? "",
    dietary_preference: profile.dietary_preference ?? "",
    allergies: Array.isArray(profile.allergies) ? profile.allergies.join(", ") : "",
  };
}

function validateForm(state: FormState, isUpdate: boolean, hasExistingProfile: boolean): FormErrors {
  const errors: FormErrors = {};

  // For create: no fields are required (backend allows empty profile)
  // For update: validate only filled fields
  if (!isUpdate || hasExistingProfile) {
    // For create with no existing profile: no required fields
    // For update: only validate fields that are filled
    if (state.date_of_birth && !/^\d{4}-\d{2}-\d{2}$/.test(state.date_of_birth)) {
      errors.date_of_birth = "Enter a valid date.";
    }
    if (state.height_cm) {
      const h = Number(state.height_cm);
      if (isNaN(h) || h < 50 || h > 300) errors.height_cm = "Height must be between 50 and 300 cm.";
    }
    if (state.weight_kg) {
      const w = Number(state.weight_kg);
      if (isNaN(w) || w < 10 || w > 700) errors.weight_kg = "Weight must be between 10 and 700 kg.";
    }
    // Only validate date format if provided
    if (state.date_of_birth && !/^\d{4}-\d{2}-\d{2}$/.test(state.date_of_birth)) {
      errors.date_of_birth = "Enter a valid date (YYYY-MM-DD).";
    }
  } else {
    // For update with no existing profile (shouldn't happen but handle it)
    if (!state.date_of_birth) errors.date_of_birth = "Date of birth is required.";
    if (!state.biological_sex) errors.biological_sex = "Biological sex is required.";
    if (!state.height_cm) errors.height_cm = "Height is required.";
    else {
      const h = Number(state.height_cm);
      if (isNaN(h) || h < 50 || h > 300) errors.height_cm = "Height must be between 50 and 300 cm.";
    }
    if (!state.weight_kg) errors.weight_kg = "Weight is required.";
    else {
      const w = Number(state.weight_kg);
      if (isNaN(w) || w < 10 || w > 700) errors.weight_kg = "Weight must be between 10 and 700 kg.";
    }
    if (!state.activity_level) errors.activity_level = "Activity level is required.";
    if (!state.goal) errors.goal = "Goal is required.";
  }
  return errors;
}

function buildCreatePayload(state: FormState): NutritionProfileCreateRequest {
  const payload: NutritionProfileCreateRequest = {};
  if (state.date_of_birth) payload.date_of_birth = state.date_of_birth;
  if (state.biological_sex) payload.biological_sex = state.biological_sex;
  if (state.height_cm) payload.height_cm = state.height_cm;
  if (state.weight_kg) payload.weight_kg = state.weight_kg;
  if (state.activity_level) payload.activity_level = state.activity_level;
  if (state.goal) payload.goal = state.goal;
  if (state.target_weight_kg) payload.target_weight_kg = state.target_weight_kg;
  if (state.dietary_preference) payload.dietary_preference = state.dietary_preference;
  if (state.allergies.trim()) {
    payload.allergies = state.allergies.split(",").map((a) => a.trim()).filter(Boolean);
  }
  return payload;
}

function buildUpdatePayload(state: FormState, initial: NutritionProfilePublic | null): NutritionProfileUpdateRequest {
  const payload: NutritionProfileUpdateRequest = {};
  if (state.date_of_birth !== initial?.date_of_birth) payload.date_of_birth = state.date_of_birth;
  if (state.biological_sex !== initial?.biological_sex) payload.biological_sex = state.biological_sex;
  if (state.height_cm !== initial?.height_cm) payload.height_cm = state.height_cm;
  if (state.weight_kg !== initial?.weight_kg) payload.weight_kg = state.weight_kg;
  if (state.activity_level !== initial?.activity_level) payload.activity_level = state.activity_level;
  if (state.goal !== initial?.goal) payload.goal = state.goal;
  const targetWt = state.target_weight_kg || null;
  if (targetWt !== (initial?.target_weight_kg ?? null)) payload.target_weight_kg = targetWt;
  const dietPref = state.dietary_preference || null;
  if (dietPref !== (initial?.dietary_preference ?? null)) payload.dietary_preference = dietPref;
  const allergies = state.allergies.trim()
    ? state.allergies.split(",").map((a) => a.trim()).filter(Boolean)
    : [];
  const initialAllergies = initial?.allergies ?? [];
  if (JSON.stringify(allergies) !== JSON.stringify(initialAllergies)) {
    payload.allergies = allergies;
  }
  return payload;
}

export function NutritionProfileForm({
  initial,
  loading,
  error,
  onSubmit,
  onCancel,
  isUpdate = false,
}: NutritionProfileFormProps) {
  const [formState, setFormState] = useState<FormState>(() => toFormState(initial ?? null));
  const [fieldErrors, setFieldErrors] = useState<FormErrors>({});
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  function handleChange(field: keyof FormState, value: string) {
    setFormState((prev) => ({ ...prev, [field]: value }));
    if (fieldErrors[field as keyof FormErrors]) {
      setFieldErrors((prev) => {
        const next = { ...prev };
        delete next[field as keyof FormErrors];
        return next;
      });
    }
  }

  const hasExistingProfile = !!initial;

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setSubmitError(null);

    const hasExistingProfile = !!initial;
    const errors = validateForm(formState, isUpdate, hasExistingProfile);
    setFieldErrors(errors);
    if (Object.keys(errors).length > 0) return;

    setSubmitting(true);

    const payload = isUpdate
      ? buildUpdatePayload(formState, initial ?? null)
      : buildCreatePayload(formState);

    const success = await onSubmit(payload);
    setSubmitting(false);

    if (!success) {
      setSubmitError(error || "Failed to save. Please try again.");
    }
  }

  const isSubmitting = loading || submitting;
  const displayError = error || submitError;

  return (
    <form onSubmit={handleSubmit} noValidate className="space-y-4">
      {displayError && (
        <Alert variant="error">{displayError}</Alert>
      )}

      <FormField
        label="Date of Birth"
        error={fieldErrors.date_of_birth}
        htmlFor="np-date-of-birth"
      >
        <Input
          id="np-date-of-birth"
          type="date"
          value={formState.date_of_birth}
          onChange={(e) => handleChange("date_of_birth", e.target.value)}
          disabled={isSubmitting}
          aria-invalid={!!fieldErrors.date_of_birth}
        />
      </FormField>

      <FormField
        label="Biological Sex"
        error={fieldErrors.biological_sex}
        htmlFor="np-biological-sex"
      >
        <Select
          id="np-biological-sex"
          value={formState.biological_sex}
          onChange={(e) => handleChange("biological_sex", e.target.value)}
          disabled={isSubmitting}
          aria-invalid={!!fieldErrors.biological_sex}
        >
          <option value="">Select biological sex</option>
          {Object.entries(BIOLOGICAL_SEX_LABELS).map(([value, label]) => (
            <option key={value} value={value}>{label}</option>
          ))}
        </Select>
      </FormField>

      <div className="grid gap-4 sm:grid-cols-2">
        <FormField
          label="Height (cm)"
          error={fieldErrors.height_cm}
          htmlFor="np-height"
        >
          <Input
            id="np-height"
            type="number"
            inputMode="decimal"
            min={50}
            max={300}
            step="0.1"
            placeholder="e.g. 170"
            value={formState.height_cm}
            onChange={(e) => handleChange("height_cm", e.target.value)}
            disabled={isSubmitting}
            aria-invalid={!!fieldErrors.height_cm}
          />
        </FormField>

        <FormField
          label="Weight (kg)"
          error={fieldErrors.weight_kg}
          htmlFor="np-weight"
        >
          <Input
            id="np-weight"
            type="number"
            inputMode="decimal"
            min={10}
            max={700}
            step="0.1"
            placeholder="e.g. 70"
            value={formState.weight_kg}
            onChange={(e) => handleChange("weight_kg", e.target.value)}
            disabled={isSubmitting}
            aria-invalid={!!fieldErrors.weight_kg}
          />
        </FormField>
      </div>

      <FormField
        label="Activity Level"
        error={fieldErrors.activity_level}
        htmlFor="np-activity-level"
      >
        <Select
          id="np-activity-level"
          value={formState.activity_level}
          onChange={(e) => handleChange("activity_level", e.target.value)}
          disabled={isSubmitting}
          aria-invalid={!!fieldErrors.activity_level}
        >
          <option value="">Select activity level</option>
          {Object.entries(ACTIVITY_LEVEL_LABELS).map(([value, label]) => (
            <option key={value} value={value}>{label}</option>
          ))}
        </Select>
      </FormField>

      <FormField
        label="Goal"
        error={fieldErrors.goal}
        htmlFor="np-goal"
      >
        <Select
          id="np-goal"
          value={formState.goal}
          onChange={(e) => handleChange("goal", e.target.value)}
          disabled={isSubmitting}
          aria-invalid={!!fieldErrors.goal}
        >
          <option value="">Select goal</option>
          {Object.entries(NUTRITION_GOAL_LABELS).map(([value, label]) => (
            <option key={value} value={value}>{label}</option>
          ))}
        </Select>
      </FormField>

      <FormField
        label="Target Weight (kg)"
        htmlFor="np-target-weight"
      >
        <Input
          id="np-target-weight"
          type="number"
          inputMode="decimal"
          min={10}
          max={700}
          step="0.1"
          placeholder="Optional"
          value={formState.target_weight_kg}
          onChange={(e) => handleChange("target_weight_kg", e.target.value)}
          disabled={isSubmitting}
        />
      </FormField>

      <FormField
        label="Dietary Preference"
        htmlFor="np-dietary-preference"
      >
        <Select
          id="np-dietary-preference"
          value={formState.dietary_preference}
          onChange={(e) => handleChange("dietary_preference", e.target.value)}
          disabled={isSubmitting}
        >
          <option value="">No preference</option>
          {Object.entries(DIETARY_PREFERENCE_LABELS).map(([value, label]) => (
            <option key={value} value={value}>{label}</option>
          ))}
        </Select>
      </FormField>

      <FormField
        label="Allergies"
        htmlFor="np-allergies"
      >
        <Input
          id="np-allergies"
          type="text"
          placeholder="Comma-separated, e.g. peanuts, shellfish"
          value={formState.allergies}
          onChange={(e) => handleChange("allergies", e.target.value)}
          disabled={isSubmitting}
        />
      </FormField>

      <div className="flex items-center gap-3 pt-2">
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? (
            <>
              <Spinner size="sm" className="mr-2" />
              {isUpdate ? "Saving..." : "Creating..."}
            </>
          ) : isUpdate ? (
            "Save Changes"
          ) : (
            "Create Profile"
          )}
        </Button>
        {onCancel && (
          <Button type="button" variant="secondary" onClick={onCancel} disabled={isSubmitting}>
            Cancel
          </Button>
        )}
      </div>
    </form>
  );
}