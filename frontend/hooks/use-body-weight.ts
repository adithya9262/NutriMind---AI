"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import {
  listBodyWeightHistory,
  createBodyWeightEntry as createBodyWeightEntryApi,
  deleteBodyWeightEntry as deleteBodyWeightEntryApi,
  getBodyWeightTrend,
  getBodyWeightGoalProgress,
} from "@/services/api/body-weight";
import type {
  BodyWeightEntryData,
  BodyWeightTrendData,
  BodyWeightGoalProgressData,
  HistoryStatus,
  TrendStatus,
  GoalStatus,
  CreateStatus,
  DeleteStatus,
} from "@/types/body-weight";

export interface BodyWeightState {
  historyStatus: HistoryStatus;
  entries: BodyWeightEntryData[];
  historyError: string | null;
  trendStatus: TrendStatus;
  trend: BodyWeightTrendData | null;
  trendError: string | null;
  goalStatus: GoalStatus;
  goalProgress: BodyWeightGoalProgressData | null;
  goalError: string | null;
  createStatus: CreateStatus;
  createError: string | null;
  deleteStatus: DeleteStatus;
  deletingEntryId: string | null;
  deleteError: string | null;
}

export interface BodyWeightActions {
  reloadAll: () => void;
  retryHistory: () => void;
  retryTrend: () => void;
  retryGoalProgress: () => void;
  createEntry: (loggedDate: string, weightKg: string) => Promise<boolean>;
  requestDelete: (entryId: string) => void;
  confirmDelete: () => Promise<void>;
  cancelDelete: () => void;
  clearCreateSuccess: () => void;
}

export type BodyWeightResult = BodyWeightState & BodyWeightActions;

export function useBodyWeight(): BodyWeightResult {
  const [historyStatus, setHistoryStatus] = useState<HistoryStatus>("loading");
  const [entries, setEntries] = useState<BodyWeightEntryData[]>([]);
  const [historyError, setHistoryError] = useState<string | null>(null);
  const [trendStatus, setTrendStatus] = useState<TrendStatus>("loading");
  const [trend, setTrend] = useState<BodyWeightTrendData | null>(null);
  const [trendError, setTrendError] = useState<string | null>(null);
  const [goalStatus, setGoalStatus] = useState<GoalStatus>("loading");
  const [goalProgress, setGoalProgress] = useState<BodyWeightGoalProgressData | null>(null);
  const [goalError, setGoalError] = useState<string | null>(null);
  const [createStatus, setCreateStatus] = useState<CreateStatus>("idle");
  const [createError, setCreateError] = useState<string | null>(null);
  const [deleteStatus, setDeleteStatus] = useState<DeleteStatus>("idle");
  const [deletingEntryId, setDeletingEntryId] = useState<string | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const mountedRef = useRef(true);

  // Each sub-fetch has its own independent sequence counter so a retry of
  // one sub-fetch never invalidates the in-flight results of the others.
  const historyFetchRef = useRef(0);
  const trendFetchRef = useRef(0);
  const goalFetchRef = useRef(0);

  const historyAbortRef = useRef<AbortController | null>(null);
  const trendAbortRef = useRef<AbortController | null>(null);
  const goalAbortRef = useRef<AbortController | null>(null);
  const creatingRef = useRef(false);
  const deletingRef = useRef(false);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
      historyAbortRef.current?.abort();
      trendAbortRef.current?.abort();
      goalAbortRef.current?.abort();
    };
  }, []);

  // ── History ───────────────────────────────────────────────────────────────
  const loadHistory = useCallback(async () => {
    if (!mountedRef.current) return;
    const fetchId = ++historyFetchRef.current;
    setHistoryStatus("loading");
    setHistoryError(null);

    historyAbortRef.current?.abort();
    const controller = new AbortController();
    historyAbortRef.current = controller;

    const result = await listBodyWeightHistory(controller.signal);

    if (!mountedRef.current || fetchId !== historyFetchRef.current) return;

    if (result.success) {
      const historyData = result.data;
      setEntries(historyData.entries.length === 0 ? [] : historyData.entries);
      setHistoryStatus(historyData.entries.length === 0 ? "empty" : "available");
    } else {
      setEntries([]);
      setHistoryStatus("error");
      setHistoryError(result.error.message);
    }
  }, []);

  // ── Trend ─────────────────────────────────────────────────────────────────
  const loadTrend = useCallback(async () => {
    if (!mountedRef.current) return;
    const fetchId = ++trendFetchRef.current;
    setTrendStatus("loading");
    setTrendError(null);

    trendAbortRef.current?.abort();
    const controller = new AbortController();
    trendAbortRef.current = controller;

    const result = await getBodyWeightTrend(controller.signal);

    if (!mountedRef.current || fetchId !== trendFetchRef.current) return;

    if (result.success) {
      setTrend(result.data);
      setTrendStatus("available");
    } else {
      setTrend(null);
      if (result.error.code === "BODY_WEIGHT_TREND_INSUFFICIENT_HISTORY") {
        setTrendStatus("insufficient");
      } else {
        setTrendStatus("error");
        setTrendError(result.error.message);
      }
    }
  }, []);

  // ── Goal progress ─────────────────────────────────────────────────────────
  const loadGoalProgress = useCallback(async () => {
    if (!mountedRef.current) return;
    const fetchId = ++goalFetchRef.current;
    setGoalStatus("loading");
    setGoalError(null);

    goalAbortRef.current?.abort();
    const controller = new AbortController();
    goalAbortRef.current = controller;

    const result = await getBodyWeightGoalProgress(controller.signal);

    if (!mountedRef.current || fetchId !== goalFetchRef.current) return;

    if (result.success) {
      setGoalProgress(result.data);
      setGoalStatus("available");
    } else {
      setGoalProgress(null);
      const code = result.error.code;
      if (code === "NUTRITION_PROFILE_NOT_FOUND" || code === "NUTRITION_PROFILE_INCOMPLETE") {
        setGoalStatus("missing_profile");
      } else if (code === "BODY_WEIGHT_GOAL_CURRENT_WEIGHT_NOT_FOUND") {
        setGoalStatus("missing_current_weight");
      } else if (code === "BODY_WEIGHT_GOAL_PROGRESS_INVALID") {
        setGoalStatus("invalid_goal");
      } else {
        setGoalStatus("error");
        setGoalError(result.error.message);
      }
    }
  }, []);

  // Use refs so reloadAll / createEntry / confirmDelete stay stable
  const loadHistoryRef = useRef(loadHistory);
  const loadTrendRef = useRef(loadTrend);
  const loadGoalProgressRef = useRef(loadGoalProgress);
  useEffect(() => { loadHistoryRef.current = loadHistory; }, [loadHistory]);
  useEffect(() => { loadTrendRef.current = loadTrend; }, [loadTrend]);
  useEffect(() => { loadGoalProgressRef.current = loadGoalProgress; }, [loadGoalProgress]);

  const reloadAll = useCallback(() => {
    loadHistoryRef.current();
    loadTrendRef.current();
    loadGoalProgressRef.current();
  }, []);

  const retryHistory = useCallback(() => { loadHistoryRef.current(); }, []);
  const retryTrend = useCallback(() => { loadTrendRef.current(); }, []);
  const retryGoalProgress = useCallback(() => { loadGoalProgressRef.current(); }, []);

  const createEntry = useCallback(
    async (loggedDate: string, weightKg: string): Promise<boolean> => {
      if (!mountedRef.current || creatingRef.current) return false;
      creatingRef.current = true;
      setCreateStatus("submitting");
      setCreateError(null);

      const result = await createBodyWeightEntryApi(loggedDate, weightKg);
      creatingRef.current = false;

      if (!mountedRef.current) return false;

      if (result.success) {
        setCreateStatus("success");
        loadHistoryRef.current();
        loadTrendRef.current();
        loadGoalProgressRef.current();
        return true;
      } else {
        setCreateStatus("error");
        setCreateError(result.error.message);
        return false;
      }
    },
    []
  );

  const requestDelete = useCallback((entryId: string) => {
    setDeleteStatus("confirming");
    setDeletingEntryId(entryId);
    setDeleteError(null);
  }, []);

  // Use a ref so confirmDelete's identity is stable despite reading deletingEntryId
  const deletingEntryIdRef = useRef<string | null>(null);
  useEffect(() => { deletingEntryIdRef.current = deletingEntryId; }, [deletingEntryId]);

  const confirmDelete = useCallback(async () => {
    const entryId = deletingEntryIdRef.current;
    if (!entryId || !mountedRef.current || deletingRef.current) return;
    deletingRef.current = true;
    setDeleteStatus("deleting");
    setDeleteError(null);

    const result = await deleteBodyWeightEntryApi(entryId);
    deletingRef.current = false;

    if (!mountedRef.current) return;

    if (result.success) {
      setDeleteStatus("idle");
      setDeletingEntryId(null);
      loadHistoryRef.current();
      loadTrendRef.current();
      loadGoalProgressRef.current();
    } else {
      setDeleteStatus("error");
      setDeleteError(result.error.message);
    }
  }, []);

  const cancelDelete = useCallback(() => {
    setDeleteStatus("idle");
    setDeletingEntryId(null);
    setDeleteError(null);
  }, []);

  const clearCreateSuccess = useCallback(() => {
    setCreateStatus("idle");
  }, []);

  return {
    historyStatus,
    entries,
    historyError,
    trendStatus,
    trend,
    trendError,
    goalStatus,
    goalProgress,
    goalError,
    createStatus,
    createError,
    deleteStatus,
    deletingEntryId,
    deleteError,
    reloadAll,
    retryHistory,
    retryTrend,
    retryGoalProgress,
    createEntry,
    requestDelete,
    confirmDelete,
    cancelDelete,
    clearCreateSuccess,
  };
}
