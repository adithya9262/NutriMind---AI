"use client";

import { useState, useCallback, type FormEvent } from "react";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Select } from "@/components/ui/select";
import { Calendar, Type, AlignLeft } from "lucide-react";
import { FormField } from "@/components/ui/form-field";
import { Button } from "@/components/ui/button";
import { Alert } from "@/components/ui/alert";
import {
  PRIORITY_LABELS,
  TASK_CATEGORY_LABELS,
  TASK_RECURRENCE_LABELS,
  MIN_TASK_TITLE_LENGTH,
  MAX_TASK_TITLE_LENGTH,
  MAX_TASK_DESCRIPTION_LENGTH,
  EMPTY_TASK_FORM,
  type TaskPriority,
  type TaskCategory,
  type TaskRecurrence,
  type TaskFormState,
  type TaskCreateRequest,
  type TaskUpdateRequest,
} from "@/types/tasks";
import { parseFastApiValidationErrors, type FieldError, getFieldError } from "@/lib/validation";

interface TaskFormProps {
  onSubmit: (payload: TaskCreateRequest) => Promise<boolean>;
  loading: boolean;
  error: string | null;
  apiFieldErrors?: FieldError[];
  onCancel?: () => void;
  initialData?: TaskFormState;
  isEditing?: boolean;
}

interface FieldErrors {
  title?: string;
  description?: string;
  due_date?: string;
  priority?: string;
  category?: string;
  recurrence?: string;
}

export function TaskForm({ onSubmit, loading, error, apiFieldErrors, onCancel, initialData, isEditing = false }: TaskFormProps) {
  const [form, setForm] = useState<TaskFormState>(initialData || EMPTY_TASK_FORM);
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});

  const validate = useCallback((): boolean => {
    const errors: FieldErrors = {};
    const trimmedTitle = form.title.trim();

    if (!trimmedTitle) {
      errors.title = "Title is required.";
    } else if (trimmedTitle.length < MIN_TASK_TITLE_LENGTH) {
      errors.title = "Title must not be empty.";
    } else if (trimmedTitle.length > MAX_TASK_TITLE_LENGTH) {
      errors.title = `Title must not exceed ${MAX_TASK_TITLE_LENGTH} characters.`;
    }

    if (form.description.length > MAX_TASK_DESCRIPTION_LENGTH) {
      errors.description = `Description must not exceed ${MAX_TASK_DESCRIPTION_LENGTH} characters.`;
    }

    if (form.due_date && !/^\d{4}-\d{2}-\d{2}$/.test(form.due_date)) {
      errors.due_date = "Enter a valid date (YYYY-MM-DD).";
    }

    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  }, [form]);

  const handleSubmit = useCallback(
    async (e: FormEvent) => {
      e.preventDefault();
      if (loading) return;
      if (!validate()) return;

      const payload: TaskCreateRequest = {
        title: form.title.trim(),
        priority: form.priority,
        category: form.category,
        recurrence: form.recurrence,
      };

      if (form.description.trim()) {
        payload.description = form.description.trim();
      }

      if (form.due_date) {
        payload.due_date = form.due_date;
      }

      const ok = await onSubmit(payload);
      if (ok) {
        setForm(EMPTY_TASK_FORM);
        setFieldErrors({});
      }
    },
    [form, loading, onSubmit, validate]
  );

  const handleCancel = useCallback(() => {
    setForm(EMPTY_TASK_FORM);
    setFieldErrors({});
    onCancel?.();
  }, [onCancel]);

  const updateField = useCallback(
    <K extends keyof TaskFormState>(field: K, value: TaskFormState[K]) => {
      setForm((prev) => ({ ...prev, [field]: value }));
      if (fieldErrors[field as keyof FieldErrors]) {
        setFieldErrors((prev) => {
          const next = { ...prev };
          delete next[field as keyof FieldErrors];
          return next;
        });
      }
    },
    [fieldErrors]
  );

  const mergedErrors: FieldErrors = { ...fieldErrors };
  if (apiFieldErrors) {
    for (const apiError of apiFieldErrors) {
      const field = apiError.field;
      if (!mergedErrors[field as keyof FieldErrors]) {
        mergedErrors[field as keyof FieldErrors] = apiError.message;
      }
    }
  }

  return (
    <form onSubmit={handleSubmit} noValidate className="space-y-4">
      <FormField
        label="Title"
        required
        error={mergedErrors.title}
        htmlFor="task-title"
      >
        <div className="relative">
          <Type className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-primary-muted pointer-events-none" />
          <Input
            id="task-title"
            type="text"
            value={form.title}
            onChange={(e) => updateField("title", e.target.value)}
            placeholder="Enter task title"
            disabled={loading}
            aria-required="true"
            aria-invalid={!!mergedErrors.title}
            maxLength={MAX_TASK_TITLE_LENGTH}
            className="pl-9"
          />
        </div>
      </FormField>

      <FormField
        label="Description"
        error={mergedErrors.description}
        htmlFor="task-description"
      >
        <div className="relative">
          <AlignLeft className="absolute left-3 top-3 h-4 w-4 text-primary-muted pointer-events-none" />
          <Textarea
            id="task-description"
            value={form.description}
            onChange={(e) => updateField("description", e.target.value)}
            placeholder="Optional description"
            disabled={loading}
            aria-invalid={!!mergedErrors.description}
            maxLength={MAX_TASK_DESCRIPTION_LENGTH}
            className="pl-9 min-h-[80px]"
          />
        </div>
      </FormField>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <FormField label="Category" htmlFor="task-category" error={mergedErrors.category}>
          <Select
            id="task-category"
            value={form.category}
            onChange={(e) =>
              updateField("category", e.target.value as TaskCategory)
            }
            disabled={loading}
            error={mergedErrors.category}
            aria-invalid={!!mergedErrors.category}
          >
            {(Object.keys(TASK_CATEGORY_LABELS) as TaskCategory[]).map((key) => (
              <option key={key} value={key}>
                {TASK_CATEGORY_LABELS[key]}
              </option>
            ))}
          </Select>
        </FormField>

        <FormField label="Recurrence" htmlFor="task-recurrence" error={mergedErrors.recurrence}>
          <Select
            id="task-recurrence"
            value={form.recurrence}
            onChange={(e) =>
              updateField("recurrence", e.target.value as TaskRecurrence)
            }
            disabled={loading}
            error={mergedErrors.recurrence}
            aria-invalid={!!mergedErrors.recurrence}
          >
            {(Object.keys(TASK_RECURRENCE_LABELS) as TaskRecurrence[]).map((key) => (
              <option key={key} value={key}>
                {TASK_RECURRENCE_LABELS[key]}
              </option>
            ))}
          </Select>
        </FormField>
      </div>

      <FormField label="Priority" htmlFor="task-priority" error={mergedErrors.priority}>
        <Select
          id="task-priority"
          value={form.priority}
          onChange={(e) =>
            updateField("priority", e.target.value as TaskPriority)
          }
          disabled={loading}
          error={mergedErrors.priority}
          aria-invalid={!!mergedErrors.priority}
        >
          <option value="low">{PRIORITY_LABELS.low}</option>
          <option value="medium">{PRIORITY_LABELS.medium}</option>
          <option value="high">{PRIORITY_LABELS.high}</option>
        </Select>
      </FormField>

      <FormField label="Due Date" htmlFor="task-due-date" error={mergedErrors.due_date}>
        <div className="relative">
          <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-primary-muted pointer-events-none" />
          <Input
            id="task-due-date"
            type="date"
            value={form.due_date}
            onChange={(e) => updateField("due_date", e.target.value)}
            disabled={loading}
            className="pl-9"
            aria-invalid={!!mergedErrors.due_date}
          />
        </div>
      </FormField>

      {error && (
        <Alert variant="error" className="mt-2" role="alert">
          {error}
        </Alert>
      )}

      <div className="flex gap-2">
        <Button type="submit" disabled={loading} size="sm">
          {loading ? (isEditing ? "Saving..." : "Creating...") : (isEditing ? "Save Changes" : "Add Task")}
        </Button>
        {onCancel && (
          <Button
            type="button"
            variant="secondary"
            size="sm"
            onClick={handleCancel}
            disabled={loading}
          >
            Cancel
          </Button>
        )}
      </div>
    </form>
  );
}