"use client";

import { useState, useEffect, type FormEvent } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { FormField } from "@/components/ui/form-field";
import { Alert } from "@/components/ui/alert";
import {
  MEAL_TYPE_LABELS,
  MEAL_TYPE_ORDER,
  NUTRITION_FIELD_LIMITS,
  EMPTY_ENTRY_FORM,
} from "@/types/nutrition";
import type {
  NutritionLogEntryFormState,
  NutritionLogEntryCreateRequest,
  MealType,
} from "@/types/nutrition";
import { parseFastApiValidationErrors, type FieldError } from "@/lib/validation";

interface NutritionLogEntryFormProps {
  onSubmit: (payload: NutritionLogEntryCreateRequest) => Promise<boolean>;
  loading: boolean;
  error: string | null;
  onCancel?: () => void;
  initialValues?: Partial<NutritionLogEntryFormState>;
}

interface FormErrors {
  food_name?: string;
  serving_description?: string;
  calories_kcal?: string;
  protein_g?: string;
  carbohydrate_g?: string;
  fat_g?: string;
}

const NUTRITION_FIELDS = [
  { key: "calories_kcal", label: "Calories", unit: "kcal", inputMode: "decimal" as const },
  { key: "protein_g", label: "Protein", unit: "g", inputMode: "decimal" as const },
  { key: "carbohydrate_g", label: "Carbohydrates", unit: "g", inputMode: "decimal" as const },
  { key: "fat_g", label: "Fat", unit: "g", inputMode: "decimal" as const },
];

function validateForm(state: NutritionLogEntryFormState): FormErrors {
  const errors: FormErrors = {};
  if (!state.food_name.trim()) {
    errors.food_name = "Food name is required.";
  } else if (state.food_name.trim().length > 200) {
    errors.food_name = "Food name must not exceed 200 characters.";
  }
  if (!state.serving_description.trim()) {
    errors.serving_description = "Serving description is required.";
  } else if (state.serving_description.trim().length > 200) {
    errors.serving_description = "Must not exceed 200 characters.";
  }
  for (const field of NUTRITION_FIELDS) {
    const key = field.key as keyof NutritionLogEntryFormState;
    const val = state[key] as string;
    const limits = NUTRITION_FIELD_LIMITS[key];
    if (!val || val.trim() === "") {
      errors[key as keyof FormErrors] = `${field.label} is required.`;
    } else {
      const num = Number(val);
      if (isNaN(num)) {
        errors[key as keyof FormErrors] = `${field.label} must be a valid number.`;
      } else if (num < limits.min) {
        errors[key as keyof FormErrors] = `${field.label} must not be negative.`;
      } else if (num > limits.max) {
        errors[key as keyof FormErrors] = `${field.label} must not exceed ${limits.max}.`;
      }
    }
  }
  return errors;
}

function buildCreatePayload(state: NutritionLogEntryFormState): NutritionLogEntryCreateRequest {
  return {
    entry_id: crypto.randomUUID(),
    food_name: state.food_name.trim(),
    meal_type: state.meal_type,
    serving_description: state.serving_description.trim(),
    calories_kcal: state.calories_kcal,
    protein_g: state.protein_g,
    carbohydrate_g: state.carbohydrate_g,
    fat_g: state.fat_g,
  };
}

export function NutritionLogEntryForm({
  onSubmit,
  loading,
  error,
  onCancel,
  initialValues,
}: NutritionLogEntryFormProps) {
  const [formState, setFormState] = useState<NutritionLogEntryFormState>(() => ({
    ...EMPTY_ENTRY_FORM,
    ...initialValues,
  }));
  const [fieldErrors, setFieldErrors] = useState<FormErrors>({});
  const [submitted, setSubmitted] = useState(false);

  useEffect(() => {
    if (initialValues) {
      setFormState((prev) => ({ ...prev, ...initialValues }));
      setSubmitted(false);
      setFieldErrors({});
    }
  }, [initialValues]);

  function handleChange(key: keyof NutritionLogEntryFormState, value: string) {
    setFormState((prev) => ({ ...prev, [key]: value }));
    if (submitted) {
      setFieldErrors((prev) => {
        const next = { ...prev };
        delete next[key as keyof FormErrors];
        return next;
      });
    }
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setSubmitted(true);

    const clientErrors = validateForm(formState);
    setFieldErrors(clientErrors);
    if (Object.keys(clientErrors).length > 0) return;

    const payload = buildCreatePayload(formState);
    const success = await onSubmit(payload);
    if (success) {
      setFormState(EMPTY_ENTRY_FORM);
      setSubmitted(false);
      setFieldErrors({});
    }
  }

  function handleCancel() {
    setFormState(initialValues ? { ...EMPTY_ENTRY_FORM, ...initialValues } : EMPTY_ENTRY_FORM);
    setSubmitted(false);
    setFieldErrors({});
    onCancel?.();
  }

  return (
    <form onSubmit={handleSubmit} noValidate aria-label="Add nutrition log entry">
      <div className="space-y-4">
        <div className="grid gap-4 sm:grid-cols-2">
          <FormField
            label="Food Name"
            required
            error={fieldErrors.food_name}
            htmlFor="food-name"
          >
            <Input
              id="food-name"
              value={formState.food_name}
              onChange={(e) => handleChange("food_name", e.target.value)}
              placeholder="e.g. Oatmeal"
              maxLength={200}
              aria-invalid={fieldErrors.food_name ? "true" : undefined}
              disabled={loading}
            />
          </FormField>

          <FormField
            label="Meal"
            required
            htmlFor="meal-type"
          >
            <Select
              id="meal-type"
              value={formState.meal_type}
              onChange={(e) => handleChange("meal_type", e.target.value as MealType)}
              disabled={loading}
            >
              {MEAL_TYPE_ORDER.map((mt) => (
                <option key={mt} value={mt}>
                  {MEAL_TYPE_LABELS[mt]}
                </option>
              ))}
            </Select>
          </FormField>
        </div>

        <FormField
          label="Serving Description"
          required
          error={fieldErrors.serving_description}
          htmlFor="serving-description"
        >
          <Input
            id="serving-description"
            value={formState.serving_description}
            onChange={(e) => handleChange("serving_description", e.target.value)}
            placeholder="e.g. 1 cup cooked"
            maxLength={200}
            aria-invalid={fieldErrors.serving_description ? "true" : undefined}
            disabled={loading}
          />
        </FormField>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {NUTRITION_FIELDS.map((field) => {
            const key = field.key as keyof NutritionLogEntryFormState;
            const errorKey = field.key as keyof FormErrors;
            const inputId = `entry-${field.key}`;
            return (
              <FormField
                key={field.key}
                label={`${field.label} (${field.unit})`}
                required
                error={fieldErrors[errorKey]}
                htmlFor={inputId}
              >
                <Input
                  id={inputId}
                  type="number"
                  inputMode={field.inputMode}
                  min={NUTRITION_FIELD_LIMITS[field.key].min}
                  max={NUTRITION_FIELD_LIMITS[field.key].max}
                  step={NUTRITION_FIELD_LIMITS[field.key].step}
                  value={formState[key] as string}
                  onChange={(e) => handleChange(key, e.target.value)}
                  placeholder="0"
                  aria-invalid={fieldErrors[errorKey] ? "true" : undefined}
                  disabled={loading}
                />
              </FormField>
            );
          })}
        </div>

        {error && (
          <Alert variant="error">{error}</Alert>
        )}

        <div className="flex items-center gap-3">
          <Button type="submit" disabled={loading}>
            {loading ? "Adding..." : "Add Entry"}
          </Button>
          {onCancel && (
            <Button type="button" variant="secondary" onClick={handleCancel} disabled={loading}>
              Cancel
            </Button>
          )}
        </div>
      </div>
    </form>
  );
}