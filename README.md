# NutriMind AI

NutriMind AI is a nutrition and wellness application with a Next.js frontend and a
FastAPI backend. It provides food and weight diaries, nutrition goals, tasks, food search
and recognition, reports, and an AI Coach with chat history and user-scoped memory.

## Architecture

- **Frontend:** Next.js App Router, React, TypeScript, Supabase Auth and `@supabase/ssr`.
- **Backend:** FastAPI, async SQLAlchemy, PostgreSQL, and Alembic.
- **Authentication:** Supabase manages browser sessions. Middleware validates protected
  page sessions with Supabase Auth; API requests still require a bearer token verified by
  the backend. Local email/password auth routes remain deprecated backend compatibility
  endpoints and are not used by the frontend.
- **Persistence:** 10 ORM tables and 13 Alembic revisions at this revision. The latest
  revision adds a unique nullable Supabase identity link to `users`; existing accounts
  are not backfilled automatically.
- **External services:** Supabase Auth, optional Gemini/Groq AI, USDA FoodData Central,
  and Open Food Facts.

## Local setup

1. Configure PostgreSQL and apply migrations with `alembic upgrade head` from `backend/`.
   Use an isolated development database; do not point local commands at production.
2. Copy `backend/.env.example` to `backend/.env` and set the database URL, strong JWT
   secrets, and Supabase URL/anon key/JWT secret. See `backend/README.md`.
3. Install backend dependencies with `python -m pip install -e '.[dev]'` from `backend/`.
   Start the API with `uvicorn app.main:app --reload`.
4. Copy `frontend/.env.example` to `frontend/.env.local`, set the frontend API URL and
   Supabase public URL/anon key, then run `npm ci` and `npm run dev` from `frontend/`.

The frontend uses Supabase SSR cookies so Supabase can refresh sessions. The browser SDK
must access those cookies; they are `Secure` in production and `SameSite=Lax`, but are not
`HttpOnly`. XSS prevention remains necessary. Backend APIs do not authenticate from
cookies and continue to require an `Authorization: Bearer` header.

## Checks

- Backend: `pytest` and `ruff check app tests` from `backend/`.
- Frontend: `npm test`, `npm run type-check`, `npm run lint`, and `npm run build` from
  `frontend/`.

Test and build status is not asserted here; run the relevant checks in the environment
being prepared for deployment.
