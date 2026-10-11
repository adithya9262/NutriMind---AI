# NutriMind AI Backend

FastAPI API for NutriMind AI. The backend uses async SQLAlchemy with PostgreSQL and
Alembic migrations. Its routers cover authentication, nutrition profiles and logs, body
weight, goals, tasks, food search and recognition, AI Coach, reports, and settings.

## Requirements and setup

- Python 3.11 or newer.
- PostgreSQL for application data and migration/runtime verification.
- Supabase project URL, anon key, and JWT secret for Supabase authentication.
- Optional Gemini/Groq and USDA API keys for provider-backed features.

Create a local virtual environment, then install `python -m pip install -e '.[dev]'`.
Copy `.env.example` to `.env` and configure the values below. Never commit `.env` or use a
production database for development checks.

| Setting | Purpose |
|---|---|
| `DATABASE_URL` | Async PostgreSQL connection string (`postgresql+asyncpg://...`) |
| `JWT_SECRET_KEY` | Backend access-token signing key; use a random secret of at least 32 characters |
| `REFRESH_TOKEN_SECRET_KEY` | Separate strong secret required in production configuration |
| `SUPABASE_URL`, `SUPABASE_ANON_KEY` | Supabase Auth user verification |
| `SUPABASE_JWT_SECRET` | Optional local verification of Supabase HS256 access tokens |
| `CORS_ORIGINS` | Comma-separated frontend origins |
| `GEMINI_API_KEY`, `GROQ_API_KEY`, `USDA_API_KEY` | Optional provider credentials |

Supabase account linking requires an Auth user response with `email_confirmed_at`; an
unverified identity is rejected. A migration adds `users.supabase_user_id` with a unique
index so a Supabase identity cannot silently change its linked local account. Existing
rows remain unlinked until a verified identity is explicitly synchronized.

## Run and migrate

From this directory:

```bash
alembic upgrade head
uvicorn app.main:app --reload
```

The API is mounted under `/api/v1`; health is available at `/api/v1/health`. The current
source defines 10 ORM tables and 13 Alembic revisions. No migration runs automatically
when the application starts.

## Tests and lint

```bash
pytest
ruff check app tests
ruff format --check app tests
```

Tests that require PostgreSQL or external Supabase/provider services need isolated test
configuration. Do not point test settings at production services or user data. Passing
unit tests alone does not verify database migrations, Supabase configuration, or provider
integrations end to end.
