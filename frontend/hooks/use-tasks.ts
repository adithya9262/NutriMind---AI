"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import {
  listTasks,
  createTask as createTaskApi,
  updateTask as updateTaskApi,
  completeTask as completeTaskApi,
  reopenTask as reopenTaskApi,
  deleteTask as deleteTaskApi,
} from "@/services/api/tasks";
import { parseFastApiValidationErrors, type FieldError } from "@/lib/validation";
import type {
  TaskData,
  TaskCreateRequest,
  TaskUpdateRequest,
  TaskListStatus,
  TaskCreateStatus,
  TaskActionStatus,
} from "@/types/tasks";

export interface TasksState {
  listStatus: TaskListStatus;
  tasks: TaskData[];
  listError: string | null;
  createStatus: TaskCreateStatus;
  createError: string | null;
  createValidationErrors: FieldError[];
  actionStatus: TaskActionStatus;
  actionError: string | null;
  actionValidationErrors: FieldError[];
  actionTaskId: string | null;
  deleteConfirmTaskId: string | null;
}

export interface TasksActions {
  reloadTasks: () => void;
  retryTasks: () => void;
  createTask: (payload: TaskCreateRequest) => Promise<boolean>;
  updateTask: (taskId: string, payload: TaskUpdateRequest) => Promise<boolean>;
  completeTask: (taskId: string) => Promise<boolean>;
  reopenTask: (taskId: string) => Promise<boolean>;
  requestDelete: (taskId: string) => void;
  confirmDelete: () => Promise<void>;
  cancelDelete: () => void;
  clearCreateSuccess: () => void;
}

export type TasksResult = TasksState & TasksActions;

export function useTasks(): TasksResult {
  const [listStatus, setListStatus] = useState<TaskListStatus>("loading");
  const [tasks, setTasks] = useState<TaskData[]>([]);
  const [listError, setListError] = useState<string | null>(null);
  const [createStatus, setCreateStatus] = useState<TaskCreateStatus>("idle");
  const [createError, setCreateError] = useState<string | null>(null);
  const [createValidationErrors, setCreateValidationErrors] = useState<FieldError[]>([]);
  const [actionStatus, setActionStatus] = useState<TaskActionStatus>("idle");
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionValidationErrors, setActionValidationErrors] = useState<FieldError[]>([]);
  const [actionTaskId, setActionTaskId] = useState<string | null>(null);
  const [deleteConfirmTaskId, setDeleteConfirmTaskId] = useState<string | null>(null);

  const mountedRef = useRef(true);
  const fetchRef = useRef(0);
  const abortRef = useRef<AbortController | null>(null);
  const creatingRef = useRef(false);
  const actingRef = useRef(false);
  const deletingRef = useRef(false);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
      creatingRef.current = false;
      actingRef.current = false;
      deletingRef.current = false;
      if (abortRef.current) abortRef.current.abort();
    };
  }, []);

  const loadTasks = useCallback(async (fetchId: number) => {
    setListStatus("loading");
    setListError(null);

    if (abortRef.current) abortRef.current.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    try {
      const result = await listTasks(controller.signal);

      if (fetchId !== fetchRef.current) return;

      if (result.success) {
        if (result.data.tasks.length === 0) {
          setTasks([]);
          setListStatus("empty");
        } else {
          setTasks(result.data.tasks);
          setListStatus("available");
        }
      } else {
        setTasks([]);
        setListStatus("error");
        setListError(result.error.message || "Failed to load tasks.");
      }
    } catch (err) {
      if (fetchId === fetchRef.current) {
        setTasks([]);
        setListStatus("error");
        setListError(err instanceof Error ? err.message : "An unexpected error occurred.");
      }
    }
  }, []);

  const fetchTasks = useCallback(() => {
    const fetchId = ++fetchRef.current;
    loadTasks(fetchId);
  }, [loadTasks]);

  const reloadTasks = useCallback(() => {
    fetchTasks();
  }, [fetchTasks]);

  const retryTasks = useCallback(() => {
    const fetchId = ++fetchRef.current;
    loadTasks(fetchId);
  }, [loadTasks]);

  const createTask = useCallback(
    async (payload: TaskCreateRequest): Promise<boolean> => {
      if (creatingRef.current) return false;
      creatingRef.current = true;
      setCreateStatus("submitting");
      setCreateError(null);

      const result = await createTaskApi(payload);
      creatingRef.current = false;

      if (result.success) {
        setCreateStatus("success");
        setCreateValidationErrors([]);
        fetchTasks();
        return true;
      } else {
        setCreateStatus("error");
        setCreateError(result.error.message);
        setCreateValidationErrors(parseFastApiValidationErrors(result));
        return false;
      }
    },
    [fetchTasks]
  );

  const updateTask = useCallback(
    async (taskId: string, payload: TaskUpdateRequest): Promise<boolean> => {
      if (actingRef.current) return false;
      actingRef.current = true;
      setActionStatus("updating");
      setActionTaskId(taskId);
      setActionError(null);
      setActionValidationErrors([]);

      const result = await updateTaskApi(taskId, payload);
      actingRef.current = false;

      if (result.success) {
        setActionStatus("idle");
        setActionTaskId(null);
        fetchTasks();
        return true;
      } else {
        setActionStatus("error");
        setActionError(result.error.message);
        setActionValidationErrors(parseFastApiValidationErrors(result));
        return false;
      }
    },
    [fetchTasks]
  );

  const completeTask = useCallback(
    async (taskId: string): Promise<boolean> => {
      if (actingRef.current) return false;
      actingRef.current = true;
      setActionStatus("completing");
      setActionTaskId(taskId);
      setActionError(null);

      const completedAt = new Date().toISOString();
      const result = await completeTaskApi(taskId, completedAt);
      actingRef.current = false;

      if (result.success) {
        setActionStatus("idle");
        setActionTaskId(null);
        fetchTasks();
        return true;
      } else {
        setActionStatus("error");
        setActionError(result.error.message);
        return false;
      }
    },
    [fetchTasks]
  );

  const reopenTask = useCallback(
    async (taskId: string): Promise<boolean> => {
      if (actingRef.current) return false;
      actingRef.current = true;
      setActionStatus("reopening");
      setActionTaskId(taskId);
      setActionError(null);

      const result = await reopenTaskApi(taskId);
      actingRef.current = false;

      if (result.success) {
        setActionStatus("idle");
        setActionTaskId(null);
        fetchTasks();
        return true;
      } else {
        setActionStatus("error");
        setActionError(result.error.message);
        return false;
      }
    },
    [fetchTasks]
  );

  const requestDelete = useCallback((taskId: string) => {
    setDeleteConfirmTaskId(taskId);
    setActionError(null);
  }, []);

  const confirmDelete = useCallback(async () => {
    const currentId = deleteConfirmTaskId;
    if (!currentId || deletingRef.current) return;
    deletingRef.current = true;
    setActionStatus("deleting");
    setActionTaskId(currentId);
    setActionError(null);

    const result = await deleteTaskApi(currentId);
    deletingRef.current = false;

    if (result.success) {
      setActionStatus("idle");
      setActionTaskId(null);
      setDeleteConfirmTaskId(null);
      fetchTasks();
    } else {
      setActionStatus("error");
      setActionError(result.error.message);
    }
  }, [deleteConfirmTaskId, fetchTasks]);

  const cancelDelete = useCallback(() => {
    setDeleteConfirmTaskId(null);
    setActionError(null);
  }, []);

  const clearCreateSuccess = useCallback(() => {
    setCreateStatus("idle");
  }, []);

  return {
    listStatus,
    tasks,
    listError,
    createStatus,
    createError,
    createValidationErrors,
    actionStatus,
    actionError,
    actionValidationErrors,
    actionTaskId,
    deleteConfirmTaskId,
    reloadTasks,
    retryTasks,
    createTask,
    updateTask,
    completeTask,
    reopenTask,
    requestDelete,
    confirmDelete,
    cancelDelete,
    clearCreateSuccess,
  };
}
