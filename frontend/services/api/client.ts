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
}

function buildHeaders(token?: boolean): HeadersInit {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (token) {
    const accessToken = getAccessToken("backend") || getAccessToken("supabase");
    if (accessToken) {
      headers["Authorization"] = `Bearer ${accessToken}`;
    }
  }
  return headers;
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

async function doFetch<T>(
  url: string,
  method: string,
  body: unknown | undefined,
  useToken: boolean,
  controller: AbortController,
  timeoutId: ReturnType<typeof setTimeout>
): Promise<ApiResponse<T>> {
  try {
    const requestHeaders = buildHeaders(useToken);
    
    const fetchOptions: RequestInit = {
      method,
      headers: requestHeaders,
      signal: controller.signal,
      cache: "no-store",
    };

    if (body !== undefined && method !== "GET") {
      fetchOptions.body = JSON.stringify(body);
    }

    const response = await fetch(url, fetchOptions);
    clearTimeout(timeoutId);

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
    clearTimeout(timeoutId);
    if (error instanceof Error) {
      if (error.name === "AbortError") {
        if (method !== "GET") {
          import("sonner").then(({ toast }) => toast.error("Request timed out. The server may be unreachable."));
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
      if (method !== "GET") {
        import("sonner").then(({ toast }) => toast.error(error.message || "Network Error"));
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

  const { controller, timeoutId } = createTimeoutSignal(timeoutMs, options.signal);
  return doFetch<T>(url, method, body, useToken, controller, timeoutId);
}

export function apiGet<T>(
  path: string,
  options?: RequestOptions
): Promise<ApiResponse<T>> {
  return request<T>(path, "GET", undefined, options);
}

export function apiPost<T>(
  path: string,
  body?: unknown,
  options?: RequestOptions
): Promise<ApiResponse<T>> {
  return request<T>(path, "POST", body, options);
}

export function apiPatch<T>(
  path: string,
  body?: unknown,
  options?: RequestOptions
): Promise<ApiResponse<T>> {
  return request<T>(path, "PATCH", body, options);
}

export function apiPut<T>(
  path: string,
  body?: unknown,
  options?: RequestOptions
): Promise<ApiResponse<T>> {
  return request<T>(path, "PUT", body, options);
}

export function apiDelete<T>(
  path: string,
  options?: RequestOptions
): Promise<ApiResponse<T>> {
  return request<T>(path, "DELETE", undefined, options);
}
