"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import { getAIUsage, getAIUsageHistory, type AIUsage, type AIUsageHistory, type UsagePeriod } from "@/services/api/ai-coach";

export interface AIUsageState {
  usage: AIUsage | null;
  usageLoading: boolean;
  historyPeriod: UsagePeriod;
  history: AIUsageHistory | null;
  historyLoading: boolean;
  /** ms until the next midnight UTC reset */
  msUntilReset: number;
}

export interface AIUsageActions {
  refreshUsage: () => Promise<void>;
  loadHistory: (period: UsagePeriod) => Promise<void>;
  /** Call after every sent message so the counter is immediately accurate. */
  optimisticMessageIncrement: () => void;
}

export type AIUsageResult = AIUsageState & AIUsageActions;

function msUntilMidnightUTC(): number {
  const now = new Date();
  const tomorrow = new Date(
    Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate() + 1)
  );
  return Math.max(0, tomorrow.getTime() - now.getTime());
}

export function useAIUsage(): AIUsageResult {
  const [usage, setUsage] = useState<AIUsage | null>(null);
  const [usageLoading, setUsageLoading] = useState(true);
  const [history, setHistory] = useState<AIUsageHistory | null>(null);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyPeriod, setHistoryPeriod] = useState<UsagePeriod>("7d");
  const [msUntilReset, setMsUntilReset] = useState(() => msUntilMidnightUTC());

  const mountedRef = useRef(true);
  const resetTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
      if (resetTimerRef.current) clearTimeout(resetTimerRef.current);
    };
  }, []);

  // Update countdown every second
  useEffect(() => {
    const tick = setInterval(() => {
      if (!mountedRef.current) return;
      setMsUntilReset(msUntilMidnightUTC());
    }, 1000);
    return () => clearInterval(tick);
  }, []);

  const refreshUsage = useCallback(async () => {
    if (!mountedRef.current) return;
    setUsageLoading(true);
    try {
      const res = await getAIUsage();
      if (!mountedRef.current) return;
      if (res.success && res.data) {
        setUsage(res.data);
        // Schedule an auto-refresh right after the reset time
        if (resetTimerRef.current) clearTimeout(resetTimerRef.current);
        const ms = msUntilMidnightUTC() + 2000; // +2s buffer
        resetTimerRef.current = setTimeout(() => {
          if (mountedRef.current) refreshUsage();
        }, ms);
      }
    } finally {
      if (mountedRef.current) setUsageLoading(false);
    }
  }, []);

  const loadHistory = useCallback(async (period: UsagePeriod) => {
    if (!mountedRef.current) return;
    setHistoryPeriod(period);
    setHistoryLoading(true);
    try {
      const res = await getAIUsageHistory(period);
      if (!mountedRef.current) return;
      if (res.success && res.data) {
        setHistory(res.data);
      }
    } finally {
      if (mountedRef.current) setHistoryLoading(false);
    }
  }, []);

  const optimisticMessageIncrement = useCallback(() => {
    setUsage((prev) => {
      if (!prev) return prev;
      return { ...prev, messages_used: prev.messages_used + 1 };
    });
  }, []);

  // Load on mount
  useEffect(() => {
    refreshUsage();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return {
    usage,
    usageLoading,
    historyPeriod,
    history,
    historyLoading,
    msUntilReset,
    refreshUsage,
    loadHistory,
    optimisticMessageIncrement,
  };
}

/** Format ms-until-reset as "Resets in Xh Ym" or "Resets in Xs". */
export function formatResetCountdown(ms: number): string {
  const totalSec = Math.ceil(ms / 1000);
  if (totalSec <= 0) return "Resetting…";
  const h = Math.floor(totalSec / 3600);
  const m = Math.floor((totalSec % 3600) / 60);
  const s = totalSec % 60;
  if (h > 0) return `Resets in ${h}h ${m}m`;
  if (m > 0) return `Resets in ${m}m ${s}s`;
  return `Resets in ${s}s`;
}
