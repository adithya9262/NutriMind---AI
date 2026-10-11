# NutriMind AI Repository Audit

**Audit date:** 2026-10-11
**Scope:** source, configuration, tests, dependency manifests, and available local checks. No production service or database was contacted.

> Historical audit snapshot: this report predates the security remediation changes. Its
> account-linking, CSV export, and frontend token-storage findings have subsequent source
> changes. It is not an end-to-end security certification; check current code and test
> results before relying on it.

## Executive summary

The repository implements a Next.js 15 / React 19 frontend, a FastAPI backend, PostgreSQL persistence through SQLAlchemy and Alembic, and Supabase Auth with backend-issued JWT support. The backend also implements AI Coach sessions and memory, using Gemini and Groq integrations, plus USDA/Open Food Facts search and food image recognition.

One critical authentication bypass was confirmed in Supabase account synchronization and fixed. The endpoint had accepted any parseable JWT claims after Supabase verification failed, then could map the claimed email to an existing local account and issue a NutriMind token. The unsigned-claim fallback is removed and a forged-token regression test was added. Other fixes align AI quota dates with the advertised UTC reset and prevent raw provider/database exception text from reaching API clients.

The audit records **1 P0, 3 P2, and 2 P3 findings**: five were fixed, and the stale root README status is deferred.

Frontend checks now pass for all 475 tests and the production build. TypeScript's standalone check still fails on old Playwright QA scripts. The backend regression tests for the new fixes pass, but the complete backend suite stalls on its first auth route test under the available dependency/runtime combination. A full Ruff check also reports existing repository-wide violations. The checkout has an empty `.git` directory, so Git status and a final Git diff cannot be produced; review was limited to inspecting edited files and generated check results.

## Verified architecture

| Area | Observed implementation |
|---|---|
| Frontend | Next.js App Router, React, TypeScript, Supabase SSR client/middleware; protected routes cover dashboard, goals, tasks, nutrition, weight, settings, and AI Coach. |
| Authentication | Supabase Auth is used by the browser. The backend verifies Supabase tokens through `/auth/v1/user` or a configured Supabase JWT secret, and also verifies its own issuer/audience-bound HS256 access tokens. Legacy backend email/password routes remain. |
| API | FastAPI routers under `/api/v1` cover authentication, profile, goals, tasks, food logs, body weights, food search/recognition, AI Coach, reports, settings, and health. |
| Persistence | Async SQLAlchemy with PostgreSQL/asyncpg and Alembic. ORM metadata loads 10 tables: `users`, `nutrition_profiles`, `nutrition_logs`, `body_weights`, `goals`, `tasks`, `chat_sessions`, `chat_messages`, `ai_usage_trackers`, and `ai_user_memories`. Alembic contains 12 revision files, one base and one head. |
| AI and external data | AI Coach service supports Gemini and Groq; semantic memories are retrieved per user. Food search uses USDA when configured and falls back to Open Food Facts. Food recognition is present. |
| Nutrition logic | Domain calculations use `Decimal`, metric inputs, activity multipliers, goal adjustments, and a 1200 kcal minimum target; BMI is calculated as kg / m². |
| Configuration | `.env.example` files are templates. No real `.env` file was present. Database, JWT, Supabase and AI keys are supplied through environment settings. |

The root README contains older phase notes that say AI/external APIs and certain tables or routes are absent. Current code and ORM metadata supersede those claims.

## Baseline and verification results

The first check attempt could not run because project dependencies were not installed. Dependencies were then installed into `frontend/node_modules` and an isolated temporary Python environment; no dependency manifest or lockfile was intentionally changed.

| Check | Result |
|---|---|
| Frontend tests (`npm test -- --reporter=dot`) | **475 passed** across 54 files after correcting stale test expectations. |
| Frontend type check (`npm run type-check`) | **Failed** with TypeScript errors in legacy `frontend/test/*.spec.ts` Playwright/debug scripts (e.g. missing `body` on request objects, optional properties used without narrowing, nullable page text, implicit `any`). |
| Frontend lint (`npm run lint`) | **Passed with warnings**: eight unused-variable warnings. Next.js reports `next lint` is deprecated. |
| Frontend production build (`npm run build`) | **Passed**; 18 application routes built. The build emitted the same unused-variable warnings. |
| Backend focused regressions | **2 passed**: forged Supabase JWT rejection and UTC quota-day selection. |
| Backend focused domain subset | **378 passed, 10 skipped** across auth regression, AI quota date, nutrition calculations, task domain, and token tests; one Pydantic deprecation warning. |
| Backend full suite | **Not completed**: the run collected 6,390 tests under Python 3.14, then stalled at `TestRouteRegistration.test_register_path_exists`; faulthandler showed the asyncio loop waiting without a response. The same request stalls by itself under Python 3.12 when using the newest resolved FastAPI 0.143 / Starlette 1.7 dependencies. |
| Backend compile check | **Passed** (`compileall` over `app` and `tests`). |
| Backend Ruff lint | **Failed**: 241 findings across the repository, including import ordering, deprecated style, long lines, ambiguous names, and whitespace. |
| Backend Ruff format check | **Failed**: 43 files would be reformatted. No repository-wide formatting sweep was applied. |
| Database/migration runtime | ORM metadata and migration graph inspected statically. No configured database URL or isolated PostgreSQL instance was available for live migration/CRUD verification. |
| Browser verification | Not performed. |

Because the repository has no usable Git metadata, a pre-change test baseline and final Git diff could not be recorded. The `.git` directory exists but contains no repository files.

## Deferred documentation issue

- **P3:** Root `README.md` still contains historical phase/status statements that conflict with the current code (for example, claims that there are no AI APIs and only five ORM tables). The verified architecture above is based on source and configuration. A broad README rewrite was outside the safe, focused remediation scope; refresh the status summary and mark older phase notes as historical.

## Findings and remediation

### NM-001 — P0 — Unverified Supabase JWT claims could mint a backend session — Fixed

- **Affected code:** `backend/app/api/v1/auth.py`, `/api/v1/auth/supabase-sync`.
- **Evidence:** after `verify_supabase_token()` returned `None`, the handler decoded the supplied JWT with `verify_signature=False`, accepted `sub` and `email`, synchronized the account, and issued a backend JWT. An attacker could forge those claims for an existing email.
- **Impact:** account takeover and access to that account's profile, nutrition, goals, weight, tasks, and AI history.
- **Fix:** removed the unsigned decode fallback. Sync now returns 401 unless Supabase verification returns an identity.
- **Related fix:** removed diagnostic output from the same handler that printed the user's email, identity IDs, and a prefix of the stored password hash.
- **Regression check:** a regression creates a validly formed, attacker-signed HS256 JWT and verifies it is rejected before any DB query. The focused test passes.

### NM-002 — P2 — AI quota day could disagree with its UTC reset timestamp — Fixed

- **Affected code:** `backend/app/api/v1/ai_coach.py` quota upsert, usage history, image analysis and meal-plan accounting.
- **Evidence:** `_next_reset_utc()` advertises midnight UTC, while quota row keys and history ranges previously used `date.today()`, which follows the host timezone.
- **Impact:** on a non-UTC host, users could see a reset timestamp that did not match when quotas actually reset or which usage row the API considered current.
- **Fix:** introduced `_today_utc()` and used it for AI Coach date selection.
- **Regression check:** focused test asserts the helper derives its day using `datetime.now(UTC)`; it passes.

### NM-003 — P2 — Raw internal exception messages were returned to clients — Fixed

- **Affected code:** `backend/app/api/v1/ai_coach.py` chat/stream/image-analysis failures and `backend/app/api/v1/settings.py` account deletion/export/import failures.
- **Evidence:** handlers returned `str(exc)` or used it in client-visible error details. Provider and database exceptions can include internal service or query details.
- **Impact:** unnecessary disclosure of internal failure information to authenticated clients.
- **Fix:** client responses now use generic actionable messages; server logs retain exception context for diagnosis.
- **Verification:** source inspection and backend compile check. No dedicated response-contract regression test was added for each failure path.

### NM-004 — P2 — Authentication diagnostics exposed account identifiers and a password-hash prefix — Fixed

- **Affected code:** `backend/app/api/v1/auth.py`, Supabase sync handler.
- **Evidence:** a diagnostic logger and `print()` included the Supabase email, subject, resolved local user ID/email, and the first 12 characters of `user.password_hash`.
- **Impact:** unnecessary personal data and password-hash material in application logs/console output.
- **Fix:** removed the diagnostic logging and print statement.
- **Verification:** source inspection confirmed no diagnostic string or password-hash prefix output remains in the handler.

### NM-005 — P3 — Frontend component tests asserted superseded UI behavior — Fixed

- **Affected tests:** `frontend/__tests__/app/landing-page.test.tsx`, `frontend/__tests__/components/body-weight-history-list.test.tsx`, and `frontend/__tests__/components/nutrition-profile-form.test.tsx`.
- **Evidence:** tests expected a removed landing headline/status panel, a different locale date string, and required fields for profile creation. Current UI uses different copy/date formatting, and the form explicitly permits an incomplete initial profile.
- **Impact:** valid current behavior was reported as broken, reducing confidence in the suite.
- **Fix:** updated tests to assert the current accessible copy, use the app's date formatter, and verify an empty profile can be submitted.
- **Regression check:** affected test files pass (24 tests); full frontend suite passes (475 tests).

## Security and data-integrity assessment

- Aside from NM-001, reviewed protected resource routes derive user ownership from `get_current_user`; goals, tasks, logs, weights, reports, and AI sessions include authenticated user scoping in their queries/services.
- Supabase JWT verification checks signature, expiry, and the `authenticated` audience when a Supabase JWT secret is configured. The remote Supabase user endpoint is used when configured. Backend JWTs validate signature, issuer, audience, expiry, and access-token type.
- CSV export uses Python's CSV writer, which quotes values, but formula injection behavior was not verified in a spreadsheet client. Excel/CSV import/export was not exercised end to end.
- Upload MIME/size handling, live provider timeout behavior, PostgreSQL constraints under concurrency, and actual cross-user API behavior were not exercised against running infrastructure.
- No real environment files or credentials were found in the repository. `.env.example` contains placeholder values only.
- AI context building is user-filtered and includes profile data, goals, nutrition, body weight, recent assistant messages, and retrieved user memories. Provider integration and prompt-injection resistance were reviewed from source only; no live LLM test was run.

## Remaining limitations and next steps

1. Re-run the backend suite on the project's supported Python 3.11/3.12 environment and compatible FastAPI/Starlette versions; diagnose the ASGI validation request hang before relying on backend suite totals.
2. Repair the standalone frontend type-check errors in the Playwright QA scripts, keeping strict checks enabled.
3. Establish a pinned backend dependency lock (or constraints file) so framework versions and lint behavior are reproducible; project manifests currently specify broad lower bounds.
4. Address the repository-wide Ruff findings in focused groups after establishing a clean baseline; current Ruff formatter reports 47 files outside a clean format state.
5. Run migration upgrade/downgrade and core authenticated journeys against an isolated PostgreSQL database, then exercise browser flows with configured Supabase credentials.
6. Refresh the root README's phase/status claims to match the implemented AI routes, 10 ORM tables, and 12 migration revisions.
