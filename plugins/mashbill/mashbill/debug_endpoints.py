"""Dev-only debug channel (D-2026-06-09-D).

Two directions over one flavor gate:

*Read* — the viewer POSTs a screen snapshot (theme, per-node computed colours,
layout rects, watermark presence, …) to ``/api/debug``; an external agent
(Claude Code) GETs it to verify what it cannot observe directly.

*Drive* — the agent POSTs a snippet to ``/api/debug/command`` and blocks; the
viewer polls the same path, runs the snippet, and POSTs the value back to
``/api/debug/result``, which releases the blocked ask. Without this the app can
only be driven by a person's hands.

Both exist because CDP tools (chrome-devtools, Playwright) cannot attach to the
Tauri **WKWebView** on macOS, and ``tauri-driver`` does not support macOS.

In-memory only (cleared on restart), localhost-bound like the rest of the
engine, and NOT part of the product surface. The drive half runs arbitrary
script inside the app, so it lives behind the same registration gate as the
rest: ``http_app`` adds these routes only under ``MASHBILL_DEBUG=1``, which the
shell sets only when the debug feature is compiled in. A release build has no
route and the release bundle has no runner.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any

from starlette.requests import Request
from starlette.responses import JSONResponse

# Single latest snapshot. The viewer overwrites it on each probe; the agent
# reads the most recent screen state. Keyed so future probes (e.g. named
# captures) can extend without breaking the `latest` contract.
_DEBUG_STORE: dict[str, Any] = {}

# --- drive half -------------------------------------------------------------
# One command in flight at a time. Concurrency here would buy nothing (a single
# agent drives a single window) and would cost the guarantee that a refused
# command is visible: a queue that silently reorders is worse than a 409.
_PENDING: dict[str, Any] | None = None
_RESULTS: dict[int, dict[str, Any]] = {}
_WAITERS: dict[int, asyncio.Event] = {}
# When the viewer last asked for work. A bare timeout cannot tell "the app was
# never running" from "the snippet hung"; this does.
_LAST_POLL_AT: float | None = None
# Every screen that has asked for work, by the id it gave itself. More than one
# can be open at once (a stale tab beside a fresh one), and an answer that does
# not name its screen reads as one screen contradicting itself.
_PAGES: dict[str, dict[str, Any]] = {}
# Set when a command is waiting to be taken. A screen may hold its request open
# on this instead of asking again on a timer — macOS slows timers in a window
# that sits behind another one, and the viewer's loop stopped for 11 minutes
# that way (O-00000066).
# Made on first use, not at import: an Event binds to the loop it was created
# on, and the app is built fresh per test / per run.
_ARRIVED: asyncio.Event | None = None
_ARRIVED_LOOP: asyncio.AbstractEventLoop | None = None
_NEXT_ID = 1

DEFAULT_COMMAND_TIMEOUT_MS = 10_000


def _arrived() -> asyncio.Event:
    """The "a command is waiting" flag, bound to the loop now running."""
    global _ARRIVED, _ARRIVED_LOOP
    loop = asyncio.get_running_loop()
    if _ARRIVED is None or _ARRIVED_LOOP is not loop:
        _ARRIVED = asyncio.Event()
        _ARRIVED_LOOP = loop
    return _ARRIVED


def reset_debug_store() -> None:
    """Clear the in-memory snapshot and any in-flight command (tests + fresh sessions)."""
    global _PENDING, _LAST_POLL_AT, _NEXT_ID, _ARRIVED
    _DEBUG_STORE.clear()
    _PENDING = None
    _RESULTS.clear()
    _WAITERS.clear()
    _PAGES.clear()
    _ARRIVED = None
    _LAST_POLL_AT = None
    _NEXT_ID = 1


async def debug_post_endpoint(request: Request) -> JSONResponse:
    """Store the viewer's latest screen snapshot."""
    try:
        payload = await request.json()
    except ValueError:
        return JSONResponse({"error": "invalid json"}, status_code=400)
    _DEBUG_STORE["latest"] = payload
    return JSONResponse({"ok": True})


async def debug_get_endpoint(request: Request) -> JSONResponse:
    """Return the latest snapshot (``{}`` before the first POST)."""
    return JSONResponse(dict(_DEBUG_STORE))


async def debug_command_post_endpoint(request: Request) -> JSONResponse:
    """Agent side: hand the running app a snippet and wait for its value.

    Blocks until the viewer answers or ``timeout_ms`` elapses, so the caller
    needs one request instead of a post-then-poll dance.
    """
    global _PENDING, _NEXT_ID
    try:
        payload = await request.json()
    except ValueError:
        return JSONResponse({"error": "invalid json"}, status_code=400)
    script = payload.get("script")
    if not isinstance(script, str) or not script.strip():
        return JSONResponse({"error": "script required"}, status_code=400)
    if _PENDING is not None:
        return JSONResponse(
            {"error": "a command is already waiting", "id": _PENDING["id"]},
            status_code=409,
        )

    command_id = _NEXT_ID
    _NEXT_ID += 1
    waiter = asyncio.Event()
    _WAITERS[command_id] = waiter
    _PENDING = {"id": command_id, "script": script}
    wanted = payload.get("page")
    if isinstance(wanted, str) and wanted:
        _PENDING["page"] = wanted
    _arrived().set()

    def give_up() -> None:
        """Unarm this command. Runs however the ask ends — timeout, or the
        asker disappearing (its own deadline, a dropped connection). Cleanup
        used to live only on the timeout path, so a cancelled ask left the
        command armed forever and every later ask got 409 until the engine was
        restarted."""
        global _PENDING
        if _PENDING is not None and _PENDING["id"] == command_id:
            _PENDING = None
            _arrived().clear()
        _WAITERS.pop(command_id, None)

    timeout_ms = payload.get("timeout_ms", DEFAULT_COMMAND_TIMEOUT_MS)
    try:
        await asyncio.wait_for(waiter.wait(), float(timeout_ms) / 1000)
    except TimeoutError:
        give_up()
        _RESULTS.pop(command_id, None)
        # Speak about the screen this command named, not about any screen. A
        # screen stays on the list after it closes, so borrowing another
        # screen's check-in would report a departed screen as a live one whose
        # snippet hung — backwards from what this field is for.
        if isinstance(wanted, str) and wanted:
            last_poll_at = _PAGES.get(wanted, {}).get("last_poll_at")
        else:
            last_poll_at = _LAST_POLL_AT
        return JSONResponse(
            {"id": command_id, "error": "timeout", "last_poll_at": last_poll_at},
            status_code=504,
        )
    except asyncio.CancelledError:
        give_up()
        _RESULTS.pop(command_id, None)
        raise

    _WAITERS.pop(command_id, None)
    result = _RESULTS.pop(command_id, {})
    return JSONResponse({"id": command_id, **result})


async def debug_command_get_endpoint(request: Request) -> JSONResponse:
    """Viewer side: take the waiting command, or ``{}`` when there is none.

    A screen identifies itself in the query so the answer can name it and so a
    command aimed at one screen is not taken by another.
    """
    global _PENDING, _LAST_POLL_AT
    _LAST_POLL_AT = time.time()
    page = request.query_params.get("page")
    wait_ms = request.query_params.get("wait_ms")
    if wait_ms and _PENDING is None:
        try:
            await asyncio.wait_for(_arrived().wait(), float(wait_ms) / 1000)
        except (TimeoutError, ValueError):
            pass
    if page:
        _PAGES[page] = {
            "id": page,
            "title": request.query_params.get("title", ""),
            "url": request.query_params.get("url", ""),
            "last_poll_at": _LAST_POLL_AT,
        }
    if _PENDING is None:
        return JSONResponse({})
    wanted = _PENDING.get("page")
    if wanted is not None and wanted != page:
        return JSONResponse({})
    taken = _PENDING
    _PENDING = None
    _arrived().clear()
    return JSONResponse(taken)


async def debug_pages_endpoint(request: Request) -> JSONResponse:
    """Which screens have asked for work, newest check-in first.

    A screen that closes cannot say so, so it stays here. ``seen_ago_s`` is how
    the caller tells a live screen from a departed one — a screen polls every
    quarter second, so anything past a second or two is gone.
    """
    now = time.time()
    pages = [
        {**p, "seen_ago_s": round(now - p["last_poll_at"], 1)}
        for p in sorted(_PAGES.values(), key=lambda p: p["last_poll_at"], reverse=True)
    ]
    return JSONResponse({"pages": pages})


async def debug_result_post_endpoint(request: Request) -> JSONResponse:
    """Viewer side: report what the snippet returned, or how it failed."""
    try:
        payload = await request.json()
    except ValueError:
        return JSONResponse({"error": "invalid json"}, status_code=400)
    command_id = payload.get("id")
    waiter = _WAITERS.get(command_id) if isinstance(command_id, int) else None
    if waiter is None:
        return JSONResponse({"error": "no one is waiting for this id"}, status_code=404)
    _RESULTS[command_id] = {k: payload[k] for k in ("ok", "value", "error") if k in payload}
    if isinstance(payload.get("page"), str):
        _RESULTS[command_id]["from"] = payload["page"]
    waiter.set()
    return JSONResponse({"ok": True})
