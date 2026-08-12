"use client";

import { useEffect, useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { motion } from "framer-motion";
import { PageHeader } from "@/components/ui/page-header";
import { Card } from "@/components/ui/card";
import { Alert } from "@/components/ui/alert";
import { FormField } from "@/components/ui/form-field";
import { Input } from "@/components/ui/input";
import { SectionHeader } from "@/components/ui/section-header";
import { useDailyNutritionLogs } from "@/hooks/use-daily-nutrition-logs";
import { DailyNutritionProgressCard } from "@/components/daily-nutrition-progress-card";
import { DailyNutritionSummaryCard } from "@/components/daily-nutrition-summary-card";
import { NutritionLogEntryForm } from "@/components/nutrition-log-entry-form";
import { NutritionLogEntryList } from "@/components/nutrition-log-entry-list";
import type { MealType, NutritionLogEntryFormState } from "@/types/nutrition";
import { Calendar } from "lucide-react";

function NutritionLogsContent() {
  const searchParams = useSearchParams();
  const {
    selectedDate,
    entriesStatus,
    entries,
    entriesError,
    summaryStatus,
    summary,
    summaryError,
    progressStatus,
    progress,
    progressError,
    createStatus,
    createError,
    deleteStatus,
    deletingEntryId,
    deleteError,
    setSelectedDate,
    retryEntries,
    retrySummary,
    retryProgress,
    createEntry,
    requestDelete,
    confirmDelete,
    cancelDelete,
    clearCreateSuccess,
  } = useDailyNutritionLogs();

  const [initialFormValues, setInitialFormValues] = useState<Partial<NutritionLogEntryFormState> | undefined>();

  useEffect(() => {
    const foodName = searchParams.get("food_name");
    if (foodName) {
      setInitialFormValues({
        food_name: foodName,
        serving_description: searchParams.get("serving_description") || "1 serving",
        calories_kcal: searchParams.get("calories_kcal") || "0",
        protein_g: searchParams.get("protein_g") || "0",
        carbohydrate_g: searchParams.get("carbohydrate_g") || "0",
        fat_g: searchParams.get("fat_g") || "0",
        meal_type: (searchParams.get("meal_type") as MealType) || "breakfast",
      });
    }
  }, [searchParams]);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Food Diary"
        description="Log your daily food intake and track your nutrition targets."
      />

      {createStatus === "success" && (
        <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
          <Alert variant="success" dismissible onDismiss={clearCreateSuccess}>
            Entry added successfully.
          </Alert>
        </motion.div>
      )}

      {/* Date Selector */}
      <Card className="p-4 sm:p-5">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-brand-light">
              <Calendar className="h-5 w-5 text-brand" />
            </div>
            <div>
              <p className="text-sm font-semibold text-primary">Log Date</p>
              <p className="text-xs text-primary-secondary">Select a date to view or add entries</p>
            </div>
          </div>
          <div className="w-full sm:w-auto">
            <FormField htmlFor="log-date">
              <Input
                id="log-date"
                type="date"
                value={selectedDate}
                onChange={(e) => setSelectedDate(e.target.value)}
                className="w-full sm:w-48"
                aria-label="Date"
              />
            </FormField>
          </div>
        </div>
      </Card>

      {/* Target Progress */}
      <DailyNutritionProgressCard
        progress={progress}
        status={progressStatus}
        error={progressError}
        onRetry={retryProgress}
      />

      {/* Daily Summary */}
      <DailyNutritionSummaryCard
        summary={summary}
        status={summaryStatus}
        error={summaryError}
        onRetry={retrySummary}
      />

      {/* Add Log Entry Form */}
      <section aria-labelledby="add-entry-heading">
        <SectionHeader
          title="Add Log Entry"
          description="Log a meal or food item for the selected date."
        />
        <Card className="p-6">
          <NutritionLogEntryForm
            onSubmit={createEntry}
            loading={createStatus === "submitting"}
            error={createError}
            initialValues={initialFormValues}
          />
        </Card>
      </section>

      {/* Log Entries List */}
      <NutritionLogEntryList
        entries={entries}
        status={entriesStatus}
        error={entriesError}
        deleteStatus={deleteStatus}
        deletingEntryId={deletingEntryId}
        deleteError={deleteError}
        onDelete={requestDelete}
        onCancelDelete={cancelDelete}
        onConfirmDelete={confirmDelete}
        onRetry={retryEntries}
      />
    </div>
  );
}

export default function NutritionLogsPage() {
  return (
    <Suspense fallback={<div className="p-6">Loading Food Diary...</div>}>
      <NutritionLogsContent />
    </Suspense>
  );
}
