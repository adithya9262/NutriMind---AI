# Deployment Guide — NutriMind AI Frontend

## Production build

```powershell
cd frontend
npm ci                 # reproducible install
npm run build          # next build → .next/
npm run start          # serve the production build (or deploy output to a host)
```

Static export is not used; the app is served as a Node/Next server (or via a compatible
host such as Vercel, Node server, or container).

## Environment variables

Set in the deployment environment (not committed):

| Variable | Required | Example |
|----------|----------|---------|
| `NEXT_PUBLIC_API_URL` | Yes | `https://api.nutrimind.example.com/api/v1` |

Only `NEXT_PUBLIC_`-prefixed variables reach the browser. Backend secrets stay server-side.

## Deployment checklist

- [ ] `NEXT_PUBLIC_API_URL` points to the production backend (HTTPS).
- [ ] `npm ci && npm run build` succeeds in CI.
- [ ] `npm run lint`, `npm run type-check`, `npm test` green in CI.
- [ ] Backend CORS allows the frontend origin.
- [ ] No `.env.local` / secrets committed; `.gitignore` covers `.env*`.
- [ ] Health/connectivity verified against the production backend.
- [ ] TLS terminated in front of the app; secure cookies/headers configured by the host.

## Post-deployment verification

1. **Landing** loads at `/` (public).
2. **Auth** — register/login redirect correctly; unauthenticated visits to
   `/dashboard`, `/tasks`, etc. redirect to `/login?redirect=...`.
3. **Protected routes** render the app shell (sidebar on desktop, bottom nav on mobile).
4. **API connectivity** — a logged-in session can load dashboard/tasks/weight data.
5. **Error boundary** — triggering an app error shows `error.tsx`, not a blank crash.
6. **Responsive** — verify mobile (bottom nav), tablet, desktop (sidebar), ultra-wide
   (max-width container, no overflow).
7. **404** — unknown routes render `not-found.tsx`.

## Rollback strategy

- **Immutable builds:** keep the previous successful build artifact; redeploy it to roll back.
- **Git tag:** redeploy the prior release tag (e.g. `v1.0.0`) if needed.
- **Backend coupling:** frontend v2.0 uses the same frozen backend contracts as v1.0 — no
  coordinated backend rollback is required for a frontend-only rollback.
- **Cache:** purge CDN/edge cache for the app origin after a rollback to avoid stale assets.

## Monitoring recommendations

- **Synthetic checks:** probe `/` and a protected route (post-login) from a monitor.
- **Error tracking:** capture client exceptions (the `error.tsx` boundary logs to console;
  wire to a reporting service if desired).
- **Web vitals:** track LCP/CLS (note the `avatar.tsx` `<img>` LCP warning as a known item).
- **API health:** alert on `NEXT_PUBLIC_API_URL/health` failures.
- **Console errors:** watch for 401 storms (token expiry) and CORS misconfigurations.
