"""Dev-only debug channel (D-2026-06-09-D).

The viewer POSTs a screen snapshot (theme, per-node computed colours, layout
rects, watermark presence, …) to ``/api/debug``; an external agent (Claude
Code) GETs it to verify what it cannot observe directly — CDP tools
(chrome-devtools, Playwright) cannot attach to the Tauri **WKWebView** on
macOS, and ``tauri-driver`` does not support macOS. This channel is the
introspection bridge in their place.

In-memory only (cleared on restart), localhost-bound like the rest of the
engine, and NOT part of the product surface — it holds whatever the viewer's
debug mode chooses to send.
"""

from __future__ import annotations

from typing import Any

from starlette.requests import Request
from starlette.responses import JSONResponse

# Single latest snapshot. The viewer overwrites it on each probe; the agent
# reads the most recent screen state. Keyed so future probes (e.g. named
# captures) can extend without breaking the `latest` contract.
_DEBUG_STORE: dict[str, Any] = {}


def reset_debug_store() -> None:
    """Clear the in-memory snapshot (tests + fresh sessions)."""
    _DEBUG_STORE.clear()


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
