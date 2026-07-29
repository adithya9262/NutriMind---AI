import { getAccessToken } from "@/lib/token-storage"
import type { FoodRecognitionResponse } from "@/types/nutrition"

export async function analyzeFoodImage(file: File) {
  const formData = new FormData()
  formData.append("file", file)

  const baseUrl =
    process.env.NEXT_PUBLIC_API_URL?.replace(/\/+$/, "") || "http://localhost:8001"
  const url = `${baseUrl}/food-recognition/analyze`

  const token = getAccessToken("supabase") || getAccessToken("backend")

  const response = await fetch(url, {
    method: "POST",
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: formData,
  })

  return response.json() as Promise<FoodRecognitionResponse>
}
