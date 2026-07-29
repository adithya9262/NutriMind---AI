import { apiGet } from "./client";
import type { SearchResult } from "@/types/search";

export async function globalSearch(q: string) {
  return apiGet<SearchResult>(`/search?q=${encodeURIComponent(q)}`);
}
