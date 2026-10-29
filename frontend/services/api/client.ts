import type { ApiErrorResponseBody, ApiResponse } from "@/types/api";
import { getAccessToken } from "@/lib/token-storage";

const inflightRequests = new Map<string, Promise<unknown>>();

function getRequestKey(method: string, path: string, body?: unknown): string {
  return `${method}:${path}:${body ? JSON.stringify(body) : ""}`;
}

function dispatchSessionExpired() {
  if (typeof window !== "undefined") {
    window.dispatchEvent(new CustomEvent("nutrimind:session-expired"));
  }
}

function getBaseUrl(): string {
  const url = process.env.NEXT_PUBLIC_API_URL;
  if (!url) {
    throw new Error(
      "NEXT_PUBLIC_API_URL is not defined. " +
        "Set it in .env.local or the environment."
    );
  }
  return url.replace(/\/+$/, "");
}

interface RequestOptions {
  timeout?: number;
  signal?: AbortSignal;
  token?: boolean;
  retries?: number;
  retryable?: boolean;
}

const RETRYABLE_STATUS_CODES = new Set([429, 500, 502, 503, 504]);
const DEFAULT_MAX_RETRIES = 2;
const BASE_RETRY_DELAY_MS = 1000;

function isRetryableError(status: number, method: string, retryable: boolean): boolean {
  if (!retryable) return false;
  if (method !== "GET") return false; // Only retry GET requests by default
  return RETRYABLE_STATUS_CODES.has(status);
}

function isAbortError(error: unknown): boolean {
  if (error instanceof Error && error.name === "AbortError") return true;
  // Also handle DOMException (thrown by fetch when AbortSignal aborts)
  if (typeof DOMException !== "undefined" && error instanceof DOMException && error.name === "AbortError") return true;
  return false;
}

function parseRetryAfter(header: string | null): number | null {
  if (!header) return null;
  const seconds = Number(header);
  if (!Number.isNaN(seconds)) return seconds * 1000;
  const date = Date.parse(header);
  if (!Number.isNaN(date)) return Math.max(0, date - Date.now());
  return null;
}

async function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function parseErrorBody(body: unknown): string {
  if (body && typeof body === "object") {
    const err = (body as Record<string, unknown>).error;
    if (err && typeof err === "object") {
      const msg = (err as Record<string, unknown>).message;
      if (typeof msg === "string") return msg;
    }
    const msg = (body as Record<string, unknown>).message;
    if (typeof msg === "string") return msg;
  }
  return "";
}

function createTimeoutSignal(
  timeoutMs: number,
  parentSignal?: AbortSignal
): { controller: AbortController; timeoutId: ReturnType<typeof setTimeout> } {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  if (parentSignal) {
    parentSignal.addEventListener(
      "abort",
      () => {
        clearTimeout(timeoutId);
        controller.abort(parentSignal.reason);
      },
      { once: true }
    );
  }

  return { controller, timeoutId };
}

async function doFetchWithRetry<T>(
  url: string,
  method: string,
  body: unknown | undefined,
  useToken: boolean,
  controller: AbortController,
  timeoutId: ReturnType<typeof setTimeout>,
  maxRetries: number,
  retryable: boolean,
  parentSignal?: AbortSignal
): Promise<ApiResponse<T>> {
  let attempt = 0;
  let currentController = controller;
  let currentTimeoutId = timeoutId;

  while (true) {
    try {
      const requestHeaders = await buildHeaders(useToken);

      const fetchOptions: RequestInit = {
        method,
        headers: requestHeaders,
        signal: currentController.signal,
        cache: "no-store",
      };

      if (body !== undefined && method !== "GET") {
        fetchOptions.body = JSON.stringify(body);
      }

      const response = await fetch(url, fetchOptions);
      clearTimeout(currentTimeoutId);

      if (!response.ok) {
        if (response.status === 401 && useToken) {
          dispatchSessionExpired();
        }

        let errorMessage = `Request failed with status ${response.status}`;
        let errorBody: unknown;
        try {
          errorBody = await response.json();
          const parsed = parseErrorBody(errorBody);
          if (parsed) errorMessage = parsed;
        } catch {
          /* ignore JSON parse errors */
        }

        const errorResponse: ApiResponse<T> = {
          success: false as const,
          error: {
            code: "HTTP_ERROR",
            message: errorMessage,
            request_id: "",
            details: undefined,
          },
        };

        if (errorBody && typeof errorBody === "object") {
          const eb = errorBody as Record<string, unknown>;
          if (eb.error && typeof eb.error === "object") {
            const e = eb.error as Record<string, unknown>;
            errorResponse.error.code =
              typeof e.code === "string" ? e.code : "HTTP_ERROR";
            errorResponse.error.request_id =
              typeof e.request_id === "string"
                ? e.request_id
                : errorResponse.error.request_id;
            errorResponse.error.details =
              e.detail !== undefined ? e.detail : e.details;
          }
        }

        const shouldRetry =
          attempt < maxRetries && isRetryableError(response.status, method, retryable);

        if (shouldRetry) {
          attempt++;
          const retryAfter = parseRetryAfter(response.headers.get("Retry-After"));
          const delay = retryAfter ?? BASE_RETRY_DELAY_MS * Math.pow(2, attempt - 1);
          await sleep(delay);
          // Create fresh controller and timeout for retry, preserving original parent signal
          const { controller: newController, timeoutId: newTimeoutId } = createTimeoutSignal(
            8000,
            parentSignal
          );
          currentController = newController;
          currentTimeoutId = newTimeoutId;
          continue;
        }

        if (method !== "GET") {
          import("sonner").then(({ toast }) => {
            toast.error(errorResponse.error.message || "An error occurred");
          });
        }

        return errorResponse;
      }

      const text = await response.text();
      let parsed: unknown;
      try {
        parsed = JSON.parse(text);
      } catch {
        return {
          success: false as const,
          error: {
            code: "INVALID_JSON",
            message: "Server returned invalid JSON.",
            request_id: "",
          },
        };
      }

      return parsed as ApiResponse<T>;
    } catch (error) {
      clearTimeout(currentTimeoutId);
      if (isAbortError(error)) {
        if (method !== "GET") {
          import("sonner").then(({ toast }) =>
            toast.error("Request timed out. The server may be unreachable.")
          );
        }
        return {
          success: false as const,
          error: {
            code: "TIMEOUT",
            message: "Request timed out. The server may be unreachable.",
            request_id: "",
          },
        };
      }

      if (error instanceof Error) {
        const shouldRetry =
          attempt < maxRetries && retryable && method === "GET";

        if (shouldRetry) {
          attempt++;
          const delay = BASE_RETRY_DELAY_MS * Math.pow(2, attempt - 1);
          await sleep(delay);
          // Create fresh controller and timeout for retry, preserving original parent signal
          const { controller: newController, timeoutId: newTimeoutId } = createTimeoutSignal(
            8000,
            parentSignal
          );
          currentController = newController;
          currentTimeoutId = newTimeoutId;
          continue;
        }

        if (method !== "GET") {
          import("sonner").then(({ toast }) =>
            toast.error(error.message || "Network Error")
          );
        }
        return {
          success: false as const,
          error: {
            code: "NETWORK_ERROR",
            message: error.message,
            request_id: "",
          },
        };
      }

      return {
        success: false as const,
        error: {
          code: "UNKNOWN_ERROR",
          message: "An unknown error occurred.",
          request_id: "",
        },
      };
    }
  }
}

async function buildHeaders(token?: boolean): Promise<HeadersInit> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (token) {
    const accessToken = await getAccessToken();
    if (accessToken) {
      headers["Authorization"] = `Bearer ${accessToken}`;
    }
  }
  return headers;
}

async function request<T>(
  path: string,
  method: string,
  body?: unknown,
  options: RequestOptions = {}
): Promise<ApiResponse<T>> {
  const baseUrl = getBaseUrl();
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  const url = `${baseUrl}${normalizedPath}`;
  const timeoutMs = options.timeout ?? 8000;
  const useToken = options.token ?? true;
  const maxRetries = options.retries ?? DEFAULT_MAX_RETRIES;
  const retryable = options.retryable ?? true;

  const requestKey = getRequestKey(method, normalizedPath, body);

  // Deduplicate in-flight GET requests
  if (method === "GET") {
    const existing = inflightRequests.get(requestKey);
    if (existing) {
      return existing as Promise<ApiResponse<T>>;
    }
  }

  const { controller, timeoutId } = createTimeoutSignal(timeoutMs, options.signal);

  const promise = doFetchWithRetry<T>(
    url,
    method,
    body,
    useToken,
    controller,
    timeoutId,
    maxRetries,
    retryable,
    options.signal
  ).finally(() => {
    inflightRequests.delete(requestKey);
  });

  if (method === "GET") {
    inflightRequests.set(requestKey, promise);
  }

  return promise;
}

export function apiGet<T>(
  path: string,
  options?: RequestOptions
): Promise<ApiResponse<T>> {
  return request<T>(path, "GET", undefined, { ...options, retryable: true });
}

export function apiPost<T>(
  path: string,
  body?: unknown,
  options?: RequestOptions
): Promise<ApiResponse<T>> {
  return request<T>(path, "POST", body, { ...options, retryable: false });
}

export function apiPatch<T>(
  path: string,
  body?: unknown,
  options?: RequestOptions
): Promise<ApiResponse<T>> {
  return request<T>(path, "PATCH", body, { ...options, retryable: false });
}

export function apiPut<T>(
  path: string,
  body?: unknown,
  options?: RequestOptions
): Promise<ApiResponse<T>> {
  return request<T>(path, "PUT", body, { ...options, retryable: false });
}

export function apiDelete<T>(
  path: string,
  options?: RequestOptions
): Promise<ApiResponse<T>> {
  return request<T>(path, "DELETE", undefined, { ...options, retryable: false });
}