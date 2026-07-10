"""Re-pin (INT-f) — on a re-publish, map the format F ID-diff onto the work
items that realize the changed/removed slugs. Proposal is deterministic and
read-only; the human approves, then `reopen_items` mutates. (04-pipeline:
ID-diff *proposes* stale, a person approves before reopening.)
"""

from __future__ import annotations

from pathlib import Path

from solera.planning import create_item
from solera.repin import propose_repin, reopen_items
from solera.workspace import Workspace


def _ws(tmp_path: Path) -> Workspace:
    return Workspace(tmp_path / ".noory" / "solera")


def test_propose_repin_maps_diff_to_realizing_items(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    a = create_item(ws, "action", "A", gate="true", realizes=["feature/login"])
    create_item(ws, "action", "B", gate="true", realizes=["service/auth"])
    c = create_item(ws, "action", "C", gate="true", realizes=["entity/old"])

    old = [
        {"id": "feature/login", "hash": "a"},
        {"id": "service/auth", "hash": "b"},
        {"id": "entity/old", "hash": "c"},
    ]
    new = [
        {"id": "feature/login", "hash": "AAA"},  # changed
        {"id": "service/auth", "hash": "b"},  # unchanged
        # entity/old removed
    ]
    prop = propose_repin(ws, old, new)
    assert prop["stale"] == [a.id]  # realizes a changed slug
    assert prop["escalate"] == [c.id]  # realizes a removed slug
    # item B (unchanged slug) is left alone — progress is not lost


def test_reopen_items_sets_done_back_to_todo(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    leaf = create_item(ws, "action", "A", gate="true", realizes=["feature/login"])
    ws.write_item(ws.load_item(leaf.id).model_copy(update={"status": "done"}))
    reopen_items(ws, [leaf.id])
    assert ws.load_item(leaf.id).status == "todo"


def test_reopen_invalidates_done_ancestors(tmp_path: Path) -> None:
    """Reopening a leaf must break its ancestors' `done` rollup — a container is
    `done` only when all its children are done (the rollup invariant). Else a
    parent reads `done` with reopened work under it (pipeline-dogfood finding)."""
    from solera.supervisor import complete, start_next

    ws = _ws(tmp_path)
    story = create_item(ws, "story", "S")
    leaf = create_item(
        ws, "action", "A", gate="true", realizes=["feature/login"], parent=story.id
    )
    start_next(ws)
    assert complete(ws, leaf.id, cwd=tmp_path).passed is True
    assert ws.load_item(story.id).status == "done"  # rollup marked the parent done

    reopen_items(ws, [leaf.id])
    assert ws.load_item(leaf.id).status == "todo"
    assert ws.load_item(story.id).status != "done"  # ancestor invalidated
