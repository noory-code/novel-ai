"""D2-2 — planning: create WorkItems at any altitude, decompose into children."""

from pathlib import Path

from solera.planning import create_item, next_item_id
from solera.workspace import Workspace


def _ws(tmp_path: Path) -> Workspace:
    return Workspace(tmp_path / ".noory" / "solera")


def test_next_item_id_is_level_prefixed(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    assert next_item_id(ws, "initiative") == "INIT-001"
    assert next_item_id(ws, "epic") == "EPIC-001"
    assert next_item_id(ws, "story") == "STORY-001"
    assert next_item_id(ws, "action") == "ACT-001"


def test_next_item_id_falls_back_for_custom_level(tmp_path: Path) -> None:
    assert next_item_id(_ws(tmp_path), "theme") == "THEME-001"


def test_create_root_item_is_compliant(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    item = create_item(ws, "story", "Ship the thing.")
    assert item.id == "STORY-001"
    assert item.status == "todo"
    assert item.children == []
    assert ws.load_item("STORY-001") == item  # parses back unchanged


def test_create_leaf_with_gate(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    leaf = create_item(ws, "action", "Create out.txt", gate="test -f out.txt")
    assert leaf.is_leaf is True
    assert leaf.gate == "test -f out.txt"


def test_create_child_appends_to_parent(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    story = create_item(ws, "story", "box")
    a1 = create_item(ws, "action", "one", gate="true", parent=story.id)
    a2 = create_item(ws, "action", "two", gate="true", parent=story.id)
    assert ws.load_item(story.id).children == [a1.id, a2.id]
    assert a1.id == "ACT-001" and a2.id == "ACT-002"


def test_ids_increment_per_level(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    create_item(ws, "story", "a")
    create_item(ws, "story", "b")
    assert next_item_id(ws, "story") == "STORY-003"
    assert next_item_id(ws, "action") == "ACT-001"  # independent per level
