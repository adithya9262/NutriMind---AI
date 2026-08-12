from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from .api.v1.router import router as api_v1_router
from .core.config import Settings
from .core.exceptions import (
    global_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from .core.logging import setup_logging
from .core.middleware import RequestIDMiddleware
from .db.session import db_manager


def create_app(settings: Settings | None = None) -> FastAPI:
    if settings is None:
        settings = Settings()

    setup_logging(settings=settings)

    @asynccontextmanager
    async def _lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        if settings.DATABASE_URL:
            db_manager.initialize(settings.DATABASE_URL)
        yield
        await db_manager.dispose()

    app = FastAPI(
        title=settings.APP_NAME,
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=_lifespan,
    )

    cors_origins = settings.cors_origins_list

    cors_kwargs = {
        "allow_origins": cors_origins,
        "allow_credentials": True,
        "allow_methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        "allow_headers": ["*", "Authorization", "Content-Type", "X-Request-ID", "Content-Disposition"],
        "expose_headers": ["X-Request-ID", "Content-Disposition", "Authorization"],
    }

    if settings.APP_ENV == "development":
        cors_kwargs["allow_origin_regex"] = r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"

    app.add_middleware(CORSMiddleware, **cors_kwargs)

    app.add_middleware(RequestIDMiddleware)

    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, global_exception_handler)

    app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)

    @app.get("/")
    async def root():
        return {
            "name": settings.APP_NAME,
            "status": "running",
            "docs": "/docs",
        }

    return app


app = create_app()

