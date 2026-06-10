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
import shutil
import socket
from pathlib import Path

_log = logging.getLogger(__name__)

DEFAULT_HTTP_PORT = 5170

LEGACY_DIRNAME = ".solera"
NEW_RELATIVE = Path(".noory") / "solera"
# Ignore ONLY our subtree. ``.noory/`` is SHARED with sibling plugins whose
# artifacts are source-of-truth data (plot canvases) — a blanket
# ``.noory/`` ignore would silently untrack them (evonest v1.1.1 incident).
GITIGNORE_ENTRY = ".noory/solera/"


def _carry_gitignore_intent(project: Path) -> None:
    """A project that ignored ``.solera/`` must keep ignoring the data after
    the move — otherwise the next blanket ``git add`` silently tracks runtime
    data. Only appends when the user had the legacy entry; never invents
    ignore policy for projects that tracked their data on purpose."""
    gitignore = project / ".gitignore"
    if not gitignore.is_file():
        return
    content = gitignore.read_text(encoding="utf-8")
    if LEGACY_DIRNAME + "/" in content and GITIGNORE_ENTRY not in content:
        with open(gitignore, "a", encoding="utf-8") as f:
            f.write(f"\n# Solera workspace data (R9 location)\n{GITIGNORE_ENTRY}\n")


def resolve_solera_root(project_path: str) -> Path:
    """Resolve the Solera workspace root directory under a project path.

    Resolution order:
      1. ``{project_path}/.noory/solera/`` — R9 location (preferred).
         If a legacy ``.solera/`` exists and the new root does not, the
         legacy dir is lazily migrated here (one ``shutil.move``, same
         volume). When BOTH roots exist (half-migrated / user-restored),
         the new root wins and the legacy dir is preserved for the user to
         reconcile — never merged blindly.
      2. ``{project_path}/.solera/`` — pre-R9 location, accepted only if
         migration above did not happen (won't be reached on the happy path
         because step 1 moves it). Kept as a defensive fallback.
      3. ``{project_path}/workspace/`` — v3 location, accepted with a
         DeprecationWarning. To be removed in solera-map v0.2.0.
      4. ``{project_path}/`` itself — last-ditch fallback for callers that
         already point at the workspace dir (any name).

    A directory qualifies as a Solera workspace if it contains either
    ``concepts/`` or ``identity/``. Raises ``FileNotFoundError`` otherwise.
    """
    base = Path(project_path).expanduser().resolve()
    new_root = base / NEW_RELATIVE
    legacy = base / LEGACY_DIRNAME
    if legacy.is_dir() and not new_root.exists():
        new_root.parent.mkdir(exist_ok=True)
        shutil.move(str(legacy), str(new_root))
        _carry_gitignore_intent(base)
        _log.info("migrated legacy %s -> %s (R9)", legacy, new_root)

    candidates: list[tuple[Path, str | None]] = [
        (new_root, None),
        (legacy, None),
        (base / "workspace", "v3"),
        (base, None),
    ]
    for candidate, deprecation_label in candidates:
        if (candidate / "concepts").exists() or (candidate / "identity").exists():
            if deprecation_label == "v3":
                _log.warning(
                    "Reading from legacy %s layout at %s. Run "
                    "`solera-migrate-workspace-to-dotsolera` to relocate to "
                    ".noory/solera/. solera-map v0.2.0 will drop this fallback.",
                    deprecation_label,
                    candidate,
                )
            return candidate.resolve()
    raise FileNotFoundError(
        f"No Solera workspace found under {project_path!r} "
        "(looked for `.noory/solera/`, `.solera/`, `workspace/`, and bare directory)"
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
