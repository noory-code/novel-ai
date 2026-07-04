"""Viewer-context rendezvous store (D-2026-06-15-D).

The HTTP sidecar (which the viewer POSTs to) and the external agent's
``--mcp-stdio`` process are SEPARATE processes that share only the filesystem
(D-2026-06-14-A). So the viewer's live context is exchanged through a small
JSON file at a deterministic, ``plot_root``-keyed path under the OS temp dir.
These tests pin the write/read contract + liveness (timestamp TTL on a shared
machine clock).
"""

from __future__ import annotations

from pathlib import Path

from starlette.testclient import TestClient

from mashbill.broadcast import BroadcastHub
from mashbill.http_app import create_http_app
from mashbill.viewer_context import (
    TTL_SECONDS,
    read_viewer_context,
    write_viewer_context,
)
from mashbill.workspace import resolve_plot_root

_SEL = [{"id": "n1", "kind": "core_value", "label": "Trust"}]


def test_write_then_read_returns_fresh_context(tmp_path: Path) -> None:
    plot_root = tmp_path / "proj"
    plot_root.mkdir()
    base = tmp_path / "rt"
    base.mkdir()
    write_viewer_context(plot_root, scope="foundation", selection=_SEL, now=1000.0, base_dir=base)
    ctx = read_viewer_context(plot_root, now=1001.0, base_dir=base)
    assert ctx["active_canvas"] == "foundation"
    assert ctx["selection"] == _SEL
    assert ctx["has_viewer"] is True
    assert ctx["stale"] is False
    assert ctx["updated_at"] == 1000.0
    assert "Discovery" in ctx["framing"]  # framing carries the canvas playbook


def test_framing_carries_full_coaching_system_prompt(tmp_path: Path) -> None:
    """MCP-path parity (Phase 3): the external agent sees the same system prompt
    the in-app path uses — guard + tone + the canvas's coaching playbook — not a
    bare one-liner (D-2026-06-19-F: the primary path must not be context-poorer
    than in-app)."""
    plot_root = tmp_path / "proj"
    plot_root.mkdir()
    base = tmp_path / "rt"
    base.mkdir()
    write_viewer_context(plot_root, scope="services", selection=_SEL, now=1000.0, base_dir=base)
    ctx = read_viewer_context(plot_root, now=1001.0, base_dir=base)
    framing = ctx["framing"]
    assert "Never invent project details" in framing  # the hallucination guard
    assert "without it" in framing.lower()  # the Services JTBD playbook


def test_read_missing_file_is_empty_and_stale(tmp_path: Path) -> None:
    plot_root = tmp_path / "proj"
    plot_root.mkdir()
    base = tmp_path / "rt"
    base.mkdir()
    ctx = read_viewer_context(plot_root, now=1.0, base_dir=base)
    assert ctx["has_viewer"] is False
    assert ctx["stale"] is True
    assert ctx["active_canvas"] is None
    assert ctx["selection"] == []
    assert ctx["framing"] == ""


def test_read_past_ttl_is_stale_and_empty_but_reports_age(tmp_path: Path) -> None:
    plot_root = tmp_path / "proj"
    plot_root.mkdir()
    base = tmp_path / "rt"
    base.mkdir()
    write_viewer_context(plot_root, scope="actors", selection=_SEL, now=1000.0, base_dir=base)
    ctx = read_viewer_context(plot_root, now=1000.0 + TTL_SECONDS + 1, base_dir=base)
    assert ctx["stale"] is True
    assert ctx["has_viewer"] is False
    assert ctx["active_canvas"] is None
    assert ctx["selection"] == []
    assert ctx["updated_at"] == 1000.0  # age still surfaced


def test_last_write_wins(tmp_path: Path) -> None:
    plot_root = tmp_path / "proj"
    plot_root.mkdir()
    base = tmp_path / "rt"
    base.mkdir()
    write_viewer_context(plot_root, scope="foundation", selection=[], now=1000.0, base_dir=base)
    write_viewer_context(plot_root, scope="services", selection=_SEL, now=1005.0, base_dir=base)
    ctx = read_viewer_context(plot_root, now=1006.0, base_dir=base)
    assert ctx["active_canvas"] == "services"
    assert ctx["selection"] == _SEL
    assert ctx["updated_at"] == 1005.0


def test_distinct_projects_dont_collide(tmp_path: Path) -> None:
    a = tmp_path / "a"
    a.mkdir()
    b = tmp_path / "b"
    b.mkdir()
    base = tmp_path / "rt"
    base.mkdir()
    write_viewer_context(a, scope="foundation", selection=[], now=1.0, base_dir=base)
    write_viewer_context(b, scope="actors", selection=[], now=1.0, base_dir=base)
    assert read_viewer_context(a, now=1.0, base_dir=base)["active_canvas"] == "foundation"
    assert read_viewer_context(b, now=1.0, base_dir=base)["active_canvas"] == "actors"


def test_feature_scope_framing(tmp_path: Path) -> None:
    plot_root = tmp_path / "proj"
    plot_root.mkdir()
    base = tmp_path / "rt"
    base.mkdir()
    write_viewer_context(plot_root, scope="feature:svc_1", selection=[], now=1.0, base_dir=base)
    ctx = read_viewer_context(plot_root, now=1.0, base_dir=base)
    assert ctx["active_canvas"] == "feature:svc_1"
    assert "Execution" in ctx["framing"]


# --- POST /api/viewer/context endpoint (writes to the default OS temp) -------


def _client() -> TestClient:
    return TestClient(create_http_app(hub=BroadcastHub(enable_watchers=False)))


def test_post_records_context(tmp_path: Path) -> None:
    client = _client()
    resp = client.post(
        "/api/viewer/context",
        json={
            "project_path": str(tmp_path),
            "scope": "foundation",
            "selection": _SEL,
        },
    )
    assert resp.status_code == 202
    # Read it back through the default-temp path the MCP tool will use.
    import time

    ctx = read_viewer_context(resolve_plot_root(str(tmp_path)), now=time.time())
    assert ctx["active_canvas"] == "foundation"
    assert ctx["selection"] == _SEL
    assert ctx["has_viewer"] is True


def test_post_requires_project_path() -> None:
    resp = _client().post("/api/viewer/context", json={"scope": "foundation"})
    assert resp.status_code == 400
    assert "project_path" in resp.json()["error"]


def test_post_rejects_invalid_scope(tmp_path: Path) -> None:
    resp = _client().post(
        "/api/viewer/context",
        json={"project_path": str(tmp_path), "scope": "bogus"},
    )
    assert resp.status_code == 400
    assert "scope" in resp.json()["error"]


def test_post_sanitizes_malformed_selection(tmp_path: Path) -> None:
    import time

    resp = _client().post(
        "/api/viewer/context",
        json={
            "project_path": str(tmp_path),
            "scope": "actors",
            "selection": "not-a-list",
        },
    )
    assert resp.status_code == 202
    ctx = read_viewer_context(resolve_plot_root(str(tmp_path)), now=time.time())
    assert ctx["selection"] == []  # malformed dropped, no crash


# --- get_viewer_context MCP tool (end-to-end POST → tool) -------------------


def test_mcp_tool_reads_what_the_viewer_posted(tmp_path: Path) -> None:
    from mashbill.mcp_tools import get_viewer_context

    _client().post(
        "/api/viewer/context",
        json={
            "project_path": str(tmp_path),
            "scope": "feature:svc_9",
            "selection": _SEL,
        },
    )
    ctx = get_viewer_context(str(tmp_path))
    assert ctx["active_canvas"] == "feature:svc_9"
    assert ctx["selection"] == _SEL
    assert ctx["has_viewer"] is True
    assert "Execution" in ctx["framing"]


def test_mcp_tool_empty_when_no_viewer(tmp_path: Path) -> None:
    from mashbill.mcp_tools import get_viewer_context

    # A fresh project nobody has reported on → no live context.
    ctx = get_viewer_context(str(tmp_path))
    assert ctx["has_viewer"] is False
    assert ctx["active_canvas"] is None
    assert ctx["selection"] == []
