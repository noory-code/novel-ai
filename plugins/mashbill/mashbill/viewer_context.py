"""Viewer-context rendezvous store (D-2026-06-15-D).

Gives the external agent (the user's CLI on the ``--mcp-stdio`` process) the
same canvas context the in-app chat has — current active canvas + node
selection + per-canvas framing. The MCP process and the HTTP sidecar are
SEPARATE processes (D-2026-06-14-A) sharing only the filesystem, so the context
is exchanged through a small JSON file at a deterministic, ``plot_root``-keyed
path under the OS temp dir.

  * The HTTP process writes on ``POST /api/viewer/context`` (one debounced
    ``App`` effect + a heartbeat).
  * The MCP process reads in ``get_viewer_context``.

Both run on the same machine, so a server-stamped ``updated_at`` and the
reader's ``time.time()`` share one clock — a report older than ``TTL_SECONDS``
is stale. The heartbeat keeps an idle-but-open viewer fresh, so ``stale`` /
absent ⇒ "no live viewer" and the agent never treats stale context as current.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

from mashbill.chat_context import build_system_prompt

# A report older than this (server clock vs reader clock — same machine) counts
# as stale. The viewer heartbeat (~30s) keeps an open viewer well inside it.
TTL_SECONDS = 90.0

# The controls the viewer reports land in every coach turn's context, so their
# number and length stay bounded. Each group (canvas buttons, tabs, the buttons
# outside the canvas) is capped on its own.
CONTROLS_CAP = 24
CONTROL_LABEL_CAP = 60

_FILE_PREFIX = "mashbill-viewer-context-"


def _empty(updated_at: float | None = None) -> dict[str, Any]:
    """The 'no live context' shape — the agent must not treat this as current."""
    return {
        "active_canvas": None,
        "selection": [],
        "controls": [],
        "tabs": [],
        "page_controls": [],
        "framing": "",
        "updated_at": updated_at,
        "stale": True,
        "has_viewer": False,
    }


def _context_path(plot_root: Path, base_dir: Path | None) -> Path:
    base = base_dir if base_dir is not None else Path(tempfile.gettempdir())
    key = hashlib.sha256(str(plot_root.resolve()).encode("utf-8")).hexdigest()[:16]
    return base / f"{_FILE_PREFIX}{key}.json"


def sanitize_controls(raw: Any) -> list[str]:
    """Keep the distinct, non-empty control labels, trimmed and capped."""
    if not isinstance(raw, list):
        return []
    labels: list[str] = []
    for item in raw:
        if not isinstance(item, str):
            continue
        label = " ".join(item.split())[:CONTROL_LABEL_CAP]
        if label and label not in labels:
            labels.append(label)
    return labels[:CONTROLS_CAP]


def write_viewer_context(
    plot_root: Path,
    *,
    scope: str,
    selection: list[dict[str, Any]],
    now: float,
    controls: list[str] | None = None,
    tabs: list[str] | None = None,
    page_controls: list[str] | None = None,
    base_dir: Path | None = None,
) -> None:
    """Atomically record the viewer's latest context for ``plot_root``.

    ``controls`` are the labels of the buttons on the canvas, ``tabs`` the
    canvas tabs, and ``page_controls`` the buttons outside the canvas (beside
    the tabs, in an open panel); the viewer owns their wording.
    Last-writer-wins: the temp-file + ``os.replace`` swap means a reader never
    sees a half-written file, and the most recent write is what the agent reads.
    """
    path = _context_path(plot_root, base_dir)
    payload = {
        "scope": scope,
        "selection": selection,
        "controls": sanitize_controls(controls),
        "tabs": sanitize_controls(tabs),
        "page_controls": sanitize_controls(page_controls),
        "updated_at": now,
    }
    tmp = path.parent / f"{path.name}.{os.getpid()}.tmp"
    tmp.write_text(json.dumps(payload), encoding="utf-8")
    os.replace(tmp, path)


def read_viewer_context(
    plot_root: Path,
    *,
    now: float,
    ttl: float = TTL_SECONDS,
    base_dir: Path | None = None,
) -> dict[str, Any]:
    """Read the viewer's latest context for ``plot_root``.

    Returns the live ``{active_canvas, selection, controls, tabs,
    page_controls, framing, updated_at, stale: False, has_viewer: True}`` when a
    fresh report exists; otherwise the empty / stale shape (carrying
    ``updated_at`` when a stale report's age is known). A report without one of
    the control groups (an older viewer, a harness without a screen) reads as
    none of that group.
    """
    path = _context_path(plot_root, base_dir)
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        return _empty()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return _empty()
    if not isinstance(data, dict):
        return _empty()

    updated_at = data.get("updated_at")
    if not isinstance(updated_at, (int, float)):
        return _empty()
    if now - updated_at > ttl:
        return _empty(updated_at=float(updated_at))

    scope = data.get("scope")
    selection = data.get("selection")
    if not isinstance(scope, str) or not isinstance(selection, list):
        return _empty()

    return {
        "active_canvas": scope,
        "selection": selection,
        "controls": sanitize_controls(data.get("controls")),
        "tabs": sanitize_controls(data.get("tabs")),
        "page_controls": sanitize_controls(data.get("page_controls")),
        # MCP-path parity (Phase 3): hand the external agent the SAME system
        # prompt the in-app path uses — guard + coach tone + the canvas's
        # coaching playbook — so the primary path is never context-poorer than
        # in-app (D-2026-06-19-F).
        "framing": build_system_prompt(scope),
        "updated_at": float(updated_at),
        "stale": False,
        "has_viewer": True,
    }
