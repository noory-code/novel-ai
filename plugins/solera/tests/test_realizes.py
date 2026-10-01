"""`realizes` — the connective tissue between a work item and the format F
element it builds (INT-f). A leaf declares which stable slug(s) it realizes; the
ID-diff on re-publish then knows which work goes stale.
"""

from __future__ import annotations

from pathlib import Path

from solera.planning import create_item
from solera.supervisor import ready_leaves
from solera.workspace import Workspace


def _ws(tmp_path: Path) -> Workspace:
    return Workspace(tmp_path / ".noory" / "solera")


def test_realizes_roundtrips(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    root = create_item(ws, "story", "Ship auth")
    leaf = create_item(
        ws,
        "action",
        "Build login",
        gate="true",
        parent=root.id,
        realizes=["feature/login"],
    )
    assert ws.load_item(leaf.id).realizes == ["feature/login"]


def test_realizes_defaults_empty_and_back_compat(tmp_path: Path) -> None:
    """An item authored without `realizes` (older files) still parses, as []."""
    ws = _ws(tmp_path)
    leaf = create_item(ws, "action", "No link", gate="true")
    assert ws.load_item(leaf.id).realizes == []


def test_duplicate_realizes_in_existing_item_still_loads_and_is_ready(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    ws.items_dir.mkdir(parents=True)
    ws.item_path("ACT-001").write_text(
        """\
---
level: action
status: todo
gate: "true"
children: []
realizes:
- feature/login
- feature/login
---
Build login.
"""
    )

    assert ws.load_item("ACT-001").realizes == ["feature/login", "feature/login"]
    assert ready_leaves(ws) == (["ACT-001"], [])
