"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import {
  getNutritionProfile,
  createNutritionProfile as createNutritionProfileApi,
  updateNutritionProfile as updateNutritionProfileApi,
  getNutritionCalculations,
  getPersonalizedNutritionSummary,
} from "@/services/api/nutrition-profile";
import type {
  NutritionProfilePublic,
  NutritionProfileCreateRequest,
  NutritionProfileUpdateRequest,
  NutritionMetricsData,
  NutritionTargetsData,
  NutritionSummaryData,
  NutritionProfileStatus,
  CalculationsStatus,
  SummaryStatus,
} from "@/types/nutrition";

function getTodayString(): string {
  const d = new Date();
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

export interface NutritionProfileState {
  profileStatus: NutritionProfileStatus;
  profile: NutritionProfilePublic | null;
  profileError: string | null;
  calculationsStatus: CalculationsStatus;
  calculations: { metrics: NutritionMetricsData; targets: NutritionTargetsData } | null;
  calculationsError: string | null;
  summaryStatus: SummaryStatus;
  summary: NutritionSummaryData | null;
  summaryError: string | null;
}

export interface NutritionProfileActions {
  loadProfile: () => Promise<void>;
  createProfile: (payload: NutritionProfileCreateRequest) => Promise<boolean>;
  updateProfile: (payload: NutritionProfileUpdateRequest) => Promise<boolean>;
  retryCalculations: () => Promise<void>;
  retrySummary: () => Promise<void>;
  clearProfileError: () => void;
}

export type NutritionProfileResult = NutritionProfileState & NutritionProfileActions;

export function useNutritionProfile(): NutritionProfileResult {
  const [profileStatus, setProfileStatus] = useState<NutritionProfileStatus>("loading");
  const [profile, setProfile] = useState<NutritionProfilePublic | null>(null);
  const [profileError, setProfileError] = useState<string | null>(null);
  const [calculationsStatus, setCalculationsStatus] = useState<CalculationsStatus>("idle");
  const [calculations, setCalculations] = useState<{ metrics: NutritionMetricsData; targets: NutritionTargetsData } | null>(null);
  const [calculationsError, setCalculationsError] = useState<string | null>(null);
  const [summaryStatus, setSummaryStatus] = useState<SummaryStatus>("idle");
  const [summary, setSummary] = useState<NutritionSummaryData | null>(null);
  const [summaryError, setSummaryError] = useState<string | null>(null);

  const mountedRef = useRef(true);
  // Each fetch type gets its own independent sequence counter so they
  // don't clobber each other when running concurrently.
  const profileFetchRef = useRef(0);
  const calcFetchRef = useRef(0);
  const summaryFetchRef = useRef(0);

  const profileAbortRef = useRef<AbortController | null>(null);
  const calcAbortRef = useRef<AbortController | null>(null);
  const summaryAbortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
      profileAbortRef.current?.abort();
      calcAbortRef.current?.abort();
      summaryAbortRef.current?.abort();
    };
  }, []);

  // ── Calculations ──────────────────────────────────────────────────────────
  const loadCalculations = useCallback(async () => {
    if (!mountedRef.current) return;
    const fetchId = ++calcFetchRef.current;
    setCalculationsStatus("loading");
    setCalculationsError(null);

    calcAbortRef.current?.abort();
    const controller = new AbortController();
    calcAbortRef.current = controller;

    const today = getTodayString();
    const result = await getNutritionCalculations(today, controller.signal);

    if (!mountedRef.current || fetchId !== calcFetchRef.current) return;

    if (result.success) {
      setCalculations(result.data);
      setCalculationsStatus("available");
    } else {
      setCalculations(null);
      setCalculationsStatus("error");
      setCalculationsError(result.error.message);
    }
  }, []);

  // ── Summary ───────────────────────────────────────────────────────────────
  const loadSummary = useCallback(async () => {
    if (!mountedRef.current) return;
    const fetchId = ++summaryFetchRef.current;
    setSummaryStatus("loading");
    setSummaryError(null);

    summaryAbortRef.current?.abort();
    const controller = new AbortController();
    summaryAbortRef.current = controller;

    const today = getTodayString();
    const result = await getPersonalizedNutritionSummary(today, controller.signal);

    if (!mountedRef.current || fetchId !== summaryFetchRef.current) return;

    if (result.success) {
      setSummary(result.data);
      setSummaryStatus("available");
    } else {
      setSummary(null);
      setSummaryStatus("error");
      setSummaryError(result.error.message);
    }
  }, []);

  // ── Profile ───────────────────────────────────────────────────────────────
  // Stable ref so settings page useEffect doesn't re-fire when
  // loadCalculations / loadSummary identities change.
  const loadCalculationsRef = useRef(loadCalculations);
  const loadSummaryRef = useRef(loadSummary);
  useEffect(() => { loadCalculationsRef.current = loadCalculations; }, [loadCalculations]);
  useEffect(() => { loadSummaryRef.current = loadSummary; }, [loadSummary]);

  const loadProfile = useCallback(async (retried = false) => {
    if (!mountedRef.current) return;
    const fetchId = ++profileFetchRef.current;
    setProfileStatus("loading");
    setProfileError(null);

    profileAbortRef.current?.abort();
    const controller = new AbortController();
    profileAbortRef.current = controller;

    const result = await getNutritionProfile(controller.signal);

    if (!mountedRef.current || fetchId !== profileFetchRef.current) return;

    if (result.success) {
      setProfile(result.data.profile);
      setProfileStatus("available");
      // Fire sub-fetches via refs so loadProfile's identity stays stable
      loadCalculationsRef.current();
      loadSummaryRef.current();
    } else {
      if (result.error.code === "NUTRITION_PROFILE_NOT_FOUND") {
        setProfile(null);
        setProfileStatus("missing");
      } else if (!retried) {
        // One automatic retry for transient failures
        setTimeout(() => loadProfile(true), 500);
      } else {
        setProfile(null);
        setProfileStatus("read_error");
        setProfileError(result.error.message);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // intentionally empty — uses refs for sub-fetches

  // Re-fetch profile from backend after update to guarantee sync
  const reloadProfileFromBackend = useCallback(async (): Promise<boolean> => {
    if (!mountedRef.current) return false;
    const fetchId = ++profileFetchRef.current;
    profileAbortRef.current?.abort();
    const controller = new AbortController();
    profileAbortRef.current = controller;
    const result = await getNutritionProfile(controller.signal);
    if (!mountedRef.current || fetchId !== profileFetchRef.current) return false;
    if (result.success) {
      setProfile(result.data.profile);
      setProfileStatus("available");
      loadCalculationsRef.current();
      loadSummaryRef.current();
      return true;
    }
    return false;
  }, []);

  // ── Create ────────────────────────────────────────────────────────────────
  const createProfileAction = useCallback(
    async (payload: NutritionProfileCreateRequest): Promise<boolean> => {
      if (!mountedRef.current) return false;
      setProfileStatus("creating");
      setProfileError(null);

      const result = await createNutritionProfileApi(payload);

      if (!mountedRef.current) return false;

      if (result.success) {
        // Re-fetch from backend to guarantee sync
        return await reloadProfileFromBackend();
      } else {
        setProfileStatus("create_error");
        setProfileError(result.error.message);
        return false;
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    []
  );

  // ── Update ────────────────────────────────────────────────────────────────
  const updateProfileAction = useCallback(
    async (payload: NutritionProfileUpdateRequest): Promise<boolean> => {
      if (!mountedRef.current) return false;
      setProfileStatus("updating");
      setProfileError(null);

      const result = await updateNutritionProfileApi(payload);

      if (!mountedRef.current) return false;

      if (result.success) {
        // Re-fetch from backend to guarantee sync
        return await reloadProfileFromBackend();
      } else {
        setProfileStatus("update_error");
        setProfileError(result.error.message);
        return false;
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    []
  );

  const retryCalculations = useCallback(async () => {
    await loadCalculationsRef.current();
  }, []);

  const retrySummary = useCallback(async () => {
    await loadSummaryRef.current();
  }, []);

  const clearProfileError = useCallback(() => {
    setProfileError(null);
  }, []);

  return {
    profileStatus,
    profile,
    profileError,
    calculationsStatus,
    calculations,
    calculationsError,
    summaryStatus,
    summary,
    summaryError,
    loadProfile,
    createProfile: createProfileAction,
    updateProfile: updateProfileAction,
    retryCalculations,
    retrySummary,
    clearProfileError,
  };
}
