# NutriMind AI Frontend — Release Notes v2.0.0

## Executive summary

Version 2.0 is a complete, production-approved redesign of the NutriMind AI frontend. The
application moves from the original scaffold to a cohesive **dark forest-glass design system**
spanning all 11 pages. Every data view now ships with consistent loading, empty, and error
states; layouts are fully responsive from mobile to ultra-wide; and components meet baseline
accessibility (keyboard navigation, visible focus, ARIA, semantic HTML, labelled forms,
WCAG-AA contrast).

This release is a **UI/design-system delivery only**. No backend contracts changed; no new
API endpoints were added; demo/placeholder content remains clearly labeled. Final QA: build
green, type-check clean, lint clean, **465/465 tests passing**.

## New UI

- Unified dark forest-glass visual language across public and protected surfaces.
- Glassmorphic sidebar, header, cards, and modals with consistent `glass`/`glass-card`
  treatments and a new `.premium-shadow` elevation token.
- Refined typography hierarchy, spacing scale, and motion vocabulary (`fade-in`,
  `slide-up`, `scale-in`, `pulse-soft`, `shimmer`).
- Mobile bottom navigation (`MobileBottomNav`) for primary destinations on small screens,
  with a slide-over drawer for full navigation.

## New Design System

- CSS custom-property tokens in `app/globals.css` mapped into the Tailwind theme
  (`colors`, `borderRadius`, `boxShadow`, `fontFamily`, `animation`, `keyframes`).
- Opaque translucent tokens (`bg-brand-light`, `bg-error-light`, `bg-surface-low`,
  `border-brand`, etc.) used in place of `/NN` opacity modifiers, because Tailwind colors
  are defined as full `var()` values (opacity modifiers are silently dropped).
- Shared utilities added during polish: `.glass-card`, `.premium-shadow`, `.no-scrollbar`.
- Single icon library (lucide-react), single font (Geist), no duplicate component systems.

## Landing

- Hero with brand mark and primary CTAs, biometric-dashboard preview, optimization-modules
  grid, AI coach demo, pricing section, CTA band, and footer.
- Responsive from mobile to ultra-wide; smooth scroll-to-section anchors.

## Authentication

- Login, Register, and Forgot Password pages with field-level validation, accessible error
  messaging (`role="alert"`), password visibility toggles, and `autoComplete` semantics.
- Open-redirect-safe `?redirect=` handling; demo notice on the forgot-password flow.

## Dashboard

- Greeting card, daily optimization protocol (demo), activity feed (demo), AI insight card,
  nutrition-progress module, weekly chart, stat cards, and quick-action shortcuts.
- Loading skeletons and graceful empty/missing-data states.

## Food Diary

- Meal timeline, macro summary, daily nutrition summary and progress cards, remaining-
  calories card, and AI insight mini.
- Entry create/list/delete flows with loading, empty, error, and retry states sourced from
  backend hooks.

## AI Coach

- Conversation sidebar, message thread (user/assistant bubbles), composer with send states,
  suggested-prompt chips, and an empty-conversation state.
- `no-scrollbar` styling on the suggestion strip; sticky header uses an opaque surface
  (translucent modifier removed during polish).

## Weight Tracker

- Entry form, history list, trend chart (Recharts), goal-progress velocity ring, milestone
  cards, and a floating action button (FAB).
- FAB repositioned (`bottom-24 lg:bottom-6`) so it clears the mobile bottom navigation.
- Loading, empty-history, and error states throughout.

## Tasks

- Create / list / complete / reopen / delete with inline accessible confirmation.
- Priority-grouped display, task statistics, task summary, and empty state.
- Loading, empty, and retryable error states.

## Nutrition Search

- Search input with suggestions, categorized results, food cards, macro cards, and a
  nutrition-facts panel.
- Grid hardened with `minmax(0,1fr)` to prevent overflow; empty-search and favorite states.
- Demo catalog (clearly labeled) behind a frontend adapter — no backend search endpoint yet.

## Settings

- Profile, notification, and appearance sections.
- **Known limitation:** appearance/notification toggles are UI-only and non-functional
  (no persistence). This is pre-existing and out of scope for the redesign.

## Accessibility improvements

- Semantic landmarks (`aside`/`nav`/`main`), `aria-label`/`aria-current` on navigation.
- Form fields associated via `<label>`/`htmlFor`; errors exposed with `role="alert"`.
- Visible focus states on interactive elements; keyboard-dismissible mobile drawer (Escape).
- `error.tsx` boundary, `loading.tsx`, and `not-found.tsx` present.
- Invisible-text bug (undefined `--color-on-primary` → fixed to `text-[var(--color-bg)]`)
  resolved during polish.

## Responsive improvements

- Mobile: bottom nav + drawer; tablet/desktop: persistent sidebar (`lg` breakpoint).
- Grids use `minmax(0,1fr)` and `min-w-0` to prevent horizontal overflow and clipping.
- Sticky headers and FAB cleared of the mobile bottom nav; no layout shift on route change.

## Performance improvements

- Removed 8 dead component files and associated dead-import surface.
- No new runtime dependencies; shared bundle ~102 kB + per-route chunks.
- Build output fully static-prerendered (15 routes).

## Dead code removed

The following unused components (zero importers, no tests) were deleted during Final Polish:

- `components/app-sidebar.tsx`, `components/app-header.tsx` (legacy re-export shims)
- `components/dashboard-feature-card.tsx`, `components/dashboard-nutrition-status.tsx`
- `components/ai-coach/typing-indicator.tsx`
- `components/ui/breadcrumb.tsx`, `components/ui/progress-ring.tsx`,
  `components/ui/page-container.tsx`

(Shim-named tests `app-sidebar.test.tsx` / `app-header.test.tsx` were retained because they
import the real `layout/` components directly and still pass.)

## Testing summary

- **465 tests passing** across **53 test files** (Vitest + Testing Library).
- Covers UI primitives, every page, API services, data hooks, auth context, and layout.
- No focused/skipped tests; no snapshot bloat.

## Build summary

- `next build` succeeds; 15 routes, all prerendered as static content.
- First Load JS: 102 kB shared; route pages 118–278 kB.
- Only residual lint warning: `avatar.tsx` `<img>` (pre-existing, see Known limitations).

## Known limitations

1. **Settings toggles are non-functional** (appearance/notification) — UI placeholders.
2. **Token storage uses `localStorage`** — accessible to same-origin JavaScript (XSS exposure).
   See `SECURITY.md`.
3. **Nutrition Search uses a labeled demo catalog** — no backend search endpoint yet.
4. **AI Coach is a presentational shell** — no streaming/LLM backend wired in v2.0.
5. **`avatar.tsx` uses `<img>`** — LCP/optimization warning; candidate for `next/image`.
6. **Tailwind opacity modifiers** (`bg-brand/10`) do not apply because colors are full
   `var()` values; use opaque `*-light`/`*-subtle` tokens instead.

## Technical debt

- Migrate color tokens to `<alpha-value>` channel form to enable native opacity modifiers.
- Move auth tokens to HttpOnly cookies (requires backend session support).
- Wire real AI streaming and a nutrition-search backend; replace demo adapters.
- Migrate `avatar.tsx` to `next/image`; add `priority`/`sizes` to above-the-fold media.
- Add focus-trap + Escape handling to the body-weight delete confirmation dialog.
- Respect `prefers-reduced-motion` on heavier Framer Motion entrances.
- Minor naming inconsistency: feature components split between `components/<feature>/`
  subdirs and flat `components/<feature>-*` files (distinct, non-duplicate).
