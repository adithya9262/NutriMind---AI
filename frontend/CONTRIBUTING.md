# Contributing to NutriMind AI Frontend

## Development setup

```powershell
cd frontend
npm install
copy .env.example .env.local
npm run dev
```

Requires Node.js 18.18+ and a running backend at `NEXT_PUBLIC_API_URL`.

## Coding conventions

- **TypeScript strict** — no `any`, no `ts-ignore`/`ts-nocheck`, no broad `eslint-disable`.
- **Functional components + hooks**; avoid class components.
- **No real domain logic in the frontend** — nutrition/weight/task calculations belong to the
  backend. The frontend only displays backend values.
- **No hardcoded URLs or secrets** — use `NEXT_PUBLIC_API_URL` and the API client.
- **No `console.log`/debugger** in committed code; `error.tsx` may log errors intentionally.
- **No commented-out code**; delete dead code rather than leave it disabled.
- **Keep files under ~500 lines**; extract components when a file grows.

## Naming conventions

- **Components:** PascalCase files and exports (`TaskCard.tsx` → `TaskCard`).
- **Hooks:** `use` prefix, camelCase (`useDailyNutritionLogs`).
- **Services:** kebab-case files, feature-scoped (`services/api/tasks.ts`).
- **Types:** PascalCase interfaces/types; shared types in `types/`.
- **Tests:** co-located in `__tests__/` mirroring the source path
  (`__tests__/components/task-card.test.tsx`).
- **CSS classes:** Tailwind utilities; custom tokens via the design system only.

## Testing requirements

- New features **must** ship tests covering loading, empty, and error states.
- Use `@testing-library/react` + `user-event`; query by role/label, not implementation.
- Every page/component change should keep `npm test` green.
- No `.only`/`.skip` left in committed tests.
- Run the full gate before opening a PR:
  ```powershell
  npm run lint && npm run type-check && npm run build && npm test
  ```

## Commit message format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body (optional)>
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `perf`, `security`.
Example: `fix(weight): clear FAB from mobile bottom nav`.

## Pull request checklist

- [ ] `npm run lint`, `npm run type-check`, `npm run build`, `npm test` all pass
- [ ] No hardcoded secrets, URLs, or API keys
- [ ] New functionality has tests (loading/empty/error covered)
- [ ] Design tokens used from the system (no ad-hoc colors or dropped opacity modifiers)
- [ ] Accessibility: labelled inputs, visible focus, ARIA where needed
- [ ] Responsive: verified mobile → desktop, no overflow/clipping
- [ ] No dead code or commented-out blocks left behind
- [ ] Docs updated if behavior/contract changed

## Review guidelines

- Verify the change uses the centralized API client and existing auth context.
- Confirm no new domain formulas were introduced on the frontend.
- Check that demo/placeholder content remains clearly labeled.
- Prefer small, focused PRs; request changes on missing tests or broken a11y/responsive behavior.
- Protect the frozen backend contracts — frontend changes must not assume undocumented
  backend behavior.
