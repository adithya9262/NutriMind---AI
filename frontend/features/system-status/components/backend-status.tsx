"use client";

import { useHealthCheck } from "@/hooks/use-health-check";
import { StatusIndicator } from "@/components/ui/status-indicator";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

export function BackendStatus() {
  const { status, message, retry } = useHealthCheck();

  const indicatorStatus = status === "connected" ? "healthy" : status;

  return (
    <Card aria-live="polite" aria-busy={status === "checking"}>
      <div className="flex items-center gap-3">
        <StatusIndicator status={indicatorStatus as "healthy" | "unavailable" | "checking"} />
        <div className="flex-1 min-w-0">
          <p className="font-medium text-sm">{message}</p>
          <p className="text-xs mt-0.5 text-[var(--color-text-muted)]">
            {status === "checking" &&
              "Making a request to the health endpoint."}
            {status === "connected" &&
              "API is responding correctly."}
            {status === "unavailable" &&
              "The backend server may be offline or starting up."}
          </p>
        </div>
        {status === "unavailable" && (
          <Button onClick={retry} variant="secondary" size="sm">
            Retry connection
          </Button>
        )}
      </div>
    </Card>
  );
}
