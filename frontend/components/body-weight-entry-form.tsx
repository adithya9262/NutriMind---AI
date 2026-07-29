"use client";

import { useState, useCallback, type FormEvent } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { FormField } from "@/components/ui/form-field";
import { Alert } from "@/components/ui/alert";
import { Card } from "@/components/ui/card";
import { getLocalCalendarDate } from "@/lib/dates";
import {
  MIN_WEIGHT_KG,
  MAX_WEIGHT_KG,
  WEIGHT_STEP,
} from "@/types/body-weight";

interface BodyWeightEntryFormProps {
  onSubmit: (loggedDate: string, weightKg: string) => Promise<boolean>;
  loading: boolean;
  error: string | null;
  onCancel?: () => void;
}

export function BodyWeightEntryForm({
  onSubmit,
  loading,
  error,
  onCancel,
}: BodyWeightEntryFormProps) {
  const currentDate = getLocalCalendarDate();
  const [loggedDate, setLoggedDate] = useState(currentDate);
  const [weightKg, setWeightKg] = useState("");
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  const validate = useCallback((): boolean => {
    const errors: Record<string, string> = {};

    if (!loggedDate) {
      errors.logged_date = "Date is required.";
    }

    if (!weightKg) {
      errors.weight_kg = "Weight is required.";
    } else {
      const num = Number(weightKg);
      if (isNaN(num) || num < MIN_WEIGHT_KG || num > MAX_WEIGHT_KG) {
        errors.weight_kg = `Weight must be between ${MIN_WEIGHT_KG} and ${MAX_WEIGHT_KG} kg.`;
      }
    }

    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  }, [loggedDate, weightKg]);

  const handleSubmit = useCallback(
    async (e: FormEvent) => {
      e.preventDefault();
      if (loading) return;
      if (!validate()) return;
      await onSubmit(loggedDate, weightKg);
    },
    [loading, loggedDate, weightKg, validate, onSubmit]
  );

  const handleCancel = useCallback(() => {
    if (onCancel) onCancel();
  }, [onCancel]);

  return (
    <Card>
      <form onSubmit={handleSubmit} noValidate>
        <div className="space-y-4">
          {error && (
            <Alert variant="error">{error}</Alert>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <FormField
              label="Date"
              required
              error={fieldErrors.logged_date}
              htmlFor="bw-logged-date"
            >
              <Input
                id="bw-logged-date"
                type="date"
                value={loggedDate}
                onChange={(e) => setLoggedDate(e.target.value)}
                disabled={loading}
                aria-invalid={fieldErrors.logged_date ? "true" : undefined}
                max={currentDate}
              />
            </FormField>

            <FormField
              label="Weight (kg)"
              required
              error={fieldErrors.weight_kg}
              htmlFor="bw-weight-kg"
            >
              <Input
                id="bw-weight-kg"
                type="number"
                inputMode="decimal"
                value={weightKg}
                onChange={(e) => setWeightKg(e.target.value)}
                disabled={loading}
                placeholder="e.g. 70.00"
                min={MIN_WEIGHT_KG}
                max={MAX_WEIGHT_KG}
                step={WEIGHT_STEP}
                aria-invalid={fieldErrors.weight_kg ? "true" : undefined}
              />
            </FormField>
          </div>

          <div className="flex gap-2">
            <Button type="submit" disabled={loading}>
              {loading ? "Saving..." : "Add Weight"}
            </Button>
            {onCancel && (
              <Button
                type="button"
                variant="secondary"
                onClick={handleCancel}
                disabled={loading}
              >
                Cancel
              </Button>
            )}
          </div>
        </div>
      </form>
    </Card>
  );
}
