# Security Policy — NutriMind AI Frontend

## Authentication

- Supabase Auth owns browser login, registration, OAuth, refresh, and logout. The browser
  session is persisted by `@supabase/ssr` in cookies. Middleware calls Supabase Auth to
  validate protected page requests; cookie presence alone is never accepted.
- Authenticated API requests obtain the current Supabase session token through the Supabase
  client and send it in `Authorization: Bearer <token>`. Backend authorization remains
  mandatory and does not trust frontend middleware or an auth cookie.
- `ProtectedRoute` gates all `(protected)` routes. Unauthenticated users are redirected to
  `/login` with a safe `?redirect=` parameter (validated to start with `/` and not `//`,
  preventing open redirects).
- Logout uses Supabase `signOut`, clearing the Supabase-managed session and auth context.

## Token handling

- **Storage:** the Supabase SSR client manages chunked session cookies and refresh behavior;
  there is no separate custom localStorage token store or backend-token mirror.
- **Cookie flags:** cookies use `Secure` in production and `SameSite=Lax`. The browser
  Supabase client must read and refresh its session, so these cookies are not `HttpOnly`.
  Same-origin JavaScript can access session material; XSS can still steal tokens.
- **Safeguards:** auth diagnostics do not log user objects or bearer tokens; API tokens are
  sent only in authorization headers and are not placed in URLs.
- **No secrets in the client:** `NEXT_PUBLIC_API_URL` and the Supabase project URL/public
  anon key are browser-safe. Backend signing keys, database URLs, service-role keys, and
  provider API keys must never be exposed to the frontend.

## Known limitations

1. **Supabase session cookie visibility** — `@supabase/ssr` browser refresh requires
   JavaScript access. A server-only HttpOnly session would require a server-side auth and API
   proxy with refresh handling; that broader design is not implemented.
2. **CSRF** — backend APIs authenticate from explicit bearer headers, not ambient cookies.
   Supabase auth endpoints use the Supabase SDK flow.
3. **Settings toggles are non-functional** — they do not persist or change behavior, so they
   cannot introduce a security-affecting state change.
4. **Demo/placeholder content** is frontend-only and clearly labeled; it never reaches the
   backend as real data.

## Recommended future improvements

- Consider a server-side auth/API proxy if HttpOnly-only session cookies become a product
  requirement; preserve refresh rotation and add CSRF defenses as part of that design.
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
- [x] No parallel custom localStorage bearer-token store.
- [x] Middleware validates Supabase sessions instead of trusting a constant cookie.
- [ ] Verify full Supabase and backend session lifecycle in the deployment environment.
- [ ] (Planned) Add CSP / SRI / dependency scanning.
