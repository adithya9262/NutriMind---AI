# NutriMind AI — Frontend

> **Version 2.0.0** — Complete UI redesign with the dark "forest-glass" design system.
> Production-approved and ready for deployment.

Intelligent nutrition and wellness companion. This is the Next.js TypeScript frontend for
the NutriMind AI platform, featuring a redesigned, production-ready user experience across
11 pages: Landing, Authentication, Dashboard, Food Diary, AI Coach, Weight Tracker, Tasks,
Nutrition Search, and Settings.

## Project overview

NutriMind AI helps users track nutrition, body weight, and daily optimization tasks with an
AI coaching assistant. The frontend consumes a FastAPI backend (separate repository module)
over a typed, centralized API client. Version 2.0 delivers a cohesive dark forest-glass
visual language, fully responsive layouts (mobile drawer → desktop sidebar), accessible
components, and comprehensive loading / empty / error states on every data view.

## Features

| Area | Highlights |
|------|-----------|
| **Landing** | Hero, biometric dashboard preview, optimization modules, coach demo, pricing, CTA band, footer |
| **Authentication** | Login, Register, Forgot Password with field validation and accessible error messaging |
| **Dashboard** | Greeting, daily protocol, activity feed, AI insight card, nutrition progress, weekly chart, quick actions |
| **Food Diary** | Meal timeline, macro summary, daily nutrition summary/progress, remaining-calories card, AI insight mini, entry form |
| **AI Coach** | Conversation list, message thread, composer, suggested prompts, empty state |
| **Weight Tracker** | Entry form, history list, trend chart, goal-progress ring, milestone cards, FAB |
| **Tasks** | Create / list / complete / reopen / delete with inline confirmation, priority grouping, statistics |
| **Nutrition Search** | Search input, suggestions, categorized results, food cards, macro cards, nutrition facts |
| **Settings** | Profile, notification, and appearance sections (appearance toggles are UI-only placeholders) |

## Tech stack

- **Framework:** Next.js 15 (App Router), React 19
- **Language:** TypeScript (strict)
- **Styling:** Tailwind CSS v3 with CSS custom-property design tokens
- **Animation:** Framer Motion
- **Icons:** lucide-react
- **Charts:** Recharts
- **Utilities:** class-variance-authority, clsx, tailwind-merge
- **Fonts:** Geist
- **Testing:** Vitest + @testing-library/react + jsdom

## Screenshots

> Screenshots to be added. Recommended captures:
>
> - `docs/screenshots/landing.png` — Landing hero
> - `docs/screenshots/dashboard.png` — Dashboard overview
> - `docs/screenshots/food-diary.png` — Food Diary timeline
> - `docs/screenshots/ai-coach.png` — AI Coach conversation
> - `docs/screenshots/weight-tracker.png` — Weight Tracker charts
> - `docs/screenshots/tasks.png` — Tasks board
> - `docs/screenshots/nutrition-search.png` — Nutrition Search results
> - `docs/screenshots/settings.png` — Settings page
> - `docs/screenshots/mobile-nav.png` — Mobile bottom navigation

## Folder structure

```
frontend/
├── app/
│   ├── (auth)/                # Public: login, register, forgot-password
│   ├── (protected)/           # Authenticated app (shared shell layout)
│   │   ├── dashboard/
│   │   ├── nutrition/
│   │   │   ├── logs/
│   │   │   └── search/
│   │   ├── ai-coach/
│   │   ├── body-weight/
│   │   ├── tasks/
│   │   └── settings/
│   ├── error.tsx              # Global error boundary
│   ├── loading.tsx            # Global loading
│   ├── not-found.tsx          # 404
│   ├── layout.tsx             # Root layout (AuthProvider, fonts)
│   └── globals.css            # Design tokens + utility classes
├── components/
│   ├── layout/                # Sidebar, header, mobile nav, bottom nav
│   ├── ui/                    # Reusable primitives (Button, Card, Input, ...)
│   ├── landing/               # Landing sections
│   ├── dashboard/ food-diary/ ai-coach/ weight/ tasks/ nutrition-search/
│   └── auth/                  # OAuth buttons, divider
├── contexts/                  # auth-context
├── hooks/                     # Feature data hooks
├── services/api/              # Typed API client + per-feature services
├── lib/                       # token-storage, utils
├── types/                     # Shared TypeScript types
└── __tests__/                 # Vitest suite
```

## Installation

```powershell
cd frontend
npm install
```

Requirements: Node.js 18.18+ and npm 10+.

## Environment variables

Copy the example file and adjust if needed:

```powershell
copy .env.example .env.local
```

| Variable | Required | Description |
|----------|----------|-------------|
| `NEXT_PUBLIC_API_URL` | Yes | Base URL of the backend API (default `http://localhost:8000/api/v1`) |

> Only `NEXT_PUBLIC_`-prefixed variables are safe for the browser. Backend secrets must
> never be exposed here.

## Running locally

```powershell
# From the project root, start PostgreSQL + backend, then:
cd frontend
npm run dev
```

The app is available at http://localhost:3000 and expects the backend at
`http://localhost:8000/api/v1` (see `NEXT_PUBLIC_API_URL`).

## Running tests

```powershell
npm test            # single run (Vitest)
npm run test:watch  # watch mode
npm run test:ui     # Vitest UI
```

## Build commands

| Command | Description |
|---------|-------------|
| `npm run dev` | Start development server |
| `npm run build` | Production build |
| `npm run start` | Start production server |
| `npm run lint` | Run ESLint |
| `npm run type-check` | Run TypeScript type checking (`tsc --noEmit`) |

## Deployment

1. Set `NEXT_PUBLIC_API_URL` to the production backend URL.
2. `npm run build` then `npm run start` (or deploy the build output to a static/Node host).
3. Verify the health/connectivity and protected-route redirects post-deploy (see `DEPLOYMENT.md`).

## Architecture overview

- **Route groups:** `(auth)` (public) and `(protected)` (authenticated shell) under the App Router.
- **Design system:** CSS custom properties in `globals.css` mapped into Tailwind theme tokens;
  opaque `*-light` / `*-subtle` tokens for translucent layers (Tailwind colors are full
  `var()` values, so `/NN` opacity modifiers are intentionally not used).
- **State:** React Context (`AuthProvider`) + feature-level data hooks.
- **API:** Single centralized client (`services/api/client.ts`) with Bearer injection and
  typed success/error envelopes.
- **Auth:** Token persisted in `localStorage` (see Security notes); `ProtectedRoute` gates
  `(protected)` routes with login redirect preserving `?redirect=`.

See `ARCHITECTURE.md` for the full breakdown.

## Design system overview

- **Palette:** Deep forest background (`#081610`), layered glass surfaces, brand green
  (`#62df7d`) accent, semantic success/warning/error/info.
- **Surfaces:** `bg-surface`, `bg-surface-low/high/highest`, `glass`, `.glass-card`.
- **Typography:** Geist sans; primary/secondary/muted text hierarchy.
- **Radius:** sm → 2xl scale. **Shadow:** sm → xl + `glass` + `.premium-shadow`.
- **Motion:** `fade-in`, `slide-up`, `scale-in`, `pulse-soft`, `shimmer` (Framer Motion on
  key entrances).

## Future roadmap

See `RELEASE_NOTES_v2.0.md` → Known limitations & `docs/FUTURE_FEATURES.md` (repo root) for
aspirational features (real AI streaming, functional settings toggles, nutrition-search
backend, image optimization, HttpOnly cookie auth).

## License

Proprietary — see repository owner. Not licensed for redistribution.
