"""D-2026-06-09-D — dev-only debug channel for WKWebView introspection.

The viewer POSTs a screen snapshot (theme, per-node computed colours, layout
rects, watermark presence) to ``/api/debug``; an external agent GETs it to
verify what it cannot see directly (CDP tools can't attach to the Tauri
WKWebView on macOS). In-memory, not part of the product surface.
"""

from __future__ import annotations

import pytest
from starlette.testclient import TestClient

from mashbill.broadcast import BroadcastHub
from mashbill.debug_endpoints import reset_debug_store
from mashbill.http_app import create_http_app


@pytest.fixture(autouse=True)
def _enable_debug(monkeypatch: pytest.MonkeyPatch) -> None:
    """The debug channel is flavor-gated: routes exist only when MASHBILL_DEBUG=1
    (set by the shell's debug flavor when spawning the sidecar)."""
    monkeypatch.setenv("MASHBILL_DEBUG", "1")


def _client() -> TestClient:
    return TestClient(create_http_app(hub=BroadcastHub(enable_watchers=False)))


def test_debug_routes_absent_without_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    """Release flavor (no MASHBILL_DEBUG): the debug surface must not exist."""
    monkeypatch.delenv("MASHBILL_DEBUG", raising=False)
    client = _client()
    assert client.get("/api/debug").status_code == 404
    # 405 when the viewer-dist StaticFiles mount swallows the path — either
    # way the debug handler is not registered.
    assert client.post("/api/debug", json={"x": 1}).status_code in (404, 405)


def test_debug_store_empty_initially() -> None:
    reset_debug_store()
    r = _client().get("/api/debug")
    assert r.status_code == 200
    assert r.json() == {}


def test_debug_post_then_get_roundtrip() -> None:
    reset_debug_store()
    client = _client()
    snap = {
        "theme": "dark",
        "watermark": False,
        "nodes": [{"id": "a", "fg": "rgb(15, 23, 42)", "rect": {"w": 150, "h": 150}}],
    }
    pr = client.post("/api/debug", json=snap)
    assert pr.status_code == 200
    r = client.get("/api/debug")
    assert r.json()["latest"] == snap


def test_debug_post_overwrites_latest() -> None:
    reset_debug_store()
    client = _client()
    client.post("/api/debug", json={"v": 1})
    client.post("/api/debug", json={"v": 2})
    assert _client().get("/api/debug").json()["latest"] == {"v": 2}


def test_debug_post_rejects_invalid_json() -> None:
    reset_debug_store()
    r = _client().post(
        "/api/debug", content=b"not json", headers={"content-type": "application/json"}
    )
    assert r.status_code == 400
