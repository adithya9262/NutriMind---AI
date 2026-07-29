import { apiGet, apiPost, apiPatch, apiDelete } from "./client";
import type {
  TaskCreateRequest,
  TaskUpdateRequest,
  TaskCompleteRequest,
  TaskData,
  TaskListData,
  TaskSuccessResponse,
  TaskListSuccessResponse,
  TaskDeleteSuccessResponse,
} from "@/types/tasks";

export async function listTasks(signal?: AbortSignal) {
  return apiGet<TaskListData>("/tasks", { signal });
}

export async function getTask(taskId: string, signal?: AbortSignal) {
  return apiGet<TaskData>(
    `/tasks/${encodeURIComponent(taskId)}`,
    { signal }
  );
}

export async function createTask(
  payload: TaskCreateRequest,
  signal?: AbortSignal
) {
  return apiPost<TaskData>("/tasks", payload, { signal });
}

export async function updateTask(
  taskId: string,
  payload: TaskUpdateRequest,
  signal?: AbortSignal
) {
  return apiPatch<TaskData>(
    `/tasks/${encodeURIComponent(taskId)}`,
    payload,
    { signal }
  );
}

export async function completeTask(
  taskId: string,
  completedAt: string,
  signal?: AbortSignal
) {
  const body: TaskCompleteRequest = { completed_at: completedAt };
  return apiPost<TaskData>(
    `/tasks/${encodeURIComponent(taskId)}/complete`,
    body,
    { signal }
  );
}

export async function reopenTask(taskId: string, signal?: AbortSignal) {
  return apiPost<TaskData>(
    `/tasks/${encodeURIComponent(taskId)}/reopen`,
    undefined,
    { signal }
  );
}

export async function deleteTask(taskId: string, signal?: AbortSignal) {
  return apiDelete<Record<string, never>>(
    `/tasks/${encodeURIComponent(taskId)}`,
    { signal }
  );
}
