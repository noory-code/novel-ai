"""Create a lightweight upstream master from a downstream reference (D-2026-06-19-C).

A service / feature reference to an actor / core_value / identity is
**pick-OR-create**: when no existing master matches, a real master node is
created on its HOME canvas — name only, flagged incomplete, deepened later by the
home-canvas coach (mission/core_value = D-2026-06-16-K/L, etc.) — instead of
free-typing (which D-2026-06-17-B bans). This module is the single home for two
facts: which canvas owns each referenceable master kind, and how a fresh one is
positioned so it doesn't stack on the anchor.
"""

from __future__ import annotations

from pathlib import Path

from mashbill.canvas_io import create_node
from mashbill.models_canvas import CanvasKind

# Referenceable master kind → its home canvas (the SSOT for where each master
# lives). Actors own ``actor``; Foundation owns ``core_value`` + ``identity``.
_MASTER_HOME: dict[str, CanvasKind] = {
    "actor": "actors",
    "core_value": "foundation",
    "identity": "foundation",
}


def create_master(plot_root: Path, project_id: str, kind: str, label: str) -> str:
    """Create a lightweight master node of ``kind`` on its home canvas; return id.

    A thin reference-flow wrapper over :func:`mashbill.canvas_io.create_node` (the
    single SSOT for node creation, D-2026-06-27-B): it resolves *which* canvas
    owns the master kind and delegates the actual append. ``kind`` must be one of
    ``actor`` / ``core_value`` / ``identity`` (the referenceable masters);
    anything else raises ``ValueError``. ``label`` is the master's name and must
    be non-blank. The node carries only its label (deep typed fields stay empty —
    filled later by the home-canvas coach), so it reads as incomplete until then.
    The id is minted server-side.
    """
    if kind not in _MASTER_HOME:
        raise ValueError(f"not a referenceable master kind: {kind!r}")
    name = label.strip()
    if not name:
        raise ValueError("master label required")
    home = _MASTER_HOME[kind]
    out = create_node(plot_root, project_id, home, kind, {"label": name})
    return str(out["node"]["id"])
