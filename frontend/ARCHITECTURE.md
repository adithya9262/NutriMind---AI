# NutriMind AI Frontend — Architecture

## Frontend architecture

The frontend is a **Next.js 15 App Router** single-page application (React 19, TypeScript
strict). It is a presentation/consumption layer over a separate FastAPI backend and holds no
domain calculation logic — all nutrition, weight, and task math is performed server-side.

Key principles:

- **One API client.** All network access goes through `services/api/client.ts`.
- **One auth model.** `AuthProvider` context + `ProtectedRoute` guard.
- **One design system.** CSS custom properties mapped into Tailwind tokens.
- **Feature isolation.** Each feature owns its components, hook, and API service.
- **Placeholder strategy.** Demo content is centralized and labeled; never presented as real.

## Routing

App Router with route groups:

```
app/
├── (auth)/            # Public, unauthenticated
│   ├── login/
│   ├── register/
│   └── forgot-password/
├── (protected)/       # Wrapped by ProtectedRoute + shared app shell
│   ├── dashboard/
│   ├── nutrition/
│   │   ├── page.tsx        # /nutrition (profile + calculations + summary)
│   │   ├── logs/           # /nutrition/logs (Food Diary)
│   │   └── search/         # /nutrition/search (Nutrition Search)
│   ├── ai-coach/
│   ├── body-weight/
│   ├── tasks/
│   └── settings/
├── layout.tsx         # Root: fonts + AuthProvider
├── error.tsx          # Error boundary
├── loading.tsx        # Route-level loading
└── not-found.tsx      # 404
```

Navigation targets are centralized in `components/layout/sidebar.tsx` (desktop) and
`components/layout/mobile-bottom-nav.tsx` (mobile). All `href`s resolve to existing routes.

## Component hierarchy

```
RootLayout (fonts, AuthProvider)
└── (auth) | (protected)
    ├── (auth) pages ──────────────▶ auth components (oauth-buttons, divider)
    └── (protected) ProtectedLayout
        ├── Sidebar (lg+)
        ├── MobileNav (drawer)
        ├── Header
        ├── main
        │   └── Page
        │       ├── ui/ primitives (Button, Card, Input, ...)
        │       └── feature/ components (dashboard/*, food-diary/*, ...)
        └── MobileBottomNav (mobile)
```

Reusable primitives live in `components/ui/`; feature components live in per-feature folders
(`dashboard/`, `food-diary/`, `ai-coach/`, `weight/`, `tasks/`, `nutrition-search/`,
`landing/`, `auth/`, `layout/`).

## Design system

- **Tokens** are CSS custom properties in `app/globals.css` (`:root`):
  background, surface (low/high/highest), brand (default/hover/light/muted/subtle/primary/
  dim), accent, success/warning/error/info (+ `light` variants), text (primary/secondary/
  muted), border (+ light), radius scale, shadow scale.
- **Tailwind mapping** in `tailwind.config.ts` references those variables.
- **Translucency note:** colors are full `var()` values, so `bg-brand/10` style opacity
  modifiers do not apply. Use opaque tokens (`bg-brand-light`, `border-brand`,
  `bg-surface-low`).
- **Utilities:** `.glass`, `.glass-card`, `.gradient-brand`, `.glow`, `.premium-shadow`,
  `.scrollbar-thin`, `.no-scrollbar`, `.animate-fade-in` (and slide-up/scale-in/pulse-soft/
  shimmer).

## Authentication flow

1. `AuthProvider` (mounted in root layout) reads the token via `lib/token-storage.ts`
   (`localStorage`) and, if present, calls `fetchCurrentUser`.
2. `ProtectedRoute` renders a loading spinner while `state === "loading"`, `null` while
   redirecting, and children once `authenticated`. Unauthenticated users are pushed to
   `/login?redirect=<path>` (redirect validated to start with `/` and not `//`).
3. Login/Register call `services/api/auth.ts`, store the token + user, and redirect.
4. Logout clears the token and context state.
5. The API client injects `Authorization: Bearer <token>` on authenticated requests.

## API layer

`services/api/client.ts` exposes typed `apiGet/apiPost/apiPut/apiDelete` helpers:

- Reads `NEXT_PUBLIC_API_URL`.
- 8-second `AbortController` timeout.
- Injects the Bearer token from `getAccessToken()`.
- Parses the backend success/error envelope (`{ success, message, data, error }`).
- Handles network errors and invalid JSON safely; 401 surfaces for future auth-error dispatch.

Per-feature services wrap the client: `auth.ts`, `body-weight.ts`, `nutrition-logs.ts`,
`nutrition-profile.ts`, `nutrition-search.ts`, `tasks.ts`.

## State management

- **Global:** `AuthProvider` context (`state`, `user`, `login`, `logout`).
- **Feature:** custom hooks (`hooks/use-*.ts`) own loading/empty/error/retry state and
  stale-request protection (fetch-counter / AbortController refs). No global store library.
- **Persistence:** only the auth token is persisted (localStorage). No feature data is
  stored client-side.

## Folder organization

```
app/            Routes (route groups, error/loading/not-found, globals.css)
components/     UI primitives + feature + layout components
contexts/       React context providers
hooks/          Feature data hooks
services/api/   API client + per-feature services
lib/            token-storage, utils (cn)
types/          Shared TypeScript types
__tests__/      Vitest suite (mirrors source structure)
```

## Reusable components

`components/ui/`: Button, Input, Textarea, Select, Label, Card, Badge, Alert, Spinner,
Skeleton, EmptyState, ErrorState, PageHeader, SectionHeader, FormField, StatusIndicator.

Cross-feature patterns: `PageHeader` (one `h1` per page), `FormField` (label + error via
`role="alert"`), `EmptyState`/`ErrorState`/`Skeleton` for consistent states.

## Placeholder strategy

Demo/seed content is centralized in each feature's `placeholders.ts`
(e.g. `components/tasks/placeholders.ts`, `components/nutrition-search/placeholders.ts`,
`components/weight/placeholders.ts`, `components/food-diary/placeholders.ts`,
`components/ai-coach/placeholders.ts`) and clearly labeled (e.g. `TASKS_DEMO_LABEL`,
`NUTRITION_SEARCH_DEMO_LABEL`). Dashboard demo data lives in module-scoped constants. No
demo value is presented as real backend data.

## Testing strategy

- **Runner:** Vitest + jsdom + @testing-library/react + jest-dom + user-event.
- **Structure:** `__tests__/` mirrors `app/` and `components/`; unit tests for UI primitives,
  API services, hooks, and context; integration tests for pages and forms.
- **Coverage:** 465 tests / 53 files. Loading, empty, and error branches are exercised.
- **Invariants:** audit tests assert no duplicate routes/components, correct auth gating,
  and backend-contract fidelity.
- **Commands:** `npm test` (run), `npm run test:watch`, `npm run test:ui`.
