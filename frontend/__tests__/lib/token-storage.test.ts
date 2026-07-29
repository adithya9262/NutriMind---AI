import { describe, it, expect, vi, beforeEach } from "vitest";

const mockStorage: Record<string, string> = {};
const mockGetItem = vi.fn((key: string) => mockStorage[key] ?? null);
const mockSetItem = vi.fn((key: string, value: string) => { mockStorage[key] = value; });
const mockRemoveItem = vi.fn((key: string) => { delete mockStorage[key]; });

Object.defineProperty(globalThis, "localStorage", {
  value: {
    getItem: mockGetItem,
    setItem: mockSetItem,
    removeItem: mockRemoveItem,
  },
  writable: true,
  configurable: true,
});

describe("token-storage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    Object.keys(mockStorage).forEach((k) => delete mockStorage[k]);
  });

  it("stores and retrieves supabase token", async () => {
    const { setAccessToken, getAccessToken } = await import("@/lib/token-storage");
    setAccessToken("test-token", "supabase");
    expect(getAccessToken("supabase")).toBe("test-token");
  });

  it("stores and retrieves backend token", async () => {
    const { setAccessToken, getAccessToken } = await import("@/lib/token-storage");
    setAccessToken("test-token", "backend");
    expect(getAccessToken("backend")).toBe("test-token");
  });

  it("removes token", async () => {
    const { setAccessToken, getAccessToken, removeAccessToken } = await import("@/lib/token-storage");
    setAccessToken("test-token", "supabase");
    removeAccessToken("supabase");
    expect(getAccessToken("supabase")).toBeNull();
  });

  it("treats token types independently", async () => {
    const { setAccessToken, getAccessToken } = await import("@/lib/token-storage");
    setAccessToken("supa-token", "supabase");
    setAccessToken("backend-token", "backend");
    expect(getAccessToken("supabase")).toBe("supa-token");
    expect(getAccessToken("backend")).toBe("backend-token");
  });

  it("clearAllTokens removes both", async () => {
    const { setAccessToken, getAccessToken, clearAllTokens } = await import("@/lib/token-storage");
    setAccessToken("supa-token", "supabase");
    setAccessToken("backend-token", "backend");
    clearAllTokens();
    expect(getAccessToken("supabase")).toBeNull();
    expect(getAccessToken("backend")).toBeNull();
  });
});
