import re
from contextvars import ContextVar
from uuid import uuid4

from starlette.types import ASGIApp, Message, Receive, Scope, Send

request_id_var: ContextVar[str] = ContextVar("request_id", default="")

_REQUEST_ID_PATTERN = re.compile(r"^[a-zA-Z0-9\-_.]+$")
_MAX_REQUEST_ID_LENGTH = 64


def get_request_id() -> str:
    return request_id_var.get()


class RequestIDMiddleware:
    """Pure ASGI middleware avoids task-group response hangs in BaseHTTPMiddleware."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = {key.lower(): value for key, value in scope.get("headers", [])}
        raw_request_id = headers.get(b"x-request-id", b"")
        req_id = raw_request_id.decode("latin-1")

        if (
            not req_id
            or len(req_id) > _MAX_REQUEST_ID_LENGTH
            or not _REQUEST_ID_PATTERN.match(req_id)
        ):
            req_id = uuid4().hex

        scope.setdefault("state", {})["request_id"] = req_id
        token = request_id_var.set(req_id)

        async def send_with_request_id(message: Message) -> None:
            if message["type"] == "http.response.start":
                response_headers = [
                    (name, value)
                    for name, value in message.get("headers", [])
                    if name.lower() != b"x-request-id"
                ]
                response_headers.append((b"x-request-id", req_id.encode("latin-1")))
                message = {**message, "headers": response_headers}
            await send(message)

        try:
            await self.app(scope, receive, send_with_request_id)
        finally:
            request_id_var.reset(token)
