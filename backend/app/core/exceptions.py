import logging

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .middleware import get_request_id

logger = logging.getLogger(__name__)


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    request_id = get_request_id() or "-"
    errors = exc.errors()
    sanitized_errors: list[dict[str, object]] = []
    for err in errors:
        clean: dict[str, object] = {}
        for k, v in err.items():
            if k == "input":
                continue
            if k == "ctx":
                clean[k] = str(v)
            else:
                clean[k] = v
        sanitized_errors.append(clean)
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed.",
                "request_id": request_id,
                "details": sanitized_errors,
            },
        },
        headers={"X-Request-ID": request_id},
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    request_id = get_request_id() or "-"
    headers = dict(exc.headers or {})
    headers["X-Request-ID"] = request_id
    if isinstance(exc.detail, dict):
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.detail,
            headers=headers,
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=headers,
    )


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = get_request_id() or "-"
    logger.exception(
        "Unhandled exception",
        extra={"request_id": request_id},
    )
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred.",
                "request_id": request_id,
            },
        },
        headers={"X-Request-ID": request_id},
    )
