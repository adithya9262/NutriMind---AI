import re
from contextvars import ContextVar
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request

request_id_var: ContextVar[str] = ContextVar("request_id", default="")

_REQUEST_ID_PATTERN = re.compile(r"^[a-zA-Z0-9\-_.]+$")
_MAX_REQUEST_ID_LENGTH = 64


def get_request_id() -> str:
    return request_id_var.get()


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        req_id = request.headers.get("X-Request-ID", "")

        if (
            not req_id
            or len(req_id) > _MAX_REQUEST_ID_LENGTH
            or not _REQUEST_ID_PATTERN.match(req_id)
        ):
            req_id = uuid4().hex

        request_id_var.set(req_id)

        response = await call_next(request)
        response.headers["X-Request-ID"] = req_id

        return response
