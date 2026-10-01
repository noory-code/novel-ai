"""Environment-gated authentication for Solera's HTTP and WebSocket surfaces."""

from __future__ import annotations

import hmac
import os
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

ENV_VAR = "SOLERA_AUTH_TOKEN"
WS_TOKEN_PARAM = "auth"
_BEARER_PREFIX = "Bearer "


def configured_token() -> str | None:
    """Read the live auth token; blank or missing disables authentication."""
    raw = os.environ.get(ENV_VAR, "").strip()
    return raw or None


def is_authorized(presented: str | None, expected: str | None) -> bool:
    """Compare a presented token in constant time, or allow when auth is disabled."""
    if expected is None:
        return True
    if presented is None:
        return False
    return hmac.compare_digest(presented, expected)


def extract_bearer(authorization_header: str | None) -> str | None:
    """Extract a bearer token using a case-insensitive scheme."""
    if not authorization_header:
        return None
    value = authorization_header.strip()
    if not value.lower().startswith(_BEARER_PREFIX.lower()):
        return None
    return value[len(_BEARER_PREFIX) :].strip() or None


class AuthMiddleware(BaseHTTPMiddleware):
    """Require the configured bearer token for API routes except health."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        expected = configured_token()
        if expected is None or (request.method == "GET" and request.url.path == "/api/health"):
            return await call_next(request)
        if not request.url.path.startswith("/api/"):
            return await call_next(request)
        presented = extract_bearer(request.headers.get("authorization"))
        if presented is None:
            return JSONResponse({"error": "auth token required"}, status_code=401)
        if not is_authorized(presented, expected):
            return JSONResponse({"error": "invalid auth token"}, status_code=401)
        return await call_next(request)


def check_ws_token(presented: str | None) -> bool:
    """Return whether a WebSocket query token satisfies the live setting."""
    return is_authorized(presented, configured_token())
