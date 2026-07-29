import { apiDelete } from "./client";
import { getAccessToken } from "@/lib/token-storage";

export async function deleteAccount() {
  return apiDelete<Record<string, never>>("/settings/account");
}

export async function exportData(format: "csv" | "xlsx" | "json" | "pdf" | "txt" = "csv") {
  const baseUrl =
    process.env.NEXT_PUBLIC_API_URL?.replace(/\/+$/, "") || "http://localhost:8001";

  const token = getAccessToken("supabase") || getAccessToken("backend");

  const response = await fetch(`${baseUrl}/settings/export?format=${format}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });

  if (!response.ok) throw new Error("Export failed");

  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const disposition = response.headers.get("Content-Disposition") || "";
  const match = disposition.match(/filename="?([^";\n]+)"?/);
  const filename = match ? match[1] : `nutrimind_export_${new Date().toISOString().split("T")[0]}.${format}`;
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  window.URL.revokeObjectURL(url);
}
