"use client";

import { useState, useCallback, useRef, useEffect, useMemo } from "react";
import {
  listGoals as listGoalsApi,
  createGoal as createGoalApi,
  updateGoal as updateGoalApi,
  deleteGoal as deleteGoalApi,
} from "@/services/api/goals";
import { parseFastApiValidationErrors, type FieldError } from "@/lib/validation";
import type {
  GoalData,
  GoalCreateRequest,
  GoalUpdateRequest,
  GoalListStatus,
  GoalCreateStatus,
  GoalActionStatus,
} from "@/types/goals";

export interface GoalsState {
  listStatus: GoalListStatus;
  goals: GoalData[];
  listError: string | null;
  createStatus: GoalCreateStatus;
  createError: string | null;
  createValidationErrors: FieldError[];
  actionStatus: GoalActionStatus;
  actionError: string | null;
  actionValidationErrors: FieldError[];
  actionGoalId: string | null;
  deleteConfirmGoalId: string | null;
}

export interface GoalsActions {
  reloadGoals: () => void;
  retryGoals: () => void;
  createGoal: (payload: GoalCreateRequest) => Promise<boolean>;
  updateGoal: (goalId: string, payload: GoalUpdateRequest) => Promise<boolean>;
  requestDelete: (goalId: string) => void;
  confirmDelete: () => Promise<void>;
  cancelDelete: () => void;
  clearCreateSuccess: () => void;
}

export type GoalsResult = GoalsState & GoalsActions;

export function useGoals(): GoalsResult {
  const [listStatus, setListStatus] = useState<GoalListStatus>("loading");
  const [goals, setGoals] = useState<GoalData[]>([]);
  const [listError, setListError] = useState<string | null>(null);
  const [createStatus, setCreateStatus] = useState<GoalCreateStatus>("idle");
  const [createError, setCreateError] = useState<string | null>(null);
  const [createValidationErrors, setCreateValidationErrors] = useState<FieldError[]>([]);
  const [actionStatus, setActionStatus] = useState<GoalActionStatus>("idle");
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionValidationErrors, setActionValidationErrors] = useState<FieldError[]>([]);
  const [actionGoalId, setActionGoalId] = useState<string | null>(null);
  const [deleteConfirmGoalId, setDeleteConfirmGoalId] = useState<string | null>(null);

  const mountedRef = useRef(true);
  const fetchRef = useRef(0);
  const creatingRef = useRef(false);
  const actingRef = useRef(false);
  const deletingRef = useRef(false);

  // Refs for stable function references - set synchronously
  const loadGoalsRef = useRef<((fetchId: number) => Promise<void>) | null>(null);
  const fetchGoalsRef = useRef<(() => void) | null>(null);
  const reloadGoalsRef = useRef<(() => void) | null>(null);
  const retryGoalsRef = useRef<(() => void) | null>(null);
  const createGoalRef = useRef<((payload: GoalCreateRequest) => Promise<boolean>) | null>(null);
  const updateGoalRef = useRef<((goalId: string, payload: GoalUpdateRequest) => Promise<boolean>) | null>(null);
  const requestDeleteRef = useRef<((goalId: string) => void) | null>(null);
  const confirmDeleteRef = useRef<(() => Promise<void>) | null>(null);
  const cancelDeleteRef = useRef<(() => void) | null>(null);
  const clearCreateSuccessRef = useRef<(() => void) | null>(null);

  // Define loadGoals as a regular function (not useCallback)
  // It will be assigned to the ref below
  const loadGoals = async (fetchId: number) => {
    console.log("[useGoals] loadGoals START fetchId:", fetchId, "fetchRef.current:", fetchRef.current);
    setListStatus("loading");
    setListError(null);

    try {
      const result = await listGoalsApi();
      console.log("[useGoals] loadGoals API result:", result);

      if (fetchId !== fetchRef.current) {
        console.log("[useGoals] loadGoals STALE fetchId:", fetchId, "fetchRef.current:", fetchRef.current);
        return;
      }

      if (result.success) {
        if (result.data.goals.length === 0) {
          setGoals([]);
          setListStatus("empty");
        } else {
          setGoals(result.data.goals);
          setListStatus("available");
        }
      } else {
        setGoals([]);
        setListStatus("error");
        setListError(result.error.message || "Failed to load goals.");
      }
      console.log("[useGoals] loadGoals COMPLETE listStatus:", result.success ? (result.data.goals.length === 0 ? "empty" : "available") : "error");
    } catch (err) {
      if (fetchId === fetchRef.current) {
        setGoals([]);
        setListStatus("error");
        setListError(err instanceof Error ? err.message : "An unexpected error occurred.");
        console.log("[useGoals] loadGoals ERROR:", err);
      }
    }
  };

  // Assign to refs synchronously during render
  loadGoalsRef.current = loadGoals;

  const fetchGoals = () => {
    const fetchId = ++fetchRef.current;
    loadGoalsRef.current?.(fetchId);
  };
  fetchGoalsRef.current = fetchGoals;

  const reloadGoals = () => {
    fetchGoalsRef.current?.();
  };
  reloadGoalsRef.current = reloadGoals;

  const retryGoals = () => {
    const fetchId = ++fetchRef.current;
    loadGoalsRef.current?.(fetchId);
  };
  retryGoalsRef.current = retryGoals;

  const createGoal = async (payload: GoalCreateRequest): Promise<boolean> => {
    if (!mountedRef.current || creatingRef.current) return false;
    creatingRef.current = true;
    setCreateStatus("submitting");
    setCreateError(null);
    setCreateValidationErrors([]);

    const result = await createGoalApi(payload);
    creatingRef.current = false;

    if (!mountedRef.current) return false;

    if (result.success) {
      setCreateStatus("success");
      fetchGoalsRef.current?.();
      return true;
    } else {
      setCreateStatus("error");
      setCreateError(result.error.message);
      setCreateValidationErrors(parseFastApiValidationErrors(result));
      return false;
    }
  };
  createGoalRef.current = createGoal;

  const updateGoal = async (goalId: string, payload: GoalUpdateRequest): Promise<boolean> => {
    if (!mountedRef.current || actingRef.current) return false;
    actingRef.current = true;
    setActionStatus("updating");
    setActionGoalId(goalId);
    setActionError(null);
    setActionValidationErrors([]);

    const result = await updateGoalApi(goalId, payload);
    actingRef.current = false;

    if (!mountedRef.current) return false;

    if (result.success) {
      setActionStatus("idle");
      setActionGoalId(null);
      fetchGoalsRef.current?.();
      return true;
    } else {
      setActionStatus("error");
      setActionError(result.error.message);
      setActionValidationErrors(parseFastApiValidationErrors(result));
      return false;
    }
  };
  updateGoalRef.current = updateGoal;

  const requestDelete = (goalId: string) => {
    setDeleteConfirmGoalId(goalId);
    setActionError(null);
  };
  requestDeleteRef.current = requestDelete;

  const confirmDelete = async () => {
    const currentId = deleteConfirmGoalId;
    if (!currentId || !mountedRef.current || deletingRef.current) return;
    deletingRef.current = true;
    setActionStatus("deleting");
    setActionGoalId(currentId);
    setActionError(null);

    const result = await deleteGoalApi(currentId);
    deletingRef.current = false;

    if (!mountedRef.current) return;

    if (result.success) {
      setActionStatus("idle");
      setActionGoalId(null);
      setDeleteConfirmGoalId(null);
      fetchGoalsRef.current?.();
    } else {
      setActionStatus("error");
      setActionError(result.error.message);
    }
  };
  confirmDeleteRef.current = confirmDelete;

  const cancelDelete = () => {
    setDeleteConfirmGoalId(null);
    setActionError(null);
  };
  cancelDeleteRef.current = cancelDelete;

  const clearCreateSuccess = () => {
    setCreateStatus("idle");
  };
  clearCreateSuccessRef.current = clearCreateSuccess;

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  const stableActions = useMemo<GoalsActions>(() => ({
    reloadGoals: () => reloadGoalsRef.current?.(),
    retryGoals: () => retryGoalsRef.current?.(),
    createGoal: (payload: GoalCreateRequest) => createGoalRef.current?.(payload) ?? Promise.resolve(false),
    updateGoal: (goalId: string, payload: GoalUpdateRequest) => updateGoalRef.current?.(goalId, payload) ?? Promise.resolve(false),
    requestDelete: (goalId: string) => requestDeleteRef.current?.(goalId),
    confirmDelete: () => confirmDeleteRef.current?.() ?? Promise.resolve(),
    cancelDelete: () => cancelDeleteRef.current?.(),
    clearCreateSuccess: () => clearCreateSuccessRef.current?.(),
  }), []);

  return {
    listStatus,
    goals,
    listError,
    createStatus,
    createError,
    createValidationErrors,
    actionStatus,
    actionError,
    actionValidationErrors,
    actionGoalId,
    deleteConfirmGoalId,
    ...stableActions,
  };
}
