"""Transport-isolation guards — the engine stays headless (open-core boundary).

Migration Phase B (D-2026-06-20-A). The adversarial verification of the
overhaul (TECH_REVIEW C2) confirmed the engine's 4-layer seam — pure domain ↓
MCP/HTTP adapters ↓ server composition — but flagged that **no automated test
pins it**, so a careless future import could silently couple the headless
engine to a transport library (or the MCP path to the viewer's HTTP stack)
without anything failing. These guards close that gap:

  1. The pure-domain modules import NO transport library (starlette / uvicorn /
     fastmcp) — verified in a fresh interpreter so transitive leaks are caught.
  2. The MCP adapter (``mcp_tools``) does not import the HTTP-for-viewer stack
     (``http_app`` / ``broadcast`` / ``watcher`` / ``api_endpoints``) — an
     MCP-only consumer must not drag in the viewer realtime stack. (It *does*
     pull starlette transitively via ``fastmcp``; that is the library's own
     dependency, not a Novel leak, so this guard is scoped to Novel modules.)
  3. The HTTP app builds with NO viewer dist present — the engine runs headless
     after the viewer leaves the repo (Phase C depends on this).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import mashbill.http_app as http_app_mod
from mashbill.http_app import create_http_app

_MCP_TOOLS = Path(http_app_mod.__file__).resolve().parent / "mcp_tools.py"

# The pure-domain layer (TECH_REVIEW: folder_io / models / git_store /
# edge_semantics + the per-area model modules).
# ``folder_io`` is a facade, so importing it transitively pulls storage /
# canvas_io / project_io / detail_sync too. (Per-node publish — node_publish /
# md_publish / propagation — retired in D-2026-06-22-H.)
_PURE_DOMAIN_MODULES = (
    "folder_io",
    "models",
    "git_store",
    "edge_semantics",
    "models_kinds",
    "models_foundation",
    "models_actors",
    "models_composition",
    "models_union",
    "models_canvas",
)

_TRANSPORT_LIBS = ("starlette", "uvicorn", "fastmcp")

# The HTTP-for-viewer stack the MCP adapter must not import.
_HTTP_FOR_VIEWER = ("http_app", "broadcast", "watcher", "api_endpoints")


def test_pure_domain_modules_dont_leak_transport() -> None:
    """Importing the pure-domain layer in a FRESH interpreter must not pull
    any transport library into ``sys.modules`` (incl. transitively). A future
    ``import starlette`` in ``folder_io`` would break the headless boundary —
    this catches it."""
    imports = "; ".join(f"import mashbill.{m}" for m in _PURE_DOMAIN_MODULES)
    code = (
        "import sys; "
        f"{imports}; "
        f"leaked=sorted(t for t in {_TRANSPORT_LIBS!r} "
        "if any(k==t or k.startswith(t+'.') for k in sys.modules)); "
        "print(','.join(leaked)); "
        "sys.exit(1 if leaked else 0)"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        "pure-domain modules leaked a transport import "
        f"({result.stdout.strip()!r}) — the engine must stay headless. "
        f"stderr: {result.stderr.strip()}"
    )


def test_mcp_adapter_does_not_import_http_for_viewer_stack() -> None:
    """``mcp_tools`` (the MCP adapter) must not import the viewer's HTTP/realtime
    stack — the MCP-only path stays independent of the browser transport."""
    src = _MCP_TOOLS.read_text(encoding="utf-8")
    offenders = [
        mod
        for mod in _HTTP_FOR_VIEWER
        if f"from mashbill.{mod} import" in src
        or f"import mashbill.{mod}" in src
    ]
    assert not offenders, (
        f"mcp_tools.py imports the HTTP-for-viewer stack {offenders} — "
        "the MCP adapter must not depend on the browser transport."
    )


def test_http_app_builds_without_viewer_dist(monkeypatch) -> None:  # noqa: ANN001
    """The engine builds its HTTP app even when no viewer dist exists, mounting
    only ``/api`` + ``/ws`` (no static ``/`` mount). This is the headless path
    the bundle / post-split engine relies on (Phase C)."""
    monkeypatch.setattr(http_app_mod, "find_viewer_dist", lambda: None)
    app = create_http_app()
    paths = {getattr(r, "path", None) for r in app.routes}
    assert "/api/health" in paths, "API surface must exist headless"
    # No catch-all static mount at "/" when there is no viewer dist.
    mount_paths = {getattr(r, "path", None) for r in app.routes if r.__class__.__name__ == "Mount"}
    assert "/" not in mount_paths, "must not mount a static viewer when dist is absent"
