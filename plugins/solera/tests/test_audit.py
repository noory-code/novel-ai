"""D2-2 — workspace audit: tree integrity across WorkItem files."""

from pathlib import Path

from solera.audit import audit_workspace
from solera.formats import Progress, WorkItem
from solera.planning import create_item
from solera.workspace import Workspace


def _ws(tmp_path: Path) -> Workspace:
    return Workspace(tmp_path / ".noory" / "solera")


def test_clean_tree_has_no_problems(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    story = create_item(ws, "story", "box")
    create_item(ws, "action", "step", gate="true", parent=story.id)
    ws.write_progress(Progress(item=None))
    assert audit_workspace(ws) == []


def test_flags_referenced_child_with_no_file(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    story = create_item(ws, "story", "box")
    create_item(ws, "action", "step", gate="true", parent=story.id)
    ws.item_path("ACT-001").unlink()  # remove file, keep the reference
    problems = audit_workspace(ws)
    assert any("ACT-001" in p.detail and p.kind == "missing-child" for p in problems)


def test_flags_multi_parent(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    leaf = create_item(ws, "action", "shared", gate="true")  # ACT-001
    s1 = create_item(ws, "story", "one")  # STORY-001
    s2 = create_item(ws, "story", "two")  # STORY-002
    ws.write_item(ws.load_item(s1.id).model_copy(update={"children": [leaf.id]}))
    ws.write_item(ws.load_item(s2.id).model_copy(update={"children": [leaf.id]}))
    assert any(p.kind == "multi-parent" for p in audit_workspace(ws))


def test_flags_cycle(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    a = WorkItem(id="A", level="epic", status="todo", children=["B"], goal="a")
    b = WorkItem(id="B", level="story", status="todo", children=["A"], goal="b")
    ws.write_item(a)
    ws.write_item(b)
    assert any(p.kind == "cycle" for p in audit_workspace(ws))


def test_flags_dangling_pointer(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    create_item(ws, "story", "box")
    ws.write_progress(Progress(item="ACT-404"))
    assert any("ACT-404" in p.detail for p in audit_workspace(ws))


def test_flags_malformed_item(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    ws.items_dir.mkdir(parents=True)
    ws.item_path("STORY-001").write_text("garbage, no frontmatter\n")
    assert any("STORY-001" in p.detail for p in audit_workspace(ws))
