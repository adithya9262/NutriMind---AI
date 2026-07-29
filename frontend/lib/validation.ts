import type { ApiErrorResponseBody } from "@/types/api";

export interface FieldError {
  field: string;
  message: string;
}

export function parseFastApiValidationErrors(errorBody: unknown): FieldError[] {
  if (!errorBody || typeof errorBody !== "object") return [];

  const err = (errorBody as Record<string, unknown>).error;
  if (!err || typeof err !== "object") return [];

  let detail = (err as Record<string, unknown>).detail;
  if (!detail || !Array.isArray(detail)) {
    detail = (err as Record<string, unknown>).details;
  }
  if (!detail || !Array.isArray(detail)) return [];

  const fieldErrors: FieldError[] = [];

  for (const item of detail) {
    if (typeof item !== "object" || item === null) continue;

    const loc = (item as Record<string, unknown>).loc;
    const msg = (item as Record<string, unknown>).msg;

    if (!loc || !Array.isArray(loc) || typeof msg !== "string") continue;

    // FastAPI loc format: ["body", "field_name"] or ["body", "field", "subfield"]
    // We want the field name (last element that's not "body")
    const fieldPath = loc.filter((part): part is string => typeof part === "string" && part !== "body");
    if (fieldPath.length === 0) continue;

    const field = fieldPath.join(".");
    
    // Convert technical Pydantic messages to user-friendly ones
    let message = msg;
    if (msg.includes("Input should be a valid")) {
      if (msg.includes("date")) message = "Enter a valid date.";
      else if (msg.includes("number") || msg.includes("integer")) message = "Enter a valid number.";
      else if (msg.includes("string")) message = "Enter valid text.";
      else message = "Enter a valid value.";
    } else if (msg.includes("Input should be")) {
      message = msg.replace("Input should be", "").trim();
      message = message.charAt(0).toLowerCase() + message.slice(1);
    } else if (msg.includes("Field required")) {
      message = "This field is required.";
    } else if (msg.includes("String should have at least")) {
      const match = msg.match(/at least (\d+)/);
      message = match ? `Must be at least ${match[1]} character(s).` : "Value is too short.";
    } else if (msg.includes("String should have at most")) {
      const match = msg.match(/at most (\d+)/);
      message = match ? `Must be at most ${match[1]} character(s).` : "Value is too long.";
    } else if (msg.includes("Greater than")) {
      message = "Value must be greater than 0.";
    } else if (msg.includes("Less than")) {
      message = "Value is too large.";
    }

    fieldErrors.push({ field, message });
  }

  return fieldErrors;
}

export function getFieldError(fieldErrors: FieldError[], fieldName: string): string | undefined {
  return fieldErrors.find((e) => e.field === fieldName)?.message;
}

export function mapFastApiFieldToFrontend(apiField: string): string {
  const mapping: Record<string, string> = {
    "title": "title",
    "description": "description",
    "due_date": "due_date",
    "priority": "priority",
    "category": "category",
    "recurrence": "recurrence",
  };
  return mapping[apiField] || apiField;
}