"""Project path → Solera root resolution, plus HTTP port helpers.

Everything in this module is pure: no I/O, no asyncio, no Starlette. The
reason to isolate it is that almost every other module in the package needs
``resolve_solera_root``, and the port helpers are used both by the entry
point and by the HTTP app factory; keeping them here avoids pulling in
Starlette/uvicorn whenever a caller only needs ``resolve_solera_root``.
"""

from __future__ import annotations

import logging
import os
import socket
from pathlib import Path

_log = logging.getLogger(__name__)

DEFAULT_HTTP_PORT = 5170


def resolve_solera_root(project_path: str) -> Path:
    """Resolve the Solera workspace root directory under a project path.

    Resolution order (Solera v4):
      1. ``{project_path}/.solera/`` — v4 location (preferred).
      2. ``{project_path}/workspace/`` — v3 location, accepted with a
         DeprecationWarning. To be removed in solera-map v0.2.0.
      3. ``{project_path}/`` itself — last-ditch fallback for callers that
         already point at the workspace dir (any name).

    A directory qualifies as a Solera workspace if it contains either
    ``concepts/`` or ``identity/``. Raises ``FileNotFoundError`` otherwise.
    """
    base = Path(project_path).expanduser().resolve()
    candidates: list[tuple[Path, str | None]] = [
        (base / ".solera", None),
        (base / "workspace", "v3"),
        (base, None),
    ]
    for candidate, deprecation_label in candidates:
        if (candidate / "concepts").exists() or (candidate / "identity").exists():
            if deprecation_label == "v3":
                _log.warning(
                    "Reading from legacy %s layout at %s. Run "
                    "`solera-migrate-workspace-to-dotsolera` to relocate to .solera/. "
                    "solera-map v0.2.0 will drop this fallback.",
                    deprecation_label,
                    candidate,
                )
            return candidate
    raise FileNotFoundError(
        f"No Solera workspace found under {project_path!r} "
        "(looked for `.solera/`, `workspace/`, and bare directory)"
    )


# Deprecated alias kept for one minor version so external callers / tests
# updating in lockstep don't break. Internal call sites use
# `resolve_solera_root` directly.
resolve_workspace = resolve_solera_root


def resolved_port() -> int:
    """Read the HTTP port from ``SOLERA_MAP_PORT`` with a safe fallback."""
    raw = os.environ.get("SOLERA_MAP_PORT")
    if not raw:
        return DEFAULT_HTTP_PORT
    try:
        return int(raw)
    except ValueError:
        _log.warning("Invalid SOLERA_MAP_PORT=%r; falling back to %d", raw, DEFAULT_HTTP_PORT)
        return DEFAULT_HTTP_PORT


def port_is_free(port: int) -> bool:
    """Best-effort check for whether ``port`` is currently bindable on loopback."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.bind(("127.0.0.1", port))
        except OSError:
            return False
    return True


def find_viewer_dist() -> Path | None:
    """Locate ``viewer/dist/`` produced by Vite.

    Plugin runtime path: ``${CLAUDE_PLUGIN_ROOT}/viewer/dist``.
    Dev path: walk up from this file until we find ``viewer/dist/index.html``.
    """
    env = os.environ.get("CLAUDE_PLUGIN_ROOT")
    if env:
        candidate = Path(env) / "viewer" / "dist"
        if (candidate / "index.html").exists():
            return candidate
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "viewer" / "dist"
        if (candidate / "index.html").exists():
            return candidate
    return None
