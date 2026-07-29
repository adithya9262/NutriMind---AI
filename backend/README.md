# NutriMind AI — Backend

FastAPI backend for the NutriMind AI nutrition and wellness companion.

## Current Phase — 6B-2: Full Local Stack Smoke Validation, Core User-Journey Verification, and Release Readiness (completed)

Phase 6B-2 performs a complete live-stack validation against a real local PostgreSQL database and running FastAPI/Next.js servers. All 71 live HTTP smoke tests pass, covering every core user journey. No production code was changed, no new ORM tables, migrations, endpoints, or routes were added.

### Phase 6B-2 smoke test results

- **71 live smoke tests passed**, 0 failed
- **CORS**: OPTIONS preflight returns correct origin `http://localhost:3000`, Authorization and Content-Type allowed
- **Registration**: 201 created, valid response envelope, access_token present, no password/password_hash exposed
- **Duplicate registration**: 409 `EMAIL_ALREADY_REGISTERED`
- **Login**: 200 with valid credentials; 401 with wrong password; 401 with unknown account
- **Auth errors**: 401 with missing token (`AUTHENTICATION_REQUIRED`); 401 with bad token (`INVALID_ACCESS_TOKEN`)
- **Current user**: `GET /auth/me` returns correct email for authenticated user
- **Nutrition profile**: 404 when missing, 201 on create, 200 on get (fields match), PATCH update persists
- **Calculations**: `GET /nutrition-profile/calculations` returns 200
- **Summary**: `GET /nutrition-profile/summary` returns 200
- **Nutrition logs**: 201 create, 200 list (entry present), 200 daily summary, 200 target progress, 200 delete (entry absent)
- **Body weight**: 201 create (2 entries), 422 trend with 1 entry only, 200 trend with 2 entries, 200 goal progress, 200 delete, empty history after cleanup
- **Tasks**: 201 create, 200 list, 200 get, 200 complete (status=completed), 200 reopen (status=pending), 200 delete, 404 after deletion
- **User isolation**: Account A cannot access B's tasks (404), cannot delete B's tasks (404)
- **Response privacy**: No `password_hash`, no `Traceback` exposed in any endpoint
- **Request ID**: `X-Request-ID` header present in all responses

### Local startup walkthrough

1. **PostgreSQL** — Ensure a local PostgreSQL instance is running on port 5432 with database `nutrimind` and user `nutrimind`.
2. **Backend** — `cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000`
3. **Frontend** — `cd frontend && npm run dev`
4. **Smoke test** — `cd backend && python run_smoke.py` (starts backend, runs 71 checks, stops backend)

### Verified architecture invariants

- 6358 backend tests passing, 0 failed
- Ruff format: 144 files formatted (clean)
- Ruff lint: clean
- `create_app()` succeeds; two calls return distinct instances
- OpenAPI generation succeeds with exactly 1 BearerAuth scheme
- Exactly 5 ORM tables: `users`, `nutrition_profiles`, `nutrition_logs`, `body_weights`, `tasks`
- Exactly 5 linear Alembic revisions (head `a7b8c9d0e5f`)
- No database connection during application import
- No automatic migration on startup
- Offline PostgreSQL upgrade SQL generated successfully
- Offline PostgreSQL downgrade SQL generated successfully
- No real `.env` committed, no real secrets/API keys
- No JWT/token values printed in documentation
- No hardcoded production backend URL

### Frontend regression (Phase 6B-2)

- 469 tests passing (53 files, 0 failures)
- TypeScript type-check: clean (0 errors)
- ESLint: clean (0 warnings or errors)
- Production build: successful (12 routes)

## Previous Phase — 6B-1: Final Full Regression, Integration Validation, Documentation, and Freeze (completed)

Phase 6B-1 performs the complete end-to-end regression of the entire backend and frontend, validates all architecture invariants, updates documentation, and freezes the combined Phase 6B baseline. No new features, ORM changes, migration changes, or dependencies were added.

### Phase 6B-1 regression results

- **Complete backend test suite**: 6358 passed, 0 failed, 3 warnings (PytestDeprecationWarning, InsecureKeyLengthWarning)
- **Expected count verification**: 6358 total (6336 previous frozen baseline + 22 new integration tests)
- **Ruff format**: 151 files already formatted (clean)
- **Ruff lint**: All checks passed
- **create_app()**: Succeeds; two independent calls return distinct applications
- **OpenAPI generation**: Succeeds; exactly 1 BearerAuth scheme
- **ORM tables**: Exactly 5 — `users`, `nutrition_profiles`, `nutrition_logs`, `body_weights`, `tasks`
- **Alembic revisions**: Exactly 5 linear revisions — `3f0c6eb4f49e` (base) → `99a3b19be1b8` → `b8a7c3d9e1f2` → `e5f6a7b8c9d0` → `a7b8c9d0e5f` (head)
- **Migration head**: `a7b8c9d0e5f`
- **No database connection during import**: Confirmed
- **No automatic migration**: Confirmed
- **Offline PostgreSQL upgrade SQL**: Generates successfully (all 5 migrations)
- **Offline PostgreSQL downgrade SQL**: Generates successfully (all 5 migrations in reverse)
- **No real .env files**: Only `.env.example` templates exist
- **No real secrets/API keys**: All values are placeholders
- **No JWT/token values printed in documentation**: Documentation references only describe token handling, never expose actual tokens
- **No hardcoded production backend URL**: All URLs reference localhost
- **No new dependencies**: Dependencies unchanged from Phase 5E-6

### Frontend regression (Phase 6B-1)

- **Frontend tests**: 469 passed (53 files, 0 failures)
- **TypeScript type-check**: Clean (0 errors)
- **ESLint**: No warnings or errors
- **Production build**: Successful (12 routes, static generation)
- **No new frontend dependencies**: Dependencies unchanged from Phase 6A-6

## Previous Phase — 5E-6: Task Management Final Audit, Hardening, and Freeze (completed)

Phase 5E-6 performs the final cross-layer audit, hardening validation, regression verification, documentation update, and freeze for the complete Phase 5E Task Management module. No new features were added.

- **Domain audit (app/core/tasks.py, app/core/task_exceptions.py)** — verified: `TaskPriority` enum exactly `low/medium/high`; `TaskStatus` enum exactly `pending/completed`; `Task` frozen+slotted dataclass with exact 7 public fields in exact order; UUID/title/description/due-date validation strict; state invariants (`PENDING`→`completed_at=None`, `COMPLETED`→`completed_at!=None`); `create_task`/`complete_task`/`reopen_task`/`order_tasks` pure, deterministic, no system-clock fallback; exception hierarchy `TaskError`→`InvalidTaskError`/`TaskAlreadyCompletedError`/`TaskNotCompletedError`/`TaskNotFoundError`/`DuplicateTaskIdError` with exact safe messages; zero framework/database/AI dependencies
- **Schema audit (app/schemas/tasks.py, app/schemas/__init__.py)** — verified: input schemas `extra="forbid"`; immutable schemas `frozen=True`; `from_attributes=True` only on `TaskData`; public `TaskData` exposes only 7 approved fields; no `user_id`, ORM `id`, `created_at`, `updated_at`, SQLAlchemy state exposed; `TaskPriority`/`TaskStatus` reuse domain enums; enum JSON values lowercase; `from_domain()` exact copy, no ordering/logic/clock; success responses use `Literal[True]` with stable default messages; no duplicate schema definitions
- **ORM audit (app/models/task.py, app/models/user.py, app/models/__init__.py)** — verified: `Task` registered once, `__tablename__="tasks"`; 11 exact columns; UUID PK strategy correct; `user_id` FK→`users.id` ON DELETE CASCADE; composite unique `(user_id, task_id)`; enum persistence lowercase; title/description lengths match domain; `due_date` SQL `Date`; `completed_at` `DateTime(timezone=True)`; check constraint `pending↔completed_at IS NULL` / `completed↔completed_at IS NOT NULL`; index `ix_tasks_user_id_status_due_date`; `User.tasks` back_populates symmetric, cascade `all, delete-orphan`; zero prohibited columns
- **Migration audit (alembic/versions/a7b8c9d0e5f_create_tasks.py)** — verified: exactly 5 revision files, 1 base (`3f0c6eb4f49e`), 1 head (`a7b8c9d0e5f`), linear chain, no branches/cycles; upgrade creates enums/table/constraints/FK/index; enum values lowercase; constraint names match convention; downgrade order: drop index → drop table → drop enums (no CASCADE); offline PostgreSQL upgrade/downgrade SQL generate successfully; no auto-migration on import/`create_app()`
- **Repository audit (app/repositories/task.py)** — verified: `AsyncSession` DI; all reads user-scoped; no `task_id`-only lookup; `create` receives `user_id` ownership explicitly; `delete` accepts verified ORM object; deterministic ordering delegated to frozen `order_tasks()`; flush-only (no commit/rollback/refresh); duplicate `uq_tasks_user_id_task_id` → `DuplicateTaskIdError`; unrelated `IntegrityError` propagates; no raw SQL/constraint leakage; no generic CRUD abstraction; zero cross-user leakage
- **Service audit (app/services/task.py)** — verified: framework-independent (no FastAPI/Starlette/HTTPException/SQLAlchemy/AsyncSession); no transaction ownership; delegates persistence to `TaskRepository`; delegates `create_task`/`complete_task`/`reopen_task`/`order_tasks` to frozen domain helpers; no duplicated validation/formulas; ownership via `user_id`; wrong-user→`TaskNotFoundError`; no mutation of original domain/ORM objects
- **API audit (app/api/v1/tasks.py, app/api/v1/router.py)** — verified: exactly 6 operations across 4 paths (`POST /tasks`, `GET /tasks`, `GET /tasks/{id}`, `POST /tasks/{id}/complete`, `POST /tasks/{id}/reopen`, `DELETE /tasks/{id}`); no duplicate router; single include; all endpoints use `get_current_user` + `get_db_session`; ownership from `current_user.id` only; no `user_id` in body/query/path/header; all require `BearerAuth` (exactly 1 scheme); static routes safe relative to `/{task_id}`; UUID path params typed; malformed UUID→422; schemas reused; no direct SQLAlchemy in routes; no manual status/completed_at mutation; no system-clock fallback; `completed_at` caller-supplied preserved; GET read-only; writes commit once after service success; expected failures roll back; commit failures handled; no unnecessary refresh/autocommit
- **Error contract audit** — verified stable codes/messages: `TaskNotFoundError`→404 `TASK_NOT_FOUND` "Task was not found."; `DuplicateTaskIdError`→409 `TASK_ID_ALREADY_EXISTS` "A task with this task ID already exists."; `TaskAlreadyCompletedError`→409 `TASK_ALREADY_COMPLETED` "Task is already completed."; `TaskNotCompletedError`→409 `TASK_NOT_COMPLETED` "Task is not completed."; `InvalidTaskError`→422 `INVALID_TASK` "Task data is invalid."; persistence→503 `TASK_PERSISTENCE_ERROR` "Task data could not be saved."; unexpected→500 `INTERNAL_SERVER_ERROR` "An unexpected error occurred."; `request_id` body + `X-Request-ID` header; no raw exception/SQL/constraint/table/stack/secret exposure; auth 401 retains `WWW-Authenticate: Bearer`; inactive→403
- **Auth/authorization audit** — verified: missing/malformed/invalid/expired/unknown/inactive token behaviors correct; auth before repository/service work; all ops scoped to `current_user.id`; wrong-user indistinguishable from missing; no cross-user list/get/complete/reopen/delete; no `user_id` injection
- **Response privacy audit** — verified: responses expose only `task_id, title, description, priority, status, due_date, completed_at`; zero forbidden fields
- **OpenAPI audit** — verified: all 6 ops + 4 paths; correct request/response schemas; UUID path format; `completed_at` datetime; `BearerAuth` on all ops; exactly 1 `BearerAuth` scheme; unique operation IDs; no duplicate task schemas; existing auth/nutrition/body-weight/trend/goal/health/root routes unchanged
- **Cross-layer invariant tests added** — `tests/test_phase_5e_final_audit.py` (106 tests) covering domain/schema/ORM constant/enum/field/length alignment; status/`completed_at` consistency; repository user-scoping + flush-only; service transaction independence; API transaction ownership; complete/reopen domain-helper reuse; ordering reuse; no system-clock fallback; exact route inventory; auth on all ops; no `user_id` input; response privacy; OpenAPI correctness; 1 BearerAuth; ORM table count/names; migration count/head/base/linearity; zero prohibited features; no `.env`/secrets; import/factory safety; no auto-migration
- **Regression verification** — all 6230 baseline tests pass (6117 Phase 5E-4 + 113 Phase 5E-5) + 106 new audit tests = 6336 total passed; ruff format/lint clean; Python 3.11.9, FastAPI 0.115.0, Pydantic 2.11.4, SQLAlchemy 2.0.36, Alembic 1.14.1, asyncpg 0.30.0; exactly 5 ORM tables, 5 migrations, head `a7b8c9d0e5f`, 1 `BearerAuth`
- **Phase 5E frozen** — confirmed no reminders, recurrence, notifications, categories, tags, subtasks, sharing, analytics, AI/LLM, external APIs, API keys, frontend work, new dependencies, new ORM tables/columns, new migrations, system-clock fallbacks; no `.env` or real secret added; nothing committed/pushed; next phase not started

- **Task endpoints inventory** — `POST /api/v1/tasks` (201), `GET /api/v1/tasks` (200), `GET /api/v1/tasks/{task_id}` (200/404), `POST /api/v1/tasks/{task_id}/complete` (200/404/409), `POST /api/v1/tasks/{task_id}/reopen` (200/404/409), `DELETE /api/v1/tasks/{task_id}` (200/404)
- **Architecture** — Domain (`app/core/tasks.py`) → Schema (`app/schemas/tasks.py`) → ORM (`app/models/task.py`) → Repository (`app/repositories/task.py`) → Service (`app/services/task.py`) → API (`app/api/v1/tasks.py`); each layer frozen and verified
- **Authentication & ownership** — `BearerAuth` on all 6 ops; `current_user.id` is the sole ownership source; no `user_id` in request data; wrong-user = 404
- **Transaction ownership** — API commits/rollbacks; repository flush-only; service transaction-free
- **Response privacy** — 7 public fields only; no internal IDs/timestamps/auth data
- **Error contract** — 7 stable error codes with safe messages, `request_id`/`X-Request-ID`, no SQL/secret exposure
- **ORM** — 5 tables: `users`, `nutrition_profiles`, `nutrition_logs`, `body_weights`, `tasks`
- **Migrations** — 5 linear revisions; head `a7b8c9d0e5f`; base `3f0c6eb4f49e`
- **Tests** — 6336 passed (6230 baseline + 106 new audit); 0 failed; 0 skipped (Phase 5E-6 baseline; Phase 6B-1 regression: 6358 passed)
- **Ruff** — format clean, lint clean
- **Phase 5E status** — **FROZEN**; ready for next explicitly approved phase

## Previous Phase — 5E-5: Authenticated Task CRUD API Endpoints (completed)

- **Router** — `app/api/v1/tasks.py`; `APIRouter(prefix="/tasks", tags=["Tasks"])`; included under `/api/v1` via `app/api/v1/router.py`; six authenticated endpoints:
  - `POST   /api/v1/tasks` — create (201); accepts `TaskCreate`; generates a new public `task_id` via `uuid.uuid4()` (schema/domain does not supply one); calls pure-domain `create_task()` then `TaskService.create_task()`; commits exactly once on success; rolls back on failure; returns `TaskSuccessResponse`
  - `GET    /api/v1/tasks` — list (200); user-scoped via `current_user.id`; calls `TaskService.list_tasks()`; preserves the frozen deterministic `order_tasks()` ordering; read-only (no commit/flush/refresh); returns `TaskListSuccessResponse`
  - `GET    /api/v1/tasks/{task_id}` — get by id (200/404); `task_id` is a UUID path parameter; user-scoped; wrong-user indistinguishable from missing; read-only; returns `TaskSuccessResponse`
  - `POST   /api/v1/tasks/{task_id}/complete` — complete (200/404/409); body `TaskCompleteRequest(completed_at: datetime)`; caller-supplied `completed_at` (no system clock); reuses frozen `TaskService.complete_task()` → `complete_task()` exactly once; commits once; preserves `TaskAlreadyCompletedError` (409 `TASK_ALREADY_COMPLETED`); returns `TaskCompletionSuccessResponse`
  - `POST   /api/v1/tasks/{task_id}/reopen` — reopen (200/404/409); no body; reuses frozen `TaskService.reopen_task()` → `reopen_task()` exactly once; commits once; preserves `TaskNotCompletedError` (409 `TASK_NOT_COMPLETED`); returns `TaskReopenSuccessResponse`
  - `DELETE /api/v1/tasks/{task_id}` — delete (200/404); user-scoped; commits once; returns `TaskDeleteSuccessResponse`
- **Authentication/authorization** — every endpoint requires the existing `BearerAuth` scheme via `get_current_user`; ownership derived exclusively from `current_user.id`; no `user_id` accepted in request body/query/path/header; authentication failures (missing/malformed/invalid/expired/unknown/inactive) match existing endpoint behavior
- **Transaction ownership** — API layer owns commits/rollbacks; repository is flush-only; service is transaction-free; read endpoints never commit/mutate; each successful write commits exactly once; no commit before service success; no hidden autocommit
- **Error mapping** — `TaskNotFoundError` → 404 `TASK_NOT_FOUND`; `DuplicateTaskIdError` → 409 `TASK_ID_ALREADY_EXISTS`; `TaskAlreadyCompletedError` → 409 `TASK_ALREADY_COMPLETED`; `TaskNotCompletedError` → 409 `TASK_NOT_COMPLETED`; `InvalidTaskError` → 422 `INVALID_TASK`; persistence failures → 503 `TASK_PERSISTENCE_ERROR`; unexpected → global 500 `INTERNAL_SERVER_ERROR`; no raw SQL/constraint/stack-trace/secret/ORM-id exposure; `request_id` in body and `X-Request-ID` header preserved
- **Response privacy** — public responses expose only the seven `TaskData` fields (`task_id`, `title`, `description`, `priority`, `status`, `due_date`, `completed_at`); no `user_id`, ORM `id`, `created_at`, `updated_at`, SQLAlchemy state, email, password hash, tokens
- **Route ordering** — static subpaths (`/complete`, `/reopen`) declared after the collection route; UUID path parameter typed as `UUID` so malformed UUIDs produce 422 validation (not 404/500); no path collisions
- **OpenAPI** — all six operations appear under `/api/v1/tasks`; every operation requires `BearerAuth`; UUID params use `format: uuid`; datetime request uses `format: date-time`; request/response schemas reference existing `Task*` components; exactly one `BearerAuth` security scheme remains; existing non-task routes unchanged
- **New test module** — `tests/test_task_api.py` (113 tests) covering: router registration + inventory (A), static-route ordering + path-collision safety (B), OpenAPI paths/methods/bodies/params/responses/operation-IDs/BearerAuth (C), authentication matrix (missing/malformed/invalid/expired/unknown/inactive × all six endpoints) (D), POST success (E), POST validation (F), duplicate task ID (G), GET list success (H), empty list (I), deterministic ordering preservation (J), GET-by-ID success (K), missing task (L), wrong-user isolation (M), complete success (N), already-completed error (O), caller-supplied `completed_at` preservation (P), no system-clock fallback (Q), reopen success (R), reopen-pending error (S), DELETE success (T), DELETE missing/wrong-user (U), exact commit counts (V), no commit/flush/refresh on reads (W), rollback on expected write failures (X), unexpected-error handling (Y), request-ID preservation (Z), safe error messages (AA), response privacy (AB), no `user_id` request parameter (AC), repository/service reuse (AD), no route-level ordering/complete/reopen duplication (AE), existing regressions (AF), phase-boundary enforcement (AG)
- **Updated phase-boundary tests** — `tests/test_tasks.py`, `tests/test_task_schemas.py`, `tests/test_task_service.py` now assert the task API router exists and task routes appear in OpenAPI; `test_existing_route_inventory_unchanged` in `test_body_weight_schemas.py`, `test_body_weight_goal_schemas.py`, `test_task_schemas.py` updated to include the four new task paths
- **ORM/migration integrity unchanged** — exactly 5 ORM tables (`users`, `nutrition_profiles`, `nutrition_logs`, `body_weights`, `tasks`); exactly 5 linear migration revisions (head `a7b8c9d0e5f`); exactly 1 `BearerAuth` OpenAPI scheme; no `.env` or real secrets; nothing committed/pushed
- **No prohibited scope** — no reminders, no recurrence, no notifications, no categories, no tags, no subtasks, no sharing, no AI/LLM prioritization/recommendations, no external APIs, no API keys, no new ORM table/column, no new migration, no system-clock fallback
- **Backend final verified test count:** **6230 passed** (6117 Phase 5E-4 verified baseline + 113 new Phase 5E-5 API tests); ruff format and lint clean; Python 3.11.9, FastAPI 0.115.0, Pydantic 2.11.4, SQLAlchemy 2.0.36, Alembic 1.14.1, asyncpg 0.30.0; exactly 5 ORM tables, 5 migration revisions, head a7b8c9d0e5f, exactly 1 BearerAuth scheme; Phase 5E-5 completed and ready for the next explicitly approved phase (Phase 5E-6)

- **New TaskRepository** — `app/repositories/task.py`; class `TaskRepository(session: AsyncSession)`; constructor stores the injected `AsyncSession` and performs no database work; follows the audited repository conventions (`_is_unique_constraint_violation` helper, `select` style, `scalars().all()` / `one_or_none()` extraction, flush-only, no commit/rollback/refresh)
- **Repository user-scoping** — every lookup is user-scoped: `list_by_user_id(*, user_id)` filters `WHERE user_id == user_id`; `get_by_user_and_task_id(*, user_id, task_id)` filters `WHERE user_id == user_id AND task_id == task_id`; no `get_by_task_id` and no task_id-only query exists; cross-user tasks are never exposed
- **Repository `create(*, user_id, task: DomainTask)`** — receives user ownership separately, maps all seven domain fields (`task_id`, `title`, `description`, `priority`, `status`, `due_date`, `completed_at`) and `user_id` exactly to the ORM `Task`; never generates a new public `task_id` (caller/domain-owned), never sets the ORM `id` manually; `add()` then `flush()`; returns the created ORM object; no commit/rollback/refresh
- **Composite duplicate translation** — on `IntegrityError` caused specifically by `uq_tasks_user_id_task_id`, translates to `DuplicateTaskIdError` ("A task with this task ID already exists.") preserving exception chaining; unrelated `IntegrityError` and non-`IntegrityError` propagate unchanged; no SQL/constraint name/user ID/task ID leaked in the public message
- **Repository `update(*, task)` and `delete(*, task)`** — `update` flushes a previously loaded tracked ORM object once and returns it; `delete` deletes the exact supplied loaded ORM object (no unscoped second lookup) then flushes; both are flush-only with no commit/rollback/refresh/refresh
- **New TaskService** — `app/services/task.py`; class `TaskService(repository: TaskRepository)`; constructor stores the injected repository and performs no side effects; framework-independent (no FastAPI/Starlette/HTTPException/status codes), database-framework-independent (no SQLAlchemy/AsyncSession/`app.db` import, no `session.add`/`session.delete`/`commit`/`rollback`/`flush`/`refresh` text), and transaction-free
- **Service list/get** — `list_tasks(*, user_id)` delegates to the repository exactly once, converts ORM rows to domain `Task` objects via a private `_orm_to_domain` helper, and applies the frozen `order_tasks()` exactly once (no duplicated ordering/CASE formula, no system clock); `get_task(*, user_id, task_id)` delegates the user-scoped lookup exactly once and raises `TaskNotFoundError` ("Task was not found.") when absent or not owned; wrong-user behaves as not found
- **Service create/complete/reopen/delete** — `create_task(*, user_id, task: DomainTask)` delegates persistence exactly once, preserving exact frozen domain values (no revalidation, no mutation); `complete_task(*, user_id, task_id, completed_at)` and `reopen_task(*, user_id, task_id)` load via both IDs, raise `TaskNotFoundError` if absent, convert the ORM row to a domain `Task`, call the frozen `complete_task()` / `reopen_task()` exactly once (preserving caller-provided `completed_at`, no system-clock fallback), apply only `status`/`completed_at` from the returned domain object to the tracked ORM row, and persist through `repository.update`; the frozen `TaskAlreadyCompletedError` / `TaskNotCompletedError` propagate unchanged; `delete_task(*, user_id, task_id)` loads via both IDs, raises `TaskNotFoundError` if absent, and passes the loaded ORM object to `repository.delete` (never deletes by `task_id` alone)
- **New exceptions** — `app/core/task_exceptions.py` gains `TaskNotFoundError` (`default_message = "Task was not found."`) and `DuplicateTaskIdError` (`default_message = "A task with this task ID already exists."`); both under `TaskError`; existing `TaskError`/`InvalidTaskError`/`TaskAlreadyCompletedError`/`TaskNotCompletedError` unchanged; framework-independent messages with no SQL/constraint name/database detail/user ID/task ID/stack trace/HTTP status/FastAPI/Starlette/SQLAlchemy/Pydantic content
- **Package exports** — `app/repositories/__init__.py` now exports `TaskRepository`; `app/services/__init__.py` now exports `TaskService`; existing exports unchanged
- **New tests** — `tests/test_task_repository.py` (comprehensive: module/exports, constructor, user-scoped list/get, create field mapping + caller-owned `task_id` + no manual `id` + flush, duplicate `uq_tasks_user_id_task_id` translation with safe message and chaining, unrelated `IntegrityError`/non-`IntegrityError` propagation, delete of exact object, update flush, source boundaries) and `tests/test_task_service.py` (comprehensive: module/exports, constructor, list delegation + frozen `order_tasks` once + exact ordering, get delegation + `TaskNotFoundError`, create delegation, complete/reopen reuse of frozen domain functions + caller `completed_at` + only state fields mutated + `TaskAlreadyCompletedError`/`TaskNotCompletedError` propagation, delete ownership enforcement, framework/transaction independence, purity); existing boundary tests `test_no_task_repository` / `test_no_task_service` in `tests/test_tasks.py` and `tests/test_task_schemas.py` were flipped to assert the repository and service now exist
- **ORM/migration/route integrity unchanged** — exactly 5 ORM tables (`users`, `nutrition_profiles`, `nutrition_logs`, `body_weights`, `tasks`), exactly 5 linear migration revisions (head `a7b8c9d0e5f`), exactly 1 BearerAuth OpenAPI scheme, no `/tasks` route, no task API router
- **No prohibited scope** — no task API router, no `/tasks` endpoint, no request handlers, no application API transaction ownership, no frontend task UI, no reminders, no recurrence, no notifications, no categories, no tags, no subtasks, no sharing, no AI prioritization, no recommendations, no external APIs, no API keys, no new ORM model, no ORM changes, no migration changes, no dependency changes
- **Phase 5E-1 domain, Phase 5E-2 schemas, Phase 5E-3 ORM/migration were not modified**; the repository and service import and reuse the frozen task-domain contracts
- **Backend final verified test count:** **6117 passed** (5955 Phase 5E-3 verified baseline + 162 new Phase 5E-4 repository/service tests); ruff format and lint clean; Python 3.11.9, FastAPI 0.115.0, Pydantic 2.11.4, SQLAlchemy 2.0.36, Alembic 1.14.1, asyncpg 0.30.0; exactly 5 ORM tables, 5 migration revisions, head a7b8c9d0e5f, exactly 1 BearerAuth scheme; no `.env` or real secret; nothing committed or pushed; Phase 5E-4 is completed and ready for the next explicitly approved phase (Phase 5E-5)

## Previous Phase — 5E-3: Task ORM Model and Migration Foundation (completed)

Task ORM model and Alembic migration foundation added in the backend (no repository, no service, no API endpoint, no persistence layer, no frontend). Reuses the frozen Phase 5E-1 domain enums (`TaskPriority` `low`/`medium`/`high`, `TaskStatus` `pending`/`completed`) and the frozen Phase 5E-2 response schemas. The `tasks` table is now registered in `Base.metadata`; no application-layer persistence, no `/tasks` route, and no reminder/recurrence/notification/category/tag/AI features were added.

- **New Task ORM model** — `app/models/task.py`; SQLAlchemy 2.0 declarative model `Task(Base, TimestampMixin)` with table `tasks`; reuses the repository's exact `Base` (`app.db.base`) and `TimestampMixin` conventions; imports only SQLAlchemy, the frozen Phase 5E-1 domain enums/constants, and `app.db.base`/`app.models.mixins`; no repository/service/router/API/FastAPI/Starlette/Pydantic-specific/Alembic/AI dependencies
- **Columns** — `id` (UUID PK, application-generated `uuid.uuid4()` default, non-null, not exposed by `TaskData`), `user_id` (UUID FK → `users.id`, ON DELETE CASCADE, non-null, never caller-controlled through future public task schemas), `task_id` (UUID, caller-owned public identifier, non-null, no automatic default, not the database PK, unique only within a user's ownership scope), `title` (String(200) non-null, reuses `MAX_TASK_TITLE_LENGTH`), `description` (String(2000) nullable, reuses `MAX_TASK_DESCRIPTION_LENGTH`), `priority` (PostgreSQL native enum `task_priority` persisting `low`/`medium`/`high`, non-null, `values_callable` returns `.value`), `status` (PostgreSQL native enum `task_status` persisting `pending`/`completed`, non-null), `due_date` (SQL `Date`, nullable, no default, no server default; past/current/future accepted), `completed_at` (DateTime(timezone=True), nullable, no default, no server default — never auto-populated), plus inherited `created_at`/`updated_at` from `TimestampMixin`; no extra columns
- **Composite uniqueness** — named `uq_tasks_user_id_task_id` enforces `(user_id, task_id)` unique; different users may reuse the same caller-owned `task_id`; no global `task_id` uniqueness
- **State consistency check** — named `ck_tasks_status_completed_at_consistency` enforces `(status = 'pending' AND completed_at IS NULL) OR (status = 'completed' AND completed_at IS NOT NULL)`; no overdue / due-date-versus-current-date / due-date-versus-completed-at / current-time / system-clock-dependent checks
- **Lookup index** — named non-unique composite `ix_tasks_user_id_status_due_date` on `(user_id, status, due_date)`; no redundant standalone `user_id` index, no redundant `task_id` index (the composite unique already provides the access path), and no indexes on `title`/`description`/`priority`-alone/`completed_at`/`created_at`/`updated_at`
- **Relationships** — `User.tasks: Mapped[list[Task]]` (one-to-many, `back_populates="user"`, `cascade="all, delete-orphan"`) added to `app/models/user.py`; `Task.user: Mapped[User]` (many-to-one, `back_populates="tasks"`); symmetric; existing `User` relationships (`nutrition_profile`, `nutrition_logs`, `body_weights`) unchanged; no relationships to NutritionProfile/NutritionLog/BodyWeight/reminder/AI entities
- **Model registration** — `app/models/__init__.py` now exports `Task`; importing `app.models` registers `tasks` in `Base.metadata`; existing model imports unchanged; exactly one `Task` ORM implementation
- **New Alembic migration** — `alembic/versions/a7b8c9d0e5f_create_tasks.py`; `down_revision = "e5f6a7b8c9d0"`; creates the `task_priority` and `task_status` PostgreSQL enums, the `tasks` table with exactly the eleven columns, the named FK (ON DELETE CASCADE), the composite unique constraint, the state-consistency check, and the composite lookup index; downgrade drops the index, drops the table, then drops `task_status` and `task_priority` enums (after the table, no CASCADE); existing migration files unmodified; enums created exactly once (no duplicate enum creation), offline PostgreSQL SQL generation succeeds
- **Exactly 5 ORM tables** — `users`, `nutrition_profiles`, `nutrition_logs`, `body_weights`, `tasks`; exactly 5 linear migration revisions; exactly one base (`3f0c6eb4f49e`) and one head (`a7b8c9d0e5f`); no branches/cycles; exactly 1 BearerAuth OpenAPI scheme; no `/tasks` route
- **No prohibited scope** — no TaskRepository, no TaskService, no task API router, no `/tasks` endpoint, no task values persisted by application services, no reminders, no recurrence, no notifications, no categories, no tags, no AI prioritization, no recommendations, no external APIs, no API keys, no frontend work
- **Phase 5E-1 domain code was not modified; Phase 5E-2 schema code was not modified; the schemas import and reuse the frozen task-domain contracts**
- **Backend final verified test count:** **5955 passed** (5791 Phase 5E-2 verified baseline + 164 new Phase 5E-3 model/migration tests); ruff format and lint clean; Python 3.11.9, FastAPI 0.115.0, Pydantic 2.11.4, SQLAlchemy 2.0.36, Alembic 1.14.1, asyncpg 0.30.0; exactly 5 ORM tables, 5 migration revisions, head a7b8c9d0e5f, exactly 1 BearerAuth scheme; no `.env` or real secret; nothing committed or pushed; Phase 5E-3 is completed and ready for the next explicitly approved phase (Phase 5E-4)

## Previous Phase — 5E-2: Task Schema Foundation (completed)

- **New strict schema module** — `app/schemas/tasks.py`; Pydantic v2, framework-independent, imports only Python standard library, Pydantic, and the frozen Phase 5E-1 domain types/constants; no FastAPI/Starlette/SQLAlchemy/Alembic/database/repository/service/router/network/environment/system-clock/random/IO dependencies
- **`TaskCreate`** — input schema (`ConfigDict(extra="forbid")`, not frozen — `NutritionProfileCreate` is also unfrozen, so the create-schema class is not uniformly frozen in this codebase) with `title: str`, `description: str | None = None`, `priority: TaskPriority = TaskPriority.MEDIUM`, `due_date: date | None = None`; title is stripped and length-validated against `MIN_TASK_TITLE_LENGTH`/`MAX_TASK_TITLE_LENGTH` (empty/whitespace-only/null-byte/control-character rejected, internal spaces and case preserved, no truncation); description is stripped and length-validated against `MAX_TASK_DESCRIPTION_LENGTH` (empty/whitespace-only → `None`, internal line breaks preserved, null bytes and control characters rejected); `priority` reuses `TaskPriority` (default `MEDIUM`, invalid values and booleans rejected); `due_date` reuses the domain `date`-only rule (datetime rejected, no system-clock fallback); no `date.today()` / `datetime.now()` / `datetime.utcnow()`
- **`TaskData`** — immutable public response schema (`ConfigDict(extra="forbid", frozen=True, from_attributes=True)`) with the seven public fields in exact task order (`task_id`, `title`, `description`, `priority`, `status`, `due_date`, `completed_at`); strict validation enforces the task-state invariant (a `PENDING` task must have `completed_at is None`; a `COMPLETED` task must have `completed_at is not None`); reuses `TaskPriority` and `TaskStatus`; `from_domain()` copies all seven values exactly with no recalculation, no normalization beyond schema validation, no status/priority/date change, no timezone conversion, no generated values, no system-clock usage, and no mutation of the domain `Task`; deterministic
- **`TaskListData`** — immutable collection schema (`ConfigDict(extra="forbid", frozen=True)`) with `tasks: tuple[TaskData, ...]`; `from_domain()` accepts any `Iterable[Task]` (tuple/list/generator/iterator), delegates to `TaskData.from_domain()` for every task, preserves input order exactly, and does not call `order_tasks()` or mutate caller-owned collections; empty list is valid
- **Success-response schemas** — `TaskSuccessResponse` (default message `"Task created successfully."`), `TaskListSuccessResponse` (`"Tasks retrieved successfully."`), `TaskDeleteSuccessResponse` (`"Task deleted successfully."`, no `data` field), `TaskCompletionSuccessResponse` (`"Task completed successfully."`), `TaskReopenSuccessResponse` (`"Task reopened successfully."`); all use `success: Literal[True] = True`, `extra="forbid"`, required non-null `data` where specified, and reject `False`/`null`/`extra` fields
- **Enum/serialization reuse** — `TaskPriority` (`low`/`medium`/`high`) and `TaskStatus` (`pending`/`completed`) reused directly (no duplicate enums); serialize as lowercase domain values; `task_id` serializes as a standard UUID string; `due_date` serializes as ISO `YYYY-MM-DD`; `completed_at` serializes as an ISO datetime (naive datetimes unchanged, timezone-aware offsets preserved); no `user_id`, ORM id, `created_at`, `updated_at`, or `_sa_instance_state` exposed
- **Schema package exports** — `app/schemas/__init__.py` now exports `TaskCreate`, `TaskData`, `TaskListData`, `TaskSuccessResponse`, `TaskListSuccessResponse`, `TaskDeleteSuccessResponse`, `TaskCompletionSuccessResponse`, `TaskReopenSuccessResponse`; existing exports unchanged
- **Domain/schema dependency direction** — schema layer imports domain types; domain layer (`app/core/tasks.py`) remains Pydantic-independent and does not import the schema layer; no circular dependency
- **`test_tasks.py` Phase-5E-1 boundary test updated narrowly** — the old `test_no_task_schema_module` (which asserted no task schema existed) now asserts the expected task-schema module exists and is exported; no other 5E-1 behavior changed
- **195 new deterministic tests** — `tests/test_task_schemas.py` covering module/exports, `TaskCreate` (field set/order/config, title/description strip/normalize/length/control/null-byte rejection, priority enum + bool rejection, due-date date-only + datetime rejection, no system-clock), `TaskData` (seven-field set/order/config, frozen, from_attributes, pending/completed invariant, enum reuse/rejection, privacy/exclusion), `from_domain()` exact-copy/no-recalculation/no-mutation/determinism, `TaskListData` (required/non-null/empty/tuple-storage/nested-frozen/extra-rejection) and `from_domain()` (tuple/list/generator/iterator, order preservation, no `order_tasks()` call, no caller mutation), all five success responses (exact fields, `Literal[True]`, exact default messages, custom message, required/non-null `data`, `TaskDelete` has no `data` and rejects it, extra-field rejection), serialization (UUID/ISO-date/ISO-datetime/offset-preservation/lowercase enums/no internal fields), schema purity (no FastAPI/Starlette/SQLAlchemy/Alembic/database/repository/service/network/environment/system-clock/random/AI), dependency direction, and phase-boundary regression (no ORM/repository/service/router/migration/`/tasks` route, unchanged route inventory, unchanged ORM metadata, 4 migrations, head `e5f6a7b8c9d0`, one BearerAuth scheme)
- **No prohibited scope** — no Task ORM model, no migration, no repository, no service, no API endpoint, no `/tasks` route, no persistence, no reminders, no recurrence, no notifications, no recommendation, no AI/LLM, no frontend work, no dependency added, no `.env` or real secret added, nothing committed or pushed, no Phase 5E-3 work started
- **ORM/migration/route integrity unchanged** — exactly 4 ORM tables (`users`, `nutrition_profiles`, `nutrition_logs`, `body_weights`), exactly 4 linear migration revisions (head `e5f6a7b8c9d0`), exactly 1 BearerAuth OpenAPI scheme, no `/tasks` route
- **Phase 5E-1 domain code was not modified**; the schemas import and reuse the frozen task-domain contracts
- **Backend final verified test count:** **5791 passed** (5596 Phase 5E-1 verified baseline + 195 new Phase 5E-2 schema tests); ruff format and lint clean; Python 3.11.9, FastAPI 0.115.0, Pydantic 2.11.4, SQLAlchemy 2.0.36, Alembic 1.14.1, asyncpg 0.30.0; exactly 4 ORM tables, 4 migration revisions, head e5f6a7b8c9d0, exactly 1 BearerAuth scheme; no `.env` or real secret; nothing committed or pushed; Phase 5E-2 is completed and ready for the next explicitly approved phase (Phase 5E-3)

## Previous Phase — 5E-1: Pure Task Domain Foundation (completed)

Pure, deterministic, framework-independent task-domain foundation added in the backend. No Pydantic schemas, no ORM models, no Alembic migrations, no repositories, no services, no API endpoints, no persistence, no frontend work, no AI/LLM.

- **New pure domain modules** — `app/core/tasks.py` and `app/core/task_exceptions.py`; only Python standard library, `uuid`, `collections.abc`, and the task-exception module imported; no FastAPI/Starlette/Pydantic/SQLAlchemy/Alembic/database/repository/service/router/network/environment/system-clock/random/filesystem/AI dependencies
- **Validation constants** — `MIN_TASK_TITLE_LENGTH = 1`, `MAX_TASK_TITLE_LENGTH = 200`, `MAX_TASK_DESCRIPTION_LENGTH = 2000`; reused everywhere in the module (no duplicated hardcoded limits)
- **`TaskPriority` (StrEnum)** — `LOW = "low"`, `MEDIUM = "medium"`, `HIGH = "high"`; exactly three members; no numeric values; deterministic priority ordering (`HIGH` → `MEDIUM` → `LOW`) via an immutable `MappingProxyType` mapping, never relying on alphabetical enum ordering
- **`TaskStatus` (StrEnum)** — `PENDING = "pending"`, `COMPLETED = "completed"`; exactly two members; no in-progress/cancelled/archived/deleted states
- **`Task`** — `@dataclass(frozen=True, slots=True)` with exact field order `task_id: UUID`, `title: str`, `description: str | None`, `priority: TaskPriority`, `status: TaskStatus`, `due_date: date | None`, `completed_at: datetime | None`; no `user_id`, ORM id, timestamps, reminders, recurrence, category, tags, or nutrition/body-weight links; `__post_init__` validation rejects invalid `task_id`/title/description/priority/status/`due_date`; datetime supplied as a due date is rejected even though `datetime` subclasses `date`; `completed_at` type validated; invariants enforced (a `PENDING` task must have `completed_at is None`; a `COMPLETED` task must have `completed_at is not None`)
- **`create_task(*, task_id, title, description, priority, due_date)`** — keyword-only factory returning an immutable `PENDING` task with `completed_at = None`; strips and validates the title (internal spaces and case preserved, no truncation, no case change); normalizes the description (empty/whitespace-only becomes `None`, internal line breaks preserved, no truncation); caller owns all date semantics — `date.today()` / `datetime.now()` / `datetime.utcnow()` are never called
- **`complete_task(*, task, completed_at)`** — pure transformation returning a new `Task` with `status = COMPLETED` and the exact caller-provided `completed_at` (naive and timezone-aware datetimes preserved exactly, no timezone conversion, no system clock); raises `TaskAlreadyCompletedError` if already completed; the original task is never mutated
- **`reopen_task(*, task)`** — pure transformation returning a new `PENDING` task with `completed_at = None`; raises `TaskNotCompletedError` if not completed; original unchanged
- **`order_tasks(*, tasks)`** — accepts any `Iterable[Task]` (tuple/list/generator/iterator), materializes exactly once, validates every member, and returns a `tuple` (never mutates caller-owned collections); deterministic order: pending before completed → due-date before undated → earlier due date before later → higher priority before lower (`HIGH`, `MEDIUM`, `LOW`) → `title.casefold()` ascending → `task_id` ascending as the final tie-breaker; uses a sentinel date (not the current date) so no urgency/overdue inference occurs
- **Exception hierarchy** — `TaskError(Exception)` → `InvalidTaskError` (`default_message = "Task data is invalid."`), `TaskAlreadyCompletedError` (`default_message = "Task is already completed."`), `TaskNotCompletedError` (`default_message = "Task is not completed."`); framework-independent (no FastAPI/Starlette/Pydantic/SQLAlchemy/Alembic/HTTP-status/session imports); exact safe messages with no raw title/description/UUID/date/internal data; `str(exc)` equals the exact public message
- **146 new deterministic tests** — `tests/test_task_exceptions.py` (32: hierarchy, exact messages, safe no-raw-value messages, default-message attribute, framework/database independence) and `tests/test_tasks.py` (114: constants, enums, dataclass structure/frozen/slots/order/equality/hashability, direct construction valid/invalid, `create_task`, `complete_task`, `reopen_task`, `order_tasks` across tuple/list/generator/iterator/materialization/input-immutability/every ordering rule/tie-breakers/determinism, domain purity, phase-boundary regression); all high-value invariants not already protected elsewhere
- **No prohibited scope** — no Pydantic schema, no ORM model, no migration, no repository, no service, no API endpoint, no `/tasks` route, no persistence, no reminders, no recurrence, no notifications, no recommendation, no AI/LLM, no frontend work, no dependency added, no `.env` or real secret added, nothing committed or pushed, no Phase 5E-2 work started
- **ORM/migration/route integrity unchanged** — exactly 4 ORM tables (`users`, `nutrition_profiles`, `nutrition_logs`, `body_weights`), exactly 4 linear migration revisions (head `e5f6a7b8c9d0`), exactly 1 BearerAuth OpenAPI scheme, no `/tasks` route
- **Phase 5D remains frozen and unchanged**; the new task domain is a separate, independent pure module
- **Backend final verified test count:** **5596 passed** (5450 Phase 5D verified baseline + 146 new Phase 5E-1 task tests); ruff format and lint clean; Python 3.11.9, FastAPI 0.115.0, Pydantic 2.11.4, SQLAlchemy 2.0.36, Alembic 1.14.1, asyncpg 0.30.0; exactly 4 ORM tables, 4 migration revisions, head e5f6a7b8c9d0, exactly 1 BearerAuth scheme; no `.env` or real secret; nothing committed or pushed; Phase 5E-1 is completed and ready for the next explicitly approved phase (Phase 5E-2)

## Previous Phase — 5D-3: Authenticated Body-Weight Goal Progress API (completed)

One authenticated, read-only endpoint `GET /api/v1/body-weights/goal-progress` that orchestrates the existing NutritionProfile and BodyWeight foundations to compute body-weight goal progress, reusing the frozen Phase 5D-1 domain calculation and the frozen Phase 5D-2 response schema. No new ORM model, no migration, no repository/service, no persistence, no profile synchronization.

All 5418 tests pass (5327 Phase 5D-2 verified baseline + 91 new Phase 5D-3 API tests).
Ruff format and lint pass.
No production defects found. No dependency changes. No ORM/migration changes. No new layers introduced.
Phase 5D-1 is frozen and unchanged. Phase 5D-2 is completed and unchanged. Phase 5D-3 is completed and unchanged.

### Phase 5D-2 highlights

- **New strict schema module** — `app/schemas/body_weight_goals.py`; Pydantic v2, framework-independent, imports only Python standard library, Pydantic, existing body-weight constants, and the frozen Phase 5D-1 domain types (`BodyWeightGoalDirection`, `BodyWeightGoalStatus`, `BodyWeightGoal`, `BodyWeightGoalProgressResult`); no FastAPI/Starlette/SQLAlchemy/Alembic/database/repository/service/router/network/environment/system-clock/random/IO dependencies
- **`BodyWeightGoalCreate`** — input schema (`ConfigDict(extra="forbid", frozen=True)`) with `starting_weight_kg` and `target_weight_kg`; accepts `Decimal`, `int`, finite `float`, and numeric string; rejects bool/None/empty string/whitespace-only string/malformed string/NaN/Infinity/negative Infinity; quantizes with `BODY_WEIGHT_DECIMAL_PLACES` using `ROUND_HALF_UP`, then validates against `MIN_BODY_WEIGHT_KG`/`MAX_BODY_WEIGHT_KG` (boundary validation after rounding); Decimal preserved in Python and serialized as JSON strings; equal start/target accepted (MAINTAIN goal supported); no direction/progress/remaining/percentage/status calculated
- **`BodyWeightGoalData`** — immutable response schema (`ConfigDict(extra="forbid", frozen=True)`) with `starting_weight_kg`, `target_weight_kg`, `direction: BodyWeightGoalDirection`; strict validation: weights finite and within the body-weight range (rejects bool/NaN/Infinity/non-finite/null and out-of-range); reuses the existing `BodyWeightGoalDirection` enum (no duplicate); `from_domain()` copies all three values exactly with no arithmetic, no rounding, no direction reclassification, no mutation of the domain object; deterministic
- **`BodyWeightGoalProgressData`** — immutable response schema (`ConfigDict(extra="forbid", frozen=True)`) with the nine fields in domain order: `starting_weight_kg`, `current_weight_kg`, `target_weight_kg`, `direction`, `total_change_required_kg`, `change_achieved_kg`, `remaining_change_kg`, `progress_percentage`, `status`; weights must be finite, positive, and within `MIN..MAX`; `total_change_required_kg` must be strictly greater than zero; `change_achieved_kg`, `remaining_change_kg`, and `progress_percentage` accept signed values; negative progress, zero progress, exactly 100%, above-100%, and negative remaining change are all preserved without capping or clamping; reuses `BodyWeightGoalDirection` and `BodyWeightGoalStatus` enums; `from_result()` copies all nine values exactly with no arithmetic, no rounding, no clamping, no capping, no direction reclassification, no status reclassification, no mutation of the domain result; deterministic
- **`BodyWeightGoalSuccessResponse`** — success envelope with `success: Literal[True] = True`, default message `"Body-weight goal created successfully."`, and required non-null `data: BodyWeightGoalData`; `extra="forbid"`; not frozen (follows existing project convention)
- **`BodyWeightGoalProgressSuccessResponse`** — success envelope with `success: Literal[True] = True`, default message `"Body-weight goal progress calculated successfully."`, and required non-null `data: BodyWeightGoalProgressData`; `extra="forbid"`; not frozen
- **Enum reuse and serialization** — `BodyWeightGoalDirection` and `BodyWeightGoalStatus` reused directly (no duplicate enums); serialize as lowercase domain values (`decrease`/`maintain`/`increase`, `not_started`/`in_progress`/`target_reached`/`target_passed`)
- **Decimal preservation** — all Decimal values remain `Decimal` in Python; serialize as JSON strings (no float conversion); negative, zero, and above-100 values preserved exactly
- **Schema package exports** — `app/schemas/__init__.py` now exports `BodyWeightGoalCreate`, `BodyWeightGoalData`, `BodyWeightGoalProgressData`, `BodyWeightGoalSuccessResponse`, `BodyWeightGoalProgressSuccessResponse`; existing exports unchanged
- **Domain/schema dependency direction** — schema layer imports domain types; domain layer (`app/core/body_weight_goals.py`) remains Pydantic-independent and does not import the schema layer; no circular dependency
- **163 new deterministic tests** — `tests/test_body_weight_goal_schemas.py` covering module/exports, `BodyWeightGoalCreate` (field set/order/config, input types, rejection cases, range/boundary-after-rounding, ROUND_HALF_UP, equal start/target, no direction/progress calculation, no mutation), `BodyWeightGoalData` (field set/order/config, validation, enum reuse/rejection, lowercase serialization, `from_domain` exact copy/no arithmetic/no rounding/no direction reclassification/no mutation/deterministic), `BodyWeightGoalProgressData` (nine-field set/order/config, all-required/null/extra rejection, weight validation, `total_change_required_kg > 0`, signed change/remaining/percentage acceptance, negative/zero/exact-100/above-100/negative-remaining preservation, no clamping/capping, enum reuse/rejection, JSON string serialization, `from_result` exact nine-field copy/no arithmetic/no rounding/no clamping/no capping/no direction reclassification/no status reclassification/no mutation/deterministic), both success responses (exact fields, `Literal[True]`, false rejected, exact default message, custom message, required/non-null data, extra-field rejection, nested serialization), schema purity (no FastAPI/Starlette/SQLAlchemy/Alembic/database/repository/service/network/environment/system-clock/random/AI/filesystem), no duplicated domain logic, dependency direction, and phase-boundary regression (no goal route, unchanged route inventory, exactly one BearerAuth, unchanged ORM metadata, 4 migrations, head `e5f6a7b8c9d0`, no goal ORM model)
- **No API endpoint, no persistence, no ORM model change, no migration, no repository/service, no prediction, no goal date, no time-to-goal estimate, no recommendation, no medical interpretation, no AI/LLM, no frontend work, no dependency added, no .env files or real secrets, nothing committed or pushed, no Phase 5D-3 work started**
- **Phase 5D-1 domain code was not modified, no formula was duplicated, no direction was recalculated, no status was reclassified, no remaining value was recalculated, no percentage was recalculated, no value was persisted**

### Phase 5D-3 highlights

- **Endpoint** — exactly one authenticated, read-only route `GET /api/v1/body-weights/goal-progress` (HTTP 200), declared before `DELETE /{entry_id}` in the existing body-weight router (`app/api/v1/body_weights.py`); static path, no request body, no user_id, no starting/current/target weight parameters, no goal date, no reference date; BearerAuth required; GET is the only method
- **Orchestration only** — authenticate with `get_current_user` → build `NutritionProfileRepository(session)` → build `NutritionProfileService(repo)` → `get_profile(user_id=current_user.id)` → build `BodyWeightRepository(session)` → build `BodyWeightService(repo)` → `list_history(user_id=current_user.id)` → take the latest persisted entry (the repository returns history ordered by `logged_date desc`, so `history[0]` is the latest) → call `calculate_body_weight_goal_progress(...)` exactly once → `BodyWeightGoalProgressData.from_result(...)` exactly once → return `BodyWeightGoalProgressSuccessResponse`; the route contains no goal-direction/total-change/change-achieved/remaining-change/percentage/status/rounding/quantization/clamping/capping logic (reused from Phase 5D-1)
- **Value mapping** — `starting_weight_kg` = the existing nutrition-profile `weight_kg` field; `target_weight_kg` = the existing nutrition-profile `target_weight_kg` field; `current_weight_kg` = the latest persisted `BodyWeight.weight_kg`. The earliest history entry is never used as current weight; the profile weight is never used as current weight; the profile is never mutated or synchronized with history
- **Error handling (shared envelope)** — missing profile reuses the existing 404 `NUTRITION_PROFILE_NOT_FOUND` mapping; empty body-weight history returns 422 `BODY_WEIGHT_GOAL_CURRENT_WEIGHT_NOT_FOUND` (new domain exception `BodyWeightGoalCurrentWeightNotFoundError` in `app/core/body_weight_goal_exceptions.py`, message `At least one body-weight entry is required to calculate goal progress.`); equal starting/target weights maps the frozen `InvalidBodyWeightGoalProgressError` to 422 `BODY_WEIGHT_GOAL_PROGRESS_INVALID` with the exact frozen message; unexpected repository/service/calculation/conversion failures fall through to the existing global 500 `INTERNAL_SERVER_ERROR` envelope; no raw SQL/stack-trace/secret text is exposed; `request_id` is preserved in the body and `X-Request-ID` in the response header
- **Read-only** — the endpoint never calls commit/rollback/flush/refresh/add/add_all/delete/merge; the user, nutrition profile, and body-weight entries are unchanged; no goal-progress value is persisted; no goal ORM model, table, repository, or service exists
- **Serialization** — Decimal values serialize as JSON strings; `direction` and `status` serialize lowercase; negative progress, exactly-100%, above-100%, and negative remaining change are preserved with no clamping or capping; the exact default success message is `Body-weight goal progress calculated successfully.`
- **91 new deterministic tests** — `tests/test_body_weight_goal_progress_api.py` covering route registration/ordering, OpenAPI (GET-only, no request body, no weight/user/date parameters, BearerAuth, one scheme), authentication (missing/invalid/expired token, unknown/inactive user, WWW-Authenticate, auth-before-profile/history/calculation/conversion), current-user isolation, successful orchestration (exact kwargs, calc + from_result each called once), progress values (decrease/increase partial, not-started, target-reached, target-passed, negative/above-100/negative-remaining preserved, JSON-string/lowercase serialization, determinism), empty history, missing profile, equal start/target, unexpected failures, read-only behavior, and no formula duplication in the route
- **Existing boundary tests updated (not loosened)** — `test_body_weight_goal_schemas.py` and `test_body_weight_schemas.py` route-inventory assertions now include `/api/v1/body-weights/goal-progress`; `test_body_weight_api.py`, `test_body_weight.py`, `test_body_weight_schemas.py`, and `test_phase_5b_final_audit.py` body-weight route-count/method assertions now account for the one new GET route; `test_body_weight_trend_api.py` source-inspection bounds were tightened to the trend function so they no longer false-positive on the new goal-progress function. No test was changed to force the baseline count; every change documents the intentionally added endpoint
- **No Phase 5D-4 work started**: no goal persistence, no goal ORM model, no goal migration, no goal repository/service, no profile synchronization, no prediction, no goal dates, no time-to-goal estimates, no recommendations, no medical interpretation, no AI/LLM, no frontend work, no .env or real secret added, nothing committed or pushed

### Phase 5D-1 highlights

- Pure, deterministic, framework-independent body-weight goal domain foundation (frozen, unchanged in Phase 5D-2)
- New pure domain modules `app/core/body_weight_goals.py` and `app/core/body_weight_goal_exceptions.py`; no API endpoint, no Pydantic schema, no ORM model, no migration, no repository, no service, no persistence
- Goal direction `decrease`/`maintain`/`increase`; progress status `not_started`/`in_progress`/`target_reached`/`target_passed`; progress and remaining change not clamped (negative progress and above-100% preserved)
- Reused constants `MIN_BODY_WEIGHT_KG`, `MAX_BODY_WEIGHT_KG`, `BODY_WEIGHT_DECIMAL_PLACES`; new `BODY_WEIGHT_GOAL_PERCENTAGE_DECIMAL_PLACES = Decimal("0.01")`
- Immutable frozen/slotted dataclasses `BodyWeightGoal` and `BodyWeightGoalProgressResult`
- ORM/migration unchanged: exactly 4 tables, exactly 4 revisions, head `e5f6a7b8c9d0`
- Final verified test count at freeze: 5164 backend tests pass (5071 baseline + 93 new body-weight-goal tests); ruff format and lint pass

### Phase 5C-4 (final audit) highlights

- **Goal** — audit, harden, and freeze the body-weight trend feature across 17 layers; no new product functionality
- **Verified across layers** — domain (`body_weight.py`, `body_weight_trends.py`, `body_weight_exceptions.py`, `body_weight_trend_exceptions.py`), schema (`body_weight_trends.py`), ORM (`body_weight.py`), repository (`body_weight.py`), service (`body_weight.py`), API (`body_weights.py`), auth (`authentication.py`), error envelope (`exceptions.py`), OpenAPI, ORM metadata, and Alembic migrations
- **Domain contract** — `BodyWeightEntry` reused (not redefined); `BodyWeightTrendDirection` exactly `decreased`/`stable`/`increased`; `BodyWeightTrendResult` is `@dataclass(frozen=True, slots=True)` with the 8 documented fields in documented order; >=2 observations required; inputs materialized safely and never mutated; deterministic ordering by `logged_date` then `entry_id`; Decimal-only arithmetic with ROUND_HALF_UP; direction classified from the unrounded change; no tolerance band, no prediction, no recommendation, no medical interpretation
- **Exception contract** — `BodyWeightTrendError(Exception)` → `InsufficientBodyWeightHistoryError`; framework-independent (no FastAPI/Starlette/Pydantic/SQLAlchemy/Alembic/HTTP-status/session imports); exact safe message `"At least two body-weight entries are required to calculate a trend."`
- **Schema contract** — `BodyWeightTrendData` (`extra="forbid", frozen=True`) with the 8 fields; `observation_count` requires int >= 2 (bool rejected); dates ordered (`latest_logged_date >= first_logged_date`); weights finite and positive; signed change/percentage preserved (not capped/clamped); reuses the existing `BodyWeightTrendDirection` enum (no duplicate); `from_result()` copies all eight values exactly with no calculation/rounding/sorting/direction change and no mutation of the domain result; `BodyWeightTrendSuccessResponse` is `success: Literal[True] = True`, default message `"Body-weight trend calculated successfully."`, required non-null `data`, `extra="forbid"`; Decimal values remain Decimal in Python and serialize as JSON strings; dates serialize as ISO `YYYY-MM-DD`; direction serializes lowercase
- **Repository/service reuse** — no trend-specific repository or service; endpoint reuses `BodyWeightRepository` and `BodyWeightService`; all reads user-scoped through `list_by_user_id`/`list_history(current_user.id)`; repository source has no commit/rollback/refresh (flush-only preserved); service source has no commit/rollback/flush/refresh and no AsyncSession/FastAPI/Starlette/HTTPException imports
- **API contract** — exactly one trend endpoint `GET /api/v1/body-weights/trend`, declared before `/{entry_id}`; no second body-weight router or duplicate implementation; reuses `get_current_user` and `get_db_session`; orchestration is authenticate → build repository → build service → `list_history(current_user.id)` → convert ORM rows to `BodyWeightEntry` → `calculate_body_weight_trend(entries=...)` exactly once → `BodyWeightTrendData.from_result(...)` exactly once → `BodyWeightTrendSuccessResponse`; no duplicated sorting/absolute-change/percentage/rounding/direction logic in the route layer; HTTP 200 with exact message and all eight trend fields as JSON strings/ISO dates/lowercase direction
- **Error contract** — insufficient history → HTTP 422 `BODY_WEIGHT_TREND_INSUFFICIENT_HISTORY` with the exact safe message, `request_id` in body, `X-Request-ID` header; auth missing/invalid/expired/unknown → 401 via existing envelope; inactive user → 403; unexpected errors → existing global 500 `INTERNAL_SERVER_ERROR` handler with no raw exception/SQL/constraint/secret detail; no new global exception framework
- **Read-only / transaction safety** — endpoint never calls commit/rollback/flush/refresh/add/delete/merge; no body-weight, user, or nutrition-profile record is modified; no trend result is persisted; no trend table or column exists; repeated identical requests are deterministic
- **OpenAPI** — `GET /api/v1/body-weights/trend` exists; no POST/PATCH/PUT/DELETE trend; BearerAuth required; exactly one BearerAuth security scheme (HTTP type); response schema references `BodyWeightTrendSuccessResponse`; no user_id input exposed; static `/trend` coexists safely with `DELETE /{entry_id}`
- **Privacy/security** — public trend responses expose only the eight documented trend fields; no user_id, ORM id, entry IDs, timestamps, email, password hash, token data, or SQLAlchemy internal state; only `.env.example` (placeholder template, no real secrets) exists; no real secrets or API keys added
- **ORM/migration integrity** — exactly four ORM tables (`users`, `nutrition_profiles`, `nutrition_logs`, `body_weights`); no `body_weight_trends` table; no trend persistence columns; exactly four migration revisions; linear chain, exactly one base (`3f0c6eb4f49e`) and one head (`e5f6a7b8c9d0`); no branches/cycles; existing migration files unmodified; no migration generated
- **New final-audit tests** — `tests/test_phase_5c_final_audit.py` (7 tests) covering cross-layer domain↔schema field-name/order alignment, `BodyWeightTrendDirection` enum reuse (no duplicate), Decimal-typed schema fields, exact API orchestration (`calculate_body_weight_trend`, `BodyWeightTrendData.from_result`, and `BodyWeightService.list_history` each invoked exactly once with `current_user.id`), and that insufficient history never invokes `from_result`; all high-value cross-layer invariants not already protected elsewhere
- **No prohibited scope** — no weight predictions, goal/time-to-goal estimates, weekly/monthly trends, moving averages, trend charts/snapshots, health/adherence/nutrition scores, medical interpretation, diagnosis, treatment, recommendations, warnings, BMI/BMR/TDEE recalculation, profile synchronization, automatic profile-weight updates, AI/LLM/Groq/USDA/barcode/image recognition, or frontend work
- **No formula duplicated, no trend-specific repository/service added, no value persisted, no ORM model changed, no migration changed, no dependency added, no profile synchronization added, no prediction/recommendation/medical interpretation added, no weekly/monthly analytics added, no AI/LLM added, no frontend work, no .env or real secret added, nothing committed or pushed, no next-phase work started**
- **Final verified state** — 5071/5071 passed, 0 failed, 0 skipped; Ruff format + lint clean; Python 3.11.9, FastAPI 0.115.0, Pydantic 2.11.4, SQLAlchemy 2.0.36, Alembic 1.14.1, asyncpg 0.30.0; exactly 4 ORM tables, 4 migration revisions, linear chain, head e5f6a7b8c9d0, exactly 1 BearerAuth in OpenAPI; `create_app()` import performs no DB connection and no automatic migration; two independent `create_app()` instances are distinct; Phase 5C frozen and ready for the next explicitly specified phase

### Phase 5C-2 highlights

- **New strict schema module** — `app/schemas/body_weight_trends.py`; Pydantic v2, framework-independent, imports only Python standard library, Pydantic, and verified Phase 5C-1 domain types; no FastAPI/Starlette/SQLAlchemy/Alembic/database/repository/service/router/network/environment/system-clock/random/IO dependencies
- **`BodyWeightTrendData`** — immutable response schema (`ConfigDict(extra="forbid", frozen=True)`) with `observation_count`, `first_logged_date`, `latest_logged_date`, `starting_weight_kg`, `latest_weight_kg`, `absolute_change_kg`, `percentage_change`, `direction: BodyWeightTrendDirection`; strict validation: observation_count must be >= 2 (rejects bool/float/Decimal/string/null/zero/one/negative); dates must not be null; latest_logged_date >= first_logged_date (no system clock); starting_weight_kg and latest_weight_kg must be finite and positive (rejects bool/NaN/Infinity/zero/negative/null); absolute_change_kg and percentage_change must be finite (rejects bool/NaN/Infinity/null); signed values preserved exactly as provided by domain (no capping, no clamping, no recalculation, no direction reclassification); percentage_change values above 100 and below -100 preserved without modification
- **`BodyWeightTrendSuccessResponse`** — success-envelope schema with `success: Literal[True] = True`, default message `"Body-weight trend calculated successfully."`, and required `data: BodyWeightTrendData`; `ConfigDict(extra="forbid")`; not frozen (follows existing project convention)
- **`from_result()` naming** — follows the dominant `nutrition_calculations.py`, `nutrition_progress.py`, and `nutrition_summaries.py` convention for domain-result conversion (rather than the `from_domain()` convention used for entity types in `body_weight.py`)
- **`BodyWeightTrendDirection` enum reused** — no duplicate enum; lowercase string serialization (decreased/stable/increased)
- **Decimal preservation** — all Decimal values remain Decimal in Python; serialize as JSON strings (no float conversion); signed positive, negative, and zero values preserved; no re-quantization, no recalculation, no rounding during conversion
- **Domain module unchanged** — `app/core/body_weight_trends.py` remains Pydantic-independent; no circular dependency; schema imports domain; domain does not import Pydantic
- **130 new deterministic tests** — module exports, field set, field order, configuration (extra=forbid, frozen=True), observation_count validation (boundaries, bool/float/Decimal/string/null rejection), date validation (valid dates, same dates, latest-after-first, earlier-latest rejection), starting/latest-weight validation (finite, positive, NaN/Infinity/bool/null rejection), absolute_change_kg and percentage_change validation (signed preservation, no cap/clamp, bool/NaN/Infinity/null rejection), direction enum (reuse, valid values, invalid rejection, lowercase serialization), from_result() exact copy (no recalculation, no rounding, no direction reclassification, no mutation, deterministic), success response (exact fields, Literal[True], exact default message, required data, non-null data, extra-field rejection), serialization (Decimal preservation, Decimal JSON-string, negative/zero Decimal JSON, date ISO, no float), schema purity (no FastAPI/Starlette/SQLAlchemy/Alembic/database/repository/service/network/environment/system-clock/random/AI), dependency direction, existing body-weight schema regression
- **No API endpoint, no persistence, no ORM/migration changes, no repository/service/router changes, no trend route added, no BMI/BMR/TDEE, no predictions, no recommendations, no medical interpretation, no frontend changes, no dependencies added, no .env files or real secrets, nothing committed or pushed**
- **Phase 5C-1 domain code was not modified, no formula was duplicated, no value was recalculated, no direction was reclassified**

### Phase 5C-3 highlights

- **New authenticated, read-only endpoint** — `GET /api/v1/body-weights/trend`; reuses the frozen Phase 5C-1 `calculate_body_weight_trend()` domain function and the frozen Phase 5C-2 `BodyWeightTrendData.from_result()` / `BodyWeightTrendSuccessResponse` schemas; no new calculation, persistence, ORM, migration, dependency, or frontend code
- **Thin, orchestration-only endpoint** — `app/api/v1/body_weights.py::get_body_weight_trend()`; requires a Bearer token (reuses `get_current_user` + `BearerAuth`), loads the authenticated user's history via `BodyWeightService.list_history()`, converts ORM `BodyWeight` rows into domain `BodyWeightEntry` objects (entry_id, logged_date, weight_kg), calls `calculate_body_weight_trend(entries=...)` exactly once, wraps the result via `BodyWeightTrendData.from_result()`, and returns a `BodyWeightTrendSuccessResponse`; no formula duplication in the route layer
- **Read-only** — no persistence of trend results; no commit/flush/refresh/mutation of user or body-weight objects; uses the existing request-scoped `get_db_session`
- **Route ordering** — static `/trend` path declared BEFORE the dynamic `/{entry_id}` DELETE route on the same `APIRouter` (prefix `/body-weights`) to prevent path shadowing; no second body-weight router, no PATCH/PUT/POST on `/trend`
- **Insufficient-history contract** — when fewer than two entries exist, `calculate_body_weight_trend()` raises `InsufficientBodyWeightHistoryError` (frozen Phase 5C-1 exception), mapped by the shared error-handling layer to HTTP 422 with code `BODY_WEIGHT_TREND_INSUFFICIENT_HISTORY` and exact message `"At least two body-weight entries are required to calculate a trend."`
- **113 new deterministic tests** — `tests/test_body_weight_trend_api.py` covering route registration (on existing router, no duplicate/second router, no POST/PATCH/PUT/DELETE on `/trend`), OpenAPI (BearerAuth present, trend path listed), authentication (missing/invalid/expired/unknown/inactive tokens → 401, wrong user isolation), success (correct envelope, exact data copy, Decimal-as-string serialization, deterministic/repeatable), empty history (422 insufficient-history with exact message/code), single-entry history (422), unexpected errors, transaction ownership (read-only), domain-function reuse (no route-level percentage formula), and regression; plus updated `tests/test_body_weight_api.py` route-count invariant (3 body-weight routes) and updated Phase 5B audit invariants (route inventory, OpenAPI path count, allowed trend route)
- **No ORM model changes, no new migrations, no new trend/average/prediction/change calculations implemented, no BMI/BMR/TDEE recalculation, no nutrition-profile synchronization, no frontend changes, no dependencies added, no .env files or real secrets, nothing committed or pushed**

### Phase 5C-1 highlights

- **Pure domain module** — `app/core/body_weight_trends.py`; framework-independent, no FastAPI/Starlette/Pydantic/SQLAlchemy/database/network/filesystem/environment/AI dependencies; only Python standard-library, body-weight domain types/constants, and the trend exception module imported
- **`BodyWeightTrendDirection` (StrEnum)** — `DECREASED="decreased"`, `STABLE="stable"`, `INCREASED="increased"`; exactly three members; no UNKNOWN/IMPROVING/WORSENING; no health/goal interpretation
- **`BodyWeightTrendResult`** — `@dataclass(frozen=True, slots=True)` with `observation_count`, `first_logged_date`, `latest_logged_date`, `starting_weight_kg`, `latest_weight_kg`, `absolute_change_kg`, `percentage_change`, `direction`; no user_id, entry IDs, target, BMI/BMR/TDEE, score, prediction, or recommendation fields
- **`calculate_body_weight_trend(*, entries)`** — keyword-only pure function; accepts any iterable (tuple/list/generator/iterator); materializes exactly once; sorts by logged_date ascending then entry_id ascending as deterministic tie-breaker; never mutates caller-owned inputs
- **Minimum two observations required** — raises `InsufficientBodyWeightHistoryError` for 0 or 1 entries; exact safe message "At least two body-weight entries are required to calculate a trend."
- **Decimal-only arithmetic** — absolute change quantized to `BODY_WEIGHT_DECIMAL_PLACES` (0.01); percentage change quantized to `BODY_WEIGHT_PERCENTAGE_DECIMAL_PLACES` (0.01); both use ROUND_HALF_UP; no float conversion
- **Direction from unrounded change** — change < 0 → DECREASED, change == 0 → STABLE, change > 0 → INCREASED; no tolerance band; no goal-dependent interpretation
- **Exception hierarchy** — `BodyWeightTrendError(Exception)` → `InsufficientBodyWeightHistoryError`; framework-independent, no HTTP status, no FastAPI/Starlette/SQLAlchemy/Pydantic imports; stable safe default message
- **24 exception tests** + **93 trend tests** = 117 new deterministic tests covering enum, result structure, exceptions, insufficient-history (empty/one/tuple/list/generator), increasing/decreasing/stable trends, percentage accuracy (ROUND_HALF_UP, positive/negative/zero/repeating), ordering (ascending/descending/randomized/tuple/list/generator/iterator), ID tie-breaker, input immutability, generator consumption, repeated-call determinism, domain purity (no prohibited imports, system clock, filesystem, network), phase boundaries (no schema/ORM/repository/service/API/migration), constants
- **No Pydantic schemas, no ORM models, no migrations, no repositories, no services, no API endpoints, no persistence, no BMI/BMR/TDEE, no predictions, no recommendations, no AI/LLM, no frontend changes, no dependencies added, no .env files or real secrets**

## Previous Phase — 5B: Body-Weight Tracking Module (completed, frozen)

All 4704 tests pass (new Phase 5B final-audit cross-layer invariants).
Ruff format and lint pass.
No production defects found. No dependency changes.
Phase 5B is frozen.

### Phase 5B-5 highlights

- **Authenticated CRUD API** — `app/api/v1/body_weights.py`; follows established API conventions (kebab-case prefix `/body-weights`, reuses `get_current_user`, `get_db_session`, `BodyWeightRepository`, `BodyWeightService`)
- **POST /api/v1/body-weights** (201) — accepts `BodyWeightEntryCreate` body (`weight_kg`) + required `logged_date` query param; generates `entry_id` via `uuid.uuid4()`; calls `BodyWeightService.create_entry()` with trusted `user_id`; commits once; refreshes entry; returns `BodyWeightEntrySuccessResponse`
- **GET /api/v1/body-weights** (200) — returns authenticated user's body-weight history; calls `BodyWeightService.list_history()`; converts via `BodyWeightHistoryData.from_domain()`; read-only (no commit/flush/refresh)
- **DELETE /api/v1/body-weights/{entry_id}** (200) — dual-filter ownership enforcement; calls `BodyWeightService.delete_entry()` with both `user_id` and `entry_id`; commits once; returns `BodyWeightDeleteSuccessResponse`
- **GET /api/v1/body-weights/trend** (200) — [added in Phase 5C-3] authenticated, read-only trend endpoint; declared BEFORE the DELETE `/{entry_id}` route on the same router to avoid shadowing; requires Bearer token (reuses `get_current_user` + `BearerAuth`); loads history via `BodyWeightService.list_history()`, converts ORM `BodyWeight` rows to domain `BodyWeightEntry`, calls `calculate_body_weight_trend(entries=...)` exactly once, wraps the result via `BodyWeightTrendData.from_result()` in a `BodyWeightTrendSuccessResponse`; read-only (no commit/flush/refresh); returns HTTP 422 `BODY_WEIGHT_TREND_INSUFFICIENT_HISTORY` ("At least two body-weight entries are required to calculate a trend.") when fewer than two entries exist
- **Error mappings** — 409 → `BODY_WEIGHT_ENTRY_ALREADY_EXISTS` (duplicate date), 409 → `BODY_WEIGHT_ENTRY_ID_ALREADY_EXISTS` (duplicate entry ID), 404 → `BODY_WEIGHT_ENTRY_NOT_FOUND`, 503 → `BODY_WEIGHT_PERSISTENCE_ERROR`, 500 → `INTERNAL_SERVER_ERROR`, 422 → `VALIDATION_ERROR`
- **`BodyWeightDeleteSuccessResponse`** — added to `app/schemas/body_weight.py`; follows existing `NutritionLogDeleteSuccessResponse` pattern
- **Response schemas reused** — `BodyWeightEntryCreate`, `BodyWeightEntryData`, `BodyWeightHistoryData`, `BodyWeightEntrySuccessResponse`, `BodyWeightHistorySuccessResponse` all reused from Phase 5B-2
- **Route ordering** — static collection paths registered before dynamic `/{entry_id}` path to prevent shadowing
- **Transaction ownership preserved** — API layer owns commit/rollback; repository flush-only; service transaction-free
- **Comprehensive API tests** — `tests/test_body_weight_api.py` covering router registration, OpenAPI, authentication (missing/invalid/expired/unknown/inactive), POST success/validation/duplicate, GET history (empty/populated/read-only), DELETE success/not-found, path validation, unexpected errors, transaction ownership, architecture boundaries, and regression; plus `tests/test_body_weight_trend_api.py` (Phase 5C-3) covering the trend endpoint
- **No ORM model changes, no new migrations, no new trend/average/prediction/change calculations implemented, no BMI/BMR/TDEE recalculation, no nutrition-profile synchronization** — the trend calculation is invoked exclusively via the frozen Phase 5C-1 `calculate_body_weight_trend()` domain function and the frozen Phase 5C-2 `BodyWeightTrendData.from_result()` / `BodyWeightTrendSuccessResponse` schemas

### Phase 5B final-audit highlights

- **Comprehensive cross-layer audit** — 55 new invariants across 13 layers: cross-layer constant alignment (domain min/max/decimal-places match ORM check constraints, precision/scale, schema imports), repository user-scoping (all 4 methods always require user_id, no commit/rollback in repository source), service transaction boundaries (no commit/flush/rollback/refresh/AsyncSession in service source), API route inventory (exactly 3 methods: POST/GET/DELETE, no get-by-id, no PATCH/PUT, no summary/progress/trend/analytics) [the trend prohibition was later relaxed by Phase 5C-3, which added the read-only `GET /api/v1/body-weights/trend` endpoint], authentication (all 3 BW routes require BearerAuth in OpenAPI), response privacy (no user_id, timestamps, or ORM id in response schemas; delete response has no data field), OpenAPI invariants (exactly 1 BearerAuth, delete path with UUID param, logged_date has date format), ORM/migration integrity (exactly 4 tables, exactly 4 migrations, linear chain, correct head e5f6a7b8c9d0, one base, no prohibited columns), no prohibited functionality (no trend/prediction/BMI/BMR/TDEE in codebase), security (no .env files, no Alembic import at app startup, create_app requires no DB connection, two independent app instances), no system-clock fallback (logged_date must be required with no date default, domain never calls date.today/datetime.now), no duplicate implementation (single module/class per layer), no public user_id exposed (absent from entry-data, history-data, create-schema, success-response, delete-response)
- **Test-quality corrections** — 2 test-logic defects in the audit test module: `test_schema_validator_uses_same_bounds` now checks for imported constant names rather than stringified Decimal values (source uses `MIN_BODY_WEIGHT_KG`, not `"10.00"`); `test_post_requires_logged_date_query_param` now checks `not isinstance(p.default, date)` rather than `p.default is inspect.Parameter.empty` (FastAPI `Query(...)` produces a `FieldInfo` object, not `Parameter.empty`)
- **No production defects found** — zero genuine defects; all corrections were test-logic only
- **Final verification** — 4704/4704 passed (4649 baseline + 55 new audit tests), Ruff format + lint clean, Python 3.11.9, FastAPI 0.115.0, Pydantic 2.11.4, SQLAlchemy 2.0.36, asyncpg 0.30.0, Alembic 1.14.1; exactly 4 ORM tables, 4 migration revisions, linear chain, head e5f6a7b8c9d0, exactly 1 BearerAuth in OpenAPI; no .env files, no real secrets; two independent `create_app()` instances are distinct
- **Frozen** — no further changes to Phase 5B

### Phase 5B-4 highlights

- **BodyWeightRepository** — `app/repositories/body_weight.py`; follows established repository conventions (AsyncSession injection, `_is_unique_constraint_violation` helper, flush-only transaction boundary, no commit/rollback/refresh)
- **`list_by_user_id()`** — returns `list[BodyWeight]` filtered by `user_id`; deterministic ordering: `logged_date DESC`, then `entry_id ASC` as tie-breaker; empty list when no entries
- **`get_by_user_and_entry_id()`** — dual-filter ownership enforcement (`user_id` + `entry_id`); returns `BodyWeight | None` using `one_or_none()` semantics
- **`create()`** — accepts only trusted explicit values (`user_id`, `entry_id`, `logged_date`, `weight_kg`); no `model_dump()`, no arbitrary dicts; translates `uq_body_weights_user_id_logged_date` IntegrityError into `DuplicateBodyWeightDateError` and `uq_body_weights_user_id_entry_id` into `DuplicateBodyWeightEntryIdError`; re-raises unrelated IntegrityError and unexpected exceptions; calls flush but never commit/rollback/refresh
- **`delete()`** — accepts the already-owned ORM `BodyWeight` object; calls `session.delete(entry)` + `session.flush()`; never commit/rollback
- **BodyWeightService** — `app/services/body_weight.py`; framework-independent, no FastAPI/Starlette/SQLAlchemy imports, no HTTPException/status-codes, no session mutation
- **Constructor injection** — receives `BodyWeightRepository`; stored as `self._repository`
- **`list_history()`** — delegates `user_id` to `repository.list_by_user_id()`; preserves repository ordering; no aggregation/trend/change calculations
- **`get_entry()`** — dual-filter lookup (`user_id` + `entry_id`); raises `BodyWeightNotFoundError` when absent/cross-user; no schema validation duplication
- **`create_entry()`** — passes trusted explicit values to `repository.create()`; returns repository result; preserves all domain exceptions; no value derivation
- **`delete_entry()`** — ownership enforcement via dual-filter lookup; raises `BodyWeightNotFoundError` when absent; delegates deletion to repository
- **New domain exceptions** — `DuplicateBodyWeightEntryIdError` (duplicate entry ID), `BodyWeightNotFoundError` (entry not found); follow existing exception patterns
- **Package exports** — `BodyWeightRepository` exported from `app/repositories/__init__.py`; `BodyWeightService` exported from `app/services/__init__.py`; existing exports unchanged
- **New test files** — `tests/test_body_weight_repository.py` and `tests/test_body_weight_service.py` covering all required behaviors
- **Updated boundary tests** — `test_body_weight.py` and `test_body_weight_schemas.py` updated to assert repository and service file existence

### Phase 5B-1 highlights

- **New pure domain module** — `app/core/body_weight.py`; framework-independent, no FastAPI/Pydantic/SQLAlchemy/database/network/environment/AI dependencies; only Python standard-library and the body-weight exception module imported
- **Domain constants** — `MIN_BODY_WEIGHT_KG=Decimal("10.00")`, `MAX_BODY_WEIGHT_KG=Decimal("700.00")`, `BODY_WEIGHT_DECIMAL_PLACES=Decimal("0.01")`; all Decimal, no floats; aligned with existing nutrition-profile weight range (10-700 kg)
- **`BodyWeightEntry`** — `@dataclass(frozen=True, slots=True)` with `entry_id: UUID`, `logged_date: date`, `weight_kg: Decimal`; strict validation in `__post_init__`; caller-owned UUID; date (not datetime) enforced; Decimal or integer weight input with ROUND_HALF_UP two-decimal normalization; range 10.00-700.00 kg inclusive after rounding; no system-clock access, no silent ID generation
- **`order_body_weight_entries()`** — accepts any iterable, returns sorted tuple by logged_date ascending then entry_id ascending as tie-breaker; validates all members; no mutation of inputs
- **`ensure_unique_body_weight_dates()`** — detects duplicate logged_date values; raises `DuplicateBodyWeightDateError`; preserves original input order; no silent merge or deduplication
- **`validate_body_weight_history()`** — combines unique-date enforcement and deterministic ordering into one helper; reuses both helpers; no weight-change/trend/average/prediction calculations
- **Exception hierarchy** — `BodyWeightError` (base) → `InvalidBodyWeightError` (invalid data), `DuplicateBodyWeightDateError` (duplicate date); framework-independent, no HTTP/SQLAlchemy/Pydantic dependencies; stable safe default messages without SQL, constraint names, or credentials
- **192 new deterministic tests** — exception hierarchy/safety/purity (38), constants/field structure/UUID/date/weight/normalization/boundary/ordering/duplicate/combined/domain-purity/phase-boundary (154)
- **Kilograms-only storage** — no pounds, stone, unit-conversion, body-fat, or other measurement types
- **No API endpoint, no response schema, no persistence, no ORM/migration changes, no repository/service/router changes, no trend/average/prediction/recommendation, no BMI/BMR/TDEE recalculation, no nutrition-profile synchronization**

### Phase 5B-2 highlights

- **New strict schema module** — `app/schemas/body_weight.py`; Pydantic v2, framework-independent, imports only Python standard library, Pydantic, and verified Phase 5B-1 domain types; no FastAPI/Starlette/SQLAlchemy/Alembic/database/repository/service/router/network/environment/system-clock/random/IO dependencies
- **`BodyWeightEntryCreate`** — input schema with `extra="forbid"`; single required `weight_kg: Decimal`; accepts Decimal, integer, numeric string, and finite float input following established schema conventions; ROUND_HALF_UP two-decimal normalization; range validated against Phase 5B-1 domain constants (10.00–700.00 kg); boundary-after-rounding enforced; rejects bool/NaN/Infinity/negative Infinity; no entry_id, logged_date, user_id, or timestamps exposed
- **`BodyWeightEntryData`** — immutable public response schema (`ConfigDict(extra="forbid", frozen=True, from_attributes=True)`); three required fields (`entry_id: UUID`, `logged_date: date`, `weight_kg: Decimal`); `from_domain()` classmethod copies exactly from `BodyWeightEntry` without recalculation; Decimal preserved in Python, serialized as JSON strings; UUID serialized as standard UUID string; date serialized as ISO YYYY-MM-DD; no user_id, created_at, updated_at, or _sa_instance_state exposed
- **`BodyWeightHistoryData`** — immutable collection schema (`ConfigDict(extra="forbid", frozen=True)`); `entries: tuple[BodyWeightEntryData, ...]`; model validator rejects duplicate logged_date and duplicate entry_id values; `from_domain()` classmethod accepts any `Iterable[BodyWeightEntry]` (supports generators), preserves input order exactly, delegates to `BodyWeightEntryData.from_domain()`; does not call domain ordering or duplicate-date helpers; empty history (zero entries) is valid
- **Success response schemas** — `BodyWeightEntrySuccessResponse` (default message: "Body-weight entry processed successfully.") and `BodyWeightHistorySuccessResponse` (default message: "Body-weight history retrieved successfully."); both use `Literal[True]` for success, require data, reject null data, reject extra fields; follow the existing project success-envelope convention
- **`from_domain()` naming convention** — follows the dominant `nutrition_logs.py` `from_domain()` pattern (rather than `from_result()`), since conversion is from a domain dataclass (`BodyWeightEntry`)
- **Accepted input types** — follows the established schema-layer convention: Decimal, integer (converted via `Decimal(str(v))`), numeric string (converted via `Decimal(str(v))`), and finite float (converted via `Decimal(str(v))`); this is more permissive than the stricter domain-only rule (which accepts only Decimal and int), preserving the Pydantic API-boundary behavior used by all other existing input schemas
- **Schema/domain separation** — schema imports domain types; domain (`app/core/body_weight.py`) does not import Pydantic or the schema module; no circular dependency
- **155 new deterministic tests** — module exports, field sets, Decimal validation, normalization (ROUND_HALF_UP), range boundaries, boundary-after-rounding, extra-field rejection, forbidden-field rejection, frozen immutability, from_attributes conversion, ORM-like object conversion, dict conversion, Decimal/UUID/date serialization, from_domain exact copy, no recalculation, no mutation, history validation (empty, one-entry, multi-entry, generator support, order preservation, no schema sorting, duplicate date/ID rejection, nested frozen), success response envelopes (default/custom messages, null rejection, extra-field rejection, nested serialization, JSON), architecture purity (no prohibited imports), dependency direction, phase boundaries (no ORM/repository/service/router/API/endpoint, unchanged routes, unchanged migration count/head, unchanged ORM metadata, one BearerAuth scheme)
- **No API endpoint, no persistence, no ORM/migration changes, no repository/service/router changes, no trend/average/prediction/recommendation calculation, no BMI/BMR/TDEE recalculation, no nutrition-profile synchronization, no body-fat/measurement functionality, no AI/LLM functionality**

---

## Previous Phase — 4F-10: Nutrition Logging and Daily Progress Foundation Final Audit (completed, frozen)

All 3901 tests pass (41 new Phase 4F-10 cross-layer audit tests, 3860 foundation tests).
Ruff format and lint pass.
No production defects found. No dependency changes. No ORM/model changes.
No progress or summary values are persisted. Phase 4F is frozen.

### Phase 4F-10 highlights

- **Comprehensive final audit** — all 20 audit areas inspected: domain contracts (MealType StrEnum, immutable dataclasses, Decimal arithmetic, NaN/Infinity rejection, text validation, deterministic aggregation, no system-clock/network/database access), daily progress domain (NutritionProgressStatus StrEnum, immutable NutrientProgress/DailyNutritionProgress, Decimal arithmetic, negative remaining preserved, above-100% percentages preserved, no recalculation in route/schema layers), schema contracts (extra="forbid", frozen=True, from_attributes=True, no user_id exposure, Decimal preservation, MealType lowercase serialization, no formula duplication), ORM model (table nutrition_logs, UUID PK, FK to users ON DELETE CASCADE, composite unique user_id+entry_id, meal_type enum with lowercase values_callable, Numeric precision aligned with domain, 4 check constraints, composite index user_id+logged_date, delete-orphan relationship), migrations (exactly 3 revisions, linear chain, no branches, head b8a7c3d9e1f2, offline SQL generates correct PostgreSQL DDL, downgrade preserves users/nutrition_profiles), repository (injected AsyncSession, SQLAlchemy 2.x select, user_id filtering, deterministic ordering, flush-only, unique-constraint IntegrityError translation, no commit/rollback/close), service (framework-independent, no FastAPI/Starlette/SQLAlchemy imports, explicit repository injection, no commit/flush/rollback, ownership enforcement), CRUD API (POST/GET/DELETE with auth, user_id from current_user only, correct transaction ownership, safe error mappings), daily summary API (read-only, no commit/flush/refresh, deterministic meal ordering, empty-day valid), daily progress API (read-only, no persistence, reuses existing domain/schema helpers, no formula duplication in route, negative remaining and above-100% percentages preserved), authentication (existing get_current_user/BearerAuth reused, no duplicate scheme, no manual token parsing, user_id never accepted from input), error safety (consistent envelope with request_id, X-Request-ID, no SQL/constraint/stack/password/JWT exposure), OpenAPI (correct paths/methods, required query params, date format, single BearerAuth), transactions (API owns commit/rollback, repository never commits, service never commits, read-only endpoints never commit/flush/refresh/mutate), privacy (no user_id/email/password/hash/token/JWT/DB-id/SQLAlchemy-state in response schemas), regression (all existing behavior unchanged: auth, profile, calculations, summaries, logs), architecture boundaries (domain has no FastAPI/Starlette/SQLAlchemy/Pydantic imports, schema has no formulas, repository has no HTTP, service has no HTTP, API does not duplicate domain calculations, no circular imports), security/cleanliness (no hard-coded secrets, no .env files, no debug prints, no breakpoints, no temp scripts, no test artifacts)
- **Test-quality formatting fix** — corrected a missing blank line before `import re` in `test_nutrition_progress_api.py:1579`
- **41 new cross-layer audit tests** — cross-layer limit agreement (domain/schema/ORM numeric and text-length consistency), ORM metadata (exactly 3 tables), migration topology (3 files, linear, correct head, no branches), route ordering (/summary and /progress before /{entry_id}), OpenAPI invariants (exactly one BearerAuth, correct paths and methods, required query params), ORM constraints (FK, unique, index, check constraints), domain purity (no FastAPI/Starlette/SQLAlchemy/Pydantic in domain, no date.today/datetime.now), schema privacy (no user_id/password/token fields), application factory (two distinct instances, OpenAPI generation, no DB connection on import)
- **No production defects found** — all changes were test-quality or documentation only
- **No new features added, no progress/summary persisted, no ORM/migration changes, no dependency changes**

### Phase 4F-8 highlights (frozen)

- **New strict schema module** — `app/schemas/nutrition_progress.py`; framework-independent, imports only Python standard library, Pydantic, and verified Phase 4F-7 domain types; no FastAPI/Starlette/SQLAlchemy/Alembic/database/repository/service/router/network/environment/system-clock/random/IO dependencies
- **`NutrientProgressData`** — immutable Pydantic model (`ConfigDict(extra="forbid", frozen=True)`) with `consumed: Decimal`, `target: Decimal`, `remaining: Decimal`, `percentage: Decimal`, `status: NutritionProgressStatus`; validates finite/positive targets, finite/non-negative consumed and percentage, finite remaining (positive/zero/negative); rejects NaN/Inf/-Inf/bool; accepts Decimal, string, and float input following existing schema conventions
- **`DailyNutritionProgressData`** — immutable Pydantic model (`ConfigDict(extra="forbid", frozen=True)`) with `calories: NutrientProgressData`, `protein: NutrientProgressData`, `carbohydrate: NutrientProgressData`, `fat: NutrientProgressData`; all four sections required; extra top-level and nested fields rejected; top-level and nested mutation rejected
- **`DailyNutritionProgressSuccessResponse`** — follows existing success-envelope convention (`success: Literal[True] = True`, default message `"Daily nutrition target progress calculated successfully."`, `data: DailyNutritionProgressData`; `ConfigDict(extra="forbid")`)
- **`NutrientProgressData.from_result()`** — copies every value from `NutrientProgress` exactly; no arithmetic, no rounding, no status reclassification; does not mutate the domain result; deterministic
- **`DailyNutritionProgressData.from_result()`** — converts `DailyNutritionProgress` using nested `NutrientProgressData.from_result()` for all four sections; preserves order, negative remaining values, percentages above 100, and existing statuses
- **Existing `NutritionProgressStatus` reused** — no duplicate enum; lowercase string serialization (below_target/target_met/above_target)
- **Decimal preservation** — all Decimal values remain Decimal in Python; serialize as JSON strings (no float conversion); negative remaining values preserved; percentages above 100 preserved
- **No API endpoint, no persistence, no ORM/migration changes, no formula duplication, no health/adherence score, no recommendation/warning logic, no overall status/grade**

### Phase 4F-6 highlights

- **New authenticated endpoint** — `GET /api/v1/nutrition-logs/summary` (200); placed before `/{entry_id}` to prevent "summary" from being caught as a UUID; requires `logged_date` query parameter (ISO date, no default, no `date.today()`, no JWT-inferred date)
- **Reuses existing frozen contracts** — `get_current_user` (BearerAuth), `get_db_session`, `NutritionLogRepository.list_by_user_and_date()`, `NutritionLogService.list_daily_entries()`, `summarize_daily_nutrition_log()`, `DailyNutritionLogSummaryData.from_domain()`, `DailyNutritionLogSuccessResponse`; no new aggregation logic, no target comparison, no health score
- **Thin route** — fetches entries, converts ORM → domain, calls domain summary, wraps in schema; no duplication of domain/schema behavior; ORM-to-domain conversion done inline (not elsewhere duplicated)
- **Read-only** — no commit, flush, refresh, add, delete, rollback during success; only `session.execute()` is called (via the repository); endpoint never calls session mutation methods
- **Empty-day behavior** — HTTP 200 with zero totals and four zero-value meals (breakfast, lunch, dinner, snack) from `summarize_daily_nutrition_log`
- **Deterministic** — stable meal order (breakfast→lunch→dinner→snack); Decimal values preserved as JSON strings; MealType serialized as lowercase string; different entry input orders produce identical summary output
- **Ownership isolation** — only `current_user.id` is passed to the service; no `user_id` query/body/path parameter accepted; extra `user_id` query param ignored
- **Error mapping** — unexpected errors → HTTP 500 `INTERNAL_SERVER_ERROR` with safe message, `request_id` in body, `X-Request-ID` header; no raw SQL, exception types, or stack traces exposed
- **Route ordering** — `/summary` registered before `/{entry_id}` in the router; static paths not interpreted as UUID path params; existing POST/GET/DELETE CRUD paths unchanged
- **102 new deterministic API tests** — route registration/ordering, OpenAPI contract, authentication (missing/invalid/expired/unknown/inactive), `logged_date` validation, user isolation, repository/service reuse, empty-day, one-entry, multi-entry, multi-meal, deterministic ordering, Decimal preservation, MealType serialization, read-only, no mutation, unexpected errors, request-ID, privacy, existing CRUD regression, phase boundaries (no PUT/PATCH/DELETE/POST summary, no aggregation route, no target comparison)
- **Updated 3 existing tests** — `test_nutrition_summary_schemas.py::TestPhaseBoundaries::test_summary_endpoint_in_openapi` now expects 2 summary paths (nutrition-logs + nutrition-profile); `test_nutrition_log_api.py` updated for route count expectations and renamed tests
- **No PUT/PATCH/DELETE/POST summary routes, no aggregation persistence, no target comparison, no health score**

### Phase 4F-5 highlights

- **Three authenticated endpoints** — `POST /api/v1/nutrition-logs` (201), `GET /api/v1/nutrition-logs` (200), `DELETE /api/v1/nutrition-logs/{entry_id}` (200); all reuse the existing `get_current_user`, `get_db_session`, `NutritionLogRepository`, and `NutritionLogService`
- **POST create-entry** — accepts `NutritionLogEntryCreate` body + required `logged_date` query param; calls `NutritionLogService.create_entry()` with trusted `user_id` and explicit `logged_date`; commits once on success; rolls back and returns 409 for `NutritionLogEntryAlreadyExistsError`, 503 for `NutritionLogPersistenceError`
- **GET list daily entries** — accepts required `logged_date` query param; calls `NutritionLogService.list_daily_entries()`; returns a list of `NutritionLogEntryData` objects; read-only (no commit/flush/refresh)
- **DELETE single entry** — accepts UUID `entry_id` path param; calls `NutritionLogService.delete_entry()` (dual-filter ownership enforcement); commits once; returns 404 for `NutritionLogEntryNotFoundError`, 503 for `NutritionLogPersistenceError`
- **Error mappings** — 409 → `NUTRITION_LOG_ENTRY_ALREADY_EXISTS`, 404 → `NUTRITION_LOG_ENTRY_NOT_FOUND`, 503 → `NUTRITION_LOG_PERSISTENCE_ERROR`, 500 → `INTERNAL_SERVER_ERROR`, 422 → `VALIDATION_ERROR`
- **Response schemas** — `NutritionLogEntrySuccessResponse`, `NutritionLogEntryListData`, `NutritionLogEntryListSuccessResponse`, `NutritionLogDeleteSuccessResponse` added to `app/schemas/nutrition_logs.py`; `NutritionLogEntryData.model_config` includes `from_attributes=True`
- **Test fixes** — corrected mock `execute` assignments to use `return_value`/`side_effect` instead of reassignment; added `raise_app_exceptions=False` to test client transport to capture 500 error envelopes instead of raw exceptions
- **174 new deterministic API tests** — route registration, OpenAPI contract, authentication, create (success, validation, duplicate, persistence-failure, unexpected-failure), read (empty, data, ownership isolation, unexpected-failure), delete (success, not-found, ownership, persistence-failure, unexpected-failure), error helpers, safety, response shapes
- **No ORM/model changes, no new migrations, no aggregation, no PUT/PATCH**

### Phase 4F-4 highlights

- **Extended nutrition-log exception hierarchy** — `app/core/nutrition_log_exceptions.py` now includes five domain exceptions: `NutritionLogError` (base), `InvalidNutritionLogEntryError` (existing), `NutritionLogEntryNotFoundError` ("Nutrition log entry was not found."), `NutritionLogEntryAlreadyExistsError` ("A nutrition log entry with this identifier already exists."), `NutritionLogPersistenceError` ("Nutrition log data could not be saved."); no FastAPI/HTTPException/SQLAlchemy/status-code dependencies; stable safe default messages without SQL, constraint names, or credentials
- **`NutritionLogRepository`** — `app/repositories/nutrition_log.py`; async SQLAlchemy repository accepting `AsyncSession`; supports `list_by_user_and_date()` (deterministic meal-order CASE expression: breakfast→lunch→dinner→snack, then created_at, then id), `get_by_user_and_entry_id()` (dual-filter ownership enforcement), `create()` (explicit field mapping from `NutritionLogEntryCreate` + trusted `user_id` + explicit `logged_date`; flush-only; translates `uq_nutrition_logs_user_id_entry_id` IntegrityError into `NutritionLogEntryAlreadyExistsError` with exception chaining; unrelated IntegrityError re-raised), and `delete()` (supplied ORM object deletion + flush)
- **`NutritionLogService`** — `app/services/nutrition_log.py`; receives `NutritionLogRepository` via explicit DI; `list_daily_entries()` delegates to repository, passes `user_id` and `logged_date` unchanged; `create_entry()` delegates with trusted `user_id`, explicit `logged_date`, validated schema; `delete_entry()` enforces ownership via dual-filter lookup, raises `NutritionLogEntryNotFoundError` on missing/cross-user absence; never commits/flushes/rolls back/creates sessions
- **Transaction ownership preserved** — repository adds/deletes/flushes; service never commits/flushes/rolls back/creates sessions; future API layer owns commit/rollback
- **Package exports** — `NutritionLogRepository` exported from `app/repositories/__init__.py`; `NutritionLogService` exported from `app/services/__init__.py`; existing exports unchanged
- **Deterministic ordering** — SQL-level CASE expression for meal ordering (`MealType.BREAKFAST`→0, `LUNCH`→1, `DINNER`→2, `SNACK`→3); `created_at` ascending as secondary sort; `id` ascending as final tie-breaker
- **Frozen foundation preserved** — no ORM model changes, no new migrations, no existing migration modifications, no API routes, no aggregation persistence, no target comparisons, no daily totals, no calculated values, no recommendations, no AI integration
- **Comprehensive tests** — tested exception hierarchy for 5 exceptions; repository tests covering constructor, `list_by_user_and_date` (query structure, dual-filter, ordering, empty-list, transaction-boundary, error propagation), `get_by_user_and_entry_id` (dual-filter, ownership, one-or-none, transaction-boundary, error propagation), `create` (field mapping, trusted user_id, caller-owned entry_id, explicit logged_date, add/flush, no-commit, unique-constraint translation, unrelated IntegrityError, non-IntegrityError failure), `delete` (exact-object deletion, flush, no-commit, error propagation); service tests covering constructor, `list_daily_entries` (single delegation, unchanged params, result passthrough, no totals/targets), `create_entry` (single delegation, unchanged params, schema passthrough, duplicate preservation, no transformation), `delete_entry` (dual-filter lookup, found delete, missing not-found, cross-user absence, no-commit/flush/rollback, boundary/purity)

### Phase 4F-3 highlights (frozen)

- **New ORM model** — `app/models/nutrition_log.py` with `NutritionLog` (table `nutrition_logs`)
- **SQLAlchemy 2.x typed ORM** — `Mapped[...]`, `mapped_column`, `relationship`, `back_populates`
- **UUID primary key** — application-generated via `uuid.uuid4`, reuses existing UUID convention
- **User ownership** — `user_id` FK to `users.id` with `ON DELETE CASCADE` and explicit constraint name `fk_nutrition_logs_user_id`
- **`logged_date`** — SQL `DATE` column, required, caller-supplied calendar date (not derived from server clock)
- **Caller-owned `entry_id`** — UUID, required, composite unique with `user_id` (`uq_nutrition_logs_user_id_entry_id`) — unique per user, not globally unique
- **`food_name` and `serving_description`** — `String(200)`, required
- **`meal_type`** — PostgreSQL `sa.Enum` reusing Phase 4F-1 `MealType` (`MealType.BREAKFAST` → `"breakfast"`); lowercase persistence via `values_callable`; PostgreSQL enum type name `meal_type`
- **Decimal nutrition columns** — `Numeric(7,2)` for `calories_kcal`, `Numeric(6,2)` for `protein_g`, `carbohydrate_g`, `fat_g`; exact two-decimal storage; no Float
- **Four named range-check constraints** — `ck_nutrition_logs_calories_kcal_range` (`0..10000`), `ck_nutrition_logs_protein_g_range` (`0..1000`), `ck_nutrition_logs_carbohydrate_g_range` (`0..2000`), `ck_nutrition_logs_fat_g_range` (`0..1000`); aligned with Phase 4F-1 `MAX_*` constants
- **Lookup index** — `ix_nutrition_logs_user_id_logged_date` (non-unique, composite: `user_id` + `logged_date`); no redundant indexes
- **Timestamp mixin** — `created_at` and `updated_at` with `DateTime(timezone=True)`, `server_default=now()`
- **User relationship** — `User.nutrition_logs` (one-to-many) with `back_populates="user"` and cascade `all, delete-orphan`; existing `User.nutrition_profile` one-to-one relationship unchanged
- **Model registered** — exported in `app/models/__init__.py`, discovered by `Base.metadata` via `app/db/base.py`
- **Alembic migration `b8a7c3d9e1f2`** — creates `meal_type` enum with four lowercase values, creates `nutrition_logs` table with all columns/constraints/index; downgrade drops index, table, then enum; no CASCADE enum drop; existing migrations byte-for-byte unchanged
- **New test file** — `tests/test_nutrition_log_migration.py` (58 tests) covering revision graph, upgrade/downgrade operations, schema, constraints, enum, forbidden content, boundary checks
- **Updated model tests** — 109 model tests (was ~60) covering `NutritionLog` table structure, column types, constraints, indexes, relationships, MealType reuse, `values_callable`, no aggregation fields
- **98 new tests total** — Phase 4F-3 adds 109 model + 58 migration tests, updates 2 boundary tests; full suite 3049/3049 pass
- **No repositories, services, API endpoints, aggregation persistence, food search, external APIs, AI features, or frontend changes**
- **No dependency changes, no .env file, no secrets added**

### Phase 4F-2 highlights

- **New Pydantic schema module** — `app/schemas/nutrition_logs.py`; framework-independent, imports only Python standard library, Pydantic, and verified `app.core.nutrition_logs` types
- **`NutritionLogEntryCreate`** — immutable request schema with `extra="forbid"`, `str_strip_whitespace=True`; UUID, MealType, text validation (null byte + control character rejection, 1-200 chars), Decimal nutrition values with finite/non-negative/maximum/ROUND_HALF_UP normalization using Phase 4F-1 constants; `to_domain()` method returns verified `NutritionLogEntry`; no ID generation, no recalculation
- **`NutritionLogEntryData`** — immutable response data schema; `from_domain()` classmethod for exact conversion from `NutritionLogEntry`; Decimal preservation, strict validation
- **`DailyNutritionTotalsData`** — immutable totals schema; `from_domain()` from `DailyNutritionTotals`; no calorie-from-macro derivation
- **`MealNutritionSummaryData`** — immutable meal summary schema with nested `DailyNutritionTotalsData`; `from_domain()` from `MealNutritionSummary`; strict non-negative integer `entry_count`
- **`DailyNutritionLogSummaryData`** — immutable daily summary schema with stable four-meal order (breakfast, lunch, dinner, snack) enforced via `MEAL_TYPE_ORDER`; `from_domain()` from `DailyNutritionLogSummary`; tuple output, duplicate/missing/extra meal rejection
- **`DailyNutritionLogSuccessResponse`** — response envelope with `success: Literal[True]`, default message, and required `data: DailyNutritionLogSummaryData`; extra fields rejected
- **Domain/schema boundary** — Phase 4F-1 domain types imported, no Pydantic in domain layer, no circular imports, no domain behavior modified, no formulas duplicated
- **169 new deterministic tests** — field sets, validation, Decimal behavior, `to_domain()`, `from_domain()`, extra-field rejection, JSON serialization, meal-order invariants, architecture purity, dependency direction, no prohibited imports
- **No aggregation, no calculations, no persistence, no API endpoint** — purely a schema layer
- **No ORM changes, no migrations, no repository, no service**
- **No authentication, calculation, target, or summary behavior changed**

### Phase 4F-1 highlights

- **New pure domain module** — `app/core/nutrition_logs.py`; framework-independent, no FastAPI/Pydantic/SQLAlchemy/database/network/environment/AI dependencies; only Python standard-library and the nutrition-log exception module imported
- **`MealType` (StrEnum)** — `BREAKFAST="breakfast"`, `LUNCH="lunch"`, `DINNER="dinner"`, `SNACK="snack"`; exactly four members; no UNKNOWN/OTHER; stable declaration order
- **`MEAL_TYPE_ORDER`** — immutable tuple preserving breakfast → lunch → dinner → snack order
- **Nutrition limit constants** — `MAX_CALORIES_KCAL=Decimal("10000")`, `MAX_PROTEIN_G=Decimal("1000")`, `MAX_CARBOHYDRATE_G=Decimal("2000")`, `MAX_FAT_G=Decimal("1000")`, `NUTRITION_DECIMAL_QUANTUM=Decimal("0.01")`; all Decimal, no floats
- **`NutritionLogEntry`** — `@dataclass(frozen=True, slots=True)` with `entry_id: UUID`, `food_name: str`, `meal_type: MealType`, `serving_description: str`, `calories_kcal: Decimal`, `protein_g: Decimal`, `carbohydrate_g: Decimal`, `fat_g: Decimal`; strict validation in `__post_init__`; caller-owned UUID; text trimming and control-character rejection; Decimal-only nutrition values with ROUND_HALF_UP normalization; no auth/profile/target/health/AI fields
- **`DailyNutritionTotals`** — `@dataclass(frozen=True, slots=True)` with four Decimal fields; Decimal-only, non-negative, finite, two-decimal normalization; pure aggregation, no calorie-from-macro derivation, no target comparison
- **`MealNutritionSummary`** — `@dataclass(frozen=True, slots=True)` with `meal_type: MealType`, `entry_count: int`, `totals: DailyNutritionTotals`; non-negative count validation
- **`DailyNutritionLogSummary`** — `@dataclass(frozen=True, slots=True)` with `entry_count: int`, `totals: DailyNutritionTotals`, `meals: tuple[MealNutritionSummary, ...]`; strict four-meal invariant, exact breakfast→lunch→dinner→snack order, duplicate/missing/extra meal rejection, no silent sorting or repair
- **`calculate_daily_nutrition_totals(*, entries)`** — keyword-only pure function; requires `tuple[NutritionLogEntry, ...]`; empty tuple returns zeros; Decimal-only arithmetic; two-decimal ROUND_HALF_UP; no calorie-from-macro derivation, no target comparison, no recommendations
- **`summarize_daily_nutrition_log(*, entries)`** — keyword-only pure function; same tuple validation; delegates to `calculate_daily_nutrition_totals` for both overall and per-meal totals (no formula duplication); exactly four meal summaries in stable order; zero-entry meals included with zero totals; deterministic, no sorting by nutrition values
- **`InvalidNutritionLogEntryError`** — extends `NutritionLogError`; stable safe default message "Nutrition log entry data is invalid."; no sensitive/nutrition values, no HTTP/FastAPI/SQLAlchemy dependencies
- **Deterministic Decimal arithmetic** — no binary floats, no float conversion; ROUND_HALF_UP to two decimal places
- **Immutable domain results** — all dataclasses are frozen and slotted
- **148 new deterministic tests** — MealType, MEAL_TYPE_ORDER, constants, NutritionLogEntry validation (UUID, food-name, serving-description, meal-type, Decimal), DailyNutritionTotals, MealNutritionSummary, DailyNutritionLogSummary, calculate_daily_nutrition_totals, summarize_daily_nutrition_log, architecture purity
- **No API endpoint, no response schema, no persistence** — purely a domain layer
- **No ORM changes, no migrations, no schema modifications**
- **No authentication changes; no calculation/target/summary behavior changed**
- **No frontend changes; no .env required; no Docker/PostgreSQL required**

Phase 4E-4 audited, regression-validated, and froze the complete Phase 4E foundation (domain builder, strict schemas, authenticated read-only GET endpoint). No production defects were found. One test-quality defect was corrected in `tests/test_current_user.py` (an un-awaited coroutine assertion that emitted a `RuntimeWarning`, now `assert_awaited_once()`). The endpoint behavior, schemas, domain builder, ORM models, migrations, and dependencies are unchanged from Phase 4E-3. The Phase 4E foundation is frozen and ready for the next explicitly specified phase.

### Phase 4E-3 highlights

- **New authenticated endpoint** — `GET /api/v1/nutrition-profile/summary`
- **Bearer token required** — reuses the existing `get_current_user` dependency and the existing `BearerAuth` security scheme (no duplicate scheme, no manual token parsing, no JWT decoding)
- **Explicit `reference_date` query parameter** — required (no default), parsed by FastAPI/Pydantic as an ISO `date` (`YYYY-MM-DD`); missing/malformed/impossible dates are rejected (HTTP 422 via the existing validation envelope); `reference_date` is never inferred from `date.today()`, `datetime.now()`, or token timestamps
- **Thin orchestration-only endpoint** — resolves `current_user`, the request-scoped `AsyncSession`, the existing `NutritionProfileRepository`, the existing `NutritionProfileService.get_profile(user_id=current_user.id)`, then calls the verified `calculate_nutrition_metrics()`, `calculate_nutrition_targets()`, `build_nutrition_summary()`, and `NutritionSummaryData.from_result()` exactly once each; no formulas, summary rules, or strings live in the route
- **Current-user isolation** — loads the profile only with `current_user.id`; no `user_id` is accepted from path/query/body; BearerAuth protects the endpoint
- **Existing schema helpers reused** — the response uses `NutritionSummarySuccessResponse` and `NutritionSummaryData.from_result()`; the exact verified domain output (overview, six ordered item codes, tones) is preserved; the default success message `"Nutrition summary generated successfully."` is unchanged
- **Read-only** — no commit, flush, refresh, add, add_all, delete, merge, or direct write query; the user object and `NutritionProfile` object are never mutated; calculated metrics, targets, and summary content are NOT persisted
- **Safe error mapping** — missing profile → existing `NUTRITION_PROFILE_NOT_FOUND` (HTTP 404); `UnsupportedBMRCalculationError` → `BMR_CALCULATION_UNSUPPORTED` (HTTP 422); `CalorieTargetBelowMinimumError` → `CALORIE_TARGET_BELOW_MINIMUM` (HTTP 422); `reference_date` equal to or before `date_of_birth` → `INVALID_CALCULATION_INPUT` (HTTP 422); unexpected errors propagate to the existing global handler (`INTERNAL_SERVER_ERROR`, HTTP 500) with no raw exception detail
- **Transaction rules** — uses the existing request-scoped `get_db_session`; ORM models, Base metadata, and migrations are unchanged
- **OpenAPI** — the GET operation is documented with the `BearerAuth` security scheme and a required `reference_date` query parameter of `format: date`; exactly one bearer scheme exists; register/login/health remain public, `/auth/me` and the nutrition-profile routes remain protected; no POST/PATCH/DELETE summary operations exist; the static `/summary` route is registered before any possible dynamic route
- **108 new deterministic API tests** — route registration, OpenAPI contract, authentication (missing/invalid/expired/unknown/inactive), `reference_date` validation, user isolation, repository/service reuse, calculation orchestration spies, summary orchestration spies, success-response shape/privacy, domain-error mapping, unexpected-error safety, read-only assertions, and regressions
- **No new dependencies** — only the declared project dependencies are used
- **No frontend changes** — backend-only
- **No USDA / Groq / AI integration** — no AI-generated nutrition information, no meal plans, no cheat meals, no food/recipe/ingredient search
- **Estimates only** — BMI is a screening measure (not a diagnosis); BMR/TDEE/calorie/macro values are general estimates (not medical prescriptions); no medical approval, certification, or guaranteed outcomes are claimed

### Phase 4E-4 highlights — Final Audit and Freeze

- **Full-chain audit** — verified the domain summary module, strict schemas, authenticated GET endpoint, authentication/user-isolation, error contracts, read-only/non-persistence, privacy/response-minimization, and the OpenAPI contract
- **No production defect found** — the implementation was confirmed deterministic, authenticated, user-isolated, read-only, non-persistent, privacy-preserving, medically cautious, free of diagnosis/treatment/guarantee/prediction language, free of hidden system-clock behavior, free of formula/summary-rule duplication, and free of AI-generated content
- **Test-quality correction** — fixed one un-awaited coroutine assertion in `tests/test_current_user.py` (`awaited_once()` → `assert_awaited_once()`), removing a `RuntimeWarning`
- **Regression validation** — full suite 2607/2607 pass; Ruff format and lint clean; OpenAPI has exactly one `BearerAuth` scheme, the summary path is GET-only, `reference_date` is required with `format: date`, and all 10 operation IDs are unique
- **Integrity preserved** — ORM metadata unchanged (`users`, `nutrition_profiles`); two Alembic migration files byte-for-byte unchanged; no `create_all`/autogenerate; no `.env` or real secrets; import-time DB connection does not occur; two independent `create_app()` instances are distinct
- **Frozen** — no ORM/migration/authentication/schema/route changes; ready for the next explicitly specified phase

### Phase 4E-2 highlights

- **New strict schema module** — `app/schemas/nutrition_summaries.py`; Pydantic-based, framework-independent (no FastAPI/APIRouter/SQLAlchemy/database/repository/service/environment/network/AI imports); imports and reuses the verified Phase 4E-1 domain types (`NutritionSummaryTone`, `NutritionSummaryItem`, `NutritionSummaryResult`)
- **`NutritionSummaryItemData`** — immutable Pydantic model (`ConfigDict(extra="forbid", frozen=True)`) with `code`, `title`, `message`, `tone`; strict validation: code matches `^[A-Z][A-Z0-9_]*$` (1–100 chars, whitespace stripped, lowercase never silently uppercased); title (1–120) and message (1–1000) strip surrounding whitespace, preserve internal text/punctuation, reject control characters/null bytes; tone reuses the existing `NutritionSummaryTone` enum (no duplicate enum)
- **`NutritionSummaryData`** — immutable Pydantic model with `overview: str` and `items: tuple[NutritionSummaryItemData, ...]`; overview validated (1–1000, control-char/null-byte rejection); items stored as an immutable tuple, must contain exactly `EXPECTED_NUTRITION_SUMMARY_ITEM_COUNT` (6) entries with unique codes matching the exact ordered `EXPECTED_NUTRITION_SUMMARY_CODES` contract; wrong order/unexpected/duplicate/missing codes are rejected, never silently sorted or repaired
- **`NutritionSummarySuccessResponse`** — follows the existing success-envelope convention (`success: Literal[True] = True`, `message: str = "Nutrition summary generated successfully."`, `data: NutritionSummaryData`; `ConfigDict(extra="forbid")`)
- **Deterministic conversion helpers** — `NutritionSummaryItemData.from_result()` and `NutritionSummaryData.from_result()` copy the verified domain output exactly (no rule evaluation, no message generation, no tone selection, no code normalization, no formula calls); domain inputs are never mutated
- **No duplicated summary rules** — the schema layer only represents and converts existing Phase 4E-1 output; only the stable structural code order is expressed as a schema-level constant
- **Serialization** — tone serializes as its lowercase string value; items serialize as a JSON array; response contains no user id/email/password/hash/token/JWT/database/secret/timestamp fields
- **250 new deterministic tests** — architecture/boundary checks, item and data configuration, code/title/message/overview validation, tone reuse and serialization, conversion helpers, tuple storage, exact count/uniqueness/order validation, success-response behavior, privacy, safety-text preservation, domain compatibility, exports, and phase boundaries
- **No API endpoint, no router changes, no persistence, no ORM/migration changes, no AI** — Phase 4E-1 domain behavior and calculation API behavior are unchanged

### Phase 4E-1 highlights

- **New pure domain module** — `app/core/nutrition_summaries.py`; framework-independent, no FastAPI/Pydantic/SQLAlchemy/database/network/environment/AI dependencies; only Python standard-library and existing NutriMind domain types imported
- **`NutritionSummaryTone` (StrEnum)** — `INFORMATIONAL="informational"`, `CAUTION="caution"`; no SUCCESS/FAILURE/HEALTHY/UNHEALTHY/GOOD/BAD/DANGER values
- **`NutritionSummaryItem`** — `@dataclass(frozen=True, slots=True)` with `code`, `title`, `message`, `tone`; immutable; no global mutable state
- **`NutritionSummaryResult`** — `@dataclass(frozen=True, slots=True)` with `overview: str` and `items: tuple[NutritionSummaryItem, ...]`; tuple-based, immutable
- **`build_nutrition_summary(*, metrics, targets, goal)`** — keyword-only, deterministic, rule-based builder; takes a `NutritionCalculationResult`, a `NutritionTargetResult`, and a `NutritionGoal`; does NOT execute any formula and does NOT recalculate age/BMI/BMI-category/BMR/TDEE/calorie/macro targets; reuses verified input values
- **Six ordered summary items with stable codes** — `BMI_SCREENING_CONTEXT`, `DAILY_ENERGY_ESTIMATE`, `CALORIE_TARGET_CONTEXT`, `MACRONUTRIENT_TARGET_CONTEXT`, `GOAL_CONTEXT`, `GENERAL_ESTIMATE_LIMITATION`; deterministic order and unique codes
- **BMI screening rules** — uses the existing `BMICategory` enum; tone CAUTION for underweight/overweight/obesity, INFORMATIONAL for healthy_weight; every message states BMI is a screening measure that does not directly measure body composition or diagnose health; no malnutrition/obesity/disease diagnosis, no shame, no "you are healthy"/"perfect BMI" wording
- **Energy rules** — uses supplied `bmr_kcal_per_day` and `tdee_kcal_per_day`; explains BMR (rest) vs TDEE (total daily, activity-based); both described as estimates, not exact values
- **Calorie-target rules** — uses supplied `calorie_target_kcal_per_day`; described as a general estimate from verified TDEE and selected goal; no guarantee, no weekly/period prediction
- **Macronutrient rules** — uses supplied `protein_g_per_day`, `carbohydrate_g_per_day`, `fat_g_per_day`; described as estimated daily targets based on selected goal distribution; general guidance, not a medical prescription
- **Goal-context rules** — every existing `NutritionGoal` member (MAINTAIN_WEIGHT, LOSE_WEIGHT, GAIN_WEIGHT, GAIN_MUSCLE) handled explicitly with neutral wording; no guaranteed outcomes, no weekly/period-change predictions; unknown value fails with `ValueError`
- **General-estimate limitation** — final CAUTION item; results are general estimates, individual needs vary, and pregnancy/medical conditions/medications/athletic training/growth may require guidance from a qualified healthcare or nutrition professional
- **Deterministic overview** — explains the summary is based on verified profile calculations and selected goal; values are estimates; no medical claims, guarantees, or health-state claims; no date, time, user identifiers, or secrets
- **Validation** — rejects bool age, zero/negative age, NaN/Inf/zero/negative BMI/BMR/TDEE, calorie target below the reused `MINIMUM_CALORIE_TARGET` (exact minimum accepted), zero/negative macro targets, invalid BMI category, invalid goal, and wrong result types; Decimal-safe (no float conversion), no magic duplicated minimum value
- **No API endpoint, no response schema, no persistence** — purely a domain layer; calculation API behavior, OpenAPI, and routes are unchanged
- **156 new deterministic tests** — architecture boundaries, enum values, dataclass immutability/slots, function purity, exact item count/order/codes, BMI/energy/calorie/macro/goal/limitation content, validation, privacy, determinism, Decimal preservation; existing Phase 4D-1/4D-2/4D-3/4D-4 regressions remain unchanged and pass
- **No ORM changes, no migrations, no schema modifications**
- **No authentication changes; no nutrition-profile API behavior changes; no calculation API changes**
- **No frontend changes; no .env required; no Docker/PostgreSQL required**

### Phase 4D-4 — Authenticated Nutrition Calculation API Integration (completed)

### Phase 4D-3 highlights

- **NutritionMetricsData** — strict typed Pydantic response schema for verified Phase 4D-1 metrics (age_years, bmi, bmi_category, bmr_kcal_per_day, tdee_kcal_per_day); extra="forbid", frozen=True; Decimal values preserved; existing BMICategory reused; comprehensive validation (age > 0, finite positive Decimal for BMI/BMR/TDEE, NaN/Infinity rejection)
- **NutritionTargetsData** — strict typed Pydantic response schema for verified Phase 4D-2 targets (calorie_target_kcal_per_day, protein_g_per_day, carbohydrate_g_per_day, fat_g_per_day); extra="forbid", frozen=True; reuses existing MINIMUM_CALORIE_TARGET constant; rejects below-minimum calorie targets without silent clamping
- **CalculatedNutritionData** — combined schema nesting NutritionMetricsData and NutritionTargetsData; extra="forbid", frozen=True; metrics and goal-dependent targets remain logically separated
- **CalculatedNutritionSuccessResponse** — follows existing success envelope pattern (success: Literal[True] = True, message: str with default, data: CalculatedNutritionData); extra="forbid"
- **from_result() helpers** — optional typed class methods on NutritionMetricsData, NutritionTargetsData, and CalculatedNutritionData for safe conversion from domain result objects (NutritionCalculationResult, NutritionTargetResult); no recalculation, no mutation, no duck-typed Any
- **Schema-domain separation** — domain calculation layer (nutrition_calculations.py) remains pure Python with dataclasses; no Pydantic dependency; schemas import domain types but domain does not import schemas
- **Decimal JSON serialization** — Pydantic v2 serializes Decimal values as JSON strings; verified by tests
- **170 new deterministic tests** — covers valid construction, missing fields, null fields, extra fields, age/bmi/bmr/tdee/calorie/macro validation, NaN/Infinity, frozen immutability, JSON serialization, Decimal preservation, BMICategory reuse, from_result conversion, schema boundaries (no FastAPI/SQLAlchemy/database/network/environment), application boundaries (existing routes unchanged, no calculation endpoint, OpenAPI contract)
- **No API endpoint added** — schemas are not exposed through any router
- **No calculated values persisted** — schemas are response-only models
- **No ORM changes, no migrations, no schema modifications**
- **No authentication changes**
- **No nutrition-profile API behavior changes**
- **No frontend changes**
- **No local .env required for tests; no Docker required; no PostgreSQL required**

### Phase 4D-2 highlights

- **Calorie target function** — `calculate_calorie_target(tdee_kcal_per_day, goal)` in `app/core/nutrition_calculations.py`; applies a fixed adjustment per `NutritionGoal`; rounds to whole kcal/day (`ROUND_HALF_UP`); raises `CalorieTargetBelowMinimumError` if below 1200 kcal/day
- **Calorie adjustments** — immutable `CALORIE_ADJUSTMENTS` `MappingProxyType` with all 4 `NutritionGoal` values: maintain ±0 kcal, lose −500 kcal, gain weight +300 kcal, gain muscle +250 kcal
- **General application minimum** — `MINIMUM_CALORIE_TARGET = Decimal("1200")`; values below this raise `CalorieTargetBelowMinimumError` rather than being silently clamped
- **MacroDistribution** — `@dataclass(frozen=True, slots=True)` per-goal percentage distribution (`protein`, `fat`, `carbohydrate`); all four goals each total exactly `Decimal("1.00")`
- **MACRO_DISTRIBUTIONS** — immutable `MappingProxyType` with explicit percentages for every goal
- **Macronutrient targets** — `calculate_macronutrient_targets(calorie_target_kcal_per_day, goal)` returns `MacronutrientTargets` frozen dataclass with `protein_g_per_day`, `carbohydrate_g_per_day`, `fat_g_per_day`; uses standard energy densities (4 kcal/g for protein and carbohydrate, 9 kcal/g for fat); `ROUND_HALF_UP` to whole grams
- **Combined target result** — `calculate_nutrition_targets(tdee_kcal_per_day, goal)` returns `NutritionTargetResult` frozen dataclass; reuses `calculate_calorie_target` and `calculate_macronutrient_targets`; no formula duplication
- **CalorieTargetBelowMinimumError** — extends `NutritionCalculationError`; framework-independent; stable safe message; no HTTP status code, no FastAPI, no internal values
- **Energy conversion constants** — `PROTEIN_KCAL_PER_GRAM = Decimal("4")`, `CARBOHYDRATE_KCAL_PER_GRAM = Decimal("4")`, `FAT_KCAL_PER_GRAM = Decimal("9")`
- **Decimal arithmetic throughout** — no binary floats in any formula or constant
- **Results are estimates** — not diagnoses, not medical prescriptions, not guaranteed outcomes
- **No persistence** — calorie targets, protein targets, carbohydrate targets, and fat targets are computed in memory; no database columns, no storage, no API endpoints
- **121 new deterministic tests** — covers constants, calorie adjustments (completeness, immutability, Decimal-only), calorie target (all four goals, rounding, validation, minimum enforcement, immutability), MacroDistribution (frozen, slots, correct values, percentage totals), macro mapping (completeness, immutability), macronutrient targets (all four goals, known values, rounding, validation, frozen/slots), combined target result (all four goals, delegation, exception propagation, absent fields), exception hierarchy, domain purity
- **No API endpoints added** — targets remain internal domain logic
- **No ORM changes, no migrations, no schema modifications**
- **No authentication changes**
- **No nutrition-profile API behavior changes**
- **No frontend changes**
- **No local .env required for tests; no Docker required; no PostgreSQL required**

### Macro distributions

| Goal | Protein | Fat | Carbohydrate |
|------|---------|-----|--------------|
| Maintain weight | 25% | 30% | 45% |
| Lose weight | 30% | 30% | 40% |
| Gain weight | 25% | 25% | 50% |
| Gain muscle | 30% | 25% | 45% |

### Accuracy and safety

- Calorie targets are derived from TDEE and explicit goal adjustments; these are general product defaults and do not guarantee a particular weight-change rate
- A general application minimum of 1200 kcal/day is enforced; values below the supported floor raise a safe domain error rather than being silently clamped
- Macro percentages are explicit for every goal; protein and carbohydrate use 4 kcal/g, fat uses 9 kcal/g
- Macro gram rounding is independent per macronutrient (`ROUND_HALF_UP`); reconstructed calories may differ slightly from the calorie target
- Results are estimates, not diagnoses or medical prescriptions
- No weekly weight-change predictions, no time-to-goal predictions, no target dates
- No health scores, no recommendations, no meal plans

### Phase 4D-1 highlights

- **Pure deterministic domain functions** — `calculate_age`, `calculate_bmi`, `classify_bmi`, `calculate_bmr`, `calculate_tdee` in `app/core/nutrition_calculations.py`
- **Age calculation** — uses explicit `date_of_birth` and `reference_date` (keyword-only); no system clock, no `date.today()`, no `datetime.now()`; completed-year logic; correct handling of February 29 in non-leap years (maps to February 28); rejects same/future dates
- **BMI calculation** — standard metric formula: `weight_kg / (height_m)²`; pure `Decimal` arithmetic (no binary floats); validates finite values, range (50-300 cm, 10-700 kg), zero/negative rejection; rounded to 2 decimal places (`ROUND_HALF_UP`)
- **BMI category** — `BMICategory` enum with neutral labels (`underweight`, `healthy_weight`, `overweight`, `obesity`); CDC/WHO-aligned adult screening thresholds; classification uses unrounded BMI value to avoid threshold-crossing errors; documented as a screening measure, not a diagnosis
- **BMR — Mifflin-St Jeor equation** — male: `+5` constant, female: `−161` constant; `BiologicalSex.OTHER` and `BiologicalSex.PREFER_NOT_TO_SAY` raise `UnsupportedBMRCalculationError` because the selected equation does not define evidence-based constants for those options; no guessing, no averaging, no defaulting
- **TDEE** — `TDEE = BMR × activity_factor`; reusable `ACTIVITY_MULTIPLIERS` immutable `MappingProxyType` with all 5 `ActivityLevel` values (`1.2`, `1.375`, `1.55`, `1.725`, `1.9`)
- **Combined result** — `NutritionCalculationResult` frozen dataclass + `calculate_nutrition_metrics()` orchestrator; reuses individual functions; no formula duplication; BMI category determined from unrounded BMI
- **Domain exception hierarchy** — `NutritionCalculationError` → `UnsupportedBMRCalculationError`; framework-independent; no FastAPI, HTTPException, status codes, or sensitive data
- **Decimal arithmetic throughout** — no binary floats in formulas
- **Results are estimates** — not diagnoses, not medical prescriptions, not guaranteed
- **No persistence** — results are computed in memory; no database columns, no storage, no API endpoints
- **156 new deterministic tests** — 19 exception tests, 137 calculation tests; covers age boundaries, leap years, BMI thresholds, BMR sex constants, unsupported sex values, TDEE multipliers, domain purity (no FastAPI/SQLAlchemy/database/network/environment dependencies)
- **No API endpoints added** — calculations remain internal domain logic
- **No calorie targets, macro targets, health scores, diet plans, meal plans, food/recipe/ingredient search, USDA/Groq/AI functionality added**
- **No ORM changes, no migrations, no schema modifications**
- **No authentication changes**
- **No nutrition-profile API behavior changes**
- **No frontend changes**
- **No local .env required for tests; no Docker required; no PostgreSQL required**

### Accuracy and source documentation

- **Age formula**: Completed chronological years; leap-day mapped to February 28 in non-leap years.
- **BMI formula and categories**: CDC/WHO-aligned adult BMI screening guidance. BMI is a screening measure, does not directly measure body fat, and does not account for every individual factor.
- **BMR (Mifflin-St Jeor)**: Established predictive resting-energy equation: `BMR = 10×weight(kg) + 6.25×height(cm) − 5×age(years) + sex_constant`. Sex-specific constants exist for male (+5) and female (−161) only. Results are estimates and should not be used as a medical prescription.
- **TDEE activity multipliers**: Conventional estimation factors (`sedentary` 1.2, `lightly_active` 1.375, `moderately_active` 1.55, `very_active` 1.725, `extra_active` 1.9).

### Phase 4C highlights

- **Authenticated nutrition-profile API endpoints** — `POST /api/v1/nutrition-profile`, `GET /api/v1/nutrition-profile`, `PATCH /api/v1/nutrition-profile`
- **Bearer authentication required** for all three endpoints via existing `get_current_user()` dependency
- **Authenticated-user ownership** — endpoints use `current_user.id`; no `user_id` accepted from request body, query params, or path params
- **API-layer transaction ownership** — POST commits exactly once after successful service completion; PATCH commits exactly once; GET never commits, flushes, or mutates data
- **Safe error envelopes** — `{"success": false, "error": {"code": ..., "message": ..., "request_id": ...}}`; no `{"detail": ...}` wrapping, no SQL, no stack traces, no sensitive data
- **Error mappings** — duplicate profile → HTTP 409 `NUTRITION_PROFILE_ALREADY_EXISTS`; not found → HTTP 404 `NUTRITION_PROFILE_NOT_FOUND`; persistence failure → HTTP 503 `NUTRITION_PROFILE_UNAVAILABLE`
- **PATCH preserves existing semantics** — only explicitly supplied fields are updated; empty body is a no-op; nullable fields accept explicit null
- **Response validation** — ORM objects validated through `NutritionProfilePublic` response schema; no password, token, JWT claims, or secrets exposed
- **OpenAPI contract** — all three routes documented with BearerAuth security, correct request/response schemas, and appropriate status codes
- **No ORM changes, no migrations, no schema modifications**
- **No nutrition calculations, no BMI/BMR/TDEE, no food/recipe/ingredient search, no USDA/Groq/AI functionality**
- **No frontend changes in Phase 4C**
- **153 new deterministic API tests** — route registration, authentication (missing, invalid, expired, unknown, inactive), POST success/duplicate/persistence-failure, GET success/not-found, PATCH success/not-found/persistence-failure, ownership/IDOR protection, validation, error envelope, OpenAPI, regression
- **No local .env required for tests; no Docker required; no PostgreSQL required**

### Phase 4A highlights

- **Typed Nutrition Profile schemas** — `NutritionProfileBase`, `NutritionProfileCreate`, `NutritionProfileUpdate`, `NutritionProfilePublic`, `NutritionProfileData`, `NutritionProfileSuccessResponse`
- **Strict validation** — date-of-birth (must be before today), height (50–300 cm, 2 decimal places), weight (10–700 kg, 2 decimal places), target weight (10–700 kg, 2 decimal places, nullable), all enum fields (reuse existing `BiologicalSex`, `ActivityLevel`, `NutritionGoal`, `DietaryPreference`), NaN/Infinity rejection for all Decimal fields
- **Allergy normalization** — whitespace trimming, control-character/null-byte rejection, max 50 entries, max 100 characters per entry, case-insensitive deduplication, first-occurrence spelling preservation, order preservation, no mutation of caller-owned lists
- **PATCH semantics** — `NutritionProfileUpdate` with all fields optional; required fields (date_of_birth, biological_sex, height_cm, weight_kg, activity_level, goal) reject explicit null; nullable fields (target_weight_kg, dietary_preference) accept explicit null; allergies omitted means unchanged, empty list clears, null rejected
- **Ownership-field protection** — `id`, `user_id`, `created_at`, `updated_at` rejected from create/update schemas (`extra="forbid"`)
- **Public schema** — `from_attributes=True` for ORM compatibility; timezone-aware timestamp enforcement; no password, token, JWT claims, secrets, calculated fields, or nested User objects
- **Response envelope** — `NutritionProfileSuccessResponse` with `success: bool`, `message: str`, `data: NutritionProfileData` containing `profile: NutritionProfilePublic`
- **Existing enums reused** — no duplicate enum definitions, all four enums imported from `app.models.enums`
- **204 new deterministic schema tests** — imports, valid values, date-of-birth, height, weight, target-weight, enums, allergies, extra-field rejection, create, update PATCH semantics, public, response, schema/ORM alignment, security boundary, edge cases
- **No Nutrition Profile API endpoint, repository, service, database query, ORM change, migration, BMI/BMR/TDEE/calorie/macro calculation, diet/meal plan, USDA/Groq/AI integration, or frontend change**
- **No .env required, no Docker required, no PostgreSQL required, no real secrets stored**
- **Docker not required for tests; PostgreSQL not required for tests; no .env required for tests**

### Phase 3G highlights

- **Complete authentication foundation audit** — password security, registration, login, JWT access tokens, Bearer authentication, current-user dependency, `/auth/me`, safe error envelopes, request validation, transaction ownership, OpenAPI contract, secret storage
- **Argon2-only password hashing** via `pwdlib` — no weak hashing schemes, no reversible encryption, no plaintext storage; `hash_password()` rejects empty input; `verify_password()` safely returns `False` for unknown/invalid hash formats
- **Enumeration-resistant login** — identical HTTP 401, `INVALID_CREDENTIALS`, and `"Invalid email or password."` for both unknown email and incorrect password
- **API-owned registration transaction** — endpoint commits exactly once after user creation and token generation; rolls back on duplicate email, token configuration failure, and unexpected errors
- **Read-only login, current-user, and /auth/me** — no commit, flush, refresh, or mutation
- **Strict JWT access-token security** — HS256 only; algorithm from settings, never from token header; `AccessTokenClaims` with `extra="forbid"`, `frozen=True`; UUID-based `sub`; valid issuer/audience/type enforcement; manual `iat`/`exp` validation; raw JWT exceptions never exposed
- **Whitespace-only Bearer token correctly handled** — `Authorization: Bearer   ` returns HTTP 401, `INVALID_ACCESS_TOKEN`
- **Weak test assertions fixed** — `test_password_absent` now correctly verifies submitted password values are not present in responses
- **Safe error envelopes** — all authentication errors use `{"success": false, "error": {"code": ..., "message": ..., "request_id": ...}}`; no SQL, constraint names, stack traces, passwords, password hashes, access tokens, or JWT secrets exposed
- **X-Request-ID** preserved in both response headers and error body for all authentication endpoints
- **OpenAPI BearerAuth** — type http, scheme bearer; `/auth/me` protected; `/auth/register`, `/auth/login`, `/health` public; no refresh token, logout, role, permission, or admin routes
- **No real secrets stored** — tests use deterministic in-memory fake settings; no `.env` files created; production secrets must be injected at runtime through hosting-provider secret settings, process environment, or managed secret storage
- **No refresh-token generation, decoding, rotation, revocation, or persistence**
- **No logout, no token blacklist, no cookie authentication, no roles, no permissions, no admin authorization**
- **No database schema changes, no migrations, no ORM modifications, no frontend changes**
- **Docker not required for tests; PostgreSQL not required for tests; no .env required for tests**
- **4 new regression tests added** — whitespace-only Bearer token (4 variants); weak assertions hardened

### Phase 3F highlights

- **HTTP Bearer access-token authentication** via `HTTPBearer` (FastAPI `Security`) with `auto_error=False`
- **Current-user dependency** in `app/api/dependencies/authentication.py` — `get_current_user()` reuses `decode_access_token()` for token validation, `UserRepository.get_by_id()` for user lookup
- **User look-up by ID** — `UserRepository.get_by_id(user_id)` added using `select(User).where(User.id == user_id)` with `scalars().one_or_none()`; no session creation, commit, flush, or refresh
- **GET /api/v1/auth/me** — returns `PublicUser` (id, email, is_active, is_verified, created_at, updated_at); no password, password_hash, access token, refresh token, JWT claims, JWT secret, NutritionProfile, role, or permissions
- **Safe error responses:**
  - Missing/wrong Authorization → HTTP 401, `AUTHENTICATION_REQUIRED`, `"Authentication is required."`, `WWW-Authenticate: Bearer`
  - Invalid/malformed token → HTTP 401, `INVALID_ACCESS_TOKEN`, `"The access token is invalid."`
  - Expired token → HTTP 401, `ACCESS_TOKEN_EXPIRED`, `"The access token has expired."`
  - Unknown user → HTTP 401, `INVALID_ACCESS_TOKEN` (no user-existence disclosure)
  - Inactive user → HTTP 403, `INACTIVE_ACCOUNT`, `"This account is inactive."`
  - Token misconfiguration → HTTP 503, `AUTHENTICATION_UNAVAILABLE`
- **All token validation** goes through existing `decode_access_token()` — no direct `jwt.decode()` calls, no unverified claims, no algorithm-header trust
- **OpenAPI BearerAuth scheme** — type http, scheme bearer; `/auth/me` is protected; `/auth/register`, `/auth/login`, `/health` remain public
- **No refresh tokens, no logout, no roles, no permissions, no authentication middleware**
- **X-Request-ID** included in both response headers and error body
- **Request IDs** present on all responses
- **New tests** for `get_current_user` dependency, `/auth/me` endpoint, `get_by_id` repository method, and OpenAPI contract
- **No database schema changes, no migrations, no ORM modifications, no frontend changes**
- **No .env files created, no real secrets stored**
- **Unit tests require no Docker, no PostgreSQL, no .env**

### Phase 3C highlights

- **Authentication domain exceptions** in `app/core/auth_exceptions.py` — `AuthenticationError`, `EmailAlreadyRegisteredError`, `InvalidCredentialsError`, `InactiveAccountError`; no FastAPI, HTTP status code, or password dependencies
- **UserRepository** in `app/repositories/user.py` — `get_by_email()` (scalar lookup), `create()` (flush only, caller owns commit); no generic CRUD; no commit/close/rollback in repository
- **Unique-email conflict handling** — `create()` converts `IntegrityError` (constraint `uq_users_email`) into `EmailAlreadyRegisteredError`; unrelated `IntegrityError` re-raised; no SQL, constraint names, or password hashes exposed in domain exceptions
- **AuthenticationService** in `app/services/authentication.py` — `register()` (pre-check duplicate, hash once via `hash_password()`, persist), `authenticate()` (lookup, verify via `verify_password()`, check active); no commit, no JWT issuance, no token creation, no session creation
- **Enumeration prevention** — unknown email and wrong password both raise `InvalidCredentialsError` with identical message "Invalid email or password."
- **Inactive account** — `InactiveAccountError` raised only after valid credentials are confirmed
- **Password safety** — hashing only in authentication service via `core/security.py`; plaintext passwords never passed to repository; password hashes never returned from service methods; no passwords or hashes logged
- **115 new deterministic tests** — 24 exception tests, 41 repository tests (mock session), 50 authentication service tests (mock repository); no Docker, no PostgreSQL required
- New packages: `app/repositories/`, `app/services/`

### Phase 3B highlights

- **Authentication schemas** in `app/schemas/auth.py` — `RegisterRequest`, `LoginRequest`, `PublicUser`, `TokenPair`, `AuthResponse`
- **Email validation** via `EmailStr` (Pydantic's maintained email-validator integration)
- **Email normalization** — leading/trailing whitespace stripped, then lowercased; plus-addressing and dots preserved; no provider-specific or DNS behavior
- **Registration password policy** — minimum 8 characters, maximum 128 characters, whitespace-only rejected; passwords preserved exactly (not stripped, normalized, or hashed)
- **Login password input validation** — maximum 128 characters, empty/whitespace-only rejected; no minimum length; passwords preserved exactly
- **Extra-field protection** (`extra="forbid"`) — mass-assignment-style fields (`is_active`, `is_verified`, `is_admin`, `role`, `password_hash`, `id`, `created_at`, `updated_at`) rejected at the API boundary
- **Password representation safety** — `Field(repr=False)` hides passwords from normal `repr()` and `str()` output; passwords remain accessible through `.password`
- **PublicUser response schema** — `from_attributes=True` for ORM compatibility; contains only `id`, `email`, `is_active`, `is_verified`, `created_at`, `updated_at`; no password or token data
- **TokenPair response contract** — `access_token`, `refresh_token`, `token_type: Literal["bearer"]`; empty/whitespace-only tokens rejected; no token generation or decoding
- **AuthResponse** — combines `PublicUser` and `TokenPair` as a future authentication response contract
- **113 new deterministic schema tests** — email validation, normalization, password policy, extra-field rejection, representation safety, PublicUser ORM compatibility, TokenPair contract, AuthResponse nesting, import side effects
- **Raw Pydantic ValidationError structures** may retain rejected password input in structured error data; future authentication endpoints must sanitize validation responses and must not directly log raw validation errors
- `email-validator>=2.1,<3.0` added as an explicit runtime dependency
- No registration endpoint, login endpoint, logout endpoint, or authentication router exists
- No JWT tokens are generated or decoded
- No database queries, password hashing, or password verification occurs in schema layer

### Phase 3A highlights

- ORM metadata contains exactly `users` and `nutrition_profiles` — no unexpected tables
- All four SQLAlchemy Enum columns use `values_callable` to persist lowercase `StrEnum.value`
- Migration graph: exactly 2 revisions, 1 head (`99a3b19be1b8`), 1 base (`3f0c6eb4f49e`), no branches, no cycles
- `alembic check` reports: **No new upgrade operations detected**
- Live schema matches ORM metadata and migration: columns, types, defaults, constraints, indexes, enums
- Database row counts: `users=0`, `nutrition_profiles=0`
- Four PostgreSQL enum types with correct lowercase values and ordering
- Application imports without a database URL; creation produces two independent apps; OpenAPI schema generates correctly
- No `Base.metadata.create_all()` exists; no automatic migrations run during startup
- No credentials, seed data, or personal information in source
- No authentication, password hashing, JWT, nutrition calculations, USDA, or AI features implemented
- Docker volume `nutrimind_postgres_data` preserved

The Phase 2 database/model foundation is frozen and ready for Phase 3 authentication.

The Alembic migration `99a3b19be1b8` was applied, tested, and validated during Phases 2D-3 and 2D-4.

### What was added (Phases 2D-1 through 2D-3)

- **User ORM model** (`app/models/user.py`) — table `users` with UUID primary key, email, password_hash, is_active, is_verified, and timezone-aware timestamps
- **NutritionProfile ORM model** (`app/models/nutrition_profile.py`) — table `nutrition_profiles` with UUID primary key, foreign key to users, personal nutrition inputs (date_of_birth, biological_sex, height, weight, activity_level, goal), optional preferences (dietary_preference, allergies), and timestamps
- **UUID primary keys** — generated in application code via `uuid.uuid4` using SQLAlchemy's portable `Uuid` type
- **Timezone-aware timestamps** — `created_at` and `updated_at` with database-side server defaults
- **Domain enums** — `BiologicalSex`, `ActivityLevel`, `NutritionGoal`, `DietaryPreference` with stable lowercase database-friendly values
- **Typed SQLAlchemy relationships** — one-to-one User → NutritionProfile with `back_populates`, cascade `all, delete-orphan`, and `single_parent=True`
- **Database constraints in metadata** — unique email, unique user_id, height/weight/target-weight check constraints, foreign key with `ON DELETE CASCADE`
- **Allergies stored as JSONB** with safe `default=list` and JSON array server default
- **Calculated nutrition outputs are intentionally not stored** — age, BMI, BMR, TDEE, calorie/protein/carb/fat targets will be computed in future phases
- **65 model-focused tests** covering ORM metadata structure, constraints, enums, relationships, forbidden fields, and migration boundary
- **Alembic migration created** — revision `99a3b19be1b8` follows baseline `3f0c6eb4f49e`
- **Migration reviewed and corrected** — enum values fixed to lowercase; downgrade drops enum types; constraint names verified; redundant indexes avoided
- **45 migration-content tests** covering revision graph, upgrade/downgrade operations, schema, enums, forbidden content, and boundary checks
- **Offline SQL generation validated** — correct enum creation, table ordering, constraints, foreign keys, and credentials absence

### What does not exist yet (planned for future phases)

- Calorie targets, macronutrient targets, health scores
- Food, recipe, ingredient search
- USDA nutrition database integration
- Groq / LLM / AI chatbot functionality
- Meal plans, diet plans, cheat meals
- Recommendations
- Refresh tokens, logout, token blacklist
- Roles, permissions, admin functionality
- OAuth, social login
- Frontend integration

### Phase 2D-3 — Live Migration Validation Results

- **Migration `99a3b19be1b8`** was applied successfully to live PostgreSQL (Docker, port 5433)
- **Tables created:** `users`, `nutrition_profiles` (plus `alembic_version`)
- **Four PostgreSQL enum types created:** `biological_sex`, `activity_level`, `nutrition_goal`, `dietary_preference` — all lowercase values verified
- **Column types validated:** UUID PK, VARCHAR(320) email, VARCHAR(128) password_hash, BOOLEAN with server defaults, TIMESTAMPTZ with now() defaults, NUMERIC(5,2) with check constraints, JSONB allergies with JSON array default, DATE, and all four enum columns
- **Constraints validated:**
  - `uq_users_email` — unique email enforcement
  - `uq_nutrition_profiles_user_id` — one-profile-per-user enforcement
  - `fk_nutrition_profiles_user_id` — foreign key references `users.id`
  - `ON DELETE CASCADE` — deleting a user cascades to their profile
  - `ck_nutrition_profiles_height_cm_range` (50–300) — boundary tested at 49.99, 50.00, 300.00, 300.01
  - `ck_nutrition_profiles_weight_kg_range` (10–700) — boundary tested at 9.99, 10.00, 700.00, 700.01
  - `ck_nutrition_profiles_target_weight_kg_range` (null or 10–700) — boundary tested at null, 9.99, 10.00, 700.00, 700.01
- **Database defaults exercised:** `is_active=true`, `is_verified=false`, `created_at`/`updated_at` with timezone-aware timestamps, allergies `[]`
- **NOT NULL enforcement:** all required columns reject nulls
- **Enum enforcement:** invalid values rejected for all four enums
- **Foreign key enforcement:** nonexistent user_id rejected with FK violation
- **ORM relationship validated:** bidirectional User↔NutritionProfile with eager loading
- **Session behavior validated:** explicit commit, rollback after error, session usability after rollback
- **Downgrade tested:** `alembic downgrade 3f0c6eb4f49e` removes both tables and all four enum types; `alembic_version` preserved
- **Re-upgrade tested:** `alembic upgrade head` recreates schema without errors
- **Final database revision:** `99a3b19be1b8 (head)`
- **Final application tables empty:** both `users` and `nutrition_profiles` contain 0 rows
- **No seed data, no authentication, no nutrition calculations**
- **ORM model fix:** added `values_callable` to all four `sa.Enum` columns to map Python `StrEnum` values (lowercase) to PostgreSQL enum values, matching the migration's lowercase enum strings

### Important design decisions

- **Models are registered in `Base.metadata`** via an import in `app/db/base.py`, which Alembic discovers in `target_metadata`
- **Migration `99a3b19be1b8`** creates the `users` and `nutrition_profiles` tables and has been **applied and validated** (Phase 2D-3)
- **No physical tables exist** — metadata only
- **Enum values in the migration use lowercase strings** matching the Python `StrEnum` values, not uppercase member names
- **Downgrade drops enum types explicitly** after removing dependent tables
- **No redundant indexes** — PostgreSQL unique constraints already create unique indexes
- **Constraint names are explicit and reviewable** — `uq_users_email`, `uq_nutrition_profiles_user_id`, `fk_nutrition_profiles_user_id`, `ck_nutrition_profiles_*_range`
- Validation and business logic intentionally omitted from the ORM layer — they belong in service/schema layers

## Requirements

- Python 3.11 or newer

## Setup

### 1. Create a virtual environment

```bash
# Windows (PowerShell)
python -m venv .venv
.venv\Scripts\Activate.ps1

# Windows (Command Prompt)
python -m venv .venv
.venv\Scripts\activate.bat

# Unix / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
# Runtime dependencies
pip install .

# Development dependencies (pytest, ruff, httpx)
pip install -e ".[dev]"
```

### 3. Environment setup

```bash
cp .env.example .env
```

Edit `.env` if needed. The app works out of the box for development without modification.

### 4. Run the development server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Verify the backend

- Health endpoint: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)
- API docs (Swagger): [http://localhost:8000/docs](http://localhost:8000/docs)
- API docs (ReDoc): [http://localhost:8000/redoc](http://localhost:8000/redoc)

## Tests

```bash
pytest
```

## Code quality

```bash
# Format
ruff format .

# Format check (CI)
ruff format --check .

# Lint
ruff check .

# Lint with auto-fix
ruff check . --fix
```

## Troubleshooting

- Ensure you are in the `backend/` directory when running commands.
- Activate the virtual environment before installing dependencies or running the server.
- If `pip install -e ".[dev]"` fails, try `pip install -e ".[dev]"` with quotes.
- If port 8000 is in use, change `BACKEND_PORT` in `.env`.

## Security

- Never commit the real `.env` file.
- Never commit API keys, JWT secrets, or database passwords.
- The `.env.example` file contains placeholder values only.
- The `.gitignore` already ignores `.env` and `.venv/`.

## Project structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # Application factory and entry point
│   ├── api/
│   │   ├── __init__.py
│   │   ├── dependencies/
│   │   │   ├── __init__.py
│   │   │   └── authentication.py  # get_current_user dependency
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── auth.py            # Auth endpoints (register, login, me)
│   │       ├── health.py          # Health check endpoint
│   │       ├── nutrition_profile.py # Nutrition profile API endpoints
│   │       └── router.py          # API v1 router
│   ├── core/
│   │   ├── __init__.py
│   │   ├── auth_exceptions.py             # Authentication domain exceptions
│   │   ├── config.py                      # Pydantic settings
│   │   ├── exceptions.py                  # Centralized exception handlers
│   │   ├── logging.py                     # Structured logging setup
│   │   ├── middleware.py                  # Request-ID middleware
│   │   ├── nutrition_log_exceptions.py    # Phase 4F-1 nutrition-log domain exceptions
│   │   ├── nutrition_logs.py              # Phase 4F-1 nutrition-log domain
│   │   ├── nutrition_profile_exceptions.py # Nutrition profile domain exceptions
│   │   ├── security.py                    # Password hashing (Argon2 via pwdlib)
│   │   ├── token_exceptions.py            # Token domain exceptions
│   │   └── tokens.py                      # JWT access token creation/decoding
│   ├── db/
│   │   ├── __init__.py
│   │   ├── base.py            # Declarative Base
│   │   ├── dependencies.py    # get_db_session dependency
│   │   └── session.py         # Database session factory
│   ├── models/
│   │   ├── __init__.py
│   │   ├── enums.py           # Domain enums (BiologicalSex, ActivityLevel, etc.)
│   │   ├── mixins.py          # Timestamp mixin
│   │   ├── nutrition_profile.py
│   │   └── user.py
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── nutrition_profile.py  # NutritionProfileRepository
│   │   └── user.py               # UserRepository
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── auth.py                      # Auth schemas
│   │   ├── nutrition_calculations.py    # Phase 4D-3 nutrition calculation schemas
│   │   └── nutrition_profile.py         # NutritionProfile schemas
│   └── services/
│       ├── __init__.py
│       ├── authentication.py      # AuthenticationService
│       └── nutrition_profile.py   # NutritionProfileService
├── alembic/
│   ├── env.py                # Async Alembic migration environment
│   ├── script.py.mako        # Migration template
│   ├── README
│   └── versions/
│       ├── 3f0c6eb4f49e_baseline.py
│       └── 99a3b19be1b8_create_users_and_nutrition_profiles.py
├── alembic.ini
├── tests/
│   ├── __init__.py
│   ├── test_auth_api.py                    # Auth API endpoint tests
│   ├── test_auth_exceptions.py             # Auth domain exception tests (24 tests)
│   ├── test_auth_me.py                     # /auth/me endpoint tests
│   ├── test_auth_schemas.py                # Auth schema validation tests (113 tests)
│   ├── test_authentication_service.py      # AuthenticationService tests (50 tests)
│   ├── test_current_user.py                # get_current_user dependency tests
│   ├── test_database.py                    # Database lifecycle tests
│   ├── test_health.py                      # Health endpoint and middleware tests
│   ├── test_migrations.py                  # Migration configuration tests
│   ├── test_models.py                      # ORM model metadata tests
│   ├── test_model_migration.py             # Migration content tests
│   ├── test_nutrition_calculation_schemas.py # Phase 4D-3 schema tests (170 tests)
│   ├── test_nutrition_log_exceptions.py    # Phase 4F-1 nutrition-log exception tests (27 tests)
│   ├── test_nutrition_logs.py              # Phase 4F-1 domain tests (148 tests)
│   ├── test_nutrition_profile_api.py       # Phase 4C API tests (153 tests)
│   ├── test_nutrition_profile_exceptions.py # Exception tests (35 tests)
│   ├── test_nutrition_profile_repository.py # Repository tests (133 tests)
│   ├── test_nutrition_profile_schemas.py    # Schema tests (204 tests)
│   ├── test_nutrition_profile_service.py    # Service tests (95 tests)
│   ├── test_security.py                    # Password hashing tests
│   ├── test_settings.py                    # Settings validation tests
│   ├── test_token_exceptions.py            # Token exception tests
│   ├── test_tokens.py                      # JWT token tests
│   └── test_user_repository.py             # UserRepository tests (41 tests)
├── .env.example
├── pyproject.toml
└── README.md
```

### Phase 4D-4 — Authenticated Nutrition Calculation API Integration

- **New authenticated endpoint** — `GET /api/v1/nutrition-profile/calculations`
- **Bearer token required** — reuses the existing `get_current_user` dependency and the existing `BearerAuth` security scheme (no duplicate scheme, no manual token parsing, no JWT decoding)
- **Explicit `reference_date` query parameter** — required (no default), parsed by FastAPI/Pydantic as an ISO `date` (`YYYY-MM-DD`); missing/malformed/impossible dates are rejected (HTTP 422 via the existing validation envelope); `reference_date` is never inferred from `date.today()`, `datetime.now()`, or token timestamps, keeping age calculations deterministic and timezone-independent
- **Existing calculation functions reused** — the endpoint calls the verified `calculate_nutrition_metrics()` and `calculate_nutrition_targets()` domain functions directly; no formulas are duplicated in the router
- **Existing schema helpers reused** — the response uses `CalculatedNutritionSuccessResponse` and `CalculatedNutritionData.from_results()`; Decimal values are preserved and serialized as JSON strings; the `BMICategory` enum serializes as its lowercase value
- **Derived read-only representation** — calculations are computed on demand from the authenticated user's persisted nutrition profile and the caller-supplied `reference_date`; calculated values are NOT persisted; no calculation record, no calculation history, no profile mutation, no user mutation
- **Profile lookup reuse** — loads the profile via the existing `NutritionProfileRepository` / `NutritionProfileService.get_profile()` using `current_user.id`; missing profile maps to the existing `NUTRITION_PROFILE_NOT_FOUND` (HTTP 404) contract
- **Safe error mapping** — reuses the existing error envelope with `request_id`:
  - Missing/invalid/expired/wrong-issuer/wrong-audience/wrong-type token → existing auth contract (HTTP 401) with `WWW-Authenticate: Bearer`; unknown/inactive user → existing contract (401/403)
  - `UnsupportedBMRCalculationError` (biological-sex `other` / `prefer_not_to_say`) → `BMR_CALCULATION_UNSUPPORTED` (HTTP 422), stable safe message, no guessed BMR, no fallback, no target calculation
  - `CalorieTargetBelowMinimumError` → `CALORIE_TARGET_BELOW_MINIMUM` (HTTP 422), stable safe message, no silent clamping
  - Invalid age inputs (`reference_date` equal to or before `date_of_birth`) → `INVALID_CALCULATION_INPUT` (HTTP 422)
  - Unexpected errors propagate to the existing global exception handler (`INTERNAL_SERVER_ERROR`, HTTP 500) with no raw exception detail exposed
- **Transaction rules** — uses the existing request-scoped `get_db_session`; no commit, flush, refresh, insert, update, or delete; ORM models, Base metadata, and migrations are unchanged
- **OpenAPI** — the GET operation is documented with the `BearerAuth` security scheme and a required `reference_date` query parameter of `format: date`; exactly one bearer scheme exists; register/login/health remain public, `/auth/me` and the nutrition-profile routes remain protected; no POST/PATCH/DELETE calculation operations exist
- **No new dependencies** — only the declared project dependencies are used
- **No frontend changes** — backend-only
- **No USDA / Groq / AI integration** — no AI-generated nutrition information, no meal plans, no cheat meals, no food/recipe/ingredient search
- **Estimates only** — BMI is a screening measure (not a diagnosis); BMR/TDEE/calorie/macro values are general estimates (not medical prescriptions); no medical approval, certification, or guaranteed outcomes are claimed

### Phase 4E-1 — Personalized Nutrition Summary Domain Foundation

- **New pure domain module** — `app/core/nutrition_summaries.py`; deterministic rule-based summaries only; no AI generation
- **No API endpoint** — the summary layer is not exposed through any router or response schema
- **No persistence** — summaries are built in memory from supplied verified results; nothing is stored
- **No new formulas** — the module reuses verified calculation results and existing enums/constants (`BMICategory`, `NutritionGoal`, `MINIMUM_CALORIE_TARGET`); no recalculation
- **Six ordered summary items** — `BMI_SCREENING_CONTEXT`, `DAILY_ENERGY_ESTIMATE`, `CALORIE_TARGET_CONTEXT`, `MACRONUTRIENT_TARGET_CONTEXT`, `GOAL_CONTEXT`, `GENERAL_ESTIMATE_LIMITATION`
- **BMI screening limitation** — every BMI message states BMI is a screening measure that does not directly measure body composition or diagnose health
- **General-estimate limitation** — final CAUTION item notes individual circumstances may require guidance from a qualified healthcare or nutrition professional
- **Immutable results** — `NutritionSummaryItem` and `NutritionSummaryResult` are frozen, slotted dataclasses; `items` is a tuple
- **Validation** — invalid manually constructed inputs (bool/zero/negative/NaN/Inf age, BMI, BMR, TDEE, calorie targets below minimum, macros, BMI category, goal) raise safe `ValueError`; Decimal-safe, no float conversion
- **Test count after validation** — 2249 backend tests pass (2093 existing + 156 new nutrition-summary tests); ruff format and lint pass

### Phase 5D-1 — Body-Weight Goal Domain Foundation

- **Phase completed** — pure, deterministic, framework-independent body-weight goal domain foundation
- **New pure domain modules** — `app/core/body_weight_goals.py` and `app/core/body_weight_goal_exceptions.py`; no API endpoint, no Pydantic schema, no ORM model, no migration, no repository, no service, no persistence
- **Goal direction** — `decrease`, `maintain`, `increase`; describes only the numerical relationship between starting and target weights (no health/medical/improvement labels)
- **Progress status** — `not_started`, `in_progress`, `target_reached`, `target_passed`; based only on numerical comparison (no on-track/off-track/healthy/risk labels)
- **Progress may be negative or above 100%** — `progress_percentage` is not clamped; moving away from target yields negative progress, passing the target yields above 100%
- **Remaining change may be negative** — `remaining_change_kg` is not clamped; it is negative after the target is passed
- **No clamping** — `change_achieved_kg`, `remaining_change_kg`, and `progress_percentage` are returned unclamped
- **No prediction** — no goal dates, no time-to-goal estimates, no weekly/monthly projections, no weight-loss-rate calculations
- **No medical interpretation** — no BMI/health/risk classifications, no recommendations, no diet/meal plans
- **No persistence** — no database access, no automatic profile synchronization; `target_weight_kg` on `NutritionProfile` (Phase 4A) remains an independent persisted field and is untouched
- **Reused constants** — `MIN_BODY_WEIGHT_KG`, `MAX_BODY_WEIGHT_KG`, `BODY_WEIGHT_DECIMAL_PLACES` imported from `app.core.body_weight` (not duplicated)
- **New constant** — `BODY_WEIGHT_GOAL_PERCENTAGE_DECIMAL_PLACES = Decimal("0.01")`
- **Immutable results** — `BodyWeightGoal` and `BodyWeightGoalProgressResult` are frozen, slotted dataclasses
- **Weight validation** — all supplied weights must be `Decimal` (bool/int/float/string/None rejected, no silent conversion), finite (NaN/Infinity rejected), within `[MIN, MAX]` inclusive; boundary validation occurs after `ROUND_HALF_UP` quantization to `BODY_WEIGHT_DECIMAL_PLACES`
- **Deterministic** — keyword-only functions, no system clock, no mutation, no randomness
- **Framework independence** — no imports of FastAPI/Starlette/Pydantic/SQLAlchemy/Alembic, no DB sessions, no HTTP status codes, no env access, no network/filesystem I/O
- **ORM/migration unchanged** — exactly 4 tables (`users`, `nutrition_profiles`, `nutrition_logs`, `body_weights`); exactly 4 Alembic revisions; head remains `e5f6a7b8c9d0`
- **Final verified test count** — 5164 backend tests pass (5071 baseline + 93 new body-weight-goal tests); ruff format and lint pass

### Phase 5D-4 — Body-Weight Goal Progress Final Audit, Hardening, and Freeze

- **Phase completed** — complete cross-layer final audit and freeze of the body-weight goal feature (Phase 5D-1 domain, Phase 5D-2 schemas, Phase 5D-3 API); no production defects were found, so no production code, ORM models, migrations, schemas, or dependencies were modified
- **Source-of-truth audit** — verified domain source, schemas, the API route, authentication, error envelope, ORM metadata, and the Alembic history directly (not prior reports)
- **Domain confirmed unchanged/correct** — enums, frozen+slotted dataclasses, Decimal-only ROUND_HALF_UP arithmetic, no float/system-clock/framework/DB/network/IO access; equal start/target raises the frozen `InvalidBodyWeightGoalProgressError`; no clamping/capping; negative/zero/100%/above-100% progress and negative remaining change preserved
- **Schema confirmed unchanged/correct** — `extra="forbid"`, `frozen=True`; bool/NaN/Infinity rejected; signed/percentage/remaining values not capped or clamped; domain enums reused and serialized lowercase; Decimal remains `Decimal` in Python and serializes as JSON strings; `from_result()` exact-copy with no recalculation/rounding/reclassification/mutation; success response `Literal[True]`, exact default message, required `data`; no `user_id`/ORM id/timestamps exposed
- **API orchestration confirmed correct** — exactly one GET `/api/v1/body-weights/goal-progress` route, declared before `/{entry_id}`, no request body or weight/user/date params; current-user-scoped profile + history lookups; `starting_weight_kg = profile.weight_kg`, `target_weight_kg = profile.target_weight_kg`, `current_weight_kg = history[0].weight_kg` (repository orders `logged_date desc, entry_id asc`); `calculate_body_weight_goal_progress(...)` and `BodyWeightGoalProgressData.from_result(...)` each called exactly once; no duplicated formula
- **Error/auth/privacy/read-only/transaction confirmed** — 401/403/404/422/500 contracts correct with `request_id`/`X-Request-ID`; `user_id` only from `current_user.id`; no cross-user leakage; no ORM object mutation; never commits/rolls back/flushes/refreshes/adds/deletes/merges; no persistence or profile synchronization; no goal ORM model/table/column
- **OpenAPI/ORM/migration confirmed** — goal-progress path documented (GET only, BearerAuth, correct schema); exactly 1 BearerAuth; exactly 4 ORM tables; exactly 4 linear migration revisions, one base, head `e5f6a7b8c9d0`
- **Phase boundaries preserved** — no goal persistence/dates/time-to-goal/predictions/recommendations/medical interpretation/AI/LLM/frontend
- **New tests** — `tests/test_phase_5d_final_audit.py` (32 tests) covering domain contracts, schema contracts, API route inventory, OpenAPI, ORM/migration integrity, application factory, and phase boundaries
- **Final verified test count** — 5450 backend tests pass (5418 Phase 5D-3 baseline + 32 new Phase 5D-4 audit tests); ruff format and lint pass; exactly 4 ORM tables; exactly 4 Alembic revisions; migration head `e5f6a7b8c9d0`; exactly 1 BearerAuth scheme; only `.env.example` template exists — no real secrets; Phase 5D is frozen and ready for the next explicitly approved phase
