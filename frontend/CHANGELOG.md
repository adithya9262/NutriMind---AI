# Changelog

All notable changes to the NutriMind AI frontend are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to Semantic Versioning.

## [2.0.0] - 2026-07-19

### Added

- Complete dark "forest-glass" design system (CSS custom-property tokens + Tailwind theme).
- New utility classes: `.glass-card`, `.premium-shadow`, `.no-scrollbar`.
- Responsive mobile bottom navigation (`MobileBottomNav`) and slide-over drawer.
- Landing page sections: hero, biometric dashboard, optimization modules, coach demo,
  pricing, CTA band, footer.
- AI Coach page (conversation list, message thread, composer, suggestions, empty state).
- Nutrition Search page (input, suggestions, categorized results, food/macro cards,
  nutrition facts) with a clearly-labeled demo catalog.
- Weight Tracker FAB and milestone cards.
- Consistent loading / empty / error states across all data views.

### Changed

- Redesigned every page (Landing, Login, Register, Forgot Password, Dashboard, Food Diary,
  AI Coach, Weight Tracker, Tasks, Nutrition Search, Settings) to the unified design system.
- Sidebar, header, and mobile nav restyled to glass surfaces with brand accent.
- Updated `border-radius` scale so `2xl` (1.5rem) is distinct from `xl` (1.25rem).
- Hardened responsive grids with `minmax(0,1fr)` and `min-w-0` to prevent overflow.
- Repositioned Weight Tracker FAB to clear the mobile bottom navigation.

### Fixed

- Replaced undefined CSS variables (`--color-surface-container-*`, `--color-on-primary`,
  `--color-tertiary`) with real design tokens (no more transparent backgrounds / invisible
  text on brand buttons).
- Replaced silently-dropped Tailwind opacity modifiers (`bg-brand/10`, `border-brand/20`,
  `bg-surface/50`, `bg-error/15`, etc.) with working opaque tokens (`bg-brand-light`,
  `bg-error-light`, `hover:border-brand`, `ring-brand-light`, ...).
- Made the AI Coach sticky header opaque (translucent `bg-surface/50` was dropped).
- Removed 8 dead component files and their dead-import surface.

### Removed

- `components/app-sidebar.tsx`, `components/app-header.tsx` (legacy re-export shims).
- `components/dashboard-feature-card.tsx`, `components/dashboard-nutrition-status.tsx`.
- `components/ai-coach/typing-indicator.tsx`.
- `components/ui/breadcrumb.tsx`, `components/ui/progress-ring.tsx`,
  `components/ui/page-container.tsx`.

### Security

- Confirmed no hardcoded secrets or API keys in source.
- Protected routes gated via `ProtectedRoute` with login redirect preserving `?redirect=`.
- Password fields use correct `autoComplete` and `type="password"` semantics.
- (See `SECURITY.md` for the known `localStorage` token-storage limitation.)

## [1.0.0] - 2026 (pre-redesign baseline)

- Initial Next.js App Router frontend with authentication, dashboard, nutrition profile,
  nutrition logging, body-weight tracking, and task management against frozen backend
  contracts. (See prior `frontend/README.md` history for phase detail.)
