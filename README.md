# NutriMind AI

Intelligent nutrition and wellness companion.

**Current status:** Phase 6B-2 — Full Local Stack Smoke Validation, Core User-Journey Verification, and Release Readiness completed. Complete live-stack validation against real local PostgreSQL database and running FastAPI/Next.js servers. All 71 smoke tests passed covering: CORS/preflight, registration (including duplicate), login (valid/invalid/unknown), auth errors (missing/bad token), current-user restoration, nutrition-profile CRUD, nutrition calculations, personalized summary, nutrition-log CRUD, daily summary, target progress, body-weight CRUD (one-entry trend rejection, two-entry trend, goal progress), task CRUD/complete/reopen, user isolation, response privacy (no password/hash/stack trace), request-ID headers, and security headers. Backend: 6358 tests passing, ruff format clean (144 files), ruff lint clean. Frontend: 469 tests passing (53 files), tsc --noEmit clean, lint clean, production build successful (12 routes). No production code changed, no new ORM tables, no new migrations, no new backend endpoints, no new frontend routes, no AI/LLM/external APIs added. Phase 6B-2 is **FROZEN**. Phase 6B-3 not started.

**Previous status:** Phase 5E-6 — Task Management Final Audit, Hardening, and Freeze completed. Phase 5E Task Management module fully audited, validated, documented, and frozen. Six authenticated task endpoints under `/api/v1/tasks` (`POST /tasks` create, `GET /tasks` list, `GET /tasks/{task_id}` get, `POST /tasks/{task_id}/complete` complete, `POST /tasks/{task_id}/reopen` reopen, `DELETE /tasks/{task_id}` delete), reusing the frozen Phase 5E-1 domain functions (`create_task`, `complete_task`, `reopen_task`, `order_tasks`), task exceptions, Phase 5E-2 schemas, Phase 5E-3 `Task` ORM/migration, and Phase 5E-4 `TaskRepository`/`TaskService`. Every endpoint requires the existing `BearerAuth` via `get_current_user`; ownership derived exclusively from `current_user.id`; `POST` generates a new public `task_id` via `uuid.uuid4()`; `completed_at` is caller-supplied for completion (no system clock). Error mapping: 404 `TASK_NOT_FOUND`, 409 `TASK_ID_ALREADY_EXISTS`/`TASK_ALREADY_COMPLETED`/`TASK_NOT_COMPLETED`, 422 `INVALID_TASK`, 503 `TASK_PERSISTENCE_ERROR`, 500 `INTERNAL_SERVER_ERROR`. Read-only endpoints never commit/mutate; write endpoints commit exactly once. All 6336 tests pass (6230 Phase 5E-5 baseline + 106 new Phase 5E-6 audit tests). Ruff format and lint pass. Exactly 5 ORM tables, exactly 5 linear migration revisions (head a7b8c9d0e5f), exactly 1 BearerAuth OpenAPI scheme. No production defects found; no production code changed. Phase 5E is **FROZEN**.

**Previous status:** Phase 5E-4 — Task Repository and Service Foundation completed. `TaskRepository` (`app/repositories/task.py`) and `TaskService` (`app/services/task.py`) added, reusing the frozen Phase 5E-1 domain functions (`create_task`, `complete_task`, `reopen_task`, `order_tasks`), task exceptions, Phase 5E-2 schemas, and Phase 5E-3 `Task` ORM/migration. `TaskRepository(session: AsyncSession)` is user-scoped for every lookup (`list_by_user_id`, `get_by_user_and_task_id` — no task_id-only query), maps all seven domain fields plus `user_id` in `create` (never generates a new public `task_id`, never sets ORM `id` manually), flushes on create/update/delete, and translates the `uq_tasks_user_id_task_id` `IntegrityError` into `DuplicateTaskIdError` with chaining. `TaskService(repository: TaskRepository)` is framework-independent, database-framework-independent, and transaction-free (no SQLAlchemy/`commit`/`rollback`/`flush`/`refresh` text); it delegates the repository exactly once, applies the frozen `order_tasks()` exactly once for user-scoped listing, raises `TaskNotFoundError` for absent/wrong-user tasks, and reuses the frozen `complete_task()`/`reopen_task()` for complete/reopen (preserving caller-provided `completed_at`, mutating only `status`/`completed_at`, propagating `TaskAlreadyCompletedError`/`TaskNotCompletedError`). New exceptions `TaskNotFoundError` and `DuplicateTaskIdError` added under `TaskError`. No task API router, no `/tasks` endpoint, no request handlers, no application API transaction ownership, no frontend, no reminders/recurrence/notifications/categories/tags/subtasks/sharing, no AI prioritization/recommendations, no external APIs, no API keys, no new ORM/migration/dependency. All 6117 tests pass (5955 Phase 5E-3 verified baseline + 162 new Phase 5E-4 repository/service tests). Ruff format and lint pass. Exactly 5 ORM tables, exactly 5 linear migration revisions (head a7b8c9d0e5f), exactly 1 BearerAuth OpenAPI scheme, no `/tasks` route, only `.env.example` exists — no real secrets. Phase 5E-1 domain, Phase 5E-2 schemas, and Phase 5E-3 ORM/migration code were not modified; Phase 5E-4 is completed and ready for the next explicitly approved phase (Phase 5E-5). **Previous status:** Phase 5E-3 — Task ORM Model and Migration Foundation completed. SQLAlchemy 2.0 ORM model `Task(Base, TimestampMixin)` (`app/models/task.py`) and Alembic migration (`alembic/versions/a7b8c9d0e5f_create_tasks.py`) added to the backend, reusing the frozen Phase 5E-1 domain enums (`TaskPriority` `low`/`medium`/`high`, `TaskStatus` `pending`/`completed`) and the frozen Phase 5E-2 schemas. The `tasks` table has eleven columns: `id` (UUID PK, application-generated `uuid.uuid4()` default), `user_id` (UUID FK → `users.id`, ON DELETE CASCADE), `task_id` (UUID, caller-owned public identifier, unique per user), `title` (String(200)), `description` (String(2000), nullable), `priority` (native enum `task_priority`), `status` (native enum `task_status`), `due_date` (Date, nullable), `completed_at` (DateTime(timezone=True), nullable), plus inherited `created_at`/`updated_at`. Named composite unique `uq_tasks_user_id_task_id`, named FK `fk_tasks_user_id`, named state-consistency check `ck_tasks_status_completed_at_consistency` (`pending`↔`completed_at IS NULL`, `completed`↔`completed_at IS NOT NULL`), and named non-unique composite lookup index `ix_tasks_user_id_status_due_date` on `(user_id, status, due_date)`. Symmetric relationships: `User.tasks` (one-to-many, `cascade="all, delete-orphan"`) and `Task.user` (many-to-one). Migration creates both enums exactly once and downgrade drops index → table → `task_status` → `task_priority` (no CASCADE); offline PostgreSQL SQL generation succeeds. No repository, no service, no API endpoint, no `/tasks` route, no application-layer persistence, no reminders/recurrence/notifications/categories/tags/recommendations, no AI/LLM, no frontend work, and no dependency were added. All 5955 tests pass (5791 Phase 5E-2 verified baseline + 164 new Phase 5E-3 model/migration tests). Ruff format and lint pass. Exactly 5 ORM tables, exactly 5 linear migration revisions (head a7b8c9d0e5f), exactly 1 BearerAuth OpenAPI scheme, only `.env.example` (placeholder template) exists — no real secrets. Phase 5E-1 domain code and Phase 5E-2 schema code were not modified; Phase 5E-3 is completed and ready for the next explicitly approved phase (Phase 5E-4).

**Previous status:** Phase 5E-2 — Task Schema Foundation completed. Pydantic v2 schema foundation for tasks added to the backend (`app/schemas/tasks.py`), reusing the frozen Phase 5E-1 domain types (`TaskPriority` `low`/`medium`/`high`, `TaskStatus` `pending`/`completed`, `Task`). Five new task schemas plus four success-response schemas: `TaskCreate` (input, extra=forbid, title/description strip+length/control validation, `priority` defaults to `MEDIUM`, `due_date` date-only), `TaskData` (immutable, extra=forbid, frozen=True, from_attributes=True, exact seven-field order, pending/completed state invariant enforced, `from_domain()` exact-copy no recalculation), `TaskListData` (immutable tuple-backed, `from_domain()` preserves input order, does not call `order_tasks()`), `TaskSuccessResponse`, `TaskListSuccessResponse`, `TaskDeleteSuccessResponse` (no `data` field), `TaskCompletionSuccessResponse`, and `TaskReopenSuccessResponse` (all `success: Literal[True]`, exact default messages, extra=forbid). Domain enums reused (no duplicates); UUID/ISO-date/ISO-datetime/lowercase-enum serialization; no `user_id`/ORM id/timestamps exposed. No ORM model, no migration, no repository, no service, no API endpoint, no `/tasks` route, no persistence, no reminders/recurrence/notifications/recommendations, no AI/LLM, no frontend work, and no dependency were added. All 5791 tests pass (5596 Phase 5E-1 verified baseline + 195 new Phase 5E-2 schema tests). Ruff format and lint pass. Exactly 4 ORM tables, exactly 4 linear migration revisions (head e5f6a7b8c9d0), exactly 1 BearerAuth OpenAPI scheme, only `.env.example` (placeholder template) exists — no real secrets. Phase 5D is frozen and unchanged; Phase 5E-1 domain code was not modified; Phase 5E-2 is completed and ready for the next explicitly approved phase (Phase 5E-3).

**Previous status:** Phase 5D-3 — Authenticated Body-Weight Goal Progress API completed. One authenticated, read-only endpoint `GET /api/v1/body-weights/goal-progress` added to the existing body-weight router (`app/api/v1/body_weights.py`). It orchestrates the existing `NutritionProfileRepository`/`NutritionProfileService` and `BodyWeightRepository`/`BodyWeightService` to compute goal progress: `starting_weight_kg` = nutrition-profile `weight_kg`, `target_weight_kg` = nutrition-profile `target_weight_kg`, `current_weight_kg` = latest persisted `BodyWeight.weight_kg`, then reuses the frozen Phase 5D-1 `calculate_body_weight_goal_progress(...)` and the frozen Phase 5D-2 `BodyWeightGoalProgressData.from_result(...)` / `BodyWeightGoalProgressSuccessResponse`. No goal direction/total-change/change-achieved/remaining-change/percentage/status/rounding logic duplicated in the route. Empty history → 422 `BODY_WEIGHT_GOAL_CURRENT_WEIGHT_NOT_FOUND`; equal start/target → 422 `BODY_WEIGHT_GOAL_PROGRESS_INVALID` (frozen `InvalidBodyWeightGoalProgressError` message); missing profile reuses 404 `NUTRITION_PROFILE_NOT_FOUND`. Endpoint is strictly read-only (no commit/rollback/flush/refresh/add/delete/merge; no profile synchronization; no persisted value). No goal ORM model, table, migration, repository, or service. No new dependency, no `.env` or real secrets. All 5418 tests pass (5327 Phase 5D-2 verified baseline + 91 new Phase 5D-3 API tests). Ruff format and lint pass. Exactly 4 ORM tables, exactly 4 linear migration revisions (head e5f6a7b8c9d0), exactly 1 BearerAuth OpenAPI scheme, only `.env.example` (placeholder template) exists — no real secrets. Phase 5D-1 is frozen and unchanged; Phase 5D-2 is completed and unchanged; Phase 5D-3 is completed and ready for the next explicitly specified phase (Phase 5D-4).

**Previous status:** Phase 5D-2 — Body-Weight Goal Schema Foundation completed. Pydantic v2 schema foundation for body-weight goals and body-weight goal progress added in the backend (`app/schemas/body_weight_goals.py`), reusing the frozen Phase 5D-1 domain types. Five new schemas: `BodyWeightGoalCreate` (input), `BodyWeightGoalData` (domain response via `from_domain()`), `BodyWeightGoalProgressData` (result response via `from_result()`), `BodyWeightGoalSuccessResponse`, and `BodyWeightGoalProgressSuccessResponse`. Domain enums `BodyWeightGoalDirection` and `BodyWeightGoalStatus` reused (no duplicate). Decimal values remain `Decimal` in Python and serialize as JSON strings. Negative progress, above-100% progress, and negative remaining change are preserved without capping or clamping. No API endpoint, no persistence, no ORM/migration/repository/service changes. No new dependency, no `.env` or real secrets. All 5327 tests pass (5164 Phase 5D-1 verified baseline + 163 new Phase 5D-2 schema tests). Ruff format and lint pass. Exactly 4 ORM tables, exactly 4 linear migration revisions (head e5f6a7b8c9d0), exactly 1 BearerAuth OpenAPI scheme, only `.env.example` (placeholder template) exists — no real secrets. Phase 5D-1 is frozen and unchanged; Phase 5D-2 is completed and ready for the next explicitly specified phase (Phase 5D-3).

**Previous status:** Phase 5C-2 — Body-Weight Trend Schema Foundation completed and frozen. Strict Pydantic v2 response schemas added (`app/schemas/body_weight_trends.py`): `BodyWeightTrendData` (immutable, extra="forbid", frozen=True) and `BodyWeightTrendSuccessResponse` (success envelope with `Literal[True]`, exact default message "Body-weight trend calculated successfully."). Reuses existing `BodyWeightTrendDirection` enum. Domain-to-schema conversion via `from_result()` copies all eight values exactly (no recalculation, no rounding, no direction reclassification). Decimal values preserved in Python, serialize as JSON strings. No API endpoint, no persistence, no ORM/migration changes, no dependency changes. All 4951 tests pass (4821 Phase 5C-1 baseline + 130 new Phase 5C-2 schema tests). Ruff format and lint pass. Exactly 4 ORM tables, 4 linear migration revisions (head e5f6a7b8c9d0), exactly 1 BearerAuth OpenAPI scheme, no .env or real secrets. Phase 5C-2 is frozen.

**Previous status:** Phase 5B — Body-Weight Tracking Module completed and frozen. Final comprehensive cross-layer audit completed: 55 new invariants across 13 layers (domain→exceptions→schemas→ORM→migration→repository→service→API→auth→error handling→privacy→OpenAPI→application integrity). All 4704 tests pass (4649 baseline + 55 new audit tests). Ruff format and lint pass. No production defects found, no dependency changes, no ORM/model/migration changes. Exactly 4 ORM tables, 4 linear migration revisions (head e5f6a7b8c9d0), exactly 1 BearerAuth OpenAPI scheme, no .env or real secrets. Phase 5B is frozen.

**Previous status:** Phase 4F-10 — Nutrition Logging and Daily Progress Foundation Final Audit completed. Comprehensive audit of the complete Phase 4F nutrition logging and daily progress foundation (domain, schemas, ORM, migrations, repositories, services, CRUD API, daily summary API, daily progress API, authentication, transactions, error safety, OpenAPI, privacy, security). No production defects were found. One test-quality formatting defect corrected (missing blank line before `import re` in `test_nutrition_progress_api.py`). 41 new cross-layer audit invariants added. All 3901 tests pass (3860 Phase 4F + 41 new). Ruff format and lint pass. ORM metadata unchanged (3 tables: users, nutrition_profiles, nutrition_logs). Migration head unchanged (`b8a7c3d9e1f2`). No progress or summary values are persisted. Phase 4F is frozen. Ready for the next explicitly specified phase.

### Phase 4E-3 — Authenticated Personalized Nutrition Summary API Integration

- **New authenticated endpoint** — `GET /api/v1/nutrition-profile/summary`; requires a Bearer token (reuses the existing `get_current_user` dependency and `BearerAuth` scheme) and a required `reference_date` query parameter (ISO `date`, `YYYY-MM-DD`); missing/malformed/impossible dates return HTTP 422
- **Thin, orchestration-only endpoint** — loads the authenticated user's profile via the existing `NutritionProfileRepository` / `NutritionProfileService.get_profile()`, then calls the verified `calculate_nutrition_metrics()`, `calculate_nutrition_targets()`, `build_nutrition_summary()`, and `NutritionSummaryData.from_result()` exactly once each; calculation formulas and summary rules remain in the domain layer
- **Read-only** — no persistence of calculated metrics, targets, or summary content; no commit/flush/refresh/mutation of the user or profile objects; uses the existing request-scoped `get_db_session`
- **Existing error contracts reused** — missing profile → `NUTRITION_PROFILE_NOT_FOUND` (404); unsupported BMR (biological-sex `other` / `prefer_not_to_say`) → `BMR_CALCULATION_UNSUPPORTED` (422); below-minimum calorie target → `CALORIE_TARGET_BELOW_MINIMUM` (422); invalid `reference_date` (equal to or before `date_of_birth`) → `INVALID_CALCULATION_INPUT` (422); unexpected errors → global `INTERNAL_SERVER_ERROR` (500)
- **Phase 4E-2 schemas reused** — response uses `NutritionSummarySuccessResponse` and `NutritionSummaryData.from_result()`; the default success message and the six ordered summary item codes/tones are unchanged
- **No new dependencies, no ORM/migration changes, no frontend changes, no AI/USDA/Groq integration, no health score, no diagnosis or treatment**

### Phase 4E-4 — Personalized Nutrition Summary Final Audit and Freeze (completed)

- **Objective** — final audit, hardening, regression-validation, and freeze of the complete Phase 4E foundation (4E-1 domain, 4E-2 schemas, 4E-3 API)
- **Result** — FROZEN; no production defects found. One test-quality defect corrected: an un-awaited coroutine assertion in `tests/test_current_user.py` (`mock_session.execute.awaited_once()` → `mock_session.execute.assert_awaited_once()`) that emitted a `RuntimeWarning`
- **Audit coverage** — domain summary module (framework-independent, deterministic, immutable, no formula duplication, no system clock, no secrets, no network, no DB), schema module (dependency direction domain→schema, `extra="forbid"` + `frozen=True`, strict validation, exact-count/unique/ordered code contract, deterministic `from_result`), authenticated GET endpoint (orchestration-only, reuses repository/service/calculation/schema helpers exactly once each, current-user isolation, explicit `reference_date`, read-only/no persistence), authentication and error contracts, OpenAPI contract (exactly one `BearerAuth`, GET-only summary, required `reference_date` of `format: date`, no duplicate operation IDs), privacy/response minimization, and ORM/migration/secret integrity
- **Nutrition-safety verification** — BMI presented as a screening measure (not a diagnosis); BMR/TDEE/calorie/macro values described as general estimates (not medical prescriptions); goal wording contextual with no guaranteed outcomes and no weekly/period-change predictions; general-limitation item clearly communicates uncertainty and individual variation; no diagnosis, treatment, guaranteed outcomes, unsupported predictions, shaming, or alarmist language
- **Final verification** — baseline 2607 tests → final 2607 tests passing (1302 Phase 4E tests + 1305 others); Ruff format and lint clean; Python 3.11.9; FastAPI 0.115.0, Pydantic 2.11.4, SQLAlchemy 2.0.36, asyncpg 0.30.0, Alembic 1.14.1, pwdlib 0.3.0, PyJWT 2.13.0; two Alembic migration files unchanged (byte-for-byte, hashes stable), migration head unchanged (`99a3b19be1b8`); ORM metadata unchanged (`users`, `nutrition_profiles`); no `.env` and no real secrets; import-time DB connection does not occur; no `create_all`/autogenerate; two independent `create_app()` instances are distinct
- **Confirmation** — no formulas duplicated, no summary rules duplicated, no AI/LLM summary generation, no calculated or summary values persisted, no ORM/migration/authentication changes, no health score/diagnosis/treatment, no outcome guarantees, no weight-change/time-to-goal predictions, no diet/meal plans, no food/recipe/ingredient features, no USDA/Groq/AI integration, no fake nutrition information, no frontend changes, no `.env` or real secrets, nothing committed or pushed
- **Readiness** — the Phase 4E foundation is frozen and ready for the next explicitly specified phase

## Planned technology stack

| Layer     | Technology                                     |
|-----------|------------------------------------------------|
| Frontend  | Next.js, TypeScript, Tailwind CSS              |
| Backend   | Python, FastAPI, SQLAlchemy, Alembic, Pydantic |
| Database  | PostgreSQL                                     |
| AI        | LangChain / LLM integration (future phase)     |
| Infra     | Docker Compose (local), TBD (production)       |

## Repository structure

```
nutrimind-ai/
├── .github/workflows/     # CI workflow definitions
├── backend/               # Python / FastAPI application
│   ├── app/               # Application package
│   ├── tests/             # Pytest test suite
│   ├── .env.example       # Backend environment template
│   ├── pyproject.toml     # Package and tooling config
│   └── README.md          # Backend documentation
├── docs/                  # Documentation
├── frontend/              # Next.js application (Phase 1E foundation)
├── .editorconfig          # Editor settings
├── .env.example           # Top-level environment template
├── .gitignore             # Comprehensive ignore rules
├── docker-compose.yml     # PostgreSQL (local dev only)
├── FUTURE_FEATURES.md     # Aspirational features
└── README.md              # This file
```

> **User and NutritionProfile tables now exist in the PostgreSQL database.**  
> Authentication, nutrition calculations, food search, recipes, AI chat, dashboards,
> diet plans, and reports have not been implemented yet.

## Backend (Phase 1B)

The backend is a FastAPI application with a clean, secure, testable foundation.

### Quick start

```bash
cd backend

# Create and activate virtual environment
python -m venv .venv
# PowerShell: .venv\Scripts\Activate.ps1
# Cmd: .venv\Scripts\activate.bat

# Install dependencies
pip install -e ".[dev]"

# Copy environment file
cp .env.example .env

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Health endpoint

```bash
curl http://localhost:8000/api/v1/health
```

Expected response:
```json
{
  "success": true,
  "message": "NutriMind API is healthy",
  "data": { "status": "healthy" }
}
```

### Tests and code quality

```bash
cd backend
pytest
ruff format --check .
ruff check .
```

See `backend/README.md` for detailed setup and commands.

## Frontend (Phase 1D)

The frontend is a Next.js application with TypeScript, Tailwind CSS, and the App Router.

### Quick start

```powershell
cd frontend
npm install
copy .env.example .env.local
npm run dev
```

### Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start development server (http://localhost:3000) |
| `npm run build` | Production build |
| `npm run start` | Start production server |
| `npm run lint` | Run ESLint |
| `npm run type-check` | Run TypeScript type checking |

### Backend connection

The frontend connects to the backend at `http://localhost:8000/api/v1`.
Start the backend before testing the connection status feature.

See `frontend/README.md` for detailed setup and commands.

## PostgreSQL (Phase 2A — Docker infrastructure)

A local PostgreSQL 16 instance is provided via Docker Compose for development. (Phase 2B added the async SQLAlchemy foundation.)

### Requirements

- Docker Desktop (Docker Engine running)

### Quick start

```bash
# Start PostgreSQL
docker compose up -d postgres

# Check container status
docker compose ps

# Check PostgreSQL readiness
docker compose exec -T postgres pg_isready -U nutrimind -d nutrimind

# View recent logs (up to 100 lines)
docker compose logs --tail=100 postgres

# Stop PostgreSQL without deleting data
docker compose stop postgres
```

### Data persistence

Database files are stored in a Docker named volume (`nutrimind_postgres_data`).

> **Warning:** Do **not** run `docker compose down -v` unless you intend to delete all database data.

### Troubleshooting — port conflict

If port 5432 is already in use (e.g., by a native PostgreSQL installation), the Docker container will fail to start. Use a different host port by setting `POSTGRES_PORT` in `.env`:

```bash
echo POSTGRES_PORT=5433>> .env
docker compose up -d postgres
```

Then update `DATABASE_URL` in `backend/.env` to match:

```
DATABASE_URL=postgresql+asyncpg://nutrimind:change_this_in_real_environments@localhost:5433/nutrimind
```

### Phase 2B — Async SQLAlchemy infrastructure

- SQLAlchemy 2.x async with asyncpg driver
- Typed declarative base (zero tables)
- Lazy async engine and reusable session factory
- FastAPI session dependency (no auto-commit, rollback on exception)
- Explicit connectivity utility (`SELECT 1`)
- Focused unit tests (mocked; no Docker required)

### Phase 2C — Alembic async migration foundation

- Alembic 1.14.1 declared runtime dependency
- `alembic.ini` with no hard-coded credentials
- Async-compatible `env.py` using existing `Base.metadata`
- One empty baseline migration (no application tables)
- 31 migration-focused tests (configuration safety, baseline structure, app isolation)
- Offline and online migration modes supported
- Migrations are explicit — they do not run during application startup

### Phase 2D-1 — Core User and NutritionProfile ORM models

- **User ORM model** — table `users` with UUID PK, email (unique), password_hash, is_active, is_verified, timestamps
- **NutritionProfile ORM model** — table `nutrition_profiles` with UUID PK, FK to users, date_of_birth, biological_sex, height, weight, activity_level, goal, optional dietary_preference and allergies (JSONB), timestamps
- **UUID primary keys** generated in application code via `uuid.uuid4`
- **Timezone-aware timestamps** with database-side defaults
- **Typed SQLAlchemy 2.x relationships** with one-to-one User → NutritionProfile
- **Explicit database constraints** (unique email, unique user_id, height/weight range checks, ON DELETE CASCADE)
- **65 model-focused tests** covering metadata structure, constraints, enums, relationships, forbidden fields, and migration boundary
- **No physical tables created** — metadata only, migration pending

### Phase 2D-2 — User/NutritionProfile Migration Generated

- **Alembic migration `99a3b19be1b8`** creates `users` and `nutrition_profiles` tables with four PostgreSQL enum types
- Migration fully reviewed and corrected (lowercase enum values, explicit downgrade enum cleanup, no redundant indexes, all constraints named)
- **45 migration-content tests** — revision graph, upgrade/downgrade operations, schema, enums, forbidden content
- **Offline SQL generation validated**

### Phase 2D-3 — Migration Applied and Live PostgreSQL Validated

- Migration `99a3b19be1b8` applied successfully to Docker PostgreSQL (port 5433)
- Physical `users` and `nutrition_profiles` tables **now exist** in `public` schema
- All columns, types, defaults, constraints, and indexes verified against live PostgreSQL catalogs
- Four PostgreSQL enum types (`biological_sex`, `activity_level`, `nutrition_goal`, `dietary_preference`) validated with correct lowercase values
- **80 live validation tests** passed covering: valid inserts, database defaults, unique constraints, NOT NULL enforcement, check constraints (height/weight/target-weight boundaries), enum enforcement, foreign key enforcement, one-profile-per-user, ON DELETE CASCADE, ORM relationships, session behavior
- Downgrade to baseline (`3f0c6eb4f49e`) tested — removes both tables and all four enum types
- Re-upgrade tested — recreates schema without errors
- Final database revision: `99a3b19be1b8 (head)`
- Both application tables empty (0 rows) — no seed data
- `values_callable` added to ORM enum columns to ensure Python `StrEnum` values (lowercase) match PostgreSQL enum values
- **No authentication, no nutrition calculations, no seed data**

### Phase 5D-1 — Body-Weight Goal Domain Foundation (backend)

- Pure, deterministic, framework-independent body-weight goal domain foundation added in the backend
- `app/core/body_weight_goals.py` and `app/core/body_weight_goal_exceptions.py` implement a validated goal definition, direction (`decrease`/`maintain`/`increase`), and descriptive progress status (`not_started`/`in_progress`/`target_reached`/`target_passed`)
- Progress percentage and remaining change are **not clamped** (may be negative or above 100%)
- No API endpoint, no Pydantic schema, no ORM model, no migration, no persistence, no prediction, no goal date, no medical interpretation, no recommendation
- Backend final verified test count: **5164 passed** (5071 baseline + 93 new); ruff format and lint clean; exactly 4 ORM tables; exactly 4 Alembic revisions; migration head `e5f6a7b8c9d0`

### Phase 5D-2 — Body-Weight Goal Schema Foundation (backend)

- Pydantic v2 schema foundation for body-weight goals and body-weight goal progress added in the backend
- `app/schemas/body_weight_goals.py` implements five new schemas: `BodyWeightGoalCreate` (input), `BodyWeightGoalData` (domain response, `from_domain()`), `BodyWeightGoalProgressData` (result response, `from_result()`), `BodyWeightGoalSuccessResponse`, and `BodyWeightGoalProgressSuccessResponse`
- `BodyWeightGoalCreate` accepts `Decimal`/`int`/finite `float`/numeric string, rejects bool/None/empty/whitespace/malformed/NaN/Infinity, quantizes with `BODY_WEIGHT_DECIMAL_PLACES` using `ROUND_HALF_UP`, then validates against `MIN_BODY_WEIGHT_KG`/`MAX_BODY_WEIGHT_KG` (boundary after rounding); equal start/target accepted
- `BodyWeightGoalData` reuses `BodyWeightGoalDirection`; `from_domain()` copies all three values exactly (no arithmetic, no rounding, no direction reclassification)
- `BodyWeightGoalProgressData` has the nine domain fields in order; weights finite/positive/in-range; `total_change_required_kg > 0`; signed change/remaining/percentage accepted; negative progress, zero progress, exactly 100%, above-100%, and negative remaining change preserved without clamping or capping; reuses `BodyWeightGoalDirection` and `BodyWeightGoalStatus`; `from_result()` copies all nine values exactly (no arithmetic, no rounding, no clamping, no direction/status reclassification)
- Success envelopes use `success: Literal[True] = True` with exact default messages; `data` required and non-null; `extra="forbid"`
- Domain enums reused (no duplicates); Decimal values preserved in Python and serialized as JSON strings; enums serialize lowercase
- `app/schemas/__init__.py` exports the five new schemas; existing exports unchanged
- No API endpoint, no Pydantic schema for persistence, no ORM model, no migration, no repository, no service, no prediction, no goal date, no time-to-goal estimate, no recommendation, no medical interpretation, no AI/LLM
- Phase 5D-1 domain code was not modified, no formula duplicated, no direction recalculated, no status reclassified
- Backend final verified test count: **5327 passed** (5164 baseline + 163 new Phase 5D-2 schema tests); ruff format and lint clean; exactly 4 ORM tables; exactly 4 Alembic revisions; migration head `e5f6a7b8c9d0`

### Phase 5D-3 — Authenticated Body-Weight Goal Progress API (backend)

- One authenticated, read-only endpoint `GET /api/v1/body-weights/goal-progress` (HTTP 200) added to the existing body-weight router (`app/api/v1/body_weights.py`); declared before `DELETE /{entry_id}`; static path, no request body, no user_id, no start/current/target weight parameters, no goal/reference date; BearerAuth required; GET is the only method
- Orchestration only: `get_current_user` → `NutritionProfileRepository(session)` → `NutritionProfileService(repo)` → `get_profile(user_id=current_user.id)` → `BodyWeightRepository(session)` → `BodyWeightService(repo)` → `list_history(user_id=current_user.id)` → latest persisted entry (`history[0]`, since the repository orders by `logged_date desc`) → `calculate_body_weight_goal_progress(...)` exactly once → `BodyWeightGoalProgressData.from_result(...)` exactly once → `BodyWeightGoalProgressSuccessResponse`. No goal-direction/total-change/change-achieved/remaining-change/percentage/status/rounding/quantization/clamping/capping logic in the route
- Value mapping: `starting_weight_kg` = nutrition-profile `weight_kg`; `target_weight_kg` = nutrition-profile `target_weight_kg`; `current_weight_kg` = latest persisted `BodyWeight.weight_kg`. The earliest history entry is never used as current weight; the profile is never mutated or synchronized
- Error handling via the shared envelope: missing profile reuses 404 `NUTRITION_PROFILE_NOT_FOUND`; empty body-weight history returns 422 `BODY_WEIGHT_GOAL_CURRENT_WEIGHT_NOT_FOUND` (new domain exception `BodyWeightGoalCurrentWeightNotFoundError` in `app/core/body_weight_goal_exceptions.py`); equal starting/target weights maps the frozen `InvalidBodyWeightGoalProgressError` to 422 `BODY_WEIGHT_GOAL_PROGRESS_INVALID` with the exact frozen message; unexpected failures fall through to the existing global 500 `INTERNAL_SERVER_ERROR` (no raw SQL/stack-trace/secret exposure); `request_id` and `X-Request-ID` preserved
- Strictly read-only: never calls commit/rollback/flush/refresh/add/add_all/delete/merge; user, profile, and body-weight entries unchanged; no goal-progress value persisted; no goal ORM model/table/repository/service
- Decimal values serialize as JSON strings; `direction`/`status` serialize lowercase; negative progress, exactly-100%, above-100%, and negative remaining change preserved with no clamping/capping; exact default success message `Body-weight goal progress calculated successfully.`
- New tests: `tests/test_body_weight_goal_progress_api.py` (91 tests) covering route registration/ordering, OpenAPI, authentication, current-user isolation, orchestration, progress values, empty history, missing profile, equal start/target, unexpected failures, read-only behavior, and no formula duplication; existing boundary tests updated to account for the one new GET route (no test count forced)
- Backend final verified test count: **5418 passed** (5327 Phase 5D-2 baseline + 91 new Phase 5D-3 API tests); ruff format and lint clean; exactly 4 ORM tables; exactly 4 Alembic revisions; migration head `e5f6a7b8c9d0`; exactly 1 BearerAuth scheme; no `.env`/real secrets

### Phase 5D-4 — Body-Weight Goal Progress Final Audit, Hardening, and Freeze (backend)

- **Phase completed** — complete cross-layer final audit and freeze of the body-weight goal feature (Phase 5D-1 domain, Phase 5D-2 schemas, Phase 5D-3 API); no production defects were found, so no production code, ORM models, migrations, schemas, or dependencies were modified
- **Source-of-truth audit** — verified domain source (`app/core/body_weight_goals.py`, `app/core/body_weight_goal_exceptions.py`), schemas (`app/schemas/body_weight_goals.py`), the API route (`app/api/v1/body_weights.py`), authentication (`app/api/depenencies/authentication.py`), error envelope (`app/core/exceptions.py`), ORM metadata, and the Alembic history directly
- **Domain confirmed unchanged and correct** — `BodyWeightGoalDirection` (`decrease`/`maintain`/`increase`), `BodyWeightGoalStatus` (`not_started`/`in_progress`/`target_reached`/`target_passed`), frozen+slotted dataclasses, Decimal-only ROUND_HALF_UP arithmetic, no float arithmetic, no system clock, no framework/DB/network/IO imports; equal start/target raises the frozen `InvalidBodyWeightGoalProgressError`; no clamping/capping; negative/zero/exactly-100%/above-100% progress and negative remaining change all preserved
- **Schema confirmed unchanged and correct** — `extra="forbid"`, `frozen=True` for immutable data schemas; bool/NaN/Infinity rejected; signed fields preserved; percentages not capped; remaining values not clamped; domain enums reused and serialized lowercase; Decimal remains `Decimal` in Python and serializes as JSON strings; `BodyWeightGoalProgressData.from_result()` copies values exactly with no recalculation/rounding/redirection/reclassification/mutation; `BodyWeightGoalProgressSuccessResponse` is `success: Literal[True] = True`, exact default message `Body-weight goal progress calculated successfully.`, required `data`, `extra="forbid"`; no `user_id`/ORM id/timestamps exposed
- **API orchestration confirmed correct** — exactly one GET `/api/v1/body-weights/goal-progress` route, declared before `/{entry_id}`, no request body or weight/user/date params; auth via existing `get_current_user`; profile + history loaded via current-user-scoped repository/service; `starting_weight_kg` = `profile.weight_kg`, `target_weight_kg` = `profile.target_weight_kg`, `current_weight_kg` = `latest_entry.weight_kg` where `latest_entry = history[0]` (repository orders `logged_date desc, entry_id asc`); `calculate_body_weight_goal_progress(...)` called exactly once; `BodyWeightGoalProgressData.from_result(...)` called exactly once; no formula duplicated in the route
- **Error contract confirmed** — missing token/invalid/expired/unknown user → 401 (with `WWW-Authenticate: Bearer`); inactive user → 403; missing profile → 404 `NUTRITION_PROFILE_NOT_FOUND`; empty history → 422 `BODY_WEIGHT_GOAL_CURRENT_WEIGHT_NOT_FOUND`; equal start/target → 422 `BODY_WEIGHT_GOAL_PROGRESS_INVALID` (exact frozen message); unexpected → global 500 `INTERNAL_SERVER_ERROR` with `request_id` and `X-Request-ID`, no raw SQL/stack/secret exposure; authentication occurs before profile/history/calculation/conversion
- **Authorization/privacy/read-only/transaction confirmed** — `user_id` only from `current_user.id`; no cross-user leakage; no `user_id` in response; no mutation of user/profile/body-weight objects; never calls commit/rollback/flush/refresh/add/delete/merge; no persistence, no profile synchronization, no goal-progress ORM model/table/column
- **OpenAPI/ORM/migration confirmed** — goal-progress path documented (GET only, BearerAuth, no request body/params, correct 200 schema); exactly 1 BearerAuth; exactly 4 ORM tables (`users`, `nutrition_profiles`, `nutrition_logs`, `body_weights`); exactly 4 linear migration revisions, one base, head `e5f6a7b8c9d0`; no goal-progress/prediction/goal-date/time-to-goal column anywhere
- **Phase boundaries preserved** — no goal persistence, no goal dates, no time-to-goal estimates, no predictions, no recommendation, no diet/meal/exercise plans, no health/adherence scores, no medical interpretation/diagnosis/treatment, no AI/LLM/Groq/USDA/barcode/image, no frontend work
- **New tests** — `tests/test_phase_5d_final_audit.py` (32 tests) covering domain contracts, schema contracts, API route inventory, OpenAPI, ORM/migration integrity, application factory, and phase boundaries; these complement (do not duplicate) the existing dedicated domain/schema/API tests
- **Backend final verified test count:** **5450 passed** (5418 Phase 5D-3 baseline + 32 new Phase 5D-4 audit tests); ruff format and lint clean; exactly 4 ORM tables; exactly 4 Alembic revisions; migration head `e5f6a7b8c9d0`; exactly 1 BearerAuth scheme; only `.env.example` template exists — no real secrets; no production behavior changed; Phase 5D is frozen and ready for the next explicitly approved phase (no Phase 5E started)

### Phase 5E-1 — Pure Task Domain Foundation (backend)

- Pure, deterministic, framework-independent task-domain foundation added in the backend (`app/core/tasks.py`, `app/core/task_exceptions.py`); only Python standard library, `uuid`, `collections.abc`, and the task-exception module imported; no FastAPI/Starlette/Pydantic/SQLAlchemy/Alembic/database/repository/service/router/network/environment/system-clock/random/filesystem/AI dependencies
- **`TaskPriority` (StrEnum)** — `low`/`medium`/`high` (exactly three members, no numeric values); deterministic ordering `HIGH` → `MEDIUM` → `LOW` via an immutable mapping, not alphabetical enum ordering
- **`TaskStatus` (StrEnum)** — `pending`/`completed` (exactly two members; no in-progress/cancelled/archived/deleted)
- **`Task`** — `@dataclass(frozen=True, slots=True)` with exact field order `task_id: UUID`, `title: str`, `description: str | None`, `priority: TaskPriority`, `status: TaskStatus`, `due_date: date | None`, `completed_at: datetime | None`; `__post_init__` validation enforces all invariants (invalid `task_id`/title/description/priority/status/`due_date` rejected; datetime-as-due-date rejected; pending must have `completed_at is None`; completed must have `completed_at is not None`)
- **`create_task()`** — keyword-only factory returning an immutable `PENDING` task with `completed_at = None`; strips/validates title (internal spaces and case preserved, no truncation), normalizes description (empty/whitespace → `None`, internal line breaks preserved); caller owns all date/time semantics — no `date.today()` / `datetime.now()` / `datetime.utcnow()`
- **`complete_task()` / `reopen_task()`** — pure transformations returning new `Task` objects (exact caller-provided `completed_at` preserved, naive and timezone-aware datetimes unchanged, no timezone conversion, no system clock); raise `TaskAlreadyCompletedError` / `TaskNotCompletedError` appropriately; originals never mutated
- **`order_tasks()`** — accepts any `Iterable[Task]`, materializes exactly once, validates every member, returns a `tuple` (caller collections never mutated); deterministic order: pending before completed → due-date before undated → earlier due date before later → higher priority before lower → `title.casefold()` ascending → `task_id` ascending; uses a sentinel date, never the current date (no urgency/overdue inference)
- **Exception hierarchy** — `TaskError(Exception)` → `InvalidTaskError` (`Task data is invalid.`), `TaskAlreadyCompletedError` (`Task is already completed.`), `TaskNotCompletedError` (`Task is not completed.`); framework-independent, exact safe messages, no raw values
- No Pydantic schema, no ORM model, no migration, no repository, no service, no API endpoint, no `/tasks` route, no persistence, no reminders/recurrence/notifications/recommendations, no AI/LLM, no frontend work, no dependency added, no `.env` or real secret, nothing committed or pushed, no Phase 5E-2 work started
- Backend final verified test count: **5596 passed** (5450 Phase 5D verified baseline + 146 new Phase 5E-1 task tests); ruff format and lint clean; exactly 4 ORM tables; exactly 4 Alembic revisions (head e5f6a7b8c9d0); exactly 1 BearerAuth scheme; no real secrets. Phase 5D is frozen and unchanged; Phase 5E-1 is completed and ready for Phase 5E-2

### Phase 5E-2 — Task Schema Foundation (backend)

- Pydantic v2 schema foundation for tasks added in the backend (`app/schemas/tasks.py`), reusing the frozen Phase 5E-1 domain types (`TaskPriority`, `TaskStatus`, `Task`); no FastAPI/Starlette/SQLAlchemy/Alembic/database/repository/service/router/network/environment/system-clock/random/AI dependencies
- `TaskCreate` (input, `extra="forbid"`): `title: str`, `description: str | None = None`, `priority: TaskPriority = TaskPriority.MEDIUM`, `due_date: date | None = None`; title stripped + length/control/null-byte validated; description stripped + length/control validated (empty → `None`, line breaks preserved); `priority` reuses `TaskPriority` (bool/invalid rejected); `due_date` is date-only (datetime rejected, no system clock)
- `TaskData` (`extra="forbid", frozen=True, from_attributes=True`): the seven public fields in exact task order; enforces the pending/completed state invariant; `from_domain()` copies all seven fields exactly (no recalculation, no normalization, no status/priority/date change, no mutation); reuses `TaskPriority`/`TaskStatus`; no `user_id`/ORM id/timestamps/`_sa_instance_state`
- `TaskListData` (`extra="forbid", frozen=True`): `tasks: tuple[TaskData, ...]`; `from_domain()` accepts any `Iterable[Task]` (tuple/list/generator/iterator), preserves input order, delegates to `TaskData.from_domain()`, does not call `order_tasks()`, does not mutate caller collections
- Four success-response schemas plus `TaskDeleteSuccessResponse`: `TaskSuccessResponse` (`Task created successfully.`), `TaskListSuccessResponse` (`Tasks retrieved successfully.`), `TaskCompletionSuccessResponse` (`Task completed successfully.`), `TaskReopenSuccessResponse` (`Task reopened successfully.`); `TaskDeleteSuccessResponse` (`Task deleted successfully.`, no `data` field); all `success: Literal[True] = True`, `extra="forbid"`, required non-null `data` where specified
- Domain enums reused (no duplicates); `task_id` serializes as UUID string; `due_date` as ISO `YYYY-MM-DD`; `completed_at` as ISO datetime (offsets preserved); `priority`/`status` serialize lowercase
- `app/schemas/__init__.py` exports the eight new task schemas; existing exports unchanged; the Phase 5E-1 `test_no_task_schema_module` boundary test was updated narrowly to assert the task-schema module now exists
- No ORM model, no migration, no repository, no service, no API endpoint, no `/tasks` route, no persistence, no reminders/recurrence/notifications/recommendations, no AI/LLM, no frontend work, no dependency added
- Backend final verified test count: **5791 passed** (5596 Phase 5E-1 verified baseline + 195 new Phase 5E-2 schema tests); ruff format and lint clean; exactly 4 ORM tables; exactly 4 Alembic revisions (head e5f6a7b8c9d0); exactly 1 BearerAuth scheme; only `.env.example` template — no real secrets. Phase 5D is frozen and unchanged; Phase 5E-1 domain code was not modified; Phase 5E-2 is completed and ready for Phase 5E-3

### What does not exist yet (planned for later phases)

- Application database-backed endpoints
- Authentication endpoints, registration, login, or JWT issuance
- Repository, CRUD, or service layer
- Nutrition calculators, USDA integration, or AI features

## Local startup order

1. **PostgreSQL** — Start Docker PostgreSQL first:
   ```bash
   docker compose up -d postgres
   ```
2. **Backend** — Start the FastAPI server:
   ```powershell
   cd backend
   .venv\Scripts\Activate.ps1
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
3. **Frontend** — Start the Next.js dev server:
   ```powershell
   cd frontend
   npm run dev
   ```

The frontend connects to `http://localhost:8000/api/v1`. The health endpoint is at `GET http://localhost:8000/api/v1/health`.

## Windows Launcher

Two batch scripts at the project root provide one-click start and stop for the local development environment on Windows.

| Script       | Action                                              |
|-------------|-----------------------------------------------------|
| `start.bat` | Double-click to launch the full development stack   |
| `stop.bat`  | Double-click to stop everything gracefully          |

### start.bat

1. Verifies Python, Node.js, and npm are installed
2. Starts PostgreSQL via `docker compose up -d postgres` (skips gracefully if Docker is unavailable)
3. Opens a **NutriMind Backend** Command Prompt and runs `python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
4. Polls `http://localhost:8000/api/v1/health` every second (up to 30 attempts) to confirm the backend is ready
5. Opens a **NutriMind Frontend** Command Prompt and runs `npm run dev`
6. Opens `http://localhost:3000` in the default browser

### stop.bat

1. Closes the **NutriMind Backend** and **NutriMind Frontend** windows (targeted by title — other `cmd.exe` windows are unaffected)
2. Runs `docker compose down` to stop PostgreSQL (if Docker is running)

> Docker PostgreSQL is optional. The launchers continue normally when Docker is not available.

## Alembic migrations

```bash
cd backend
# Apply all pending migrations
alembic upgrade head
# Generate offline SQL (upgrade)
alembic upgrade head --sql
# Generate offline SQL (downgrade to base)
alembic downgrade head:base --sql
```

## Environment template usage

Each layer has its own `.env.example` template. Copy to `.env` (backend) or `.env.local` (frontend) and adjust:

```powershell
# Root environment (Docker Compose)
copy .env.example .env

# Backend environment
cd backend
copy .env.example .env

# Frontend environment
cd frontend
copy .env.example .env.local
```

## Troubleshooting

### CORS errors (frontend cannot reach backend)

Ensure `CORS_ORIGINS` in `backend/.env` includes the frontend origin:
```
CORS_ORIGINS=http://localhost:3000
```
Restart the backend after changing this value.

### Database connection failures

1. Verify PostgreSQL is running: `docker compose ps`
2. Check PostgreSQL readiness: `docker compose exec -T postgres pg_isready -U nutrimind -d nutrimind`
3. Verify `DATABASE_URL` in `backend/.env` matches the Docker Compose configuration
4. If using a non-standard port, update both `.env` and `docker-compose.yml`

### Migration errors

- **"Target database is not up to date"** — Run `alembic upgrade head`
- **"Can't locate revision identified by '...'"** — The migration chain may be corrupted; verify the revision IDs match the files in `alembic/versions/`
- **Offline SQL generation fails** — Ensure `DATABASE_URL` is set in the environment or `backend/.env`

### Frontend API URL issues

The frontend reads the backend URL from `NEXT_PUBLIC_API_URL` in `frontend/.env.local`. Default:
```
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```
Restart the frontend dev server after changing this value.

### Stale authentication tokens

If the backend is restarted, existing JWT tokens remain valid until their expiration (default 15 minutes). If authentication errors persist after a backend restart:
1. Log out and log back in to obtain a fresh token
2. Clear `localStorage` in the browser dev tools (Application → Local Storage → Clear All)

## Security

- **Never commit `.env` files or API keys to version control.**
- Use `.env.example` as a template and keep real secrets local.
- The provided `.gitignore` ignores `.env`, `.pem`, `.key`, and `secrets/`.

## Git and GitHub workflow

```bash
# Initialize the repository (only once)
git init
git branch -M main

# Stage everything and review
git add .
git status

# Create the initial commit
git commit -m "chore: initialize NutriMind AI project"

# Connect to your GitHub repository
git remote add origin <YOUR_GITHUB_REPOSITORY_URL>

# Push to GitHub
git push -u origin main
```

### Important notes

- Replace `<YOUR_GITHUB_REPOSITORY_URL>` with your actual GitHub repository URL.
- In GitHub Desktop, select the **root project folder** (`nutrimind-ai/`) — do **not** select `frontend/` or `backend/`.
- **Do not** initialise separate Git repositories inside `frontend/` or `backend/`. There must be only **one** repository at the project root.
- Run `git status` **before every commit** to verify only the intended files are staged.
- The following must **never** be committed:
  - Real `.env` files
  - `node_modules/` and similar dependency folders
  - Cache and build output (`.next/`, `__pycache__/`, `dist/`, etc.)
  - Local database files (`*.db`, `*.sqlite`, `postgres-data/`)
  - Log files (`*.log`)
  - Uploaded or temporary files (`uploads/`, `temp/`)
  - Machine-learning model files (`*.pkl`, `*.pt`, `*.onnx`, etc.)
