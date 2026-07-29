"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { checkHealth } from "@/features/system-status/api";
import type { ConnectionStatus } from "@/features/system-status/types";

interface UseHealthCheckResult {
  status: ConnectionStatus;
  message: string;
  retry: () => void;
}

export function useHealthCheck(): UseHealthCheckResult {
  const [status, setStatus] = useState<ConnectionStatus>("checking");
  const [message, setMessage] = useState(
    "Checking backend connection\u2026"
  );
  const currentControllerRef = useRef<AbortController | null>(null);

  const performCheck = useCallback(async (signal: AbortSignal) => {
    if (signal.aborted) return;

    setStatus("checking");
    setMessage("Checking backend connection\u2026");

    const result = await checkHealth(signal);

    if (signal.aborted) return;

    setStatus(result.status);
    setMessage(
      result.status === "connected"
        ? "Backend connected"
        : result.message
    );
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    currentControllerRef.current = controller;
    performCheck(controller.signal);
    return () => {
      controller.abort();
      currentControllerRef.current = null;
    };
  }, [performCheck]);

  const retry = useCallback(() => {
    currentControllerRef.current?.abort();
    const controller = new AbortController();
    currentControllerRef.current = controller;
    performCheck(controller.signal);
  }, [performCheck]);

  return { status, message, retry };
}
