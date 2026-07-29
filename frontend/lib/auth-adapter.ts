// Auth adapter interface for future Supabase migration.
// Currently implemented with the in-house FastAPI backend.
// To migrate to Supabase, create a new adapter implementing this interface
// and swap it in auth-context.tsx.

export interface AuthAdapter {
  register(data: { email: string; password: string }): Promise<{
    success: boolean; data?: { access_token: string; user: import('@/types/auth').PublicUser }; error?: string
  }>

  login(data: { email: string; password: string }): Promise<{
    success: boolean; data?: { access_token: string; user: import('@/types/auth').PublicUser }; error?: string
  }>

  fetchCurrentUser(signal?: AbortSignal): Promise<{
    success: boolean; data?: import('@/types/auth').PublicUser; error?: string
  }>

  logout(): void

  getAccessToken(): string | null

  setSession(token: string): void

  clearSession(): void
}
