"""Engine auth seam (D-2026-06-12-F + TABLET_ARCH §지금 만들 것).

The seam:
  * If the env var ``MASHBILL_AUTH_TOKEN`` is **unset**, the engine accepts
    every request — same as v0.64.x. This keeps the dev workflow
    (``uv run mashbill-http`` + ``npm run dev`` in a regular browser at
    ``:5193``) friction-free.
  * If it's **set**, every ``/api/*`` request needs ``Authorization:
    Bearer <token>`` and every WS connection needs ``?auth=<token>``.
    Bundled Tauri builds will mint a random token at startup, pass it to
    the engine's env, and surface it to the viewer via a ``#[tauri::command]``
    so the viewer can attach the header on every fetch / WS.

Why env-gated instead of always-on: TABLET_ARCH §"지금 만들 것" pins the
*pre-wiring* — "오늘은 no-op/loopback, ``Authorization`` 헤더 배선만". A
hard-required token would break the dev loop and force every contributor to
juggle env vars; an env-gated check ships the wiring today and turns
enforcement on automatically the moment the bundled shell sets the variable.

The constant-time comparison (``hmac.compare_digest``) blocks timing-based
token guessing; even on loopback it's cheap insurance against an attacker
with same-machine code execution.
"""

from __future__ import annotations

import hmac
import os
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

# Env var name. Centralised so the Tauri shell + bundled docs + this module
# all reference one string instead of three drifting copies.
ENV_VAR = "MASHBILL_AUTH_TOKEN"

# Query parameter the WS handshake reads when env enforcement is on. Kept
# distinct from ``project_path`` so a viewer that forgets to attach the
# token gets a clear 1008 close, not a confusing 400.
WS_TOKEN_PARAM = "auth"

_BEARER_PREFIX = "Bearer "

# Endpoints that don't carry app secrets and must remain callable without a
# token. Keep tiny:
#   - ``/api/health`` — the Tauri shell probes it before injecting the token.
#   - ``/api/debug`` — the dev-only introspection channel (registered ONLY under
#     MASHBILL_DEBUG=1; in-memory, localhost). The viewer's debug probe POSTs
#     snapshots with a plain fetch and the agent GETs them, neither carrying the
#     per-launch token; the auth seam (added after the channel) must not break
#     it. Harmless in release builds — the route isn't registered there
#     (D-2026-06-23-C).
_OPEN_PATHS: frozenset[str] = frozenset({"/api/health", "/api/debug"})


def configured_token() -> str | None:
    """Return the live token, or ``None`` when enforcement is disabled.

    Reads ``os.environ`` on every call (not cached) so a test fixture that
    monkey-patches the env after import still takes effect.
    """
    raw = os.environ.get(ENV_VAR, "").strip()
    return raw or None


def is_authorized(presented: str | None, expected: str | None) -> bool:
    """Constant-time compare. ``expected is None`` → auth disabled → allow."""
    if expected is None:
        return True
    if presented is None:
        return False
    return hmac.compare_digest(presented, expected)


def extract_bearer(authorization_header: str | None) -> str | None:
    """Pull the bearer token out of an ``Authorization`` header, or ``None``.

    Tolerant of leading whitespace / case-insensitive scheme so a misbehaving
    proxy that title-cases ``bearer`` doesn't break enforcement.
    """
    if not authorization_header:
        return None
    s = authorization_header.strip()
    if not s.lower().startswith(_BEARER_PREFIX.lower()):
        return None
    return s[len(_BEARER_PREFIX) :].strip() or None


class AuthMiddleware(BaseHTTPMiddleware):
    """Gate every ``/api/*`` request behind the configured token.

    Behaviour matrix::

        env unset         → every request passes through (dev parity)
        env set, no hdr   → 401 {"error": "auth token required"}
        env set, bad tok  → 401 {"error": "invalid auth token"}
        env set, good tok → continue to the route handler
        path in OPEN_PATHS → continue regardless (health probe)
        non /api path     → continue (covers ``/ws`` — checked in the handler
                            because middleware can't run on WebSocketRoute)
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        expected = configured_token()
        if expected is None:
            return await call_next(request)
        path = request.url.path
        if not path.startswith("/api/"):
            return await call_next(request)
        if path in _OPEN_PATHS:
            return await call_next(request)
        presented = extract_bearer(request.headers.get("authorization"))
        if presented is None:
            return JSONResponse({"error": "auth token required"}, status_code=401)
        if not is_authorized(presented, expected):
            return JSONResponse({"error": "invalid auth token"}, status_code=401)
        return await call_next(request)


def build_auth_middleware() -> AuthMiddleware | None:
    """Factory used by ``http_app.create_http_app``.

    Returns ``None`` when the env says auth is off so the middleware stack
    stays a no-op cost. (BaseHTTPMiddleware adds latency even on the
    pass-through path; skipping it when we don't need it is the
    "dev parity" guarantee.)
    """
    if configured_token() is None:
        return None
    # Starlette wants the *class* + kwargs via ``Middleware(...)`` when added
    # at construction time; for app.add_middleware the instance shape works.
    # We return a marker that ``create_http_app`` checks; the real wiring
    # happens there to keep this module pure (no Starlette ``Middleware``
    # import here so unit tests don't drag Starlette in).
    # Simpler: return the class itself. Caller wraps it in ``Middleware``.
    raise NotImplementedError(  # pragma: no cover — never called
        "build_auth_middleware is a marker; create_http_app wires the class"
    )


# Tiny ASGI fixture for the WS handler — it can't ride the HTTP middleware
# because Starlette's ``BaseHTTPMiddleware`` only sees HTTP scopes. The
# WebSocketRoute checks the query param directly via ``check_ws_token``.


def check_ws_token(presented_query_value: str | None) -> bool:
    """``True`` when the WS connection may proceed."""
    return is_authorized(presented_query_value, configured_token())


# Re-export for ``http_app`` so it doesn't import the class directly.
__all__ = [
    "AuthMiddleware",
    "ENV_VAR",
    "WS_TOKEN_PARAM",
    "check_ws_token",
    "configured_token",
    "extract_bearer",
    "is_authorized",
]


def _unused(_app: ASGIApp) -> None:
    """Keep the ``ASGIApp`` import warm so mypy doesn't complain when the
    middleware class is the only consumer (mypy strict + unused-import).
    """
