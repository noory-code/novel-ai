"""Project path → Novel root resolution + HTTP port helpers.

Pure module: no I/O at import time, no asyncio, no Starlette. Every other
module in the package depends on ``resolve_plot_root``; isolating it keeps
the import graph flat.
"""

from __future__ import annotations

import logging
import os
import shutil
import socket
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mashbill.models import DirTreeNode, ProjectDoc

_log = logging.getLogger(__name__)

DEFAULT_HTTP_PORT = 5190

# --- Workspace discovery / directory-tree picker (v0.32.0, D-2026-05-31-L) ---
#
# Directories we never descend INTO during discovery / tree-building. ``.plot``
# is listed so we don't walk into a project's data folder, but it is still
# *read* as a marker (presence of ``<dir>/.plot/`` => a project directory).
# Any dotdir is also pruned (see ``_should_prune``).
PRUNE_DIRS: frozenset[str] = frozenset(
    {
        ".git",
        "node_modules",
        ".venv",
        "__pycache__",
        "dist",
        "build",
        ".plot",
        ".noory",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
    }
)
MAX_DISCOVERY_DEPTH = 8
MAX_DISCOVERY_PROJECTS = 500
MAX_TREE_DEPTH = 6
MAX_TREE_CHILDREN = 200


def _existing_data_root(directory: Path) -> Path | None:
    """The directory's Novel data root, if it has one: ``.noory/novel``,
    else the pre-rename ``.noory/plot`` or the legacy ``.plot`` (read-only
    peek — migration happens when the workspace is actually opened via
    ``resolve_plot_root``)."""
    novel = directory / ".noory" / "novel"
    if novel.is_dir():
        return novel
    noory_plot = directory / ".noory" / "plot"  # pre-2026-07-01 data-root name
    if noory_plot.is_dir():
        return noory_plot
    legacy = directory / ".plot"
    if legacy.is_dir():
        return legacy
    return None


def _should_prune(name: str) -> bool:
    """Dirs we never descend into: the explicit prune set + any dotdir."""
    return name in PRUNE_DIRS or name.startswith(".")


def enumerate_projects(plot_root: Path) -> list[ProjectDoc]:
    """Read the valid project(s) under a Novel data root, newest first.

    S2 (D-2026-06-21-AB): the canonical layout is **flat** — one project per
    root with ``project.json`` directly under it, so this returns a single-item
    list. The legacy nested ``{project_id}/`` scan is kept for un-migrated
    ``.plot`` roots (read-only discovery) and the forbidden stacking case a user
    hasn't reconciled, so those projects stay visible. The guard on
    ``create_project`` (D-2026-06-21-AA) is what keeps a *new* root single.

    Shared by ``projects_list_endpoint``, the ``list_projects`` MCP tool, and
    ``discover_projects`` (DRY — the scan loop used to be duplicated).
    """
    from mashbill.folder_io import read_project
    from mashbill.storage import _read_json

    out: list[ProjectDoc] = []
    if not plot_root.is_dir():
        return out
    # Flat layout: project.json sits directly under the root.
    flat = plot_root / "project.json"
    if flat.is_file():
        try:
            pid = _read_json(flat).get("id")
            if isinstance(pid, str):
                return [read_project(plot_root, pid)]
        except (FileNotFoundError, ValueError):
            pass
        return out
    # Legacy nested: one project per child dir.
    for child in sorted(plot_root.iterdir()):
        if not child.is_dir() or child.name == "sketches":
            continue
        try:
            out.append(read_project(plot_root, child.name))
        except (FileNotFoundError, ValueError):
            continue
    out.sort(key=lambda p: p.updated, reverse=True)
    return out


def discover_projects(workspace_root: Path) -> list[tuple[ProjectDoc, str]]:
    """Walk ``workspace_root`` for directories containing a ``.plot/`` and
    return ``(project, relative_dir)`` for every valid project, newest first.

    ``relative_dir`` is POSIX-relative to the workspace root (``"."`` for a
    root-level project). Heavy / dot directories are pruned from descent;
    depth and total count are capped. Symlinks are not followed.
    """
    root = Path(workspace_root).expanduser().resolve()
    results: list[tuple[ProjectDoc, str]] = []
    for current, dirs, _files in os.walk(root, followlinks=False):
        cur = Path(current)
        depth = len(cur.relative_to(root).parts)
        data_root = _existing_data_root(cur)
        if data_root is not None:
            rel = cur.relative_to(root).as_posix() or "."
            for proj in enumerate_projects(data_root):
                results.append((proj, rel))
            if len(results) >= MAX_DISCOVERY_PROJECTS:
                dirs[:] = []
                break
        if depth >= MAX_DISCOVERY_DEPTH:
            dirs[:] = []
        else:
            dirs[:] = sorted(d for d in dirs if not _should_prune(d))
    results.sort(key=lambda pr: pr[0].updated, reverse=True)
    return results


def build_dir_tree(workspace_root: Path, max_depth: int = MAX_TREE_DEPTH) -> DirTreeNode:
    """Build the nested directory tree for the new-project picker.

    Each node carries ``rel`` (POSIX-relative, ``"."`` for root) and
    ``has_plot``. Same prune set as discovery; depth + per-dir breadth capped.
    """
    from mashbill.models import DirTreeNode

    root = Path(workspace_root).expanduser().resolve()

    def node_for(path: Path, depth: int) -> DirTreeNode:
        rel = path.relative_to(root).as_posix() or "."
        children: list[DirTreeNode] = []
        if depth < max_depth:
            try:
                entries = sorted(
                    p for p in path.iterdir() if p.is_dir() and not _should_prune(p.name)
                )
            except OSError:
                entries = []
            for child in entries[:MAX_TREE_CHILDREN]:
                children.append(node_for(child, depth + 1))
        return DirTreeNode(
            name=path.name or rel,
            rel=rel,
            # v0.35.1 (D-2026-05-31-X) — "has_plot" means this dir holds a
            # REAL project, not merely that a ``.plot`` folder exists. A
            # stray read can leave an empty ``.plot`` behind; counting that
            # as a project made the picker label it "열기" and clicking it
            # landed in create() with nothing to open → a phantom new
            # project. ``enumerate_projects`` is the same validated scan the
            # sidebar uses, so has_plot now matches what is actually openable.
            has_plot=(lambda dr: dr is not None and len(enumerate_projects(dr)) > 0)(
                _existing_data_root(path)
            ),
            children=children,
        )

    return node_for(root, 0)


def create_workspace_dir(workspace_root: Path, rel: str) -> str:
    """Create a new directory at ``rel`` under the workspace root and return
    its POSIX-relative path.

    v0.37.0 (D-2026-05-31-AC) — backs the Add-a-Project picker's "new
    folder" affordance: a project can start in a subdirectory that does not
    exist yet (e.g. a fresh ``banana/`` in a monorepo). Path-safe via
    ``resolve_safe_path`` (rejects ``..`` / absolute / escaping). Idempotent
    (``exist_ok``) so re-creating an existing dir is a no-op.
    """
    from mashbill.file_io import resolve_safe_path

    root = Path(workspace_root).expanduser().resolve()
    target = resolve_safe_path(root, rel)
    target.mkdir(parents=True, exist_ok=True)
    return target.relative_to(root).as_posix()


def resolve_plot_root(project_path: str) -> Path:
    """Resolve ``{project_path}/.noory/plot/``, creating it on first access.

    R9 (D-2026-06-10-G): every plugin's per-project artifacts consolidate
    under ONE ``.noory/`` dotfolder (``.noory/plot/``, ``.noory/distill/``,
    …) so plugin mode and app mode share artifacts continuously. Each
    project lives at ``.noory/plot/{project_id}/``.

    A legacy pre-R9 ``.plot/`` root is migrated lazily on first access: one
    ``shutil.move`` (same volume, atomic-ish). If BOTH roots exist
    (half-migrated / user-restored), ``.noory/plot`` wins and ``.plot`` is
    left untouched for the user to reconcile — never merged blindly.

    Also performs the one-shot v0.59→v0.60 git-location migration (see
    :func:`migrate_legacy_git_to_workspace`): if the workspace was last
    opened under the design that put ``.git`` inside ``.noory/plot/``, the
    repo moves up to the workspace root — but only when no ``.git/`` is
    already there (the user could legitimately have their own).
    """
    base = Path(project_path).expanduser().resolve()
    if not base.exists():
        raise FileNotFoundError(f"project_path does not exist: {base}")
    if not base.is_dir():
        raise NotADirectoryError(f"project_path is not a directory: {base}")
    # D-2026-06-21-W — guard against double-nesting. If the caller passes a
    # path that ALREADY points at a ``.noory/plot`` data root (seen from MCP
    # callers — it created an orphaned project under
    # ``.noory/plot/.noory/plot/{id}``, invisible to discovery), use it
    # directly instead of appending another ``.noory/plot``. The workspace
    # root is then two levels up.
    if base.name in ("novel", "plot") and base.parent.name == ".noory":
        base.mkdir(parents=True, exist_ok=True)
        flatten_nested_project(base)
        migrate_legacy_git_to_workspace(base.parent.parent)
        return base
    root = base / ".noory" / "novel"
    legacy_plot = base / ".noory" / "plot"  # pre-2026-07-01 data-root name
    legacy_dotplot = base / ".plot"  # pre-R9 root
    if legacy_plot.is_dir() and not root.exists():
        root.parent.mkdir(exist_ok=True)
        shutil.move(str(legacy_plot), str(root))
        _log.info("migrated %s -> %s (plot->novel rename)", legacy_plot, root)
    elif legacy_dotplot.is_dir() and not root.exists():
        root.parent.mkdir(exist_ok=True)
        shutil.move(str(legacy_dotplot), str(root))
        _log.info("migrated legacy %s -> %s (R9)", legacy_dotplot, root)
    root.mkdir(parents=True, exist_ok=True)
    flatten_nested_project(root)
    migrate_legacy_git_to_workspace(base)
    return root


def flatten_nested_project(plot_root: Path) -> bool:
    """S2 (D-2026-06-21-AB): migrate a legacy nested ``{project_id}/`` project
    up to ``plot_root`` so one ``.noory/plot`` holds the project's files
    directly (one-project-per-dir, flat).

    Acts only when the root is **not already flat** (no ``project.json`` under
    it) AND holds **exactly one** nested project. The forbidden stacking case
    (multiple nested projects) is left untouched — auto-flattening would have to
    pick a winner; the user reconciles it (handoff S5). Returns True iff a
    project moved.
    """
    if (plot_root / "project.json").exists():
        return False  # already flat
    nested = [
        c
        for c in plot_root.iterdir()
        if c.is_dir() and c.name != "sketches" and (c / "project.json").is_file()
    ]
    if len(nested) != 1:
        return False
    src = nested[0]
    for item in src.iterdir():
        shutil.move(str(item), str(plot_root / item.name))
    src.rmdir()
    _log.info("flattened nested project %s -> %s (S2, D-2026-06-21-AB)", src, plot_root)
    return True


def workspace_root_from_plot_root(plot_root: Path) -> Path:
    """Recover the workspace root (= the user's opened folder) from the
    resolved Novel data root. ``plot_root`` is ``<workspace>/.noory/plot``;
    the user's workspace is two levels up.

    Used by endpoints that need to talk to git (which lives at the
    workspace root after D-2026-06-11-C/D), while still receiving the
    Novel data root from ``_require_plot_root``.
    """
    return plot_root.parent.parent


def migrate_legacy_git_to_workspace(workspace_root: Path) -> bool:
    """v0.59→v0.60 (D-2026-06-11-C/D): move ``.noory/plot/.git/`` up to
    the workspace root when it's safe.

    Safe = the workspace doesn't already have its own ``.git/``. If the
    user has their own repo at the workspace root, leave both alone:
    merging histories is the user's call, not Novel's. Returns True iff
    the repo moved.
    """
    legacy_git = workspace_root / ".noory" / "novel" / ".git"
    if not legacy_git.is_dir():
        # pre-2026-07-01 data-root name (resolve_plot_root normally renames the
        # whole dir to .noory/novel first, so this only fires if called direct)
        legacy_git = workspace_root / ".noory" / "plot" / ".git"
    new_git = workspace_root / ".git"
    if not legacy_git.is_dir():
        return False
    if new_git.exists():
        _log.warning(
            "legacy data-dir .git at %s left in place — workspace already "
            "has %s (user-owned)", legacy_git, new_git,
        )
        return False
    shutil.move(str(legacy_git), str(new_git))
    _log.info("migrated %s -> %s (workspace-git, D-2026-06-11-C)", legacy_git, new_git)
    return True


def resolved_port() -> int:
    """Read the HTTP port from ``MASHBILL_PORT`` with a safe fallback."""
    raw = os.environ.get("MASHBILL_PORT")
    if not raw:
        return DEFAULT_HTTP_PORT
    try:
        return int(raw)
    except ValueError:
        _log.warning("Invalid MASHBILL_PORT=%r; falling back to %d", raw, DEFAULT_HTTP_PORT)
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
