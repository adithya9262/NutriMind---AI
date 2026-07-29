export interface RegisterRequest {
  email: string;
  password: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface PublicUser {
  id: string;
  email: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  updated_at: string;
}

export interface AccessTokenData {
  user: PublicUser;
  access_token: string;
  token_type: "bearer";
  expires_in: number;
}

export interface AuthSuccessResponse {
  success: true;
  message: string;
  data: AccessTokenData;
}

export interface AuthMeResponse {
  success: true;
  message: string;
  data: PublicUser;
}

export interface ApiErrorDetail {
  code: string;
  message: string;
  request_id: string;
  details?: unknown;
}

export interface ApiErrorResponse {
  success: false;
  error: ApiErrorDetail;
}

export type AuthState = "loading" | "authenticated" | "unauthenticated";
