# Security Policy — NutriMind AI Frontend

## Authentication

- Authentication is token-based. On login/register the backend returns an `access_token`,
  which the frontend stores via `lib/token-storage.ts` and injects as
  `Authorization: Bearer <token>` on authenticated requests through the centralized API
  client.
- `ProtectedRoute` gates all `(protected)` routes. Unauthenticated users are redirected to
  `/login` with a safe `?redirect=` parameter (validated to start with `/` and not `//`,
  preventing open redirects).
- Logout clears the token from storage and resets the auth context.

## Token handling

- **Storage:** the access token is persisted in `localStorage` (key `nutrimind_access_token`).
- **Exposure:** `localStorage` is readable by any JavaScript running on the same origin.
  A successful XSS attack could exfiltrate the token. There is **no refresh token** in the
  current design, limiting the blast radius to the access-token lifetime.
- **Safeguards:** tokens are never logged, rendered, placed in URLs, or written to feature
  state. Storage access is wrapped in `try/catch` and guarded by `typeof window` checks.
- **No secrets in the client:** only `NEXT_PUBLIC_API_URL` is browser-safe. Backend
  secrets (JWT signing key, database URL, API keys) must never be exposed to the frontend.

## Known limitations

1. **`localStorage` token storage** — vulnerable to XSS token theft. The recommended fix is
   HttpOnly, Secure, SameSite cookies issued by the backend (requires backend session
   support; out of scope for v2.0).
2. **No CSRF protection on cookie auth** — only relevant if/when migrated to cookie auth;
   Bearer-token-in-header currently avoids classic CSRF but inherits the XSS exposure above.
3. **Settings toggles are non-functional** — they do not persist or change behavior, so they
   cannot introduce a security-affecting state change.
4. **Demo/placeholder content** is frontend-only and clearly labeled; it never reaches the
   backend as real data.

## Recommended future improvements

- Migrate auth tokens to HttpOnly + Secure + SameSite cookies (backend change).
- Add Subresource Integrity / strict CSP to reduce XSS blast radius.
- Add client-side input sanitization review and dependency vulnerability scanning in CI.
- Consider short-lived access tokens with refresh rotation.
- Wire `error.tsx` logging to a secure, redacted error reporter.

## Security checklist

- [x] No hardcoded secrets or API keys in source.
- [x] Protected routes redirect unauthenticated users with a safe redirect param.
- [x] Open-redirect prevention on `?redirect=`.
- [x] Password fields use `type="password"` and correct `autoComplete`.
- [x] Tokens never logged, rendered, or placed in URLs.
- [x] `localStorage` access guarded and exception-safe.
- [x] Build/lint/type-check green; no debug code committed.
- [ ] (Planned) Move tokens to HttpOnly cookies.
- [ ] (Planned) Add CSP / SRI / dependency scanning.
