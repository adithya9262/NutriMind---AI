"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import {
  listNutritionLogEntries,
  createNutritionLogEntry,
  deleteNutritionLogEntry,
  getDailyNutritionLogSummary,
  getDailyNutritionTargetProgress,
} from "@/services/api/nutrition-logs";
import { getLocalCalendarDate } from "@/lib/dates";
import type {
  NutritionLogEntryData,
  NutritionLogEntryCreateRequest,
  DailyNutritionLogSummaryData,
  DailyNutritionProgressData,
  EntryReadStatus,
  SummaryReadStatus,
  ProgressReadStatus,
  CreateStatus,
  DeleteStatus,
} from "@/types/nutrition";

export interface DailyNutritionLogsState {
  selectedDate: string;
  entriesStatus: EntryReadStatus;
  entries: NutritionLogEntryData[];
  entriesError: string | null;
  summaryStatus: SummaryReadStatus;
  summary: DailyNutritionLogSummaryData | null;
  summaryError: string | null;
  progressStatus: ProgressReadStatus;
  progress: DailyNutritionProgressData | null;
  progressError: string | null;
  createStatus: CreateStatus;
  createError: string | null;
  deleteStatus: DeleteStatus;
  deletingEntryId: string | null;
  deleteError: string | null;
}

export interface DailyNutritionLogsActions {
  setSelectedDate: (date: string) => void;
  reloadAll: () => void;
  retryEntries: () => void;
  retrySummary: () => void;
  retryProgress: () => void;
  createEntry: (payload: NutritionLogEntryCreateRequest) => Promise<boolean>;
  requestDelete: (entryId: string) => void;
  confirmDelete: () => Promise<void>;
  cancelDelete: () => void;
  clearCreateSuccess: () => void;
  clearDeleteSuccess: () => void;
}

export type DailyNutritionLogsResult = DailyNutritionLogsState &
  DailyNutritionLogsActions;

export function useDailyNutritionLogs(
  initialDate?: string
): DailyNutritionLogsResult {
  const [selectedDate, setSelectedDateState] = useState<string>(
    initialDate ?? getLocalCalendarDate()
  );
  const [entriesStatus, setEntriesStatus] = useState<EntryReadStatus>("loading");
  const [entries, setEntries] = useState<NutritionLogEntryData[]>([]);
  const [entriesError, setEntriesError] = useState<string | null>(null);
  const [summaryStatus, setSummaryStatus] = useState<SummaryReadStatus>("loading");
  const [summary, setSummary] = useState<DailyNutritionLogSummaryData | null>(null);
  const [summaryError, setSummaryError] = useState<string | null>(null);
  const [progressStatus, setProgressStatus] = useState<ProgressReadStatus>("loading");
  const [progress, setProgress] = useState<DailyNutritionProgressData | null>(null);
  const [progressError, setProgressError] = useState<string | null>(null);
  const [createStatus, setCreateStatus] = useState<CreateStatus>("idle");
  const [createError, setCreateError] = useState<string | null>(null);
  const [deleteStatus, setDeleteStatus] = useState<DeleteStatus>("idle");
  const [deletingEntryId, setDeletingEntryId] = useState<string | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const mountedRef = useRef(true);

  // Independent sequence counters — a retry of one sub-fetch never
  // invalidates the in-flight results of the others.
  const entriesFetchRef = useRef(0);
  const summaryFetchRef = useRef(0);
  const progressFetchRef = useRef(0);

  const entriesAbortRef = useRef<AbortController | null>(null);
  const summaryAbortRef = useRef<AbortController | null>(null);
  const progressAbortRef = useRef<AbortController | null>(null);
  const creatingRef = useRef(false);
  const deletingRef = useRef(false);

  useEffect(() => {
    mountedRef.current = true;
    loadEntriesRef.current(selectedDate);
    loadSummaryRef.current(selectedDate);
    loadProgressRef.current(selectedDate);
    return () => {
      mountedRef.current = false;
      entriesAbortRef.current?.abort();
      summaryAbortRef.current?.abort();
      progressAbortRef.current?.abort();
    };
  }, [selectedDate]);

  // ── Entries ───────────────────────────────────────────────────────────────
  const loadEntries = useCallback(async (date: string) => {
    if (!mountedRef.current) return;
    const fetchId = ++entriesFetchRef.current;
    setEntriesStatus("loading");
    setEntriesError(null);

    entriesAbortRef.current?.abort();
    const controller = new AbortController();
    entriesAbortRef.current = controller;

    try {
      const result = await listNutritionLogEntries(date, controller.signal);

      if (!mountedRef.current || fetchId !== entriesFetchRef.current) return;

      if (result.success) {
        setEntries(result.data.entries);
        setEntriesStatus(result.data.entries.length === 0 ? "empty" : "available");
      } else {
        setEntries([]);
        setEntriesStatus("error");
        setEntriesError(result.error.message);
      }
    } catch (err: unknown) {
      if ((err as Error)?.name === "AbortError") return;
      if (!mountedRef.current || fetchId !== entriesFetchRef.current) return;
      setEntries([]);
      setEntriesStatus("error");
      setEntriesError((err as Error)?.message || "Failed to load nutrition log entries.");
    }
  }, []);

  // ── Summary ───────────────────────────────────────────────────────────────
  const loadSummary = useCallback(async (date: string) => {
    if (!mountedRef.current) return;
    const fetchId = ++summaryFetchRef.current;
    setSummaryStatus("loading");
    setSummaryError(null);

    summaryAbortRef.current?.abort();
    const controller = new AbortController();
    summaryAbortRef.current = controller;

    try {
      const result = await getDailyNutritionLogSummary(date, controller.signal);

      if (!mountedRef.current || fetchId !== summaryFetchRef.current) return;

      if (result.success) {
        setSummary(result.data);
        setSummaryStatus("available");
      } else {
        setSummary(null);
        setSummaryStatus("error");
        setSummaryError(result.error.message);
      }
    } catch (err: unknown) {
      if ((err as Error)?.name === "AbortError") return;
      if (!mountedRef.current || fetchId !== summaryFetchRef.current) return;
      setSummary(null);
      setSummaryStatus("error");
      setSummaryError((err as Error)?.message || "Failed to load nutrition summary.");
    }
  }, []);

  // ── Progress ──────────────────────────────────────────────────────────────
  const loadProgress = useCallback(async (date: string) => {
    if (!mountedRef.current) return;
    const fetchId = ++progressFetchRef.current;
    setProgressStatus("loading");
    setProgressError(null);

    progressAbortRef.current?.abort();
    const controller = new AbortController();
    progressAbortRef.current = controller;

    try {
      const referenceDate = getLocalCalendarDate();
      const result = await getDailyNutritionTargetProgress(
        date,
        referenceDate,
        controller.signal
      );

      if (!mountedRef.current || fetchId !== progressFetchRef.current) return;

      if (result.success) {
        setProgress(result.data);
        setProgressStatus("available");
      } else {
        setProgress(null);
        if (result.error.code === "NUTRITION_PROFILE_NOT_FOUND") {
          setProgressStatus("missing_profile");
        } else {
          setProgressStatus("error");
          setProgressError(result.error.message);
        }
      }
    } catch (err: unknown) {
      if ((err as Error)?.name === "AbortError") return;
      if (!mountedRef.current || fetchId !== progressFetchRef.current) return;
      setProgress(null);
      setProgressStatus("error");
      setProgressError((err as Error)?.message || "Failed to load nutrition target progress.");
    }
  }, []);

  // Stable refs so setSelectedDate / reloadAll / createEntry stay stable
  const loadEntriesRef = useRef(loadEntries);
  const loadSummaryRef = useRef(loadSummary);
  const loadProgressRef = useRef(loadProgress);
  useEffect(() => { loadEntriesRef.current = loadEntries; }, [loadEntries]);
  useEffect(() => { loadSummaryRef.current = loadSummary; }, [loadSummary]);
  useEffect(() => { loadProgressRef.current = loadProgress; }, [loadProgress]);

  // Keep latest selected date accessible in stable callbacks
  const selectedDateRef = useRef(selectedDate);
  useEffect(() => { selectedDateRef.current = selectedDate; }, [selectedDate]);

  const deletingEntryIdRef = useRef<string | null>(null);
  useEffect(() => { deletingEntryIdRef.current = deletingEntryId; }, [deletingEntryId]);

  const fetchAll = useCallback((date: string) => {
    loadEntriesRef.current(date);
    loadSummaryRef.current(date);
    loadProgressRef.current(date);
  }, []);

  const setSelectedDate = useCallback(
    (date: string) => {
      setSelectedDateState(date);
      setEntriesStatus("loading");
      setSummaryStatus("loading");
      setProgressStatus("loading");
      setEntries([]);
      setSummary(null);
      setProgress(null);
      setEntriesError(null);
      setSummaryError(null);
      setProgressError(null);
      setCreateStatus("idle");
      setCreateError(null);
      setDeleteStatus("idle");
      setDeletingEntryId(null);
      setDeleteError(null);
      fetchAll(date);
    },
    [fetchAll]
  );

  const reloadAll = useCallback(() => {
    fetchAll(selectedDateRef.current);
  }, [fetchAll]);

  const retryEntries = useCallback(() => {
    loadEntriesRef.current(selectedDateRef.current);
  }, []);

  const retrySummary = useCallback(() => {
    loadSummaryRef.current(selectedDateRef.current);
  }, []);

  const retryProgress = useCallback(() => {
    loadProgressRef.current(selectedDateRef.current);
  }, []);

  const createEntry = useCallback(
    async (payload: NutritionLogEntryCreateRequest): Promise<boolean> => {
      if (!mountedRef.current || creatingRef.current) return false;
      creatingRef.current = true;
      setCreateStatus("submitting");
      setCreateError(null);

      const result = await createNutritionLogEntry(
        selectedDateRef.current,
        payload
      );
      creatingRef.current = false;

      if (!mountedRef.current) return false;

      if (result.success) {
        setCreateStatus("success");
        fetchAll(selectedDateRef.current);
        return true;
      } else {
        setCreateStatus("error");
        setCreateError(result.error.message);
        return false;
      }
    },
    [fetchAll]
  );

  const requestDelete = useCallback((entryId: string) => {
    setDeleteStatus("confirming");
    setDeletingEntryId(entryId);
    setDeleteError(null);
  }, []);

  const confirmDelete = useCallback(async () => {
    const entryId = deletingEntryIdRef.current;
    if (!entryId || !mountedRef.current || deletingRef.current) return;
    deletingRef.current = true;
    setDeleteStatus("deleting");
    setDeleteError(null);

    const result = await deleteNutritionLogEntry(entryId);
    deletingRef.current = false;

    if (!mountedRef.current) return;

    if (result.success) {
      setDeleteStatus("idle");
      setDeletingEntryId(null);
      fetchAll(selectedDateRef.current);
    } else {
      setDeleteStatus("error");
      setDeleteError(result.error.message);
    }
  }, [fetchAll]);

  const cancelDelete = useCallback(() => {
    setDeleteStatus("idle");
    setDeletingEntryId(null);
    setDeleteError(null);
  }, []);

  const clearCreateSuccess = useCallback(() => {
    setCreateStatus("idle");
  }, []);

  const clearDeleteSuccess = useCallback(() => {
    setDeleteStatus("idle");
  }, []);

  return {
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
    reloadAll,
    retryEntries,
    retrySummary,
    retryProgress,
    createEntry,
    requestDelete,
    confirmDelete,
    cancelDelete,
    clearCreateSuccess,
    clearDeleteSuccess,
  };
}
