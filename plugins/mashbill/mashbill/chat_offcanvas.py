"""Tell the person what a coach turn added to a canvas they are not on.

The in-app coach writes through its own MCP process, so the engine learns what a
turn changed only from the files. :func:`attach_offcanvas_additions` reads every
canvas's node ids before the turn, reads them again when the turn ends, and
attaches the nodes added outside the conversation's own canvas to the terminal
event as ``added_elsewhere`` (D-2026-10-15-A). The chat layer streams and saves
that field with the reply; the viewer shows it under the reply.
"""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator
from pathlib import Path

from mashbill.chat_providers.base import CanvasAddition, ChatStreamEvent
from mashbill.storage import _project_dir

_log = logging.getLogger(__name__)

_PRIMARY_CANVASES = ("foundation", "actors", "services", "entities")
_TERMINAL_TYPES = frozenset({"turn_complete", "error"})
# Labels named in the notice; the rest are counted.
LABELS_SHOWN = 3

# Canvas key → {node id: label}. ``None`` marks a canvas file that exists but
# could not be read, so its nodes can never be told apart from new ones.
NodeSnapshot = dict[str, dict[str, str] | None]


def own_canvas(scope: str) -> str | None:
    """The canvas a conversation scope is held on, or ``None`` for ``project``.

    ``service:<id>`` is a thread about one service on the Services canvas;
    ``feature:<id>`` is the feature's flow canvas. The project thread belongs to
    no canvas.
    """
    base, separator, scope_id = scope.partition(":")
    if base == "service" and scope_id:
        return "services"
    if base == "feature" and scope_id:
        return scope
    if base in _PRIMARY_CANVASES and not separator:
        return base
    return None


def _read_nodes(path: Path) -> dict[str, str] | None:
    """Node ids and labels from a canvas's semantic file, without migrating it.

    ``read_canvas`` heals old files on read and writes them back; this picture
    must never change the files it compares. A missing file is an empty canvas.
    """
    if not path.is_file():
        return {}
    try:
        nodes = json.loads(path.read_text(encoding="utf-8"))["nodes"]
    except (OSError, ValueError, KeyError, TypeError):
        return None
    if not isinstance(nodes, list):
        return None
    picture: dict[str, str] = {}
    for node in nodes:
        if isinstance(node, dict) and isinstance(node.get("id"), str):
            label = node.get("label")
            picture[node["id"]] = label.strip() if isinstance(label, str) else ""
    return picture


def snapshot_nodes(plot_root: Path, project_id: str) -> NodeSnapshot:
    """Every canvas's nodes: the four primary canvases, then each feature canvas."""
    folder = _project_dir(plot_root, project_id)
    picture: NodeSnapshot = {
        kind: _read_nodes(folder / kind / "canvas.json") for kind in _PRIMARY_CANVASES
    }
    for detail in sorted((folder / "services").glob("*/detail.json")):
        if detail.parent.name != "_archive":
            picture[f"feature:{detail.parent.name}"] = _read_nodes(detail)
    return picture


def additions_elsewhere(
    before: NodeSnapshot, after: NodeSnapshot, scope: str
) -> list[CanvasAddition]:
    """Nodes in ``after`` and not in ``before``, outside ``scope``'s own canvas.

    A canvas created during the turn counts from empty. A canvas unreadable on
    either side is left out. A feature canvas's root node shares the feature's id:
    it is the copy seeded when the feature was added to Services, not a node of
    its own, so it is never counted.
    """
    own = own_canvas(scope)
    found: list[CanvasAddition] = []
    for canvas, nodes in after.items():
        prior = before.get(canvas, {})
        if canvas == own or nodes is None or prior is None:
            continue
        root = canvas.partition(":")[2] if canvas.startswith("feature:") else None
        added = [(node_id, label) for node_id, label in nodes.items() if node_id not in prior]
        added = [(node_id, label) for node_id, label in added if node_id != root]
        if not added:
            continue
        found.append(
            CanvasAddition(
                canvas=canvas,
                count=len(added),
                labels=[label for _, label in added if label][:LABELS_SHOWN],
                canvas_label=(nodes.get(root) or None) if root else None,
            )
        )
    return found


def _snapshot_or_none(plot_root: Path, project_id: str | None) -> NodeSnapshot | None:
    if not project_id:
        return None
    try:
        return snapshot_nodes(plot_root, project_id)
    except Exception:  # noqa: BLE001 — the notice must not break the turn
        _log.exception("canvas snapshot failed for %s", plot_root)
        return None


async def attach_offcanvas_additions(
    events: AsyncIterator[ChatStreamEvent],
    plot_root: Path,
    project_id: str | None,
    scope: str,
) -> AsyncIterator[ChatStreamEvent]:
    """Pass events through; set ``added_elsewhere`` on the turn's terminal event.

    The before-picture is taken when this generator is first pulled, which is
    before the wrapped provider spawns its CLI.
    """
    before = _snapshot_or_none(plot_root, project_id)
    async for event in events:
        if before is not None and project_id and event.type in _TERMINAL_TYPES:
            try:
                added = additions_elsewhere(before, snapshot_nodes(plot_root, project_id), scope)
            except Exception:  # noqa: BLE001 — the notice must not break the reply
                _log.exception("canvas additions failed for %s", scope)
                added = []
            if added:
                event = event.model_copy(update={"added_elsewhere": added})
        yield event
